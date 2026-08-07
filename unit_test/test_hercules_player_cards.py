from importlib import import_module
from inspect import getclosurevars
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestNewLaborsOfHercules(unittest.TestCase):

    def test_action_checks_for_any_labor_in_play(self):
        module = import_module("cards.pack.hercules.hercules.59001b")
        ability = module.GetAbilities()[1]
        condition = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "no_labor_in_play"
        )
        world = MagicMock()
        world.FindCardsOnField.return_value = [MagicMock()]
        effect = SimpleNamespace(world=world)

        self.assertFalse(condition(effect, SimpleNamespace()))
        self.assertNotIn("owner", world.FindCardsOnField.call_args.kwargs)


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

    def test_completion_is_mandatory_and_moves_the_labor_to_victory(self):
        completion = self.module.GetAbilities()[-1]
        labor = MagicMock()
        effect = SimpleNamespace(this=labor)

        self.assertEqual(completion.type, self.module.AbilityType.ForcedInterrupt)
        with patch.object(self.module.Faces, "AddToVictoryDisplay") as add_to_victory:
            completion.operation(effect, SimpleNamespace())

        add_to_victory.assert_called_once_with([labor], effect)

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

    def test_grants_retaliate_for_only_the_current_attack(self):
        module = import_module("cards.pack.hercules.hercules.59013")
        ability = module.GetAbilities()[0]
        hercules = MagicMock()
        attack = MagicMock()
        player = MagicMock()
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))
        message = SimpleNamespace(trigger=hercules, would_atk_message=attack)

        with patch.object(module, "CountGifts", return_value=2):
            ability.operation(effect, message)

        hercules.TemporaryGain.assert_called_once_with(
            effect,
            attack,
            retaliate=2,
        )
        hercules.GainForThisActive.assert_not_called()


class TestAmadeusCho(unittest.TestCase):

    def test_redirects_before_defenders_are_chosen(self):
        module = import_module("cards.pack.hercules.hercules.59008")
        ability = module.GetAbilities()[0]

        self.assertIs(ability.when, module.Message.WhenUnitWouldAttack)
        self.assertEqual(ability.type, module.AbilityType.ForcedInterrupt)

    def test_only_redirects_attacks_against_its_controllers_identity(self):
        module = import_module("cards.pack.hercules.hercules.59008")
        ability = module.GetAbilities()[0]
        controller_identity = MagicMock()
        other_identity = MagicMock()
        controller = SimpleNamespace(
            GetIdentity=MagicMock(return_value=controller_identity),
        )
        amadeus = MagicMock()
        amadeus.GetControlByPlayer.return_value = controller
        effect = SimpleNamespace(this=amadeus)
        condition = next(
            condition
            for condition in ability.conditions
            if condition.__name__ == "attacks_your_identity"
        )

        against_controller = SimpleNamespace(
            HasTarget=MagicMock(side_effect=lambda target: target is controller_identity),
        )
        against_other_player = SimpleNamespace(
            HasTarget=MagicMock(side_effect=lambda target: target is other_identity),
        )

        self.assertTrue(condition(effect, against_controller))
        self.assertFalse(condition(effect, against_other_player))

    def test_replaces_the_initial_attack_target_with_amadeus(self):
        module = import_module("cards.pack.hercules.hercules.59008")
        ability = module.GetAbilities()[0]
        amadeus = MagicMock()
        amadeus.CastTo.return_value = amadeus
        effect = SimpleNamespace(this=amadeus)
        message = SimpleNamespace(
            ReplaceTarget=MagicMock(),
            Present_Activate=MagicMock(),
        )

        ability.operation(effect, message)

        message.ReplaceTarget.assert_called_once_with(amadeus)
        message.Present_Activate.assert_called_once_with(None, effect)


class TestHerculesGiftEvents(unittest.TestCase):

    def test_gift_of_battle_deals_five_attack_damage(self):
        module = import_module("cards.pack.hercules.hercules.59009")
        ability = module.GetAbilities()[1]
        event = MagicMock()
        event.CastTo.return_value = event
        target = MagicMock()
        effect = SimpleNamespace(this=event, targets=[target])

        ability.operation(effect, SimpleNamespace())

        event.DealDamage.assert_called_once()
        args, kwargs = event.DealDamage.call_args
        self.assertEqual(args[:3], ([target], 5, effect))
        self.assertIsInstance(kwargs["property"], module.AttackProperty)

    def test_wisdom_of_athena_removes_four_threat(self):
        module = import_module("cards.pack.hercules.hercules.59011")
        ability = module.GetAbilities()[1]
        event = MagicMock()
        event.CastTo.return_value = event
        scheme = MagicMock()
        effect = SimpleNamespace(this=event, targets=[scheme])

        ability.operation(effect, SimpleNamespace())

        event.RemoveThreatFromSchemes.assert_called_once_with(
            [scheme],
            4,
            effect,
        )


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


class TestPrinceOfPower(unittest.TestCase):

    def test_heals_hercules_for_the_attacks_excess_damage(self):
        module = import_module("cards.pack.hercules.hercules.59017")
        ability = module.GetAbilities()[0]
        identity = MagicMock()
        player = SimpleNamespace(GetIdentity=MagicMock(return_value=identity))
        prince_of_power = MagicMock()
        effect = SimpleNamespace(
            this=prince_of_power,
            GetInitiator=MagicMock(return_value=player),
        )
        message = SimpleNamespace(excess_damage=3)

        prince_operation = getclosurevars(ability.operation).nonlocals["operation"]
        prince_operation(effect, message)

        prince_of_power.HealthUnits.assert_called_once_with(
            [identity],
            3,
            effect,
        )


class TestGoldenMace(unittest.TestCase):

    def test_adds_attack_per_gift_and_overkill_to_the_basic_attack(self):
        module = import_module("cards.pack.hercules.hercules.59014")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))
        message = MagicMock()

        with patch.object(module, "CountGifts", return_value=3):
            ability.operation(effect, message)

        message.GainATKForThisAttack.assert_called_once_with(3, effect)
        message.GainOverKill.assert_called_once_with(effect)


class TestHercsHelm(unittest.TestCase):

    def test_prevents_one_damage_from_only_the_triggering_attack(self):
        module = import_module("cards.pack.hercules.hercules.59015")
        ability = module.GetAbilities()[0]
        attack = MagicMock()
        helm = MagicMock()
        effect = SimpleNamespace(this=helm)

        ability.operation(effect, attack)

        registered = helm.effect.RegisterTemp.call_args
        prevention_ability = registered.args[0]
        self.assertTrue(registered.kwargs["unregister_after_exec"])
        self.assertIs(registered.kwargs["until_event_end"], attack)
        damage_message = MagicMock()
        prevention_effect = SimpleNamespace()
        prevention_ability.operation(prevention_effect, damage_message)
        damage_message.PreventDamage.assert_called_once_with(
            1,
            prevention_effect,
        )


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

    def test_card_data_registers_hercules_and_thor_team_up(self):
        root = Path(__file__).resolve().parents[1]
        cards = json.loads((root / "data" / "cards.json").read_text(encoding="utf-8"))
        ancient_rivalry = next(
            card
            for pack in cards.values()
            for card in pack
            if card.get("card_id") == "59026"
        )

        self.assertEqual(ancient_rivalry["desc"]["TeamUp"], "Hercules;Thor")

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
