from importlib import import_module
import unittest
from unittest.mock import Mock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestRetrieveOdinsArmor(unittest.TestCase):

    def test_heals_odin_and_flips_him_to_king_side(self):
        module = import_module(
            "cards.pack.mts.the_mad_titans_shadow_campaign.21186b"
        )
        retrieve_odins_armor = module.GetAbilities()[1]

        effect = Mock()
        message = Mock()
        odin = Mock()
        odin.HasTrait.return_value = False

        with patch.object(
            module.Worlds,
            "FindCardOnField",
            return_value=odin,
        ):
            retrieve_odins_armor.operation(effect, message)

        effect.this.HealthUnits.assert_called_once_with(
            [odin],
            "All",
            effect,
        )
        odin.FlipTo.assert_called_once_with(effect, trait="KING")


if __name__ == "__main__":
    unittest.main()
