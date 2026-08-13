from importlib import import_module
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestMaxPerPlayerLimits(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "data" / "cards.json").read_text(encoding="utf-8"))
        cls.cards = [
            card
            for pack in data.values()
            if isinstance(pack, list)
            for card in pack
        ]

    def test_printed_max_one_per_player_limits_are_encoded(self):
        max_one_per_player = re.compile(
            r"max 1 (?:(?:\[\[)?team(?:\]\])? card )?per player\b"
            r"|max 1 team per player\b",
            re.IGNORECASE,
        )

        missing_limits = [
            (card["card_id"], card["name"])
            for card in self.cards
            if max_one_per_player.search(card.get("text", ""))
            and card.get("desc", {}).get("MaxPerUnit") != "1"
        ]

        self.assertEqual(missing_limits, [])

    def test_heroic_conditioning_is_limited_to_one_copy(self):
        heroic_conditioning = next(
            card for card in self.cards if card.get("card_id") == "58021"
        )

        self.assertEqual(heroic_conditioning["desc"]["MaxPerUnit"], "1")

    def test_upgrade_play_filter_rejects_a_second_copy(self):
        ability = import_module("cards.pack.wonder_man.58021").GetAbilities()[0]
        max_per_unit = next(
            check
            for check in ability.selectors[0].selector_filter.check_effect_fns
            if check.__name__ == "max_per_unit"
        )
        upgrade = SimpleNamespace(max_per_unit=1)
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=upgrade))
        )
        inventory = SimpleNamespace(HasThisType=MagicMock(return_value=1))
        identity = SimpleNamespace(GetInventoryDeck=MagicMock(return_value=inventory))

        self.assertFalse(max_per_unit(effect, identity))

        inventory.HasThisType.return_value = 0
        self.assertTrue(max_per_unit(effect, identity))


if __name__ == "__main__":
    unittest.main()
