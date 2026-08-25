import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability.factory import AbilityFactory
from game.card.card_finder import CardFinder


class TestThwartTargetRestrictions(unittest.TestCase):

    def test_can_only_thwart_this_observes_other_scheme_targets(self):
        abilities = AbilityFactory.UnitCannotThwartTarget(
            CardFinder(name="Hope Summers"),
            can_only_thwart="This",
        )

        self.assertEqual(len(abilities), 1)
        self.assertFalse(abilities[0].is_local)


if __name__ == "__main__":
    unittest.main()
