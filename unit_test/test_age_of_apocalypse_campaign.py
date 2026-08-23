import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.operate.worlds import Worlds


class TestAgeOfApocalypseCampaign(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]

    def test_mission_stats_are_per_player(self):
        cards = json.loads(
            (self.project_root / "data" / "cards.json").read_text(
                encoding="utf-8"
            )
        )["aoa"]
        by_id = {card["card_id"]: card for card in cards}

        for card_id in ("45166a", "45167a", "45168a", "45169a", "45170a"):
            with self.subTest(mission=card_id):
                self.assertEqual(
                    by_id[card_id]["desc"]["StartingThreat"],
                    "5*",
                )

        for card_id in ("45179a", "45180a", "45181a", "45182a", "45183a"):
            with self.subTest(overseer=card_id):
                self.assertEqual(by_id[card_id]["desc"]["HP"], "5*")

    def test_generic_side_scheme_queries_exclude_missions(self):
        game_area = SimpleNamespace()
        deck = MagicMock()
        world = SimpleNamespace(area_schemes_side=deck)
        game_area.world = world

        regular_scheme = MagicMock()
        regular_scheme.card.GetGameArea.return_value = game_area
        regular_scheme.HasTrait.return_value = False

        mission_scheme = MagicMock()
        mission_scheme.card.GetGameArea.return_value = game_area
        mission_scheme.HasTrait.side_effect = lambda trait: trait == "MISSION"

        deck.Get.return_value = [regular_scheme, mission_scheme]

        with patch(
            "game.operate.worlds.EncounterSideScheme.IsType",
            return_value=True,
        ), patch(
            "game.operate.worlds.PlayerSideScheme.IsType",
            return_value=False,
        ):
            self.assertEqual(
                Worlds.GetSideSchemes(game_area),
                [regular_scheme],
            )
            self.assertEqual(
                Worlds.GetSideSchemes(game_area, include_missions=True),
                [regular_scheme, mission_scheme],
            )
            self.assertEqual(
                Worlds.GetAllSideSchemes(world),
                [regular_scheme],
            )
            self.assertEqual(
                Worlds.GetAllSideSchemes(world, include_missions=True),
                [regular_scheme, mission_scheme],
            )

    def test_generic_field_queries_exclude_missions(self):
        empty_area = MagicMock()
        empty_area.GetAll.return_value = []
        side_scheme_area = MagicMock()

        world = SimpleNamespace(
            area_schemes_main=empty_area,
            area_schemes_side=side_scheme_area,
            area_environment=empty_area,
            scenario=SimpleNamespace(area_villain=empty_area),
        )
        game_area = SimpleNamespace(world=world)

        regular_scheme = MagicMock()
        regular_scheme.card.game_area = game_area
        regular_scheme.IsFaceUp.return_value = True
        regular_scheme.HasTrait.return_value = False
        regular_scheme.GetInventoryDeck.return_value.GetAll.return_value = []
        regular_scheme.GetPlacedCardArea.return_value.GetAll.return_value = []

        mission_scheme = MagicMock()
        mission_scheme.card.game_area = game_area
        mission_scheme.IsFaceUp.return_value = True
        mission_scheme.HasTrait.side_effect = lambda trait: trait == "MISSION"
        mission_scheme.GetInventoryDeck.return_value.GetAll.return_value = []
        mission_scheme.GetPlacedCardArea.return_value.GetAll.return_value = []

        side_scheme_area.GetAll.return_value = [regular_scheme, mission_scheme]

        with patch.object(Worlds, "GetPlayers", return_value=[]), patch(
            "game.operate.worlds.EncounterSideScheme.IsType",
            return_value=True,
        ):
            self.assertEqual(
                Worlds.GetOnFieldCards(game_area),
                [regular_scheme],
            )
            self.assertEqual(
                Worlds.GetOnFieldCards(game_area, include_missions=True),
                [regular_scheme, mission_scheme],
            )


if __name__ == "__main__":
    unittest.main()
