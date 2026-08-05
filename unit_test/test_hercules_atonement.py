from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestHerculesAtonement(unittest.TestCase):

    def test_ready_and_flip_continue_after_gift_enter_play_responses(self):
        module = import_module("cards.pack.hercules.hercules.59001a")
        ability = module.GetAbilities()[0]
        identity = MagicMock()
        player = SimpleNamespace(GetIdentity=MagicMock(return_value=identity))
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))
        gift = MagicMock()
        deck = SimpleNamespace(GetTop=MagicMock(return_value=gift))
        deferred = []

        with patch.object(module, "GetGiftDeck", return_value=deck), patch.object(
            module.RunAt,
            "AfterFaceEnterPlay",
            side_effect=lambda by_effect, face, operation: deferred.append(operation),
        ) as after_enter, patch.object(
            module,
            "YouMayFlipToYourAlterEgoForm",
        ) as may_flip:
            ability.operation(effect, SimpleNamespace())

            after_enter.assert_called_once()
            gift.PutIntoPlay.assert_called_once_with(
                player,
                effect,
                under_control=True,
            )
            identity.Ready.assert_not_called()
            may_flip.assert_not_called()

            self.assertEqual(len(deferred), 1)
            deferred[0]()

            identity.Ready.assert_called_once_with(effect)
            may_flip.assert_called_once_with(player, effect)

    def test_ready_and_flip_still_resolve_when_gift_deck_is_empty(self):
        module = import_module("cards.pack.hercules.hercules.59001a")
        ability = module.GetAbilities()[0]
        identity = MagicMock()
        player = SimpleNamespace(GetIdentity=MagicMock(return_value=identity))
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))
        deck = SimpleNamespace(GetTop=MagicMock(return_value=None))

        with patch.object(module, "GetGiftDeck", return_value=deck), patch.object(
            module,
            "YouMayFlipToYourAlterEgoForm",
        ) as may_flip:
            ability.operation(effect, SimpleNamespace())

        identity.Ready.assert_called_once_with(effect)
        may_flip.assert_called_once_with(player, effect)


if __name__ == "__main__":
    unittest.main()
