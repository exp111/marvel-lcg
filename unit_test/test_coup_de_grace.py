from importlib import import_module
import unittest
from unittest.mock import Mock

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestCoupDeGrace(unittest.TestCase):

    def test_campaign_upgrade_adds_damage_to_any_attack(self):
        effect = Mock()
        attack_message = Mock()
        ability = import_module(
            "cards.pack.mut_gen.brawler.32176"
        ).GetAbilities()[0]

        ability.operation(effect, attack_message)

        attack_message.DealAdditionalDamage.assert_called_once_with(3, effect)
        attack_message.GainOverKill.assert_called_once_with(effect)
        attack_message.GainATKForThisAttack.assert_not_called()


if __name__ == "__main__":
    unittest.main()
