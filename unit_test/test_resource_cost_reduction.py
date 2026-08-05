from importlib import import_module
from types import SimpleNamespace
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability.factory import AbilityFactory
from game.element.cost import Cost


class TestResourceCostReduction(unittest.TestCase):

    def test_shared_reducer_subtracts_from_play_cost(self):
        reducer = AbilityFactory.ReduceCostToPlayFaceWhen(
            None,
            1,
            "AnyPlayer",
        )
        message = CostMessage("3")
        source = object()

        reducer.operation(SimpleNamespace(this=source), message)

        self.assertEqual(message.cost.val, 2)

    def test_uncanny_x_men_uses_controller_only_reducer(self):
        reducer = import_module("cards.pack.storm.36018").GetAbilities()[-1]
        controller = object()
        effect = SimpleNamespace(
            context=SimpleNamespace(ask_player=controller),
        )

        self.assertTrue(
            reducer.conditions[2](effect, SimpleNamespace(to_player=controller))
        )
        self.assertFalse(
            reducer.conditions[2](effect, SimpleNamespace(to_player=object()))
        )


class CostMessage:

    def __init__(self, value):
        self.cost = Cost(value)
        self.check_effect = SimpleNamespace(
            this=SimpleNamespace(
                card=SimpleNamespace(
                    ui=SimpleNamespace(
                        cost=SimpleNamespace(Add=lambda effect, source: None),
                    ),
                ),
            ),
        )

    def UpdateCost(self, value, by_effect):
        self.cost += value


if __name__ == "__main__":
    unittest.main()
