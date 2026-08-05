from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.card.face.attribute.has_setup import HasSetup
from game.player.element.player_setup import PlayerSetup


class TestPermanentPlayerSetup(unittest.TestCase):

    def test_printed_permanent_card_enters_play_before_shuffle(self):
        permanent_face = SimpleNamespace(printed_permanent=True)
        regular_face = SimpleNamespace(printed_permanent=False)
        player = SimpleNamespace()
        effect = SimpleNamespace()

        permanent_face.PutIntoPlay = MagicMock()
        regular_face.PutIntoPlay = MagicMock()

        with patch(
            "game.player.element.player_setup.HasPermanent.IsType",
            side_effect=lambda face: face is permanent_face,
        ):
            PlayerSetup.PutPermanentCardsIntoPlay(
                [
                    SimpleNamespace(face=permanent_face),
                    SimpleNamespace(face=regular_face),
                ],
                player,
                effect,
            )

        permanent_face.PutIntoPlay.assert_called_once_with(player, effect)
        regular_face.PutIntoPlay.assert_not_called()

    def test_printed_setup_card_resolves_setup_after_entering_play(self):
        player = SimpleNamespace()
        effect = SimpleNamespace()
        face = SimpleNamespace(
            printed_setup=1,
            GetControlByOrOwner=MagicMock(return_value=player),
            PutIntoPlay=MagicMock(return_value=True),
            Setup=MagicMock(),
        )

        with patch(
            "game.card.face.attribute.has_setup.Player.IsType",
            return_value=True,
        ):
            HasSetup.ProcessSetup(face, effect)

        face.PutIntoPlay.assert_called_once_with(player, effect)
        face.Setup.assert_called_once_with(False)

if __name__ == "__main__":
    unittest.main()
