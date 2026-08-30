from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.database import CardsDB
from engine.lib.version import Ver
from game.card.factory import CardFactory


ROOT = Path(__file__).resolve().parents[1]
UNDERLING_CARD_IDS = (
    [str(card_id) for card_id in range(60076, 60110)]
    + ["60110a", "60110b", "60111a", "60111b", "60112", "60113a", "60113b"]
    + [str(card_id) for card_id in range(60114, 60121)]
)
UNDERLING_SLUGS = ["electro", "hammerhead", "purple_man", "typhoid_mary"]


class TestFearNoEvilUnderlingRegistration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Ver.Initialize()
        CardsDB.Initialize()

    def test_all_four_sets_initialize_through_card_factory(self):
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1

        for card_id in UNDERLING_CARD_IDS:
            with self.subTest(card_id=card_id):
                paper = CardsDB.FindCardPaper(card_id)
                face = CardFactory.CreateFace(paper, world)
                abilities = CardsDB.FindAbilities(card_id, paper.pack, paper.set_name)
                self.assertEqual(face.paper.card_id, card_id)
                self.assertTrue(abilities)

    def test_menu_registers_every_underling_except_kingpin(self):
        sets_info = json.loads(
            (ROOT / "data" / "sets_info.json").read_text(encoding="utf-8")
        )["60. Fear No Evil"]

        self.assertEqual(
            sets_info["underlings"],
            ["bullseye", "electro", "hammerhead", "purple_man", "typhoid_mary"],
        )
        self.assertNotIn("kingpin", sets_info["underlings"])

    def test_standard_and_expert_presets_use_the_correct_villain_stages(self):
        expected = {
            "electro": (["60076", "60077"], ["60077", "60078"]),
            "hammerhead": (["60086", "60087"], ["60087", "60088"]),
            "purple_man": (["60097", "60098"], ["60098", "60099"]),
            "typhoid_mary": ([], []),
        }

        for slug, (standard_villains, expert_villains) in expected.items():
            with self.subTest(slug=slug):
                standard = json.loads(
                    (ROOT / "data" / "scenarios" / f"{slug}.json").read_text(
                        encoding="utf-8"
                    )
                )
                expert = json.loads(
                    (ROOT / "data" / "scenarios" / f"{slug}_expert.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(standard["kind"], "underling")
                self.assertEqual(standard["villain"], standard_villains)
                self.assertEqual(expert["villain"], expert_villains)
                self.assertEqual(standard["encounter_sets"], ["standard"])
                self.assertEqual(expert["encounter_sets"], ["standard", "expert"])

        standard_typhoid = json.loads(
            (ROOT / "data" / "scenarios" / "typhoid_mary.json").read_text(
                encoding="utf-8"
            )
        )
        expert_typhoid = json.loads(
            (ROOT / "data" / "scenarios" / "typhoid_mary_expert.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(standard_typhoid["set_aside"], ["60110a,60110b"])
        self.assertEqual(expert_typhoid["set_aside"], ["60111a,60111b"])
        self.assertEqual(standard_typhoid["encounters"].count("60120"), 3)

    def test_printed_stats_and_special_keywords_match_the_scans(self):
        papers = {
            paper["card_id"]: paper
            for paper in json.loads(
                (ROOT / "data" / "cards.json").read_text(encoding="utf-8")
            )["fne"]
        }

        self.assertEqual(papers["60076"]["desc"]["SCH"], "1*")
        self.assertEqual(papers["60077"]["desc"]["SCH"], "1*")
        self.assertEqual(papers["60078"]["desc"]["SCH"], "2*")
        self.assertEqual(
            papers["60078"]["text"],
            "<b>When Revealed</b>: Place 3 charge counters per player on Electric "
            "Charge.\n[star] <b>Forced Response</b>: After Electro schemes, place "
            "2 charge counters on Electric Charge.",
        )
        self.assertEqual(papers["60080"]["desc"]["Uses"], "3,drain")
        self.assertEqual(papers["60086"]["desc"]["ATK"], "1*")
        self.assertEqual(papers["60087"]["desc"]["ATK"], "2*")
        self.assertEqual(papers["60088"]["desc"]["ATK"], "3*")
        self.assertEqual(papers["60090"]["desc"]["SCH+"], "1")
        self.assertEqual(papers["60090"]["desc"]["Boost"], "1")
        self.assertEqual(papers["60100"]["desc"]["Boost"], "3")
        self.assertEqual(papers["60108"]["desc"]["Hinder"], "3*")
        self.assertEqual(papers["60111a"]["desc"]["Stage"], "B")
        self.assertEqual(papers["60113a"]["desc"]["Permanent"], "1")
        self.assertEqual(papers["60117"]["desc"]["ATK+"], "2")
        self.assertEqual(papers["60120"]["desc"]["Toughness"], "1")


class TestFearNoEvilUnderlingMechanics(unittest.TestCase):

    def test_electro_three_uses_the_existing_permanent_electric_charge(self):
        package = import_module("cards.pack.fne.electro")
        module = import_module("cards.pack.fne.electro.60078")
        ability = module.GetAbilities()[0]
        charge = MagicMock()
        effect = SimpleNamespace(this=MagicMock())

        with (
            patch.object(package.SetupCards, "AttachTo") as attach,
            patch.object(package, "GetElectricCharge", return_value=charge),
            patch.object(package.Faces, "PlaceCountersOn") as place,
        ):
            ability.operation(effect, MagicMock())

        attach.assert_not_called()
        place.assert_called_once_with([charge], "3*", "charge", effect)

    def test_drained_of_power_does_not_duplicate_its_printed_uses(self):
        module = import_module("cards.pack.fne.electro.60080")

        with patch.object(
            module.AbilityFactory,
            "ThisEnterPlayWithCounters",
            return_value=MagicMock(),
        ) as enter_with_counters:
            module.GetAbilities()

        enter_with_counters.assert_not_called()

    def test_electro_attack_spends_a_charge_for_boost_and_overkill(self):
        module = import_module("cards.pack.fne.electro.60079")
        ability = module.GetAbilities()[1]
        charge = MagicMock()
        charge.GetCounters.return_value = 2
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = charge
        message = MagicMock()

        with patch.object(module.Faces, "RemoveCountersOn") as remove:
            ability.operation(effect, message)

        remove.assert_called_once_with([charge], 1, "charge", effect)
        message.GiveAdditionalBoostCardForThisActivation.assert_called_once_with(1, effect)
        message.GainOverKill.assert_called_once_with(effect)

    def test_hammerhead_damages_an_already_stunned_character(self):
        module = import_module("cards.pack.fne.hammerhead.60088")
        ability = module.GetAbilities()[0]
        hammerhead = MagicMock()
        target = MagicMock()
        target.IsStunned.return_value = True
        effect = SimpleNamespace(this=hammerhead)
        message = SimpleNamespace(attacked=target)

        ability.operation(effect, message)

        hammerhead.DealDamage.assert_called_once_with([target], 2, effect)

    def test_hammerhead_stuns_a_damaged_character_that_is_not_stunned(self):
        module = import_module("cards.pack.fne.hammerhead.60086")
        ability = module.GetAbilities()[0]
        hammerhead = MagicMock()
        target = MagicMock()
        target.IsStunned.return_value = False
        effect = SimpleNamespace(this=hammerhead)
        message = SimpleNamespace(attacked=target)

        with patch.object(module.Faces, "GiveStatus", return_value=1) as give:
            ability.operation(effect, message)

        give.assert_called_once_with([target], "Stunned", effect)
        hammerhead.DealDamage.assert_not_called()
        self.assertIn("Stun the attacked character", ability.name)

    def test_hammerhead_does_not_use_fallback_damage_when_stalwart_blocks_stun(self):
        module = import_module("cards.pack.fne.hammerhead.60086")
        ability = module.GetAbilities()[0]
        hammerhead = MagicMock()
        stalwart_target = MagicMock()
        stalwart_target.IsStunned.return_value = False
        effect = SimpleNamespace(this=hammerhead)
        message = SimpleNamespace(attacked=stalwart_target)

        # Inspiring Pottery grants Stalwart. A failed stun is not the same as
        # the character already being stunned, so Hammerhead's "otherwise"
        # damage does not apply.
        with patch.object(module.Faces, "GiveStatus", return_value=0) as give:
            ability.operation(effect, message)

        give.assert_called_once_with([stalwart_target], "Stunned", effect)
        hammerhead.DealDamage.assert_not_called()

    def test_chameleon_adds_its_printed_scheme_to_the_highest_thwart(self):
        module = import_module("cards.pack.fne.hammerhead.60091")

        with patch.object(
            module.AbilityFactory,
            "ThisSetKeyword",
            return_value=MagicMock(),
        ) as set_keyword:
            module.GetAbilities()

        calculate_scheme = set_keyword.call_args.args[0]
        chameleon = MagicMock()
        chameleon.scheme = 1
        character = MagicMock()
        character.thwart = 4
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = chameleon
        ui = []

        with (
            patch.object(
                module.Worlds,
                "GetOnFieldFriendlyCharacters",
                return_value=[character],
            ),
            patch.object(module.Filter, "One", return_value=character),
            patch.object(module.HasThwart, "IsType", return_value=True),
        ):
            value, changed = calculate_scheme(effect, ui)

        self.assertEqual(value, 5)
        self.assertTrue(changed)
        self.assertEqual(ui, [character])

    def test_underboss_adds_its_boost_card_to_the_current_activation(self):
        module = import_module("cards.pack.fne.hammerhead.60093")
        ability = module.GetAbilities()[0]
        message = MagicMock()
        message.GetToPlayer.return_value.GetIdentity.return_value.IsStunned.return_value = True
        effect = SimpleNamespace(this=MagicMock())

        ability.operation(effect, message)

        message.GiveAdditionalBoostCardForThisActivation.assert_called_once_with(
            1,
            effect,
        )
        message.would_message.GiveAdditionalBoostCardForThisActivation.assert_not_called()

    def test_converted_treats_the_highest_cost_ally_as_an_influenced_minion(self):
        module = import_module("cards.pack.fne.purple_man.60100")
        with patch.object(
            module.AbilityFactory,
            "TreatAttachedCardAsMinion",
            return_value=MagicMock(),
        ) as treat:
            module.GetAbilities()

        process = treat.call_args.kwargs["process"]
        minion = MagicMock()
        process(minion, MagicMock(), MagicMock())
        minion.GainTraits.assert_called_once()
        self.assertEqual(minion.GainTraits.call_args.args[1], ["INFLUENCED"])

    def test_purple_boost_applies_during_any_enemy_activation(self):
        module = import_module("cards.pack.fne.purple_man")

        with patch.object(
            module.AbilityFactory,
            "WhenCardBecomeBoost",
            return_value=MagicMock(),
        ) as when_boost:
            module.PurpleManVillainAbilities()

        self.assertNotIn("activating_enemy", when_boost.call_args.kwargs)

    def test_typhoid_defeat_is_replaced_by_a_psyche_token_and_health_reset(self):
        module = import_module("cards.pack.fne.typhoid_mary.60110a")
        ability = module.GetAbilities()[0]
        villain = MagicMock()
        psyche = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = villain
        message = MagicMock()

        with (
            patch.object(module.Worlds, "FindCardOnField", return_value=psyche),
            patch.object(module.Faces, "PlaceCountersOn") as place,
        ):
            ability.operation(effect, message)

        message.SetBeInstead.assert_called_once_with(effect)
        place.assert_called_once_with([psyche], 1, "damage", effect)
        villain.ResetHealth.assert_called_once_with(effect)

    def test_three_tokens_on_disturbed_psyche_win_the_game(self):
        module = import_module("cards.pack.fne.typhoid_mary.60112")
        ability = module.GetAbilities()[2]
        psyche = MagicMock()
        psyche.GetAllCounters.return_value = 3
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = psyche

        with patch.object(module.Worlds, "SetGameOver") as game_over:
            ability.operation(effect, MagicMock())

        game_over.assert_called_once_with(True, effect)

    def test_typhoid_flip_at_phase_end_resolves_the_new_side(self):
        module = import_module("cards.pack.fne.typhoid_mary.60112")
        ability = module.GetAbilities()[1]
        villain = MagicMock()
        effect = SimpleNamespace(this=MagicMock())

        with patch.object(module, "GetTyphoidVillain", return_value=villain):
            ability.operation(effect, MagicMock())

        villain.card.Flip.assert_called_once_with(effect)


if __name__ == "__main__":
    unittest.main()
