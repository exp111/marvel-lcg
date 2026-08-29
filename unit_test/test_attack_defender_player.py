from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability import AbilityType
from game.ability.condition import Condition
from game.ability.factory import AbilityFactory
from game.card.face.attribute.can_attack import _divide_damage_for_attacked_player
from game.card.face.base import ClassCard
from game.message import Message
from game.message.sender.sender_card import _get_activation_target_player


class TestAttackDefenderPlayer(unittest.TestCase):

    @staticmethod
    def completed_attack(original_player, *attacked_players):
        message = object.__new__(Message.AfterUnitAttackEnd)
        message.atk_messages = [
            SimpleNamespace(attacked_you=player)
            for player in attacked_players
        ]
        message.would_atk_messages = [
            SimpleNamespace(
                property=SimpleNamespace(against_player=original_player),
            ),
        ]
        return message

    def test_defending_player_replaces_original_attacked_player(self):
        cyclops_player = object()
        nightcrawler_player = object()
        message = self.completed_attack(cyclops_player, nightcrawler_player)

        self.assertIs(message.GetAgainstPlayer(), nightcrawler_player)

    def test_original_player_is_used_when_attack_ends_before_a_target_is_resolved(self):
        cyclops_player = object()
        message = self.completed_attack(cyclops_player)

        self.assertIs(message.GetAgainstPlayer(), cyclops_player)

    def test_attacks_against_multiple_players_have_no_single_against_player(self):
        cyclops_player = object()
        nightcrawler_player = object()
        message = self.completed_attack(
            cyclops_player,
            cyclops_player,
            nightcrawler_player,
        )

        self.assertIsNone(message.GetAgainstPlayer())

    def test_boost_messages_use_defending_player(self):
        original_player = object()
        defending_player = object()
        defender = MagicMock()
        defender.GetControlByPlayer.return_value = defending_player
        being_message = SimpleNamespace(
            defender=defender,
            would_message=SimpleNamespace(
                property=SimpleNamespace(against_player=original_player),
            ),
        )

        self.assertIs(
            _get_activation_target_player(being_message),
            defending_player,
        )

    def test_scheme_boost_messages_keep_original_player(self):
        original_player = object()
        being_message = SimpleNamespace(
            would_message=SimpleNamespace(
                property=SimpleNamespace(against_player=original_player),
            ),
        )

        self.assertIs(
            _get_activation_target_player(being_message),
            original_player,
        )

    def test_boost_getters_return_resolved_defending_player(self):
        defending_player = object()
        boost_message = SimpleNamespace(
            GetToPlayer=MagicMock(return_value=defending_player),
        )
        after_boost_message = SimpleNamespace(boost_message=boost_message)

        self.assertIs(
            Message.WhenCardBecomeBoost.GetAgainstPlayer(boost_message),
            defending_player,
        )
        self.assertIs(
            Message.AfterCardBecomeBoost.GetAgainstPlayer(after_boost_message),
            defending_player,
        )

    def test_boost_interrupt_target_check_uses_defending_identity(self):
        defending_identity = object()
        defending_player = SimpleNamespace(
            GetIdentity=MagicMock(return_value=defending_identity),
        )
        message = SimpleNamespace(
            GetToPlayer=MagicMock(return_value=defending_player),
        )
        effect = object()
        rule = object()
        ability = AbilityFactory.WhenBoostCardWouldTurnedFaceUp(
            AbilityType.HeroInterrupt,
            lambda effect, message: None,
            activate_target="You",
        )
        check_activate_target = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "check_activate_target"
        )

        with patch.object(Condition, "GetYouRule", return_value=rule), \
            patch.object(Condition, "CheckWhichCard", return_value=True) as check:
            self.assertTrue(check_activate_target(effect, message))

        check.assert_called_once_with(rule, defending_identity, effect)

    def test_turned_boost_target_check_uses_defending_identity(self):
        defending_identity = object()
        defending_player = SimpleNamespace(
            GetIdentity=MagicMock(return_value=defending_identity),
        )
        message = SimpleNamespace(
            GetToPlayer=MagicMock(return_value=defending_player),
        )
        effect = object()
        ability = AbilityFactory.WhenBoostCardTurnedFaceUp(
            AbilityType.HeroInterrupt,
            None,
            lambda effect, message: None,
            activate_target="YourIdentity",
        )
        check_activate_target = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "check_activate_target"
        )

        with patch.object(Condition, "CheckWhichCard", return_value=True) as check:
            self.assertTrue(check_activate_target(effect, message))

        check.assert_called_once_with("YourIdentity", defending_identity, effect)

    def test_bombshell_allocation_is_chosen_by_defending_player(self):
        player_units = [object(), object()]
        defending_player = MagicMock()
        defending_player.GetControlCharacters.return_value = player_units
        defending_player.AskChooseFaces.return_value = [player_units[0]]
        defender = MagicMock()
        defender.GetControlByPlayer.return_value = defending_player
        effect = object()

        with patch(
            "game.card.face.attribute.can_attack.Math.DivideEvenly",
            return_value=(2, 1),
        ):
            units, divided_damage, remainder_units = _divide_damage_for_attacked_player(
                defender,
                5,
                effect,
            )

        self.assertEqual(units, player_units)
        self.assertEqual(divided_damage, 2)
        self.assertEqual(remainder_units, [player_units[0]])
        defending_player.AskChooseFaces.assert_called_once_with(
            player_units,
            (1, 1),
            effect,
        )

    def test_optional_after_attack_response_belongs_to_defending_player(self):
        defending_player = object()
        message = SimpleNamespace(
            GetAgainstPlayer=MagicMock(return_value=defending_player),
        )
        effect = SimpleNamespace(this=object())
        ability = AbilityFactory.AfterUnitAttackYou(
            AbilityType.HeroResponse,
            None,
            lambda effect, message: None,
        )
        check_against_who = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "check_against_who"
        )

        with patch.object(ClassCard, "IsType", return_value=False), \
            patch.object(Condition, "ThisIsYou", return_value=True) as check:
            self.assertTrue(check_against_who(effect, message))

        check.assert_called_once_with(effect, defending_player)

    def test_forced_encounter_response_still_resolves_for_defender(self):
        defending_player = object()
        message = SimpleNamespace(
            GetAgainstPlayer=MagicMock(return_value=defending_player),
        )
        effect = SimpleNamespace(this=object())
        ability = AbilityFactory.AfterUnitAttackYou(
            AbilityType.ForcedResponse,
            None,
            lambda effect, message: None,
        )
        check_against_who = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "check_against_who"
        )

        with patch.object(ClassCard, "IsType", return_value=False), \
            patch.object(Condition, "ThisIsYou") as check:
            self.assertTrue(check_against_who(effect, message))

        check.assert_not_called()

    def test_youll_pay_for_that_checks_defending_identity(self):
        ability = import_module("cards.pack.hlk.10016").GetAbilities()[0]
        check_identity_took_damage = ability.conditions[-1]
        defending_identity = object()
        message = SimpleNamespace(
            attacked_you=SimpleNamespace(
                GetIdentity=MagicMock(return_value=defending_identity),
            ),
            attacked=defending_identity,
            to_player=SimpleNamespace(
                GetIdentity=MagicMock(return_value=object()),
            ),
        )

        self.assertTrue(check_identity_took_damage(object(), message))


if __name__ == "__main__":
    unittest.main()
