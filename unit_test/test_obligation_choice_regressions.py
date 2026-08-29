from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


def get_obligation_choices(module_name):
    module = import_module(module_name)
    ability = module.GetAbilities()[0]
    obligation = MagicMock()
    obligation.CastTo.return_value = obligation
    identity = MagicMock()
    player = MagicMock()
    player.GetIdentity.return_value = identity
    player.IsAlterEgo.return_value = True
    effect = SimpleNamespace(this=obligation)
    message = SimpleNamespace(
        GetGaveToPlayer=MagicMock(return_value=player),
    )

    with patch.object(module, "YouMayFlipToYourAlterEgoForm"):
        ability.operation(effect, message)

    return module, obligation, identity, player, effect, player.ChooseAbilities.call_args.args[1:]


class TestCareForCassie(unittest.TestCase):

    def test_empty_hand_still_applies_form_restriction_and_discards_obligation(self):
        module, obligation, _, player, effect, choices = get_obligation_choices(
            "cards.pack.ant.ant_man.12025"
        )
        discard_choice = choices[1]
        choice_effect = SimpleNamespace(
            targets=[],
            GetPaidResources=MagicMock(),
        )

        with patch.object(module.Faces, "DiscardAll") as discard_all, patch.object(
            module.Players,
            "CannotChangeFormDuringNextTurn",
        ) as cannot_change_form:
            discard_choice.operation(choice_effect, SimpleNamespace())

        cannot_change_form.assert_called_once_with(player, effect)
        self.assertEqual(
            discard_all.call_args_list,
            [call([], effect), call([obligation], effect)],
        )


class TestRedDreams(unittest.TestCase):

    def test_no_mental_cards_still_deals_damage(self):
        module, obligation, identity, _, effect, choices = get_obligation_choices(
            "cards.pack.wsp.wasp.13026"
        )
        discard_choice = choices[1]
        choice_effect = SimpleNamespace(
            targets=[],
            GetPaidResources=MagicMock(),
        )

        with patch.object(module.Faces, "DiscardAll") as discard_all:
            discard_choice.operation(choice_effect, SimpleNamespace())

        identity.TakeDamage.assert_called_once_with(obligation, 1, effect)
        self.assertEqual(
            discard_all.call_args_list,
            [call([], effect), call([obligation], effect)],
        )


class TestPastDemons(unittest.TestCase):

    def test_status_penalty_remains_available_when_statuses_cannot_be_added(self):
        _, _, _, _, _, choices = get_obligation_choices(
            "cards.pack.wolv.wolverine.35027"
        )
        status_choice = choices[1]

        self.assertIsNone(
            status_choice.selectors[0].selector_filter.finder.canbe_status
        )


class TestRedRoomProgramming(unittest.TestCase):

    def test_empty_hand_discards_obligation_without_zero_damage_assignment(self):
        module, obligation, identity, _, effect, choices = get_obligation_choices(
            "cards.pack.winter.winter_soldier.54027"
        )
        discard_choice = choices[1]
        choice_effect = SimpleNamespace(
            targets=[],
            GetPaidResources=MagicMock(),
        )

        with patch.object(module.Faces, "DiscardAll", side_effect=[[], [obligation]]):
            discard_choice.operation(choice_effect, SimpleNamespace())

        identity.TakeIndirectDamage.assert_not_called()


class TestTargetedPenaltyOptions(unittest.TestCase):

    def test_penalty_choices_remain_available_with_no_matching_cards(self):
        cases = {
            "cards.pack.ant.ant_man.12025": ("Zero", 1),
            "cards.pack.bkw.black_widow.08025": ("Zero", 1),
            "cards.pack.core.black_panther.01155": ("Zero", 1),
            "cards.pack.core.iron_man.01170": ("Zero", "All"),
            "cards.pack.gam.gamora.18024": ("Zero", 2),
            "cards.pack.msm.ms_marvel.05025": ("Zero", 1),
            "cards.pack.nebu.nebula.22027": ("Zero", 2),
            "cards.pack.ncrawler.nightcrawler.48026": ("Zero", "All"),
            "cards.pack.sm.spider_man_miles_morales.27056": ("Zero", "All"),
            "cards.pack.spdr.spdr.31025": ("Zero", 1),
            "cards.pack.thor.thor.06026": ("Zero", 1),
            "cards.pack.trors.hawkeye.04026": ("Zero", 1),
            "cards.pack.trors.spider_woman.04053": ("Zero", 1),
            "cards.pack.winter.winter_soldier.54027": ("Zero", 1),
            "cards.pack.wsp.wasp.13026": ("Zero", "All"),
        }

        for module_name, expected_range in cases.items():
            with self.subTest(module_name=module_name):
                _, _, _, _, _, choices = get_obligation_choices(module_name)
                self.assertEqual(len(choices), 2)
                self.assertEqual(
                    choices[1].selectors[0].selector_range.raw_range,
                    expected_range,
                )


if __name__ == "__main__":
    unittest.main()
