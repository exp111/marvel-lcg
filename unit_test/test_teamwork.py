from importlib import import_module
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.message import Message


class TestMatchingBasicPower(unittest.TestCase):

    def test_matching_power_delegates_to_the_assault_aware_performance(self):
        ally = MagicMock()
        effect = MagicMock()
        would_message = MagicMock()
        message = Message.WhenUnitUseBasicPower(
            MagicMock(),
            "THW",
            would_message,
        )

        message.AddThatMatchingPower([ally], effect)

        would_message.AddMatchingPowerToThisPerformance.assert_called_once_with(
            ally,
            effect,
        )
        message.power = "ATK"
        message.AddThatMatchingPower([ally], effect)
        self.assertEqual(
            would_message.AddMatchingPowerToThisPerformance.call_count,
            2,
        )


class TestTeamwork(unittest.TestCase):

    def test_original_teamwork_uses_matching_power_helper(self):
        module = import_module("cards.pack.thor.06032")
        ally = MagicMock()
        effect = MagicMock()
        effect.cost_func.Get.return_value.return_exhausted_cards = [ally]
        message = MagicMock()

        with patch.object(module.Filter, "ByType", return_value=[ally]):
            module.GetAbilities()[0].operation(effect, message)

        message.AddThatMatchingPower.assert_called_once_with([ally], effect)

    def test_every_teamwork_reprint_uses_the_original_script(self):
        cards = self._cards_by_id()

        self.assertEqual(cards["33017"], {"card_id": "33017", "full_link": "06032"})
        self.assertEqual(cards["59021"], {"card_id": "59021", "full_link": "06032"})

    @staticmethod
    def _cards_by_id():
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "data" / "cards.json").read_text(encoding="utf-8"))
        return {
            card["card_id"]: card
            for pack in data.values()
            if isinstance(pack, list)
            for card in pack
        }


if __name__ == "__main__":
    unittest.main()
