from importlib import import_module
import unittest
from unittest.mock import Mock

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.element.cost import Cost
from game.element.resources import Resources


class TestMachineMan(unittest.TestCase):

    def test_up_to_cost_accepts_overpayment(self):
        self.assertTrue(
            Resources("YYYY").IsMatchCost(Cost("3", up_to=True))
        )

    def test_overpayment_caps_attack_and_thwart_bonus_at_three(self):
        module = import_module("cards.pack.vision.26022")
        machine_man = module.GetAbilities()[0]

        effect = Mock()
        message = Mock()
        ally = Mock()
        paid_resources = Mock()
        paid_resources.val = 4
        effect.this.CastTo.return_value = ally
        effect.GetPaidResources.return_value = paid_resources

        machine_man.operation(effect, message)

        ally.GainForThisActive.assert_called_once_with(
            effect,
            message,
            attack=3,
            thwart=3,
        )


if __name__ == "__main__":
    unittest.main()
