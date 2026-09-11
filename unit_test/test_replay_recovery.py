import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from core.lib.beep import Beep
from engine.log import Log, Notify
from game.scene.replay.operation import CommandDescriptor
from game.test import Test
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)
from game.world.world_render import WorldRender


FIXTURE = Path(__file__).parent / "fixtures" / "issue_96_recovered.json"
QUICK_SHIFT = "timing2 t0 WhenUnitWouldAttack a0 HeroInterrupt c22 32040"


class TestReplayRecovery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def run_replay(self, scene, devices):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Beep, "Warning"),
            patch.object(Notify, "Game") as notices,
            patch.object(Log, "Warn") as warnings,
        ):
            game = run_scene_with_devices(scene, devices, load_type="InTesting")
        errors.assert_not_called()
        return game, notices, warnings

    def test_divergent_save_rejects_auto_retry_and_accepts_a_live_choice(self):
        for retry_mode in ("auto", "next"):
            with self.subTest(retry_mode=retry_mode):
                scene = validate_file(FIXTURE)
                # The reported save omitted ending the turn and discarding
                # Change of Fortune. Its next entry was Quick Shift.
                del scene.inputs[13:15]
                for index, operation in enumerate(scene.inputs):
                    operation.step = index
                prompts = []

                def choose(prompt):
                    manager = Engine.game.controller_manager
                    prompts.append((manager.replay.current_step_id, prompt))
                    if len(prompts) == 1:
                        if retry_mode == "auto":
                            manager.skip.SetIsSkipping(True)
                        else:
                            manager.skip.SetSkipTo(14)
                        return CommandDescriptor()
                    if len(prompts) == 2:
                        # Explicitly end the player turn after the rejected
                        # retry. This must still work without reloading.
                        return CommandDescriptor()
                    return None

                game, notices, _ = self.run_replay(
                    scene, HeadlessDeviceManager(choice_provider=choose),
                )

                self.assertEqual([step for step, _ in prompts], [13, 13, 14])
                self.assertEqual(prompts[0][1].options, prompts[1][1].options)
                self.assertEqual(prompts[2][1].event_name, "End Turn")
                self.assertTrue(any(
                    "Replay paused at step 13" in call.args[0]
                    for call in notices.call_args_list
                ))
                self.assertEqual(game.controller_manager.replay.history_inputs[-1].effect.id, "")

    def test_unconvertible_ids_are_not_used_even_when_the_state_matches(self):
        for replay_id in (QUICK_SHIFT, "e999 Play c999 32040"):
            with self.subTest(replay_id=replay_id):
                scene = validate_file(FIXTURE)
                scene.inputs = scene.inputs[:14]
                # Retain the correct CRC but use an incompatible identity.
                scene.inputs[13].effect.id = replay_id
                devices = HeadlessDeviceManager(stop_when=lambda prompt: True)

                game, notices, warnings = self.run_replay(scene, devices)

                self.assertEqual(game.controller_manager.replay.current_step_id, 13)
                self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
                self.assertFalse(game.controller_manager.skip.is_skipping)
                self.assertEqual(game.controller_manager.skip.skip_to, 0)
                notices.assert_called_once()
                self.assertTrue(any(
                    "Could not restore replay choice" in str(call)
                    for call in warnings.call_args_list
                ))

    def test_stale_timing_candidate_also_leaves_a_live_prompt(self):
        scene = validate_file(FIXTURE)
        scene.inputs = scene.inputs[:16]
        scene.inputs[15].effect.id = QUICK_SHIFT.replace("t0", "t99")
        devices = HeadlessDeviceManager(stop_when=lambda prompt: True)

        game, notices, _ = self.run_replay(scene, devices)

        self.assertEqual(game.controller_manager.replay.current_step_id, 15)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenUnitWouldAttack")
        self.assertTrue(any(
            option["choice_id"].startswith("timing-")
            for option in devices.stopped_prompt.options
        ))
        notices.assert_called_once()

    def test_recovered_save_preserves_every_state_and_undo_restores_quick_shift(self):
        scene = validate_file(FIXTURE)
        expected_crcs = [operation.crc for operation in scene.inputs]
        devices = HeadlessDeviceManager(stop_when=lambda prompt: True)

        game, notices, warnings = self.run_replay(scene, devices)

        self.assertEqual(game.controller_manager.replay.current_step_id, 64)
        self.assertEqual(
            [operation.crc for operation in game.controller_manager.replay.history_inputs],
            expected_crcs,
        )
        notices.assert_not_called()
        warnings.assert_not_called()

        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Notify, "Game") as undo_notices,
            patch.object(Beep, "Warning"),
        ):
            game.session.Undo(64 - 15)
            devices.stopped_prompt = None
            with patch.object(Test, "is_in_test", True):
                game.GameSetup()
                game.GameLoop()

        errors.assert_not_called()
        undo_notices.assert_not_called()
        self.assertEqual(game.controller_manager.replay.current_step_id, 15)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenUnitWouldAttack")
        self.assertTrue(any(
            "Quick_Shift" in option["name"]
            for option in devices.stopped_prompt.options
        ))


if __name__ == "__main__":
    unittest.main()
