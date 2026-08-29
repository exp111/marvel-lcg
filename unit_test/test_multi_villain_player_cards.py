from importlib import import_module
import unittest
from unittest.mock import ANY, MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestMultiVillainPlayerCards(unittest.TestCase):

    def test_white_tiger_uses_the_chosen_villains_stage(self):
        module = import_module("cards.pack.mts.21013")
        ability = module.GetAbilities()[0]

        player = MagicMock()
        target = MagicMock()
        target.GetControlByPlayer.return_value = player

        effect = MagicMock()
        effect.targets = [target]

        villain = MagicMock()
        villain.printed_stage = 2

        with patch.object(
            module.Worlds,
            "ChooseVillain",
            return_value=villain,
        ) as choose_villain:
            ability.operation(effect, MagicMock())

        choose_villain.assert_called_once_with(
            effect,
            prompt="Choose a villain for White Tiger's stage value",
        )
        player.DrawUp.assert_called_once_with(2, effect)

    def test_in_betweener_damages_the_chosen_villain(self):
        module = import_module("cards.pack.mts.21042")
        ability = module.GetAbilities()[1]

        card = MagicMock()
        effect = MagicMock()
        effect.this.CastTo.return_value = card

        villain = MagicMock()

        with patch.object(
            module.Worlds,
            "ChooseVillain",
            return_value=villain,
        ) as choose_villain, patch.object(
            module.Faces,
            "RemoveAllFromGame",
        ) as remove_all:
            ability.operation(effect, MagicMock())

        choose_villain.assert_called_once_with(
            effect,
            prompt="Choose a villain to damage",
        )
        card.DealDamage.assert_called_once_with([villain], 2, effect)
        remove_all.assert_called_once_with([card], effect)

    def test_united_we_stand_uses_the_chosen_villains_stage(self):
        module = import_module("cards.pack.qsv.14031")
        ability = module.GetAbilities()[0]
        target_range = ability.selectors[0].selector_range.raw_range

        effect = MagicMock()
        villain = MagicMock()
        villain.printed_stage = 4

        with patch.object(
            module.Worlds,
            "ChooseVillain",
            return_value=villain,
        ) as choose_villain:
            maximum = target_range[1](effect)

        choose_villain.assert_called_once_with(
            effect,
            prompt="Choose a villain for United We Stand's stage value",
        )
        self.assertEqual(maximum, 3)

    def test_flash_freeze_only_tracks_the_attacking_villain(self):
        module = import_module("cards.pack.storm.storm.36012")
        ability = module.GetAbilities()[0]

        card = MagicMock()
        initiator = MagicMock()
        engaged_minions = [MagicMock(), MagicMock()]
        initiator.GetEngagedMinions.return_value = engaged_minions

        effect = MagicMock()
        effect.this.CastTo.return_value = card
        effect.GetInitiator.return_value = initiator

        attacking_villain = MagicMock()
        attacking_villain.CastTo.return_value = attacking_villain
        message = MagicMock()
        message.trigger = attacking_villain

        temp_ability = MagicMock()
        with patch.object(
            module.AbilityFactory,
            "WhenUnitAttackYou",
            return_value=temp_ability,
        ) as make_temp, patch.object(
            module.Worlds,
            "FindCardOnField",
            return_value=None,
        ), patch.object(
            module.Worlds,
            "GetVillains",
        ) as get_villains:
            ability.operation(effect, message)

        attacking_villain.GainForThisActive.assert_called_once_with(
            effect,
            message,
            attack=-3,
        )
        make_temp.assert_called_once_with(
            module.AbilityType.Temp0,
            [attacking_villain, *engaged_minions],
            ANY,
        )
        card.effect.RegisterTemp.assert_called_once_with(
            temp_ability,
            unregister_after_exec=False,
            until_phase_end=True,
        )
        get_villains.assert_not_called()


if __name__ == "__main__":
    unittest.main()
