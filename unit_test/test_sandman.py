from importlib import import_module
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestCityStreets(unittest.TestCase):

    def test_exhaust_cost_can_choose_a_controlled_ally(self):
        module = import_module("cards.pack.sm.sandman.27065")
        ability = module.GetAbilities()[-1]
        exhaust_cost = ability.cost_funcs[0]
        identity = MagicMock(name="identity")
        ally = MagicMock(name="ally")
        player = MagicMock()
        player.GetControlCharacters.return_value = [identity, ally]

        with patch(
            "game.selector.selector_target_helper.Select.GetYou",
            return_value=player,
        ):
            legal_targets = exhaust_cost.selector.selector_target.get_targets_fn(
                MagicMock()
            )

        self.assertEqual(exhaust_cost.selector.target_text, "YouControlUnit")
        self.assertEqual(legal_targets, [identity, ally])

    def test_removes_sand_equal_to_the_exhausted_allys_attack(self):
        module = import_module("cards.pack.sm.sandman.27065")
        ability = module.GetAbilities()[-1]
        effect = MagicMock()
        city_streets = effect.this.CastTo.return_value
        ally = MagicMock()
        ally.attack = 2
        effect.cost_func.Get.return_value.return_exhausted_cards = [ally]

        with patch.object(module.HasAttack, "IsType", return_value=True), patch.object(
            module.Faces,
            "RemoveCountersOn",
        ) as remove_counters:
            ability.operation(effect, MagicMock())

        remove_counters.assert_called_once_with(
            [city_streets],
            2,
            "sand",
            effect,
        )


if __name__ == "__main__":
    unittest.main()
