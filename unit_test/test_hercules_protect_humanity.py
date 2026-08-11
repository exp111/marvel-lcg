from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

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

    def test_forced_obligation_uses_assigned_player_as_initiator(self):
        from game.event.manager import EventManager
        from game.player import Player

        message = MagicMock()
        world = MagicMock()
        assigned_player = MagicMock(spec=Player)
        effect = MagicMock()
        effect.this.card.area.flags.is_obligations_area = True
        effect.this.GetGaveToPlayer.return_value = assigned_player
        effect.initiator = assigned_player
        effect.context = SimpleNamespace(
            bind_message=None,
            initiator=None,
            ask_player=None,
            ResetBeforeCondition=MagicMock(),
        )
        effect.checker.CheckCondition.return_value = True

        with patch.object(
            EventManager,
            "SimpleCheckEffects",
            return_value=[effect],
        ):
            available = EventManager.FilterAvailableEffects(
                message,
                [effect],
                None,
                world,
                None,
            )

        self.assertEqual(available, [effect])
        self.assertIs(effect.context.initiator, assigned_player)
        self.assertIs(effect.context.ask_player, assigned_player)
        effect.checker.CheckCondition.assert_called_once_with(message, assigned_player)

    def test_redirects_to_chosen_ally_and_removes_counter_if_hercules_defended(self):
        module = import_module("cards.pack.hercules.hercules.59004")
        ally = MagicMock()
        hercules = MagicMock()
        hercules.IsName.return_value = True
        attack_message = SimpleNamespace(defender=hercules)
        message = SimpleNamespace(
            defender=attack_message.defender,
            ReplaceTarget=MagicMock(),
            Present_Activate=MagicMock(),
        )
        self.effect.targets = [ally]

        with patch.object(
            module.RunAt,
            "AfterEventEnd",
            side_effect=lambda effect, event, operation: operation(),
        ), patch.object(module.Unit2, "IsType", return_value=True):
            self.ability.operation(self.effect, message)

        message.ReplaceTarget.assert_called_once_with(ally)
        message.Present_Activate.assert_called_once_with(None, self.effect)
        self.obligation.RemoveCountersInternal.assert_called_once_with(
            1,
            "labor",
            self.effect,
            forced=True,
        )


if __name__ == "__main__":
    unittest.main()
