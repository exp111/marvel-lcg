import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import call, patch

from engine import Engine
from engine.lib import Ver
from engine.log import Log, Notify
from cards.database import CardsDB
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)
from game.world.world_render import WorldRender


SAVE = Path(__file__).parent / "fixtures" / "issue136_establish_trust.json"
REMOVE_TRUST = (
    'hero.RemoveThreatFromSchemes([puzzle.FindOrCreateFace("60113a")], '
    '"All", DebugRule(hero))'
)


class TestEstablishTrust(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Preserve the reported save's object IDs when run after other tests.
        linked_cards = patch.object(CardsDB, "linked_papers", {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    @staticmethod
    def pass_optional(prompt):
        return (
            CommandDescriptor() if prompt.show_cancel
            else HeadlessDeviceManager._DefaultChoice(prompt)
        )

    def run_scene(self, scene, devices, *, load_type="New"):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Notify, "Game") as notices,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(scene, devices, load_type=load_type)
        errors.assert_not_called()
        expected_warnings = [
            call("VERSION", f"Version {scene.version} is lower than last version {Ver.version}")
        ] if Ver(scene.version) < Ver.version else []
        self.assertEqual(warnings.call_args_list, expected_warnings)
        notices.assert_not_called()
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game

    def new_scene(self, timing, *, expert=False, heroes=("captain_marvel",)):
        scene = SceneLoader.NewScene("rhino", None, list(heroes), 136)
        scene.campaign = validate_file(SAVE).campaign
        scene.campaign.expert = expert
        if expert:
            scene.campaign.set_aside[0] = "60111a,60111b"
        scene.rules = ["v16_all", timing]
        return scene

    def run_commands(self, scene, commands):
        commands = iter(commands)
        initial_threat = None

        def choose(prompt):
            nonlocal initial_threat
            if prompt.event_name == "WhenPlayerInTurn":
                world = Engine.game.world
                if initial_threat is None:
                    trust = next(iter(world.FindCardsOnField(name="Establish Trust")), None)
                    initial_threat = trust.threat if trust else 0
                command = next(commands, None)
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, world)
                return CommandDescriptor()
            return self.pass_optional(prompt)

        game = self.run_scene(scene, HeadlessDeviceManager(choice_provider=choose))
        return game.world, initial_threat

    def assert_mary_and_psyche(self, world, counters=1):
        self.assertEqual(world.FindCardsOnField(name="Establish Trust"), [])
        mary = world.FindCardsOnField(name="Mary Walker")
        self.assertEqual(len(mary), 1)
        self.assertTrue(mary[0].permanent)
        self.assertTrue(mary[0].card.state.is_attached)
        self.assertEqual(mary[0].GetBindFace().paper.set_name, "Typhoid Mary")
        self.assertIn(mary[0], mary[0].GetBindFace().GetInventoryDeck().GetAll())
        psyche = world.FindCardsOnField(name="Disturbed Psyche")[0]
        self.assertEqual(psyche.GetCounters("threat"), counters)
        self.assertEqual(psyche.GetAllCounters(), counters)

    def test_reported_save_flips_and_places_one_threat_counter(self):
        scene = validate_file(SAVE)
        expected_crcs = [operation.crc for operation in scene.inputs]
        devices = HeadlessDeviceManager(
            stop_when=lambda prompt: prompt.event_name == "WhenPlayerInTurn",
            choice_provider=self.pass_optional,
        )
        game = self.run_scene(scene, devices, load_type="InTesting")
        self.assertEqual(
            [operation.crc for operation in game.controller_manager.replay.history_inputs]
            [:len(scene.inputs)],
            expected_crcs,
        )
        self.assert_mary_and_psyche(game.world)
        self.assertEqual(game.world.object_manager.card_dict[106].face.paper.card_id, "60113b")

    def test_defeat_in_both_modes_and_timing_dispatchers(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for expert in (False, True):
                for heroes in (("captain_marvel",), ("captain_marvel", "spider_man")):
                    with self.subTest(timing=timing, expert=expert, players=len(heroes)):
                        scene = self.new_scene(timing, expert=expert, heroes=heroes)
                        world, initial_threat = self.run_commands(scene, [REMOVE_TRUST])
                        self.assertEqual(initial_threat, (11 if expert else 8) * len(heroes))
                        self.assert_mary_and_psyche(world)

    def test_mary_can_flip_back_and_be_defeated_again(self):
        for timing in ("v18_timing", "no_v18_timing"):
            with self.subTest(timing=timing):
                scene = self.new_scene(timing)
                world, _ = self.run_commands(scene, [
                    REMOVE_TRUST,
                    'puzzle.Damage(puzzle.FindOrCreateFace("60113b").GetBindFace(), 1)',
                    REMOVE_TRUST,
                ])
                self.assert_mary_and_psyche(world, counters=2)
                self.assertEqual(world.GetFirstPlayer().dealt_encounter_cards.GetSize(), 1)

    def test_permanent_scheme_without_flip_stays_in_play_at_zero_threat(self):
        for timing in ("v18_timing", "no_v18_timing"):
            with self.subTest(timing=timing):
                scene = SceneLoader.NewScene("rhino", None, ["captain_marvel"], 136)
                scene.rules = ["v16_all", timing]
                world, _ = self.run_commands(scene, [
                    'puzzle.PutIntoPlay("34030")',
                    'hero.RemoveThreatFromSchemes([puzzle.FindOrCreateFace("34030")], '
                    '"All", DebugRule(hero))',
                ])
                consume = world.FindCardsOnField(name="Consume the World")
                self.assertEqual(len(consume), 1)
                self.assertTrue(consume[0].permanent)
                self.assertEqual(consume[0].threat, 0)
                self.assertEqual(consume[0].amplify, 0)


if __name__ == "__main__":
    unittest.main()
