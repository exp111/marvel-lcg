import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability.factory import AbilityFactory
from game.card.face.base import Enemy


class TestAttachedIdentityRestrictions(unittest.TestCase):

    def test_defense_ability_restriction_accepts_attached_identity(self):
        abilities = AbilityFactory.UnitCannotDefend(
            "AttachedIdentity",
            Enemy,
            cannot_trigger_defense_ability=True,
        )

        self.assertEqual(len(abilities), 2)
        self.assertEqual(
            abilities[1].when.__name__,
            "CheckEffectCondition",
        )


if __name__ == "__main__":
    unittest.main()
