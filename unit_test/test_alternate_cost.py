import unittest
from unittest.mock import MagicMock

from engine import Engine  # noqa: F401

from cards.pack.ironheart.ironheart import ChildProdigy
from game.element.cost import Cost
from game.element.resources import Resources


class TestAlternateCosts(unittest.TestCase):
    def test_ironheart_level_two_exposes_both_payment_options(self):
        cost = ChildProdigy(2).GetCost(MagicMock(), [])

        self.assertEqual(cost.GetPaymentText(), "B|2")

    def test_one_mental_or_two_resources_matches(self):
        cost = Cost("B", or_cost=Cost("2"))

        for resources in ("B", "G", "YY", "YR", "BB"):
            with self.subTest(resources=resources):
                self.assertTrue(Resources(resources).IsMatchCost(cost))

        for resources in ("R", "Y"):
            with self.subTest(resources=resources):
                self.assertFalse(Resources(resources).IsMatchCost(cost))

    def test_unrelated_resource_is_not_offered_for_colored_alternatives(self):
        cost = Cost("RRR", or_cost=Cost("YYY"))

        self.assertFalse(Resources("B").CanPayThisCost(cost))
        self.assertTrue(Resources("R").CanPayThisCost(cost))
        self.assertTrue(Resources("Y").CanPayThisCost(cost))


if __name__ == "__main__":
    unittest.main()
