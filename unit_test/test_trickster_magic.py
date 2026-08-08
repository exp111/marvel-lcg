import unittest
from importlib import import_module

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestTricksterMagic(unittest.TestCase):

    def test_puppet_master_defense_restriction_builds(self):
        abilities = import_module(
            "cards.pack.tt.trickster_magic.55061"
        ).GetAbilities()

        self.assertEqual(len(abilities), 3)

    def test_love_triangle_defense_restriction_builds(self):
        abilities = import_module(
            "cards.pack.tt.trickster_magic.55062"
        ).GetAbilities()

        self.assertEqual(len(abilities), 4)


if __name__ == "__main__":
    unittest.main()
