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

    @staticmethod
    def make_effect(legal_target_count):
        return SimpleNamespace(
            context=SimpleNamespace(
                all_legal_targets=[None] * legal_target_count,
            ),
        )


if __name__ == "__main__":
    unittest.main()
