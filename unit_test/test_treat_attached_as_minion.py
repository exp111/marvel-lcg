from __future__ import annotations

import unittest
from unittest.mock import patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.database import CardsDB
from engine.lib import Ver
from game.card.face.card_type import Minion
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    TimingFixture,
    build_fixture_scene,
    run_scene_with_devices,
)
from game.world.world_render import WorldRender


class TestTreatAttachedCardAsMinion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Ver.Initialize()
        CardsDB.Initialize()

    def test_beguiled_converts_iron_man_once_without_controller_error(self):
        fixture = TimingFixture(
            "beguiled_iron_man.json",
            "Beguiled converts Iron Man into a minion",
            "rhino",
            ("ironheart",),
            860001,
            (
                'Puzzle.PutIntoPlay("09039")',
                'Puzzle.CreateEncounterDeck("21178")',
            ),
            ("09039", "21178"),
        )
        stage = 0
        converted_snapshot = None

        def choose(prompt):
            nonlocal stage
            nonlocal converted_snapshot
            if prompt.event_name == "WhenPlayerInTurn" and stage == 0:
                Engine.game.controller_manager.console.SetCommand(
                    'Puzzle.Reveal("21178")',
                    Engine.game.world,
                )
                stage = 1
                return CommandDescriptor()
            if prompt.event_name == "WhenPlayerInTurn" and stage == 1:
                player = Engine.game.world.const_players[0]
                converted = player.engaged_minions.FindCard(name="Iron Man")
                assert converted is not None
                converted_snapshot = (
                    Minion.IsType(converted),
                    converted.pic_id,
                    [
                        face.paper.card_id
                        for face in converted.GetInventoryDeck().Get()
                    ],
                )
                Engine.game.controller_manager.console.SetCommand(
                    'Puzzle.Discard("Beguiled")',
                    Engine.game.world,
                )
                stage = 2
                return CommandDescriptor()
            if prompt.event_name == "WhenPlayerInTurn":
                return None
            return HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with patch.object(WorldRender, "ErrorOccurred") as error_occurred:
            game = run_scene_with_devices(
                build_fixture_scene(fixture),
                devices,
            )

        error_occurred.assert_not_called()
        player = game.world.const_players[0]
        self.assertEqual(
            converted_snapshot,
            (True, "09039", ["21178"]),
        )
        self.assertIsNotNone(player.allies.FindCard(name="Iron Man"))
        self.assertIsNone(player.engaged_minions.FindCard(name="Iron Man"))
        self.assertIsNotNone(
            game.world.scenario.encounter_discard_pile.FindCard(
                name="Beguiled",
            )
        )


if __name__ == "__main__":
    unittest.main()
