from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from engine import Engine  # noqa: F401 - establishes the project's import order
from engine.controller.controller import Controller
from game.player.element.player_phase import PlayerPhase


class TestEndPhaseHandLimit(unittest.TestCase):

    def test_player_must_discard_down_to_their_hand_size(self):
        player = MagicMock()
        cards = [MagicMock() for _ in range(6)]
        player.hand_cards.Get.return_value = cards
        player.GetCountHandSizeFaces.return_value = cards
        player.hand_size = 5
        phase = PlayerPhase(player)

        phase.MayDiscardHandCardsAndDrawUpToMax(
            "End Phase", SimpleNamespace()
        )

        discard_call = player.AskDiscardFaces.call_args
        self.assertEqual(discard_call.args[0], cards)
        self.assertEqual(discard_call.args[1], (1, "All"))
        player.DrawUp.assert_called_once_with("Max", discard_call.args[2])

    def test_discard_remains_optional_when_not_above_hand_size(self):
        player = MagicMock()
        cards = [MagicMock() for _ in range(5)]
        player.hand_cards.Get.return_value = cards
        player.GetCountHandSizeFaces.return_value = cards
        player.hand_size = 5
        phase = PlayerPhase(player)

        phase.MayDiscardHandCardsAndDrawUpToMax(
            "Resolve Mulligans", SimpleNamespace()
        )

        self.assertEqual(player.AskDiscardFaces.call_args.args[1], (0, "All"))

    def test_forced_choice_rejects_an_empty_submission_when_targets_are_required(self):
        descriptor = SimpleNamespace(target_num_range=[1, 6])

        self.assertFalse(Controller.CanSubmitEmptyChoice(True, [descriptor]))

    def test_forced_choice_allows_empty_submission_when_zero_targets_are_legal(self):
        descriptor = SimpleNamespace(target_num_range=[0, 5])

        self.assertTrue(Controller.CanSubmitEmptyChoice(True, [descriptor]))


if __name__ == "__main__":
    unittest.main()
