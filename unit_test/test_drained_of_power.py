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


SAVE = Path(__file__).parent / "fixtures" / "issue140_drained_of_power.json"
PAY = "Spend_an_energy_resource_or_2_resources_of_any_type"
DECLINE = "Do_not_pay"


class TestDrainedOfPower(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep the reported save's object IDs stable after other database tests.
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
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game

    def test_reported_save_spends_resource_and_removes_counter(self):
        scene = validate_file(SAVE)
        expected_crcs = [operation.crc for operation in scene.inputs]
        devices = HeadlessDeviceManager(stop_when=lambda prompt: True)
        game = self.run_scene(scene, devices, load_type="InTesting")
        self.assertEqual(
            [operation.crc for operation in game.controller_manager.replay.history_inputs]
            [:len(scene.inputs)],
            expected_crcs,
        )
        world = game.world
        self.assertEqual(world.object_manager.card_dict[57].face.GetCounters("drain"), 2)
        self.assertTrue(world.object_manager.card_dict[49].IsReady())
        self.assertIn(world.object_manager.card_dict[27].face,
                      world.GetFirstPlayer().discard_pile.GetAll())

    def run_ready_attempts(self, timing, payments, *, decision="pay", attempts=1):
        scene = SceneLoader.NewScene("rhino", None, ["captain_marvel"], 140)
        scene.rules = ["v16_all", timing]
        commands = [
            'puzzle.ClearHand()',
            'puzzle.PutIntoPlay("05023")',
            'puzzle.Reveal("60080")',
        ]
        for attempt in range(attempts):
            if attempt:
                commands.append('puzzle.Exhaust("05023")')
            if payments:
                cards = ", ".join(repr(card_id) for card_id in payments)
                commands.append(f"puzzle.CreateHandCards({cards})")
            commands.append('puzzle.Ready("05023")')
        commands = iter(commands)
        counter_snapshots = []

        def choose(prompt):
            world = Engine.game.world
            if prompt.event_name == "WhenPlayerInTurn":
                command = next(commands, None)
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, world)
                return CommandDescriptor()
            declines = [option for option in prompt.options
                        if option["name"].startswith(DECLINE)]
            if declines:
                drained = world.FindCardsOnField(name="Drained of Power")[0]
                counter_snapshots.append(drained.GetCounters("drain"))
                if decision == "cancel":
                    self.assertTrue(prompt.show_cancel)
                    return CommandDescriptor()
                if decision == "decline":
                    return CommandDescriptor(HeadlessDeviceManager._DescriptorId(declines[0]))
                option = next(option for option in prompt.options
                              if option["name"].startswith(PAY))
                payment_ids = []
                available = [payment_id
                             for payment in option["target_payment"]["0"]["payment"]
                             for payment_id in payment]
                for card_id in payments:
                    payment_id = next(
                        payment_id for payment_id in available
                        if payment_id not in payment_ids
                        and world.object_manager.paying_effect_dict[int(payment_id)].this.paper.card_id
                        == card_id
                    )
                    payment_ids.append(payment_id)
                return CommandDescriptor(
                    HeadlessDeviceManager._DescriptorId(option), [], payment_ids,
                )
            return (CommandDescriptor() if prompt.show_cancel
                    else HeadlessDeviceManager._DefaultChoice(prompt))

        devices = HeadlessDeviceManager(choice_provider=choose)
        game = self.run_scene(scene, devices)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        return game.world, counter_snapshots

    def test_both_costs_remove_one_counter_and_ready_upgrade(self):
        for timing in ("v18_timing", "no_v18_timing"):
            # One energy, one double-resource card, or two single-resource cards.
            for payments in (("01070",), ("01089",), ("01067", "01067")):
                with self.subTest(timing=timing, payments=payments):
                    world, counters = self.run_ready_attempts(timing, payments)
                    self.assertEqual(counters, [3])
                    self.assertEqual(world.FindCardsOnField(name="Drained of Power")[0]
                                     .GetCounters("drain"), 2)
                    self.assertTrue(world.FindCardsOnField(name="Endurance")[0].card.IsReady())
                    self.assertEqual(world.GetFirstPlayer().hand_cards.GetSize(), 0)

    def test_last_counter_discards_attachment_and_stops_charging_for_ready(self):
        for timing in ("v18_timing", "no_v18_timing"):
            with self.subTest(timing=timing):
                world, counters = self.run_ready_attempts(timing, ("01070",), attempts=4)
                self.assertEqual(counters, [3, 2, 1])
                self.assertEqual(world.FindCardsOnField(name="Drained of Power"), [])
                drained = next(card for card in world.object_manager.card_dict.values()
                               if card.face.paper.card_id == "60080")
                self.assertTrue(drained.area.flags.is_encounter_discard_pile)
                self.assertTrue(world.FindCardsOnField(name="Endurance")[0].card.IsReady())
                self.assertEqual(world.GetFirstPlayer().hand_cards.GetSize(), 1)

    def test_declining_or_cancelling_keeps_upgrade_exhausted(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for decision in ("decline", "cancel"):
                with self.subTest(timing=timing, decision=decision):
                    world, counters = self.run_ready_attempts(
                        timing, ("01070",), decision=decision,
                    )
                    self.assertEqual(counters, [3])
                    self.assertEqual(world.FindCardsOnField(name="Drained of Power")[0]
                                     .GetCounters("drain"), 3)
                    self.assertFalse(world.FindCardsOnField(name="Endurance")[0].card.IsReady())
                    self.assertEqual(world.GetFirstPlayer().hand_cards.GetSize(), 1)

    def test_unaffordable_cost_keeps_upgrade_exhausted(self):
        for timing in ("v18_timing", "no_v18_timing"):
            with self.subTest(timing=timing):
                world, _ = self.run_ready_attempts(timing, (), decision="decline")
                self.assertEqual(world.FindCardsOnField(name="Drained of Power")[0]
                                 .GetCounters("drain"), 3)
                self.assertFalse(world.FindCardsOnField(name="Endurance")[0].card.IsReady())


if __name__ == "__main__":
    unittest.main()
