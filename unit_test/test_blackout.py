from importlib import import_module
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestBlackout(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.deadpool.44053")
        self.ability = self.module.GetAbilities()[0]

        self.blackout = MagicMock()
        self.blackout.GetCounters.side_effect = [1, 2, 2, 2]

        self.scheme = MagicMock()
        scheme_target = MagicMock()
        scheme_target.CastTo.return_value = self.scheme

        self.resources = MagicMock()
        self.resources.HasColor.side_effect = lambda color: color == "R"

        self.player = MagicMock()
        self.player.AskChooseOneText.return_value = "R"

        self.effect = MagicMock()
        self.effect.this.CastTo.return_value = self.blackout
        self.effect.targets = [scheme_target]
        self.effect.GetPaidResources.return_value = self.resources
        self.effect.GetInitiator.return_value = self.player

    def resolve_with_villain(self, villain):
        finder = MagicMock()
        with patch.object(
            self.module,
            "CardFinder",
            return_value=finder,
        ) as card_finder, patch.object(
            self.module.Worlds,
            "ChooseVillain",
            return_value=villain,
        ) as choose_villain, patch.object(
            self.module.Faces,
            "PlaceCountersOn",
        ), patch.object(
            self.module.Faces,
            "DiscardAll",
        ), patch.object(
            self.module.Faces,
            "GiveStatus",
        ) as give_status:
            self.ability.operation(self.effect, MagicMock())

        card_finder.assert_called_once_with(canbe_confused=True)
        choose_villain.assert_called_once_with(
            self.effect,
            finder,
            prompt="Choose a villain to confuse",
        )
        return give_status

    def test_chooses_which_eligible_villain_to_confuse(self):
        villain = MagicMock(name="Corvus")

        give_status = self.resolve_with_villain(villain)

        give_status.assert_called_once_with(
            [villain],
            "Confused",
            self.effect,
        )

    def test_skips_the_choice_when_no_villain_can_be_confused(self):
        give_status = self.resolve_with_villain(None)

        give_status.assert_not_called()


if __name__ == "__main__":
    unittest.main()
