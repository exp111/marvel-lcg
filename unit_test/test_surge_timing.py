from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.card.face.attribute.can_surge import CanSurge
from game.player.action.player_action import PlayerAction


class TestSurgeTiming(unittest.TestCase):

    @staticmethod
    def resolve_surge(*, fixed_rules=True):
        surging_card = MagicMock()
        surging_card.surge = 1
        surging_card.card.world.rule.fix_surge = fixed_rules
        player = MagicMock()
        surge_message = MagicMock()
        surge_message.is_be_instead = False
        surge_effect = object()

        with patch(
            "game.message.Message.WhenSurgeWouldBeResolved",
            return_value=surge_message,
        ), patch("game.effect.rule.Surge", return_value=surge_effect):
            result = CanSurge.ResolveSurge(surging_card, player)

        return player, surge_message, surge_effect, result

    def test_v18_surge_deals_a_facedown_card_without_revealing_it(self):
        player, surge_message, surge_effect, result = self.resolve_surge()

        surge_message.Send.assert_called_once_with()
        player.DealEncounterCards.assert_called_once_with(
            1,
            surge_effect,
            to_end_of_queue=True,
        )
        self.assertIs(result, surge_effect)

    def test_legacy_surge_queue_order_remains_available_for_old_replays(self):
        player, _, surge_effect, _ = self.resolve_surge(fixed_rules=False)

        player.DealEncounterCards.assert_called_once_with(
            1,
            surge_effect,
            by_surge=True,
        )

    def test_normal_deals_go_to_the_end_of_the_encounter_queue(self):
        player = MagicMock()
        player.world.rule.v16_reveal = False
        face = MagicMock()
        effect = object()
        would_message = MagicMock()
        would_message.is_be_instead = False
        action = SimpleNamespace(GetPlayer=lambda: player)

        with patch(
            "game.message.Message.WhenPlayerWouldBeDealtEncounterCard",
            return_value=would_message,
        ), patch(
            "game.message.Message.AfterPlayerDealEncounterCard",
            return_value=MagicMock(),
        ), patch(
            "game.operate.faces.Faces.MoveAllToDeck",
        ) as move_to_deck:
            PlayerAction.DealEncounterCard(
                action,
                face,
                effect,
                to_end_of_queue=True,
            )

        move_to_deck.assert_called_once_with(
            [face],
            player.dealt_encounter_cards,
            "Bottom",
            effect,
        )

    def test_replaced_surge_does_not_deal_an_encounter_card(self):
        surging_card = MagicMock()
        surging_card.surge = 1
        player = MagicMock()
        surge_message = MagicMock()
        surge_message.is_be_instead = True

        with patch(
            "game.message.Message.WhenSurgeWouldBeResolved",
            return_value=surge_message,
        ):
            result = CanSurge.ResolveSurge(surging_card, player)

        player.DealEncounterCards.assert_not_called()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
