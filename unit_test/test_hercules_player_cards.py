from importlib import import_module
from inspect import getclosurevars
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestEmbodyPathos(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.hercules.hercules.59003")
        self.ability = self.module.GetAbilities()[0]
        self.labor = MagicMock()
        self.labor.CastTo.return_value = self.labor
        self.player = MagicMock()
        self.world = SimpleNamespace(started_player_num=4)
        self.effect = SimpleNamespace(this=self.labor, world=self.world)
        self.message = SimpleNamespace(GetToPlayer=MagicMock(return_value=self.player))

    def test_reveals_chosen_scheme_treating_per_player_icons_as_one(self):
        scheme = MagicMock()
        scheme.player_num = 4
        scheme.player_num_icon_override = None
        scheme.paper.desc = {
            "StartingThreat": "2*",
            "Hinder": "1*",
            "Hazard": "1",
        }
        scheme.IsInPlay.return_value = True

        def reveal(player, effect):
            self.assertEqual(scheme.player_num_icon_override, 1)
            return MagicMock()

        scheme.Reveal.side_effect = reveal

        with patch.object(self.module.Find, "Find", return_value=scheme) as find:
            self.ability.operation(self.effect, self.message)

        find.assert_called_once()
        self.assertIs(find.call_args.kwargs["who_perform"], self.player)
        self.assertEqual(
            scheme.SetPlayerNum.call_args_list,
            [call(1), call(4)],
        )
        self.assertEqual(
            scheme.InitPrintedValue.call_args_list,
            [
                call("StartingThreat", "2*"),
                call("Hinder", "1*"),
                call("StartingThreat", "2*"),
                call("Hinder", "1*"),
            ],
        )
        self.assertIsNone(scheme.player_num_icon_override)
        self.labor.AttachTo2.assert_called_once_with(scheme, self.effect)
        self.labor.PlaceThreatOnSchemes.assert_called_once_with(
            [scheme], 6, self.effect
        )

    def test_discards_labor_when_no_side_scheme_can_be_found(self):
        with patch.object(self.module.Find, "Find", return_value=None), patch.object(
            self.module.Faces,
            "DiscardAll",
        ) as discard_all:
            self.ability.operation(self.effect, self.message)

        discard_all.assert_called_once_with([self.labor], self.effect)
        self.labor.AttachTo2.assert_not_called()

    def test_discards_labor_when_chosen_scheme_cannot_be_revealed(self):
        scheme = MagicMock()
        scheme.player_num = 4
        scheme.player_num_icon_override = None
        scheme.paper.desc = {"StartingThreat": "2*"}
        scheme.Reveal.return_value = None

        with patch.object(self.module.Find, "Find", return_value=scheme), patch.object(
            self.module.Faces,
            "DiscardAll",
        ) as discard_all:
            self.ability.operation(self.effect, self.message)

        discard_all.assert_called_once_with([self.labor], self.effect)
        self.labor.AttachTo2.assert_not_called()


class TestPerPlayerIconOverride(unittest.TestCase):

    def test_worlds_uses_the_resolving_cards_local_icon_override(self):
        module = import_module("cards.pack.hercules.hercules.59003")
        face = SimpleNamespace(player_num_icon_override=1)
        world = SimpleNamespace(GetPlayerNumIcon=MagicMock(return_value=4))
        effect = SimpleNamespace(this=face, world=world)

        self.assertEqual(module.Worlds.GetPlayerNumIcon(effect), 1)
        world.GetPlayerNumIcon.assert_not_called()


class TestGauntletsOfHercules(unittest.TestCase):

    def test_interrupt_is_unavailable_when_no_gifts_are_controlled(self):
        module = import_module("cards.pack.hercules.hercules.59013")
        ability = module.GetAbilities()[0]
        gift_condition = next(
            condition
            for condition in ability.conditions
            if condition.__code__.co_filename.endswith("59013.py")
        )
        effect = SimpleNamespace(GetInitiator=MagicMock())

        with patch.object(module, "CountGifts", return_value=0):
            self.assertFalse(gift_condition(effect, SimpleNamespace()))

        with patch.object(module, "CountGifts", return_value=1):
            self.assertTrue(gift_condition(effect, SimpleNamespace()))


class TestOlympus(unittest.TestCase):

    def test_exhaust_cost_is_paid_once_by_the_resource_check_effect(self):
        module = import_module("cards.pack.hercules.hercules.59012")
        generate_resources, can_generate_resources = module.GetAbilities()

        self.assertEqual(generate_resources.cost_funcs, [])
        self.assertEqual(len(can_generate_resources.cost_funcs), 1)
        self.assertIsInstance(
            can_generate_resources.cost_funcs[0],
            module.CostFunc.Exhaust,
        )

    def test_generates_one_wild_resource_per_gift(self):
        module = import_module("cards.pack.hercules.hercules.59012")
        generate_resources, can_generate_resources = module.GetAbilities()
        player = MagicMock()
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))
        message = SimpleNamespace()

        resource_function = getclosurevars(generate_resources.operation).nonlocals["res_fn"]
        with patch.object(module, "CountGifts", return_value=1):
            generated = resource_function(effect, message)

        self.assertEqual(generated.g, 1)
        self.assertEqual(generated.val, 1)


class TestSonOfZeus(unittest.TestCase):

    def test_event_is_unavailable_when_none_of_its_effects_can_change_the_game(self):
        module = import_module("cards.pack.hercules.hercules.59010")
        ability = module.GetAbilities()[0]
        condition = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "can_resolve_son_of_zeus"
        )
        identity = SimpleNamespace(
            CanReady=MagicMock(return_value=False),
            CanGainTough=MagicMock(return_value=False),
        )
        player = SimpleNamespace(
            GetIdentity=MagicMock(return_value=identity),
            GetControlCards=MagicMock(return_value=[]),
        )
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        with patch.object(module, "CountGifts", return_value=0):
            self.assertFalse(condition(effect, SimpleNamespace()))

        with patch.object(module, "CountGifts", return_value=3):
            self.assertTrue(condition(effect, SimpleNamespace()))


class TestAncientRivalry(unittest.TestCase):

    def test_event_is_unavailable_without_an_upgrade_to_recover_or_character_to_ready(self):
        module = import_module("cards.pack.hercules.59026")
        ability = module.GetAbilities()[0]
        condition = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "can_resolve_ancient_rivalry"
        )
        player = SimpleNamespace(
            discard_pile=SimpleNamespace(FindCard=MagicMock(return_value=None)),
        )
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        with patch.object(module.Worlds, "FindCardsOnField", return_value=[]):
            self.assertFalse(condition(effect, SimpleNamespace()))

        with patch.object(module.Worlds, "FindCardsOnField", return_value=[MagicMock()]):
            self.assertTrue(condition(effect, SimpleNamespace()))


if __name__ == "__main__":
    unittest.main()
