from importlib import import_module
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestBrainstorm(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.gmw.the_market.16150")
        self.ability = self.module.GetAbilities()[0]

        self.brainstorm = MagicMock()
        self.named_type = MagicMock()
        self.top_card = MagicMock()
        self.named_type.IsType.return_value = True

        self.player = MagicMock()
        self.player.DeclareCardType.return_value = self.named_type
        self.player.LookAtDeck.return_value = [self.top_card]

        self.effect = MagicMock()
        self.effect.this.CastTo.return_value = self.brainstorm
        self.effect.GetInitiator.return_value = self.player

    def resolve_with_main_scheme(self, can_be_thwarted):
        scheme = MagicMock()
        scheme.CanBeThwartBy.return_value = can_be_thwarted
        with patch.object(
            self.module.Worlds,
            "FindMainScheme",
            return_value=scheme,
        ):
            self.ability.operation(self.effect, MagicMock())
        return scheme

    def test_patrol_does_not_prevent_playing_the_event(self):
        self.assertEqual(self.ability.selectors, [])

        scheme = self.resolve_with_main_scheme(False)

        scheme.CanBeThwartBy.assert_called_once_with(self.effect)
        self.brainstorm.RemoveThreatFromSchemes.assert_not_called()
        self.player.PlaceOnTopAndOrBottomInAnyOrder.assert_called_once_with(
            [self.top_card],
            self.effect,
        )
        self.player.DrawUp.assert_called_once_with(1, self.effect)

    def test_removes_threat_when_the_main_scheme_can_be_thwarted(self):
        scheme = self.resolve_with_main_scheme(True)

        self.brainstorm.RemoveThreatFromSchemes.assert_called_once_with(
            [scheme],
            3,
            self.effect,
        )


if __name__ == "__main__":
    unittest.main()
