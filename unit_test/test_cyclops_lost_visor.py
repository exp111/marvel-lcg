from importlib import import_module
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability.condition import Condition
from game.message import Message


class TestLostVisor(unittest.TestCase):

    def setUp(self):
        self.abilities = import_module(
            "cards.pack.cyclops.cyclops.33027"
        ).GetAbilities()

    def test_attack_restriction_follows_both_identity_faces(self):
        restriction = next(
            ability
            for ability in self.abilities
            if ability.when == Message.CheckIfUnitCanAttack
        )
        effect = MagicMock()
        message = MagicMock()

        with patch.object(Condition, "CheckWhichCard", return_value=True) as check:
            self.assertTrue(restriction.conditions[0](effect, message))

        check.assert_called_once_with(
            "AttachedIdentity",
            message.check_unit,
            effect,
        )

    def test_attack_labeled_abilities_are_also_blocked(self):
        self.assertTrue(
            any(
                ability.when == Message.CheckEffectCondition
                for ability in self.abilities
            )
        )


if __name__ == "__main__":
    unittest.main()
