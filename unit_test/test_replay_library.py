import asyncio
import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from threading import Event
from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer
from engine import Engine
from engine.device.web.server.server import GameServer
from engine.device.web.server.server_get import REPLAY_FOLDERS
from engine.device.manager.base import AskOptionPayload
from engine.lib import Json
from engine.log import Log
from engine.user.user_info import UserInfo
from game.scene import Scene, SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


class TestReplayLibrary(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()

    def run_game(self, scene, devices, *, load_type="New"):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(scene, devices, load_type=load_type)
        errors.assert_not_called()
        warnings.assert_not_called()
        return game

    def play_game(self, *, complete=False):
        scene = SceneLoader.NewScene("rhino", None, ["spider_man"], 122)
        # Record real damage and villain advancement through both stages.
        commands = iter(['villains[0].TakeDamage(hero, 100, DebugRule(hero))'] * 2)

        def choose(prompt):
            if prompt.event_name == "WhenPlayerInTurn":
                command = next(commands, None) if complete else None
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, Engine.game.world)
                return CommandDescriptor()
            return (CommandDescriptor() if prompt.show_cancel
                    else HeadlessDeviceManager._DefaultChoice(prompt))

        devices = HeadlessDeviceManager(choice_provider=choose)
        return self.run_game(scene, devices), devices

    async def client_for(self, game, devices):
        devices.AddSize = lambda *_args: None
        server = GameServer(devices)
        self.enterContext(patch.object(server, "IsAuthenticate", return_value=True))
        self.enterContext(patch.object(server, "IsVersionMatch", return_value=True))
        client = TestClient(TestServer(server.web_app))
        await client.start_server()
        self.addAsyncCleanup(client.close)
        return client

    async def test_completed_game_saves_full_history_is_listed_and_replays_to_victory(self):
        game, devices = self.play_game(complete=True)
        self.assertTrue(game.world.game_over.players_won)
        self.assertGreater(len(game.controller_manager.replay.history_inputs), len(game.scene.inputs))
        client = await self.client_for(game, devices)
        with TemporaryDirectory() as folder, patch.object(REPLAY_FOLDERS, "value", [folder]), patch.object(UserInfo, "fingerprint", "replay-test", create=True):
            response = await client.post('/save_local')
            self.assertEqual(response.status, 200)
            saved_path = Path((await response.json())["path"])
            self.assertEqual(saved_path.parent, Path(folder))
            saved, checksum = Json.LoadAsInternal(str(saved_path), Scene, check_sum="Restrict")
            self.assertEqual(checksum, "Ok")
            self.assertEqual(saved.seed, 122)
            self.assertEqual(len(saved.inputs), len(game.controller_manager.replay.history_inputs))
            self.assertTrue(saved.metadata["replay_complete"])
            self.assertEqual(game.scene.inputs, [])
            library_response = await client.get('/list_replay_files')
            self.assertEqual(library_response.headers['Cache-Control'], 'no-store')
            listing = await library_response.json()
            self.assertIn(str(saved_path).replace('\\', '/'), listing)
            summary = await (await client.get('/get_replay_json?' + str(saved_path).replace('\\', '/'))).json()
            self.assertEqual(summary["step"], len(saved.inputs))
            self.assertTrue(summary["replay_complete"])
            replay_devices = HeadlessDeviceManager()
            replayed = self.run_game(saved, replay_devices, load_type="InTesting")
            self.assertTrue(replayed.world.game_over.players_won)
            self.assertEqual(replayed.controller_manager.replay.replay_step_id, len(saved.inputs))
            self.assertIsNone(replay_devices.stopped_prompt)

    async def test_saving_during_playback_keeps_the_whole_recording_and_original_file(self):
        game, _ = self.play_game(complete=True)
        with TemporaryDirectory() as folder, patch.object(REPLAY_FOLDERS, "value", [folder]), patch.object(UserInfo, "fingerprint", "replay-test", create=True):
            original = Path(game.session.SaveReplay())
            original_bytes = original.read_bytes()
            scene, _ = Json.LoadAsInternal(str(original), Scene, check_sum="Restrict")
            devices = HeadlessDeviceManager(stop_when=lambda prompt: prompt.event_name == "WhenPlayerInTurn")
            watching = self.run_game(scene, devices, load_type="Replay")
            self.assertLess(len(watching.controller_manager.replay.history_inputs), len(scene.inputs))
            client = await self.client_for(watching, devices)
            # Support the old cached client route as well as the new POST.
            response = await client.get('/save_local')
            self.assertEqual(response.status, 200)
            copy_path = Path((await response.json())["path"])
            copied, _ = Json.LoadAsInternal(str(copy_path), Scene, check_sum="Restrict")
            self.assertEqual(Json.Dumps(copied.inputs), Json.Dumps(scene.inputs))
            self.assertTrue(copied.metadata["replay_complete"])
            self.assertNotEqual(original, copy_path)
            self.assertEqual(original.read_bytes(), original_bytes)

    async def test_end_of_recording_rejects_play_until_continue_is_requested(self):
        game, devices = self.play_game()
        game.controller_manager.replay.SetReplayInputs(game.controller_manager.replay.history_inputs[:])
        game.controller_manager.replay.SetIsReplay(True)
        # Restore the live waiting position after the headless driver exits.
        game.world.game_over.reason = None
        devices.asking_players = [0]
        client = await self.client_for(game, devices)
        before = len(game.controller_manager.replay.history_inputs)
        ask = await (await client.get('/get_ask?p=0')).json()
        self.assertTrue(ask["replay_finished"])
        rejected = await client.post('/post?p=0', data='{"id":""}')
        self.assertEqual(rejected.status, 409)
        with patch.object(game.controller_manager.console, "SetCommand") as command:
            self.assertEqual((await client.get('/debug?/step 1')).status, 409)
            command.assert_not_called()
        self.assertEqual(len(game.controller_manager.replay.history_inputs), before)
        with patch.object(devices.notify, "ExitWait", wraps=devices.notify.ExitWait) as wake:
            continued = await client.post('/continue_replay')
            self.assertEqual(continued.status, 200)
            wake.assert_called_once()
        self.assertEqual(devices.asking_players, [0])
        self.assertFalse(game.controller_manager.replay.is_replay)
        self.assertFalse((await (await client.get('/get_ask?p=0')).json())["replay_finished"])
        self.assertEqual(len(game.controller_manager.replay.history_inputs), before)
        self.assertEqual((await client.post('/post?p=0', data='{"id":""}')).status, 200)
        self.assertEqual((await client.post('/continue_replay')).status, 409)

    async def test_failed_save_returns_json_error_instead_of_image_or_success(self):
        game, devices = self.play_game()
        client = await self.client_for(game, devices)
        with patch.object(game.session, "SaveReplay", side_effect=PermissionError("Folder is not writable")):
            response = await client.post('/save_local')
        self.assertEqual(response.status, 500)
        result = await response.json()
        self.assertIn("Folder is not writable", result["error"])
        self.assertNotIn("path", result)

    async def test_download_export_contains_current_choices_and_valid_checksum(self):
        game, devices = self.play_game()
        client = await self.client_for(game, devices)
        with patch.object(UserInfo, "fingerprint", "replay-test", create=True):
            response = await client.get('/save_replay_data')
            # The wire JSON is a serialized Scene string, matching the client.
            data = await response.json()
            with TemporaryDirectory() as folder:
                file = Path(folder) / 'save.json'
                file.write_text(data, encoding='utf-8')
                saved, checksum = Json.LoadAsInternal(str(file), Scene, check_sum="Restrict")
        self.assertEqual(checksum, "Ok")
        self.assertEqual(len(saved.inputs), len(game.controller_manager.replay.history_inputs))
        self.assertFalse(saved.metadata["replay_complete"])

    def test_new_game_clears_replay_mode(self):
        game, _ = self.play_game()
        replay = game.controller_manager.replay
        replay.SetIsReplay(True)
        game.state.SetStartState("New")
        game.controller_manager.Setup(1, 0, game.scene, game.state.start_state)
        self.assertFalse(replay.is_replay)
        self.assertFalse(replay.IsReplayFinished())

    def test_undo_while_watching_preserves_mode_and_the_entire_recording(self):
        completed, _ = self.play_game(complete=True)
        with patch.object(UserInfo, "fingerprint", "replay-test", create=True):
            recording = completed.session.ReplaySnapshot()
        original_inputs = Json.Dumps(recording.inputs)
        devices = HeadlessDeviceManager(stop_when=lambda prompt: prompt.event_name == "WhenPlayerInTurn")
        watching = self.run_game(recording, devices, load_type="Replay")
        self.assertLess(len(watching.controller_manager.replay.history_inputs), len(recording.inputs))
        watching.session.Undo(1)
        self.assertEqual(Json.Dumps(watching.scene.inputs), original_inputs)
        manager = watching.controller_manager
        manager.Setup(1, 30, watching.scene, watching.state.start_state)
        self.assertTrue(manager.replay.is_replay)
        self.assertFalse(manager.replay.IsReplayFinished())
        with patch.object(UserInfo, "fingerprint", "replay-test", create=True):
            saved_again = watching.session.ReplaySnapshot()
        self.assertEqual(Json.Dumps(saved_again.inputs), original_inputs)

    async def test_resume_from_library_loads_the_last_recorded_choice(self):
        game, devices = self.play_game()
        with TemporaryDirectory() as folder, patch.object(REPLAY_FOLDERS, "value", [folder]), patch.object(UserInfo, "fingerprint", "replay-test", create=True):
            saved_path = game.session.SaveReplay()
            client = await self.client_for(game, devices)
            response = await client.get('/resume_replay?' + saved_path.replace('\\', '/'))
            self.assertEqual(response.status, 200)
            self.assertTrue(game.state.start_state.is_load)
            self.assertEqual(game.controller_manager.skip.skip_to, -1)
            game.controller_manager.InitializeSkip(game.scene, game.state.start_state)
            self.assertEqual(game.controller_manager.skip.skip_to, len(game.scene.inputs))
            self.assertTrue(game.controller_manager.skip.is_skipping)
            self.assertFalse(game.controller_manager.replay.is_replay)

    def test_watching_has_no_choice_timeout_and_continuing_restores_it(self):
        game, devices = self.play_game()
        devices.asking_players = []
        devices.timer.max_timeout = 30
        payload = AskOptionPayload('[]', '', '', '', False, '{}')
        waits = []

        def wait(_check, timeout):
            waits.append((timeout, devices.timer.start_time))
            return True

        with patch.object(devices.notify.input, "Wait", side_effect=wait):
            game.controller_manager.replay.SetIsReplay(True)
            devices.DoGetInput(payload, 0, lambda: True)
            game.controller_manager.replay.SetIsReplay(False)
            devices.DoGetInput(payload, 0, lambda: True)
        self.assertEqual(waits[0], (None, None))
        self.assertEqual(waits[1][0], 30)
        self.assertIsNotNone(waits[1][1])

    async def test_continue_reprompts_without_consuming_an_empty_choice(self):
        game, devices = self.play_game()
        game.world.game_over.reason = None
        game.controller_manager.replay.SetReplayInputs(game.controller_manager.replay.history_inputs[:])
        game.controller_manager.replay.SetIsReplay(True)
        devices.asking_players = []
        payload = devices.ask_options[0]
        ready, release = Event(), Event()
        client = await self.client_for(game, devices)

        def wait(check, _timeout):
            ready.set()
            release.wait(5)
            return check()

        with patch.object(devices.notify.input, "Wait", side_effect=wait):
            pending = asyncio.create_task(asyncio.to_thread(devices.DoGetInput, payload, 0, lambda: False))
            try:
                self.assertTrue(await asyncio.to_thread(ready.wait, 2))
                before = len(game.controller_manager.replay.history_inputs)
                response = await client.post('/continue_replay')
                self.assertEqual(response.status, 200)
            finally:
                release.set()
            result = await asyncio.wait_for(pending, 2)
        self.assertIsNone(result, 'Continue must retry the same prompt, rather than end the turn')
        self.assertEqual(len(game.controller_manager.replay.history_inputs), before)


if __name__ == '__main__':
    unittest.main()
