import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import call, patch

from engine import Engine
from engine.lib import Ver
from cards.database import CardsDB
from engine.log import Log
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)
from game.world.world_render import WorldRender


SAVE = Path(__file__).parent / "fixtures" / "issue120_bishop_kingpin.json"


class TestKingpinSideSchemeReveals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep saved object IDs stable when earlier tests loaded linked cards.
        linked_cards = patch.object(CardsDB, "linked_papers", {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    def run_scene(self, scene, devices, *, load_type="New"):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(scene, devices, load_type=load_type)
        errors.assert_not_called()
        expected_warnings = [call("VERSION", f"Version {scene.version} is lower than last version {Ver.version}")] \
            if Ver(scene.version) < Ver.version else []
        self.assertEqual(warnings.call_args_list, expected_warnings)
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game

    def test_reported_save_reveals_organized_crime_without_an_error(self):
        devices = HeadlessDeviceManager(
            stop_when=lambda prompt: prompt.event_name == "WhenPlayerInTurn",
        )
        game = self.run_scene(validate_file(SAVE), devices, load_type="InTesting")
        self.assertEqual(game.world.round_id, 4)
        self.assertEqual(len(game.world.FindCardsOnField(name="60162b")), 1)
        organized_crime = game.world.FindCardsOnField(name="60174")
        self.assertEqual(len(organized_crime), 1)
        self.assertEqual(organized_crime[0].threat, 3)

    def test_endgame_reveals_organized_crime_only_in_expert_mode(self):
        for expert in (False, True):
            with self.subTest(expert=expert):
                scene = SceneLoader.NewScene(
                    "kingpin_expert" if expert else "kingpin",
                    None, ["bishop"], 120,
                )
                prepared = False

                def choose(prompt):
                    nonlocal prepared
                    if prompt.event_name == "WhenPlayerInTurn":
                        if prepared:
                            return None
                        prepared = True
                        Engine.game.controller_manager.console.SetCommand(
                            'world.FindCardsOnField(name="60161b")[0].Advance('
                            '"2A", DebugRule(hero))',
                            Engine.game.world,
                        )
                    return (CommandDescriptor() if prompt.show_cancel
                            else HeadlessDeviceManager._DefaultChoice(prompt))

                devices = HeadlessDeviceManager(choice_provider=choose)
                game = self.run_scene(scene, devices)
                self.assertTrue(prepared)
                self.assertEqual(game.world.round_id, 1)
                self.assertEqual(len(game.world.FindCardsOnField(name="60162b")), 1)
                self.assertEqual(bool(game.world.FindCardsOnField(name="60174")), expert)

    def test_kingpins_influence_affects_only_the_defeating_players_nemesis_scheme(self):
        for in_play in (False, True):
            for legacy in (False, True):
                with self.subTest(in_play=in_play, legacy=legacy):
                    scene = SceneLoader.NewScene(
                        "kingpin", None, ["bishop", "spider_man"], 120,
                    )
                    if legacy:
                        scene.rules = [rule for rule in scene.rules if rule != "v18_timing"]
                        scene.rules.append("no_v18_timing")
                    commands = [
                        '[face for face in world.const_players[1].set_aside_nemesis_sets.Get() '
                        'if face.paper.card_id == "01166"][0].PutIntoPlay('
                        'world.const_players[1], DebugRule(world.const_players[1].GetIdentity()))',
                        'puzzle.PutIntoPlay("60173")',
                    ]
                    if in_play:
                        commands.append(
                            '[face for face in world.const_players[0].set_aside_nemesis_sets.Get() '
                            'if face.paper.card_id == "45027"][0].PutIntoPlay('
                            'world.const_players[0], DebugRule(world.const_players[0].GetIdentity()))',
                        )
                    commands.append(
                        'world.FindCardsOnField(name="60173")[0].RemoveThreatInternal('
                        'world.const_players[0].GetIdentity(), "All", '
                        'DebugRule(world.const_players[0].GetIdentity()))',
                    )
                    command_index = 0

                    def choose(prompt):
                        nonlocal command_index
                        if prompt.event_name == "WhenPlayerInTurn":
                            if command_index == len(commands):
                                return None
                            Engine.game.controller_manager.console.SetCommand(
                                commands[command_index], Engine.game.world,
                            )
                            command_index += 1
                            return CommandDescriptor()
                        return (CommandDescriptor() if prompt.show_cancel
                                else HeadlessDeviceManager._DefaultChoice(prompt))

                    devices = HeadlessDeviceManager(choice_provider=choose)
                    game = self.run_scene(scene, devices)
                    self.assertEqual(command_index, len(commands))
                    bishop_scheme = game.world.FindCardsOnField(name="45027")
                    self.assertEqual(len(bishop_scheme), 1)
                    # Reveal a missing scheme at its starting threat, or add
                    # three threat to the existing scheme without re-revealing.
                    self.assertEqual(bishop_scheme[0].threat, 7 if in_play else 4)
                    self.assertEqual(game.world.FindCardsOnField(name="01166")[0].threat, 6)
                    self.assertEqual(game.world.FindCardsOnField(name="60173"), [])
                    self.assertEqual(game.world.round_id, 1)


if __name__ == "__main__":
    unittest.main()
