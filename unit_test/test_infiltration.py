from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.operate.worlds import Worlds


class TestInfiltration(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.bp.51015")
        self.ability = self.module.GetAbilities()[0]
        self.cost = self.ability.cost_funcs[0]
        self.player = MagicMock()
        self.player.DeclareNumber.return_value = 5
        self.effect = MagicMock()
        self.deck = SimpleNamespace(shuffle_with_discard_count=0)

    def test_encounter_deck_reset_fulfills_partial_discard_cost(self):
        discarded = [MagicMock(), MagicMock()]

        def discard_and_reset(size, effect):
            self.deck.shuffle_with_discard_count += 1
            return discarded

        with patch.object(Worlds, "GetEncounterDeck", return_value=self.deck), patch.object(
            Worlds, "DiscardEncounterCards", side_effect=discard_and_reset
        ):
            paid = self.cost.call_fn([], self.effect, self.player)

        self.assertTrue(paid)
        self.assertEqual(self.cost.return_discarded_cards, discarded)
        self.player.DeclareNumber.assert_called_once_with(1, 5)

    def test_partial_discard_without_deck_reset_does_not_pay_cost(self):
        with patch.object(Worlds, "GetEncounterDeck", return_value=self.deck), patch.object(
            Worlds, "DiscardEncounterCards", return_value=[MagicMock(), MagicMock()]
        ):
            paid = self.cost.call_fn([], self.effect, self.player)

        self.assertFalse(paid)

    def test_effect_uses_the_number_of_cards_actually_discarded(self):
        discarded = [MagicMock(), MagicMock()]
        self.cost.return_discarded_cards = discarded
        event = MagicMock()
        effect = SimpleNamespace(
            this=MagicMock(),
            cost_func=SimpleNamespace(Get=MagicMock(return_value=self.cost)),
            targets=[MagicMock()],
            GetInitiator=MagicMock(return_value=MagicMock()),
        )
        effect.this.CastTo.return_value = event

        with patch.object(self.module.Filter, "ByType", return_value=[]), patch.object(
            self.module.Filter, "One", return_value=None
        ):
            self.ability.operation(effect, MagicMock())

        event.RemoveThreatFromSchemes.assert_called_once_with(
            effect.targets, len(discarded), effect
        )


if __name__ == "__main__":
    unittest.main()
