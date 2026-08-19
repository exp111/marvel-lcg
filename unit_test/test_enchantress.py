from importlib import import_module
import unittest
from unittest.mock import Mock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestEnchantress(unittest.TestCase):

    @staticmethod
    def resolve_villain_reveal(card_id: str, *, standard: bool = True):
        module = import_module(f"cards.pack.tt.enchantress.{card_id}")
        ability = module.GetAbilities()[0]
        effect = Mock()
        villain = effect.this.CastTo.return_value
        future_of_despair = Mock()

        with patch.object(
            module.SetupCards,
            "PutIntoPlay",
            return_value=future_of_despair,
        ) as put_into_play, patch.object(
            module.Worlds,
            "IsStandard",
            return_value=standard,
        ):
            ability.operation(effect, Mock())

        return effect, villain, future_of_despair, put_into_play

    def test_stage_two_adds_three_threat_per_player(self):
        effect, villain, future, put_into_play = self.resolve_villain_reveal(
            "55002"
        )

        put_into_play.assert_called_once_with(
            effect,
            name="Future of Despair",
            from_where=["SetAside"],
        )
        villain.PlaceThreatOnSchemes.assert_called_once_with(
            [future],
            "3*",
            effect,
        )

    def test_stage_three_adds_four_threat_per_player(self):
        effect, villain, future, put_into_play = self.resolve_villain_reveal(
            "55003"
        )

        put_into_play.assert_called_once_with(
            effect,
            name="Future of Despair",
            from_where=["SetAside"],
        )
        villain.PlaceThreatOnSchemes.assert_called_once_with(
            [future],
            "4*",
            effect,
        )

    def test_future_of_despair_reveal_places_a_charm_counter_on_each_enchantment(self):
        module = import_module("cards.pack.tt.enchantress.55006")
        ability = module.GetAbilities()[-1]
        effect = Mock()
        enchantments = [Mock(), Mock()]

        with patch.object(
            module.Worlds,
            "FindCardsOnField",
            return_value=enchantments,
        ) as find_cards, patch.object(
            module.Faces,
            "PlaceCountersOn",
        ) as place_counters:
            ability.operation(effect, Mock())

        find_cards.assert_called_once()
        find_effect, finder = find_cards.call_args.args
        self.assertIs(find_effect, effect)
        self.assertEqual(finder.trait, "ENCHANTMENT")
        place_counters.assert_called_once_with(
            enchantments,
            1,
            "charm",
            effect,
        )


if __name__ == "__main__":
    unittest.main()
