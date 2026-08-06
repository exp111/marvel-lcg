from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


ROOT = Path(__file__).resolve().parents[1]


class TestWonderManNemesisRegistration(unittest.TestCase):

    def test_starter_includes_obligation_and_complete_nemesis_set(self):
        starter = json.loads((ROOT / "deck" / "starter" / "wonder_man.json").read_text())

        self.assertEqual(starter["obligations"], ["58025"])
        self.assertEqual(
            starter["nemesis_set"],
            ["58026", "58027", "58028", "58029", "58029"],
        )

    def test_grim_reaper_is_registered_as_wonder_mans_nemesis(self):
        cards = json.loads((ROOT / "data" / "cards.json").read_text())
        papers = {paper["card_id"]: paper for paper in cards["wonder_man"]}

        self.assertEqual(papers["58026"]["desc"]["Nemesis"], "Wonder Man")
        for card_id in ("58026", "58027", "58028", "58029"):
            self.assertEqual(papers[card_id]["set_name"], "Wonder Man Nemesis")

    def test_selectable_nemesis_set_has_both_death_cannot_die_copies(self):
        nemesis = json.loads(
            (ROOT / "data" / "nemesis" / "wonder_man_nemesis.json").read_text()
        )

        self.assertEqual(
            nemesis["encounters"],
            ["58026", "58027", "58028", "58029", "58029"],
        )


class TestPacifism(unittest.TestCase):

    def test_tucked_card_action_discards_three_cards_then_pacifism(self):
        module = import_module("cards.pack.wonder_man.wonder_man.58025")
        ability = module.GetAbilities()[-1]
        tucked_cards = [MagicMock(), MagicMock(), MagicMock()]
        area = SimpleNamespace(GetAll=MagicMock(return_value=tucked_cards))
        ionic = SimpleNamespace(GetPlacedCardArea=MagicMock(return_value=area))
        obligation = MagicMock()
        player = SimpleNamespace(AskDiscardFaces=MagicMock(return_value=tucked_cards))
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=obligation)),
            GetInitiator=MagicMock(return_value=player),
        )

        with patch.object(module, "FindIonicPhysiology", return_value=ionic), patch.object(
            module.Faces,
            "DiscardAll",
        ) as discard_all:
            ability.operation(effect, SimpleNamespace())

        player.AskDiscardFaces.assert_called_once_with(tucked_cards, (3, 3), effect)
        discard_all.assert_called_once_with([obligation], effect)

    def test_tucked_card_action_keeps_pacifism_if_three_cards_are_not_discarded(self):
        module = import_module("cards.pack.wonder_man.wonder_man.58025")
        ability = module.GetAbilities()[-1]
        tucked_cards = [MagicMock(), MagicMock(), MagicMock()]
        area = SimpleNamespace(GetAll=MagicMock(return_value=tucked_cards))
        ionic = SimpleNamespace(GetPlacedCardArea=MagicMock(return_value=area))
        player = SimpleNamespace(AskDiscardFaces=MagicMock(return_value=tucked_cards[:2]))
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock()),
            GetInitiator=MagicMock(return_value=player),
        )

        with patch.object(module, "FindIonicPhysiology", return_value=ionic), patch.object(
            module.Faces,
            "DiscardAll",
        ) as discard_all:
            ability.operation(effect, SimpleNamespace())

        discard_all.assert_not_called()

    def test_exhaust_action_has_an_identity_exhaust_cost(self):
        module = import_module("cards.pack.wonder_man.wonder_man.58025")
        exhaust_action = module.GetAbilities()[-2]

        self.assertEqual(len(exhaust_action.cost_funcs), 1)
        self.assertIsInstance(exhaust_action.cost_funcs[0], module.CostFunc.Exhaust)


