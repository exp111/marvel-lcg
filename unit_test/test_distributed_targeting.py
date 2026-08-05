from importlib import import_module
from types import SimpleNamespace
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.selector.factory import Select


class TestDistributedTargeting(unittest.TestCase):

    def test_exact_target_count_uses_full_value_when_available(self):
        count_targets = Select.ExactTargetCountUpToAvailable(3)

        self.assertEqual(count_targets(self.make_effect(1)), 1)
        self.assertEqual(count_targets(self.make_effect(3)), 3)
        self.assertEqual(count_targets(self.make_effect(6)), 3)

    def test_exact_target_count_does_not_depend_on_prepopulated_context(self):
        count_targets = Select.ExactTargetCountUpToAvailable(3)
        selector_range = Select.From(
            range=count_targets,
            repeat_rules="Threat",
        ).selector_range
        effect = self.make_effect(0)

        self.assertEqual(selector_range.GetRepeatTargetMax(effect, [None]), 3)
        self.assertEqual(selector_range.GetTargetMin(effect, [None] * 2), 2)
        self.assertEqual(selector_range.GetTargetMax(effect, [None] * 5), 3)

    def test_fixed_value_distribution_cards_require_the_full_amount(self):
        expected_counts = {
            "cards.pack.mut_gen.defender.32187": 3,
            "cards.pack.mut_gen.defender.32188": 5,
            "cards.pack.mut_gen.peacekeeper.32194": 5,
            "cards.pack.storm.storm.36010": 3,
            "cards.pack.trors.spider_woman.04038": 3,
            "cards.pack.wsp.wasp.13003": 4,
        }

        for module_name, expected_count in expected_counts.items():
            with self.subTest(module_name=module_name):
                ability = import_module(module_name).GetAbilities()[-1]
                target_range = ability.selectors[0].selector_range.raw_range

                self.assertTrue(callable(target_range))
                self.assertEqual(
                    target_range(self.make_effect(expected_count + 2)),
                    expected_count,
                )

    def test_shadowcat_can_choose_a_zero_threat_side_scheme(self):
        ability = import_module("cards.pack.iceman.46019").GetAbilities()[1]

        self.assertIsNone(ability.selectors[0].selector_filter.finder.has_threat)

    @staticmethod
    def make_effect(legal_target_count):
        return SimpleNamespace(
            context=SimpleNamespace(
                all_legal_targets=[None] * legal_target_count,
            ),
        )


if __name__ == "__main__":
    unittest.main()
