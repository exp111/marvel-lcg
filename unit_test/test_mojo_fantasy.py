from __future__ import annotations

import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.database import CardsDB
from engine.lib import Ver
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    TimingFixture,
    build_fixture_scene,
    run_scene_with_devices,
)


class TestMojoFantasy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Ver.Initialize()
        CardsDB.Initialize()

    def test_goblin_ignores_hero_retaliate_but_takes_physical_card_damage(self):
        fixture = TimingFixture(
            "goblin_damage_restriction.json",
            "Goblin printed physical-resource damage restriction",
            "rhino",
            ("black_panther",),
            390430,
            (
                'Puzzle.ChangeFormFor(0, "Hero")',
                'Puzzle.PutIntoPlay("01058")',
                'Puzzle.CreateEncounterDeck("39043", "01188")',
                'Puzzle.Reveal("39043")',
                'Puzzle.DoAttack("Goblin")',
            ),
            ("01058", "39043", "01188"),
        )
        scene = build_fixture_scene(fixture)
        attacked_with_daredevil = False
        goblin_health_after_retaliate: int | None = None

        def choose(prompt):
            nonlocal attacked_with_daredevil, goblin_health_after_retaliate

            if prompt.event_name == "WhenUnitBeingAttack":
                return CommandDescriptor()  # Black Panther does not defend.

            if prompt.event_name == "WhenPlayerInTurn" and not attacked_with_daredevil:
                world = Engine.game.world
                goblin = world.FindCardsOnField(name="Goblin")[0]
                daredevil = world.FindCardsOnField(name="Daredevil")[0]
                goblin_health_after_retaliate = goblin.health

                option = next(
                    option
                    for option in prompt.options
                    if option.get("name") == "Attack"
                    and option.get("bind_id") == daredevil.card.object_id
                )
                attacked_with_daredevil = True
                return CommandDescriptor(
                    str(option.get("choice_id") or option["id"]),
                    [str(goblin.card.object_id)],
                    [],
                )

            if prompt.event_name == "WhenPlayerInTurn":
                return None

            return HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        game = run_scene_with_devices(scene, devices)

        self.assertEqual(goblin_health_after_retaliate, 1)
        self.assertTrue(attacked_with_daredevil)
        self.assertEqual(game.world.FindCardsOnField(name="Goblin"), [])
        self.assertIn(
            "39043",
            [
                face.paper.card_id
                for face in game.world.scenario.encounter_discard_pile.Get()
            ],
        )
        self.assertEqual(game.world.event_manager.timing_occurrences, [])


if __name__ == "__main__":
    unittest.main()
