import unittest
from unittest.mock import MagicMock

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.player.model.player_cards import PlayerCards


class TestOrderedDeckPlacement(unittest.TestCase):

    def setUp(self):
        self.player = MagicMock()
        self.player.GetPlayer.return_value = self.player
        self.player.PlaceOnBottomInAnyOrder.side_effect = (
            lambda faces, effect: PlayerCards.PlaceOnBottomInAnyOrder(
                self.player, faces, effect
            )
        )
        self.effect = MagicMock()

    @staticmethod
    def make_faces(*names):
        moves = []
        faces = []
        for name in names:
            face = MagicMock(name=name)
            face.card.area = MagicMock(name=f"{name}_deck")
            face.card.MoveToTop.side_effect = (
                lambda deck, effect, card_name=name: moves.append(("top", card_name))
            )
            face.card.MoveToBottom.side_effect = (
                lambda deck, effect, card_name=name: moves.append(("bottom", card_name))
            )
            faces.append(face)
        return faces, moves

    def test_place_on_top_preserves_selected_top_to_bottom_order(self):
        faces, moves = self.make_faces("A", "B", "C")
        self.player.AskChooseFaces.return_value = faces

        PlayerCards.PlaceOnTopInAnyOrder(self.player, faces, self.effect)

        self.assertEqual(moves, [("top", "C"), ("top", "B"), ("top", "A")])
        self.player.AskChooseFaces.assert_called_once_with(
            faces,
            "All",
            self.effect,
            peek=True,
            not_move=True,
            display_in_target_order=True,
            prompt="Place on top",
        )

    def test_place_on_bottom_preserves_selected_top_to_bottom_order(self):
        faces, moves = self.make_faces("A", "B", "C")
        self.player.AskChooseFaces.return_value = faces

        PlayerCards.PlaceOnBottomInAnyOrder(self.player, faces, self.effect)

        self.assertEqual(moves, [("bottom", "A"), ("bottom", "B"), ("bottom", "C")])
        self.player.AskChooseFaces.assert_called_once_with(
            faces,
            "All",
            self.effect,
            peek=True,
            not_move=True,
            display_in_target_order=True,
            prompt="Place on bottom",
        )

    def test_top_and_bottom_groups_each_keep_the_players_order(self):
        faces, moves = self.make_faces("A", "B", "C")
        self.player.AskChooseFaces.side_effect = [[faces[0], faces[2]], [faces[1]]]

        PlayerCards.PlaceOnTopAndOrBottomInAnyOrder(self.player, faces, self.effect)

        self.assertEqual(moves, [("top", "C"), ("top", "A"), ("bottom", "B")])
        for call in self.player.AskChooseFaces.call_args_list:
            self.assertTrue(call.kwargs["display_in_target_order"])


if __name__ == "__main__":
    unittest.main()