class TestWonderManNemesisAbilities(unittest.TestCase):

    def test_grim_reaper_deals_defeated_ally_controller_an_encounter_card(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58026")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        defeated_ally = SimpleNamespace(
            GetControlByPlayer=MagicMock(return_value=player),
            GetInventoryDeck=MagicMock(
                return_value=SimpleNamespace(Get=MagicMock(return_value=[])),
            ),
        )
        grim_reaper = MagicMock()
        effect = MagicMock()
        effect.this = grim_reaper
        attack_message = SimpleNamespace(
            target=defeated_ally,
            attacker=grim_reaper,
        )

        with patch.object(module.Condition, "CheckWhichCard", return_value=True):
            ability.operation(effect, attack_message)

        delayed_ability = grim_reaper.effect.RegisterTemp.call_args.args[0]
        delayed_ability.operation(effect, SimpleNamespace(target=defeated_ally))

        player.DealEncounterCards.assert_called_once_with(1, effect)

    def test_brother_vs_brother_cancels_attack_when_cost_cannot_be_paid(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58027")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        attacker = SimpleNamespace(GetControlByPlayer=MagicMock(return_value=player))
        message = SimpleNamespace(attacker=attacker, SetBeInstead=MagicMock())
        cost = SimpleNamespace(PayCost=MagicMock(return_value=False))
        effect = SimpleNamespace(this=MagicMock())

        with patch.object(module.CostFunc, "Discard", return_value=cost) as discard:
            ability.operation(effect, message)

        discard.assert_called_once_with("YourHandCards")
        cost.PayCost.assert_called_once_with(effect, player)
        message.SetBeInstead.assert_called_once_with(effect)

    def test_brother_vs_brother_allows_attack_after_cost_is_paid(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58027")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        attacker = SimpleNamespace(GetControlByPlayer=MagicMock(return_value=player))
        message = SimpleNamespace(attacker=attacker, SetBeInstead=MagicMock())
        cost = SimpleNamespace(PayCost=MagicMock(return_value=True))
        effect = SimpleNamespace(this=MagicMock())

        with patch.object(module.CostFunc, "Discard", return_value=cost):
            ability.operation(effect, message)

        message.SetBeInstead.assert_not_called()

    def test_activation_helper_reports_grim_reaper_in_play_when_activation_is_prevented(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis")
        player = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        result = SimpleNamespace(has_enemy=True, activated_cnt=0)

        with patch.object(
            module.Worlds.Enemies,
            "AllMinionActivateAgainstYou",
            return_value=result,
        ):
            found = module.ActivateGrimReaper(effect, player)

        self.assertTrue(found)

    def test_scythe_strike_does_not_deal_damage_when_activation_is_prevented(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58028")
        ability = module.GetAbilities()[0]
        identity = MagicMock()
        player = SimpleNamespace(GetIdentity=MagicMock(return_value=identity))
        treachery = MagicMock()
        effect = SimpleNamespace(this=SimpleNamespace(CastTo=MagicMock(return_value=treachery)))
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        with patch.object(module, "ActivateGrimReaper", return_value=True):
            ability.operation(effect, message)

        identity.TakeIndirectDamage.assert_not_called()

    def test_scythe_strike_deals_indirect_damage_when_grim_reaper_is_absent(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58028")
        ability = module.GetAbilities()[0]
        identity = MagicMock()
        player = SimpleNamespace(GetIdentity=MagicMock(return_value=identity))
        treachery = MagicMock()
        effect = SimpleNamespace(this=SimpleNamespace(CastTo=MagicMock(return_value=treachery)))
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        with patch.object(module, "ActivateGrimReaper", return_value=False):
            ability.operation(effect, message)

        identity.TakeIndirectDamage.assert_called_once_with(treachery, 2, effect)

    def test_death_cannot_die_does_not_search_when_activation_is_prevented(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58029")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        with patch.object(module, "ActivateGrimReaper", return_value=True), patch.object(
            module.Find,
            "FindAndReveal",
        ) as find_and_reveal:
            ability.operation(effect, message)

        find_and_reveal.assert_not_called()

    def test_death_cannot_die_finds_and_reveals_grim_reaper_when_absent(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58029")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        with patch.object(module, "ActivateGrimReaper", return_value=False), patch.object(
            module.Find,
            "FindAndReveal",
        ) as find_and_reveal:
            ability.operation(effect, message)

        find_and_reveal.assert_called_once_with(
            effect,
            player,
            name="Grim Reaper",
            card_type=module.Minion,
        )

    def test_death_cannot_die_boost_activates_after_current_activation(self):
        module = import_module("cards.pack.wonder_man.wonder_man_nemesis.58029")
        boost_ability = module.GetAbilities()[1]
        player = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        message = SimpleNamespace(
            GetToPlayer=MagicMock(return_value=player),
            AfterThisActivation=MagicMock(),
        )

        with patch.object(module.Worlds, "FindCardOnField", return_value=MagicMock()), patch.object(
            module,
            "ActivateGrimReaper",
        ) as activate:
            boost_ability.operation(effect, message)
            callback = message.AfterThisActivation.call_args.args[1]
            activate.assert_not_called()
            callback()

        message.AfterThisActivation.assert_called_once()
        self.assertIs(message.AfterThisActivation.call_args.args[0], effect)
        activate.assert_called_once_with(effect, player)


if __name__ == "__main__":
    unittest.main()
