import unittest
from unittest.mock import patch

from engine import Engine
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
)
from game.world.world_render import WorldRender


class TestGodOfLiesIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def test_miscreant_places_threat_after_a_treachery_resolves(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for with_side_scheme in (False, True):
                with self.subTest(timing=timing, side_scheme=with_side_scheme):
                    scene = SceneLoader.NewScene(
                        "god_of_lies", None, ["spider_man"], 93,
                    )
                    scene.rules = ["v16_all", timing]
                    scene.SetMetadataBool("is_puzzle", True)
                    # Make the normal random-avatar setup choose Miscreant.
                    scene.campaign.set_aside = [
                        card_id for card_id in scene.campaign.set_aside
                        if card_id not in (
                            "55029a,55029b", "55031a,55031b", "55032a,55032b",
                        )
                    ]
                    commands = []
                    if with_side_scheme:
                        commands.append('Puzzle.Reveal("55048")')
                    commands.append('Puzzle.Reveal("55049")')
                    command_index = 0

                    def choose(prompt):
                        nonlocal command_index
                        if prompt.event_name == "WhenPlayerInTurn":
                            if command_index == len(commands):
                                return None
                            command = commands[command_index]
                            command_index += 1
                            Engine.game.controller_manager.console.SetCommand(
                                command, Engine.game.world,
                            )
                            return CommandDescriptor()
                        return HeadlessDeviceManager._DefaultChoice(prompt)

                    devices = HeadlessDeviceManager(choice_provider=choose)
                    with patch.object(WorldRender, "ErrorOccurred") as error:
                        game = run_scene_with_devices(scene, devices)

                    error.assert_not_called()
                    self.assertEqual(command_index, len(commands))
                    self.assertIsNotNone(devices.stopped_prompt)
                    self.assertEqual(
                        devices.stopped_prompt.event_name, "WhenPlayerInTurn",
                    )
                    schemes = {
                        face.paper.card_id: face.threat
                        for face in game.world.area_schemes_main.Get()
                    }
                    # Dark Arts places 3 threat when the encounter
                    # discard pile has no minions; Miscreant then adds 1.
                    self.assertEqual(schemes, {"55033b": 4, "55028b": 0})
                    side_schemes = game.world.area_schemes_side.Get()
                    if with_side_scheme:
                        self.assertEqual(
                            [(face.paper.card_id, face.threat) for face in side_schemes],
                            [("55048", 7)],
                        )
                    else:
                        self.assertEqual(side_schemes, [])
                    self.assertEqual(game.world.event_manager.timing_occurrences, [])


if __name__ == "__main__":
    unittest.main()
