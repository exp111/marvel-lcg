from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.database import CardsDB
from engine.lib.version import Ver
from game.card.face.attribute.can_attack import AttackProperty
from game.card.factory import CardFactory
from game.message import Message


ROOT = Path(__file__).resolve().parents[1]
BULLSEYE_CARD_IDS = [
    "60065",
    "60066",
    "60067",
    "60068a",
    "60068b",
    "60069",
    "60070",
    "60071",
    "60072",
    "60073",
    "60074",
    "60075",
]


class TestBullseyeRegistration(unittest.TestCase):

    def test_complete_bullseye_set_initializes_through_card_factory(self):
        Ver.Initialize()
        CardsDB.Initialize()
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1

        for card_id in BULLSEYE_CARD_IDS:
            with self.subTest(card_id=card_id):
                paper = CardsDB.FindCardPaper(card_id)
                face = CardFactory.CreateFace(paper, world)
                abilities = CardsDB.FindAbilities(
                    card_id,
                    paper.pack,
                    paper.set_name,
                )
                self.assertEqual(face.paper.card_id, card_id)
                self.assertTrue(abilities)

    def test_card_data_has_correct_stages_icons_and_quantities(self):
        cards = json.loads(
            (ROOT / "data" / "cards.json").read_text(encoding="utf-8")
        )["fne"]
        papers = {paper["card_id"]: paper for paper in cards}

        self.assertEqual(papers["60065"]["desc"]["Stage"], "I")
        self.assertEqual(papers["60066"]["desc"]["Stage"], "II")
        self.assertEqual(papers["60067"]["desc"]["Stage"], "III")
        self.assertEqual(papers["60068a"]["desc"]["Permanent"], "1")
        self.assertEqual(papers["60072"]["desc"]["Villainous"], "1")
        self.assertEqual(papers["60073"]["desc"]["Hazard"], "1")
        self.assertEqual(papers["60073"]["desc"]["Amplify"], "1")
        self.assertEqual(papers["60070"]["desc"]["Boost"], "2")
        self.assertEqual(papers["60070"]["desc"]["ATK+"], "2")
        self.assertEqual(papers["60073"]["desc"]["Boost"], "1")
        self.assertEqual(papers["60074"]["desc"]["Boost"], "1")
        self.assertEqual(papers["60075"]["desc"]["Boost"], "3")

        sets_info = json.loads(
            (ROOT / "data" / "sets_info.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(
            int(sets_info["60. Fear No Evil"]["max_id"]),
            60075,
        )

    def test_bullseye_is_registered_as_an_interchangeable_underling(self):
        sets_info = json.loads(
            (ROOT / "data" / "sets_info.json").read_text(encoding="utf-8")
        )
        fear_no_evil = sets_info["60. Fear No Evil"]
        self.assertEqual(
            fear_no_evil["underlings"],
            ["bullseye", "electro", "hammerhead", "purple_man", "typhoid_mary"],
        )
        self.assertIn("art_museum_heist", fear_no_evil["scenarios"])

        standard = json.loads(
            (ROOT / "data" / "scenarios" / "bullseye.json").read_text(
                encoding="utf-8"
            )
        )
        expert = json.loads(
            (ROOT / "data" / "scenarios" / "bullseye_expert.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(standard["kind"], "underling")
        self.assertEqual(standard["villain"], ["60065", "60066"])
        self.assertEqual(expert["villain"], ["60066", "60067"])
        self.assertEqual(standard["schemes"], [])
        self.assertEqual(expert["schemes"], [])
        self.assertEqual(standard["set_aside"], ["60068a,60068b"])
        self.assertEqual(standard["encounters"].count("60071"), 3)
        self.assertEqual(standard["encounters"].count("60075"), 2)
        self.assertEqual(standard["encounter_sets"], ["standard"])
        self.assertEqual(expert["encounter_sets"], ["standard", "expert"])

    def test_scene_places_conditional_scenario_row_above_standard_sets(self):
        scene_html = (ROOT / "public" / "scene.html").read_text(encoding="utf-8")

        split_selector = scene_html.index('id="split-scenario-selector"')
        standard_sets = scene_html.index("<legend>Standard Sets</legend>")
        self.assertLess(split_selector, standard_sets)
        self.assertIn("mergeInterchangeableScenario", scene_html)
        self.assertIn('scenarioTitle.textContent = "Villains"', scene_html)
        self.assertIn("splitSelector.hidden = false", scene_html)


class TestBullseyeMechanics(unittest.TestCase):

    def test_deadly_sai_loads_its_printed_attack_modifier_and_boost_icons(self):
        Ver.Initialize()
        CardsDB.Initialize()
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1
        face = CardFactory.CreateFace(CardsDB.FindCardPaper("60070"), world)

        self.assertEqual(face.modify_atk, 2)
        self.assertEqual(face.printed_boost, 2)

    def test_stage_three_does_not_find_an_in_play_deranged_bloodlust(self):
        module = import_module("cards.pack.fne.bullseye.60067")
        ability = module.GetAbilities()[0]
        effect = MagicMock()

        with patch.object(module.SetupCards, "Reveal") as reveal:
            ability.operation(effect, MagicMock())

        reveal.assert_called_once_with(
            effect,
            name="Deranged Bloodlust",
            card_type=module.SchemeSide2,
            include_in_play=False,
        )

    def test_activation_registers_one_extra_boost_icon_for_that_activation(self):
        module = import_module("cards.pack.fne.bullseye.60065")
        ability = module.GetAbilities()[1]
        villain = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = villain
        attack_message = MagicMock(spec=Message.WhenUnitWouldAttack)
        activation = SimpleNamespace(would_message=attack_message)

        ability.operation(effect, activation)

        registered = villain.effect.RegisterTemp.call_args.args[0]
        self.assertEqual(
            villain.effect.RegisterTemp.call_args.kwargs,
            {
                "unregister_after_exec": False,
                "until_event_end": activation,
            },
        )
        boost_message = MagicMock()
        registered.operation(MagicMock(), boost_message)
        boost_message.UpdateBoostIcon.assert_called_once_with(+1, effect)
        attack_message.GainRanged.assert_called_once_with(effect)

    def test_spine_limits_a_damage_instance_to_three_and_flips_at_six(self):
        module = import_module("cards.pack.fne.bullseye.60068a")
        ability = module.GetAbilities()[1]
        spine = MagicMock()
        spine.GetCounters.return_value = 6
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = spine
        message = SimpleNamespace(
            will_take_damage=8,
            PreventDamage=MagicMock(),
        )

        with patch.object(module.Faces, "PlaceCountersOn") as place_counters:
            ability.operation(effect, message)

        message.PreventDamage.assert_called_once_with(5, effect)
        place_counters.assert_called_once_with([spine], 5, "damage", effect)
        spine.card.Flip.assert_called_once_with(effect)

    def test_damaged_spine_removes_three_damage_and_flips_when_empty(self):
        module = import_module("cards.pack.fne.bullseye.60068b")
        ability = module.GetAbilities()[0]
        spine = MagicMock()
        spine.GetCounters.return_value = 0
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = spine

        with patch.object(module.Faces, "RemoveCountersOn") as remove_counters:
            ability.operation(effect, MagicMock())

        remove_counters.assert_called_once_with([spine], 3, "damage", effect)
        spine.card.Flip.assert_called_once_with(effect)

    def test_deadly_sai_can_override_bullseyes_ranged_keyword(self):
        property = AttackProperty(ranged=True)
        keyword_check = object.__new__(Message.CheckIfAttackMessageHasKeyword)
        keyword_check.property = property
        keyword_check.SetLostRanged(MagicMock())

        attack = object.__new__(Message.WhenUnitWouldAttackUnit)
        attack.temp_ranged = False
        attack.property = property

        self.assertTrue(property.ranged)
        self.assertTrue(property.lost_ranged)
        self.assertFalse(attack.IsRanged())

        module = import_module("cards.pack.fne.bullseye.60070")
        with patch.object(
            module.AbilityFactory,
            "UnitAttackGainKeyword",
            return_value=MagicMock(),
        ) as gain_keyword:
            module.GetAbilities()
        gain_keyword.assert_called_once_with(
            module.BULLSEYE,
            piercing=True,
            lost_ranged=True,
        )

    def test_incessant_pursuit_redirects_the_attack_and_grants_overkill(self):
        module = import_module("cards.pack.fne.bullseye.60071")
        ability = module.GetAbilities()[1]
        pursuit = MagicMock()
        ally = MagicMock()
        pursuit.GetBindFace.return_value = ally
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = pursuit
        message = MagicMock()

        with patch.object(module.Ally, "IsType", return_value=True):
            ability.operation(effect, message)

        message.ReplaceTarget.assert_called_once_with(ally)
        message.GainOverKill.assert_called_once_with(effect)
        message.IfThisAttackDefeats.assert_called_once()
        self.assertIs(message.IfThisAttackDefeats.call_args.args[0], ally)

    def test_lady_bullseye_adds_only_one_boost_to_an_undefended_attack(self):
        module = import_module("cards.pack.fne.bullseye.60072")
        ability = module.GetAbilities()[0]
        lady_bullseye = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = lady_bullseye
        attack_message = MagicMock()
        attack_message.GetDefender.return_value = None

        ability.operation(effect, attack_message)

        temp_ability = lady_bullseye.effect.RegisterTemp.call_args.args[0]
        self.assertTrue(
            temp_ability.conditions[-1](
                MagicMock(),
                SimpleNamespace(would_atk_message=attack_message),
            )
        )
        temp_ability.operation(MagicMock(), MagicMock())
        lady_bullseye.GiveFacedownBoostCardsInternal.assert_called_once_with(
            1,
            effect,
            attack_message,
        )
        self.assertTrue(
            lady_bullseye.effect.RegisterTemp.call_args.kwargs[
                "unregister_after_exec"
            ]
        )

    def test_bullseye_boost_effects_add_cards_and_attack_keywords(self):
        weapon = import_module("cards.pack.fne.bullseye.60074")
        desire = import_module("cards.pack.fne.bullseye.60075")
        effect = MagicMock()
        weapon_message = MagicMock()
        desire_message = MagicMock()

        weapon.GetAbilities()[2].operation(effect, weapon_message)
        desire.GetAbilities()[1].operation(effect, desire_message)

        weapon_message.GiveActivatingEnemyAdditionalBoostCard.assert_called_once_with(
            1,
            effect,
        )
        weapon_message.would_atk_message.GainPiercing.assert_called_once_with(effect)
        desire_message.would_atk_message.GainOverKill.assert_called_once_with(effect)


if __name__ == "__main__":
    unittest.main()
