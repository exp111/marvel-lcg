from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.card.face.attribute.has_cost import HasCost
from game.player.action.player_action import PlayerAction


class TestGalacticArtifacts(unittest.TestCase):

    def test_rewards_use_the_defeating_player_not_the_killer_face(self):
        for card_id in ("16127", "16128", "16129"):
            with self.subTest(card_id=card_id):
                module = import_module(
                    f"cards.pack.gmw.galactic_artifacts.{card_id}"
                )
                player = MagicMock()
                message = SimpleNamespace(
                    GetDefeatingPlayer=MagicMock(return_value=player),
                    killer=MagicMock(),
                )
                effect = SimpleNamespace(
                    this=SimpleNamespace(CastTo=MagicMock()),
                )

                module.GetAbilities()[0].operation(effect, message)

                message.GetDefeatingPlayer.assert_called_once_with()
                message.killer.GetControlBy.assert_not_called()
                player.MayChooseOneAbility.assert_called_once()

    def test_crystal_ball_offers_the_defeating_player_a_discounted_card(self):
        module = import_module("cards.pack.gmw.galactic_artifacts.16130")
        player = MagicMock()
        hand_cards = [MagicMock()]
        player.hand_cards.Get.return_value = hand_cards
        message = SimpleNamespace(
            GetDefeatingPlayer=MagicMock(return_value=player),
            killer=MagicMock(),
        )
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock()),
        )

        module.GetAbilities()[0].operation(effect, message)

        message.GetDefeatingPlayer.assert_called_once_with()
        message.killer.GetControlBy.assert_not_called()
        player.PlayOneCardLikeInTurn.assert_called_once_with(
            hand_cards,
            effect,
            update_resources_cost=-3,
        )

    def test_discount_is_active_while_filtering_playable_cards(self):
        player_action = MagicMock(spec=PlayerAction)
        player = MagicMock()
        player_action.GetPlayer.return_value = player
        player_action._RegisterLikeInTurnCostModifiers.side_effect = (
            PlayerAction._RegisterLikeInTurnCostModifiers.__get__(
                player_action,
                PlayerAction,
            )
        )
        face = MagicMock(spec=HasCost)
        face.effect = MagicMock()
        play_effect = MagicMock()
        cost_modifier = MagicMock()
        face.GetTurnPlayEffects.return_value = [play_effect]
        face.effect.RegisterTemp.return_value = [cost_modifier]
        face.CanPlayBy.side_effect = lambda checked_player: (
            checked_player is player and face.effect.RegisterTemp.called
        )
        player.AskChooseFace.return_value = None

        PlayerAction.PlayOneCardLikeInTurn(
            player_action,
            [face],
            MagicMock(),
            update_resources_cost=-3,
        )

        selected_faces = player.AskChooseFace.call_args.args[0]
        self.assertEqual(selected_faces, [face])
        face.effect.RegisterTemp.assert_called_once()
        cost_modifier.UnRegisterSelf.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
