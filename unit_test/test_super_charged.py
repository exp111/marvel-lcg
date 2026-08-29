from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability.cost_func import CostFunc
from game.card.face.attribute.can_place_counter import CanPlaceCounter


class TestSuperCharged(unittest.TestCase):

    def test_attack_bonus_uses_charge_counters_from_before_discard(self):
        module = import_module("cards.pack.aoa.bishop.45006")
        ability = module.GetAbilities()[1]
        super_charged = MagicMock(spec=CanPlaceCounter)
        super_charged.card = MagicMock()
        super_charged.components = MagicMock()
        super_charged.components.counter.GetCounterNames.return_value = ["charge"]
        super_charged.GetCounters.return_value = 2

        discard_cost = CostFunc.Discard("This")
        effect = SimpleNamespace()
        with patch(
            "game.operate.faces.Faces.DiscardAll",
            return_value=[super_charged],
        ):
            self.assertTrue(discard_cost.call_fn([super_charged], effect, None))

        # Leaving play resets the live counter component before the ability resolves.
        super_charged.GetCounters.return_value = 0
        effect.this = SimpleNamespace(CastTo=MagicMock(return_value=super_charged))
        effect.cost_func = SimpleNamespace(Get=MagicMock(return_value=discard_cost))
        message = MagicMock()

        ability.operation(effect, message)

        self.assertEqual(
            discard_cost.return_discarded_counters[super_charged]["charge"],
            2,
        )
        message.GainATKForThisAttack.assert_called_once_with(4, effect)


if __name__ == "__main__":
    unittest.main()
