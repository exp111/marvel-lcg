from importlib import import_module
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability import AbilityType


class TestWonderMan(unittest.TestCase):

    def test_energy_siphon_uses_discard_for_resource_ability_type(self):
        module = import_module("cards.pack.wonder_man.wonder_man.58006")
        resource_ability = module.GetAbilities()[0]

        self.assertEqual(resource_ability.type, AbilityType.DiscardForResource)


if __name__ == "__main__":
    unittest.main()
