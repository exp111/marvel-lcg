from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestHerculesProtectHumanity(unittest.TestCase):

    def setUp(self):
        module = import_module("cards.pack.hercules.hercules.59004")
        self.ability = module.GetAbilities()[1]
        self.player = MagicMock()
        self.obligation = MagicMock()
        self.obligation.CastTo.return_value = self.obligation
        self.obligation.GetGaveToPlayer.return_value = self.player
        self.effect = SimpleNamespace(
            this=self.obligation,
            GetInitiator=MagicMock(
                side_effect=AssertionError("villain is not a player"),
            ),
        )

    def test_villain_attack_uses_obligations_assigned_player_for_allies(self):
        ally = MagicMock()
        self.player.GetControlAllies.return_value = [ally]

        self.assertTrue(self.ability.conditions[-1](self.effect, MagicMock()))
        self.effect.GetInitiator.assert_not_called()

    def test_redirect_is_unavailable_when_assigned_player_has_no_allies(self):
        self.player.GetControlAllies.return_value = []

        self.assertFalse(self.ability.conditions[-1](self.effect, MagicMock()))
        self.effect.GetInitiator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
