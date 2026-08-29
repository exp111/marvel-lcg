from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestCrisisOfFaith(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.ncrawler.nightcrawler.48026")
        self.ability = self.module.GetAbilities()[0]
        self.obligation = MagicMock()
        self.obligation.CastTo.return_value = self.obligation
        self.player = MagicMock()
        self.player.IsAlterEgo.return_value = True
        self.effect = SimpleNamespace(this=self.obligation)
        self.message = SimpleNamespace(
            GetGaveToPlayer=MagicMock(return_value=self.player),
        )

        with patch.object(self.module, "YouMayFlipToYourAlterEgoForm"):
            self.ability.operation(self.effect, self.message)

        self.choices = self.player.ChooseAbilities.call_args.args[1:]

    def test_discard_choice_accepts_attack_or_defense_events(self):
        discard_choice = self.choices[1]
        selector = discard_choice.selectors[0]

        self.assertEqual(selector.selector_range.raw_range, ("Zero", "All"))
        self.assertEqual(selector.selector_rule.raw_select_rule, "")
        self.assertEqual(
            selector.selector_filter.finder.traits,
            ["ATTACK", "DEFENSE"],
        )

    def test_discard_choice_discards_matching_events_before_obligation(self):
        discard_choice = self.choices[1]
        event = MagicMock()
        choice_effect = SimpleNamespace(
            targets=[event],
            GetPaidResources=MagicMock(),
        )

        with patch.object(self.module.Faces, "DiscardAll") as discard_all:
            discard_choice.operation(choice_effect, SimpleNamespace())

        self.assertEqual(
            discard_all.call_args_list,
            [call([event], self.effect), call([self.obligation], self.effect)],
        )


if __name__ == "__main__":
    unittest.main()
