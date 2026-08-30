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
from game.operate.setup_cards import SetupCards


ROOT = Path(__file__).resolve().parents[1]
ART_MUSEUM_CARD_IDS = [
    "60121a",
    "60121b",
    "60122",
    "60123",
    "60124",
    "60125",
    "60126",
    "60127",
]
COPS_CARD_IDS = ["60182", "60183", "60184", "60185"]
THE_OWL_CARD_IDS = ["60191", "60192", "60193", "60194"]


class TestArtMuseumHeistRegistration(unittest.TestCase):

    def test_all_three_sets_initialize_through_card_factory(self):
        Ver.Initialize()
        CardsDB.Initialize()
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1

        for card_id in ART_MUSEUM_CARD_IDS + COPS_CARD_IDS + THE_OWL_CARD_IDS:
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

    def test_scenario_uses_recommended_cops_and_the_owl_sets(self):
        scenario = json.loads(
            (ROOT / "data" / "scenarios" / "art_museum_heist.json").read_text(
                encoding="utf-8"
            )
        )
        cops = json.loads(
            (ROOT / "data" / "encounter_sets" / "cops.json").read_text(
                encoding="utf-8"
            )
        )
        the_owl = json.loads(
            (ROOT / "data" / "encounter_sets" / "the_owl.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(scenario["kind"], "main-scenario")
        self.assertEqual(scenario["villain"], [])
        self.assertEqual(scenario["schemes"], ["60121a,60121b"])
        self.assertEqual(scenario["modular_sets"], ["cops", "the_owl"])
        self.assertEqual(scenario["encounters"].count("60126"), 2)
        self.assertEqual(scenario["encounters"].count("60127"), 2)
        self.assertEqual(cops["encounters"].count("60182"), 2)
        self.assertEqual(the_owl["encounters"].count("60191"), 2)

    def test_fear_no_evil_metadata_exposes_scenario_and_modular_sets(self):
        sets_info = json.loads(
            (ROOT / "data" / "sets_info.json").read_text(encoding="utf-8")
        )["60. Fear No Evil"]

        self.assertEqual(
            sets_info["scenarios"],
            [
                "art_museum_heist",
                "the_getaway",
                "protection_racket",
                "the_raft_breakout",
                "stop_the_presses",
                "kingpin",
            ],
        )
        self.assertEqual(sets_info["fixed_scenarios"], ["kingpin"])
        self.assertEqual(
            sets_info["underlings"],
            ["bullseye", "electro", "hammerhead", "purple_man", "typhoid_mary"],
        )
        self.assertEqual(
            sets_info["encounters"],
            [
                "disasters",
                "cops",
                "drive",
                "the_owl",
                "tombstone",
                "tracksuit_mafia",
            ],
        )
        self.assertEqual(sets_info["max_id"], "60210")

    def test_printed_boost_values_and_attachment_modifiers_match_the_cards(self):
        cards = json.loads(
            (ROOT / "data" / "cards.json").read_text(encoding="utf-8")
        )["fne"]
        papers = {paper["card_id"]: paper for paper in cards}

        self.assertEqual(papers["60126"]["desc"]["Boost"], "0")
        self.assertEqual(papers["60127"]["desc"]["Boost"], "1")
        self.assertEqual(papers["60183"]["desc"]["Boost"], "0")
        self.assertEqual(papers["60193"]["desc"]["Boost"], "0")
        self.assertEqual(papers["60191"]["desc"]["ATK+"], "1")
        self.assertEqual(papers["60191"]["desc"]["SCH+"], "1")


class TestArtMuseumHeistMechanics(unittest.TestCase):

    def test_setup_attaches_one_random_art_to_the_villain(self):
        module = import_module("cards.pack.fne.art_museum_heist.60121a")
        ability = module.GetAbilities()[0]
        villain = MagicMock()
        effect = MagicMock()

        with (
            patch.object(module.Worlds, "FindVillain", return_value=villain),
            patch.object(module.SetupCards, "AttachTo") as attach_to,
        ):
            ability.operation(effect, MagicMock())

        attach_to.assert_called_once_with(
            effect,
            villain,
            trait="ART",
            card_type=module.Attachment,
            choose="Random",
            include_in_play=False,
            shuffle_others_into_encounter_deck=True,
        )

    def test_setup_helper_shuffles_the_three_unchosen_art_cards_back(self):
        effect = MagicMock()
        villain = MagicMock()
        art_cards = [MagicMock() for _ in range(4)]
        chosen_art = art_cards[0]

        with (
            patch(
                "game.operate.setup_cards.SearchInternal.FindCards",
                return_value=art_cards,
            ),
            patch(
                "game.operate.setup_cards.Random.RandomChoice",
                return_value=chosen_art,
            ),
            patch("game.operate.setup_cards.CanAttach.IsType", return_value=True),
            patch("game.operate.setup_cards.Faces.ShuffleAllTo") as shuffle_all,
        ):
            SetupCards.AttachTo(
                effect,
                villain,
                trait="ART",
                choose="Random",
                include_in_play=False,
                shuffle_others_into_encounter_deck=True,
            )

        chosen_art.AttachTo2.assert_called_once_with(villain, effect)
        shuffle_all.assert_called_once_with(
            art_cards[1:],
            "EncounterDeck",
            effect,
        )

    def test_escalation_is_one_plus_villain_art_per_player(self):
        module = import_module("cards.pack.fne.art_museum_heist.60121b")
        ability = module.GetAbilities()[0]
        inventory = MagicMock()
        inventory.FindCardSize.return_value = 3
        villain = MagicMock()
        villain.GetInventoryDeck.return_value = inventory
        effect = MagicMock()
        message = SimpleNamespace(escalation_threat=0)

        with (
            patch.object(module.Worlds, "FindVillain", return_value=villain),
            patch.object(module.Worlds, "GetPlayerNumIcon", return_value=2),
        ):
            ability.operation(effect, message)

        self.assertEqual(message.escalation_threat, 8)

    def test_art_status_applies_to_the_character_it_attaches_to(self):
        module = import_module("cards.pack.fne.art_museum_heist.60122")
        status_ability = module.GetAbilities()[2]
        target = MagicMock()
        effect = MagicMock()

        with patch.object(module.Faces, "GiveStatus") as give_status:
            status_ability.operation(effect, SimpleNamespace(to_face=target))

        give_status.assert_called_once_with([target], "Confused", effect)

    def test_art_recovery_actions_have_specific_prompt_text(self):
        expected_resource_text = {
            "60122": "Spend a [mental] resource → attach this card to your hero",
            "60123": "Spend a [wild] resource → attach this card to your hero",
            "60124": "Spend a [physical] resource → attach this card to your hero",
            "60125": "Spend an [energy] resource → attach this card to your hero",
        }

        for card_id, resource_prompt in expected_resource_text.items():
            with self.subTest(card_id=card_id):
                abilities = import_module(
                    f"cards.pack.fne.art_museum_heist.{card_id}"
                ).GetAbilities()
                names = [ability.name for ability in abilities]
                self.assertIn(resource_prompt, names)
                self.assertIn(
                    "Exhaust your hero → attach this card to your hero",
                    names,
                )

    def test_art_status_response_rejects_a_non_character_attachment_target(self):
        module = import_module("cards.pack.fne.art_museum_heist.60122")
        status_ability = module.GetAbilities()[2]
        effect = MagicMock()
        message = SimpleNamespace(trigger=MagicMock(), to_face=MagicMock())

        with patch(
            "game.ability.factory.card_move.Condition.CheckWhichCard",
            side_effect=[True, False],
        ) as check_which_card:
            is_valid = all(
                condition(effect, message)
                for condition in status_ability.conditions
            )

        self.assertFalse(is_valid)
        self.assertEqual(check_which_card.call_count, 2)
        self.assertEqual(
            check_which_card.call_args_list[1].args[:2],
            ("Character", message.to_face),
        )

    def test_art_status_character_condition_evaluates_during_setup(self):
        Ver.Initialize()
        CardsDB.Initialize()
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1
        art = CardFactory.CreateFace(CardsDB.FindCardPaper("60122"), world)
        villain = CardFactory.CreateFace(CardsDB.FindCardPaper("60065"), world)
        art.card = SimpleNamespace()
        effect = SimpleNamespace(this=art)
        message = SimpleNamespace(trigger=art, to_face=villain)
        status_ability = import_module(
            "cards.pack.fne.art_museum_heist.60122"
        ).GetAbilities()[2]

        self.assertTrue(
            all(
                condition(effect, message)
                for condition in status_ability.conditions
            )
        )

    def test_cop_replaces_scheming_with_an_attack_on_the_villain(self):
        module = import_module("cards.pack.fne.cops.60182")
        ability = module.GetAbilities()[0]
        cop = MagicMock()
        villain = MagicMock()
        effect = SimpleNamespace(this=MagicMock())
        effect.this.CastTo.return_value = cop
        message = MagicMock()

        with patch.object(module.Worlds, "FindVillain", return_value=villain):
            ability.operation(effect, message)

        message.SetBeInstead.assert_called_once_with(effect)
        cop.BasicAttack.assert_called_once_with([villain], effect)

    def test_crooked_cop_boost_deals_two_indirect_damage(self):
        module = import_module("cards.pack.fne.cops.60183")
        ability = module.GetAbilities()[1]
        identity = MagicMock()
        player = MagicMock()
        player.GetIdentity.return_value = identity
        message = MagicMock()
        message.GetToPlayer.return_value = player
        effect = MagicMock()

        ability.operation(effect, message)

        identity.TakeIndirectDamage.assert_called_once_with(effect.this, 2, effect)

    def test_the_owl_boost_grants_piercing_only_during_an_attack(self):
        module = import_module("cards.pack.fne.the_owl.60193")
        ability = module.GetAbilities()[1]
        effect = MagicMock()
        message = MagicMock()

        ability.operation(effect, message)

        message.would_atk_message.GainPiercing.assert_called_once_with(effect)
        self.assertTrue(ability.conditions[-1](effect, message))

    def test_flight_serum_does_not_duplicate_its_printed_stat_modifiers(self):
        module = import_module("cards.pack.fne.the_owl.60191")

        with patch.object(
            module.AbilityFactory,
            "GiveKeywordToAttached",
            return_value=[],
        ) as give_keyword:
            module.GetAbilities()

        give_keyword.assert_called_once_with(
            module.Enemy,
            trait="AERIAL",
        )

    def test_only_the_player_with_wanted_can_trigger_its_action(self):
        module = import_module("cards.pack.fne.cops.60184")
        ability = module.GetAbilities()[0]
        owner = MagicMock()
        other_player = MagicMock()
        wanted = MagicMock()
        wanted.GetGaveToPlayer.return_value = owner
        effect = MagicMock()
        effect.this.CastTo.return_value = wanted

        effect.GetInitiator.return_value = owner
        self.assertTrue(ability.conditions[1](effect, MagicMock()))

        effect.GetInitiator.return_value = other_player
        self.assertFalse(ability.conditions[1](effect, MagicMock()))


if __name__ == "__main__":
    unittest.main()
