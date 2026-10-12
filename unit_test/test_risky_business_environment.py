import contextlib
import io
import unittest
from unittest.mock import patch

from engine import Engine
from engine.log import Log, Notify
from game.message import Message
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


class TestRiskyBusinessEnvironment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()

    def run_commands(self, commands, *, players=1, expert=False, timing="v18_timing"):
        scene = SceneLoader.NewScene(
            "risky_business_expert" if expert else "risky_business",
            None, ["captain_marvel", "spider_man"][:players], 138,
        )
        scene.rules = ["v16_all", timing]
        commands = iter(commands)
        snapshots = []
        entries = []
        entry_send = Message.AfterCardEnterPlay.Send

        def record_entry(message):
            if message.trigger.paper.card_id in ("02006a", "02006b"):
                entries.append(message.trigger.paper.card_id)
            return entry_send(message)

        def choose(prompt):
            if len(devices.prompts) > 50:
                raise AssertionError("Unexpected repeated prompt")
            if prompt.event_name == "WhenPlayerInTurn":
                world = Engine.game.world
                environment = (
                    world.FindCardsOnField(name="Criminal Enterprise")
                    + world.FindCardsOnField(name="State of Madness")
                )[0]
                villain = world.scenario.area_villain.Get()[0]
                snapshots.append({
                    "face": environment.paper.card_id,
                    "infamy": environment.GetCounters("infamy"),
                    "madness": environment.GetCounters("madness"),
                    "villain": villain.name,
                    "health": villain.health,
                    "threat": world.area_schemes_main.Get()[0].threat,
                })
                command = next(commands, None)
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, world)
                return CommandDescriptor()
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(Message.AfterCardEnterPlay, "Send", new=record_entry),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Notify, "Game") as notices,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        # Counter initialization on a flip must not broadcast a false entry.
        self.assertEqual(entries, ["02006a"])
        return snapshots

    def test_damage_to_norman_initializes_madness_after_the_flip(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for expert in (False, True):
                for players in (1, 2):
                    with self.subTest(timing=timing, expert=expert, players=players):
                        snapshots = self.run_commands(
                            [f'puzzle.Damage("Norman Osborn", {2 * players})'],
                            timing=timing, expert=expert, players=players,
                        )
                        self.assertEqual(
                            [(s["face"], s["infamy"], s["madness"], s["villain"]) for s in snapshots],
                            [("02006a", 2 * players, 0, "Norman Osborn"),
                             ("02006b", 0, 2 * players, "Green Goblin")],
                        )
                        self.assertEqual(snapshots[0]["health"], snapshots[1]["health"])

    def test_scheming_flips_back_and_reinitializes_counters_on_every_cycle(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for expert in (False, True):
                for players in (1, 2):
                    with self.subTest(timing=timing, expert=expert, players=players):
                        counters = 2 * players
                        damage = f'puzzle.Damage("Norman Osborn", {counters})'
                        scheme = 'world.scenario.area_villain.Get()[0].DoSchemes(p, DebugRule(hero))'
                        snapshots = self.run_commands(
                            [damage] + [scheme] * counters + [damage],
                            timing=timing, expert=expert, players=players,
                        )
                        self.assertEqual(
                            [(s["face"], s["infamy"], s["madness"], s["villain"]) for s in snapshots],
                            [("02006a", counters, 0, "Norman Osborn"),
                             ("02006b", 0, counters, "Green Goblin")]
                            + [("02006b", 0, n, "Green Goblin") for n in range(counters - 1, 0, -1)]
                            + [("02006a", counters, 0, "Norman Osborn"),
                               ("02006b", 0, counters, "Green Goblin")],
                        )
                        # Goblin removes madness instead of actually scheming;
                        # Norman prevents damage while removing infamy.
                        self.assertEqual({s["threat"] for s in snapshots}, {snapshots[0]["threat"]})
                        self.assertEqual({s["health"] for s in snapshots}, {snapshots[0]["health"]})


if __name__ == "__main__":
    unittest.main()
