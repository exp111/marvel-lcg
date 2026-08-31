from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.database import CardsDB
from engine.lib.version import Ver
from game.ability import AbilityType
from game.card.factory import CardFactory
from game.message import Message


ROOT = Path(__file__).resolve().parents[1]
KINGPIN_CARD_IDS = (
    ["60159a", "60159b", "60160a", "60160b"]
    + ["60161a", "60161b", "60162a", "60162b", "60163a", "60163b"]
    + [str(card_id) for card_id in range(60164, 60177)]
)


class TestKingpinRegistration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Ver.Initialize()
        CardsDB.Initialize()

    def test_all_printed_faces_initialize(self):
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1

        for card_id in KINGPIN_CARD_IDS:
            with self.subTest(card_id=card_id):
                paper = CardsDB.FindCardPaper(card_id)
                face = CardFactory.CreateFace(paper, world)
                self.assertEqual(face.paper.card_id, card_id)
                self.assertTrue(face.ability.abilities)

    def test_scenario_uses_fixed_setup_without_standard_sets(self):
        standard = json.loads(
            (ROOT / "data" / "scenarios" / "kingpin.json").read_text(
                encoding="utf-8"
            )
        )
        expert = json.loads(
            (ROOT / "data" / "scenarios" / "kingpin_expert.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(standard["villain"], ["60159a,60159b"])
        self.assertEqual(expert["villain"], ["60160a,60160b"])
        self.assertEqual(
            standard["schemes"],
            ["60161a,60161b", "60162a,60162b"],
        )
        self.assertEqual(standard["modular_sets"], ["tombstone", "tracksuit_mafia"])
        self.assertEqual(standard["encounter_sets"], [])
        self.assertEqual(expert["encounter_sets"], ["expert"])
        self.assertIs(standard["standard_sets"], False)
        self.assertIs(expert["standard_sets"], False)
        self.assertEqual(standard["encounters"].count("60175"), 3)
        self.assertEqual(standard["encounters"].count("60176"), 3)

    def test_printed_values_match_the_scans(self):
        papers = {
            paper["card_id"]: paper
            for paper in json.loads(
                (ROOT / "data" / "cards.json").read_text(encoding="utf-8")
            )["fne"]
        }

        self.assertEqual(papers["60159a"]["desc"]["HP"], "25*")
        self.assertEqual(papers["60160a"]["desc"]["HP"], "28*")
        self.assertEqual(papers["60159b"]["traits"], ["CRIMINAL", "MARTIAL ARTIST"])
        self.assertEqual(papers["60161a"]["name"], "The King's Gambit")
        self.assertEqual(papers["60161b"]["name"], "The King's Gambit")
        self.assertEqual(papers["60161b"]["desc"]["TargetThreat"], "11*")
        self.assertEqual(papers["60162b"]["desc"]["TargetThreat"], "7*")
        self.assertEqual(papers["60165"]["desc"]["Boost"], "1*")
        self.assertEqual(papers["60168"]["desc"]["Boost"], "1*")
        self.assertEqual(papers["60171"]["desc"]["Boost"], "3")
        self.assertEqual(papers["60172"]["desc"]["Boost"], "3")
        self.assertEqual(papers["60174"]["desc"]["Boost"], "3")
        self.assertEqual(papers["60175"]["desc"]["Boost"], "0*")
        self.assertEqual(papers["60176"]["desc"]["Boost"], "1*")

    def test_menu_marks_kingpin_fixed_and_disables_both_choice_families(self):
        sets_info = json.loads(
            (ROOT / "data" / "sets_info.json").read_text(encoding="utf-8")
        )["60. Fear No Evil"]
        scene = (ROOT / "public" / "scene.html").read_text(encoding="utf-8")

        self.assertEqual(sets_info["fixed_scenarios"], ["kingpin"])
        self.assertNotIn("kingpin", sets_info["underlings"])
        self.assertIn("setInterchangeableScenarioSelectionEnabled(false)", scene)
        self.assertIn("j['standard_sets'] !== false", scene)
        self.assertIn("button[data-family=\"standard\"]", scene)
        self.assertIn("setStandardEncounterSetSelectionEnabled(allowStandardSets)", scene)
        self.assertIn("setStandardEncounterSetSelectionEnabled(true)", scene)


class TestKingpinMechanics(unittest.TestCase):

    def test_stage_one_replaces_attack_with_scheme(self):
        ability = import_module(
            "cards.pack.fne.kingpin.60159a"
        ).GetAbilities()[-1]
        villain = MagicMock()
        player = MagicMock()
        effect = MagicMock()
        effect.this.CastTo.return_value = villain
        message = MagicMock()
        message.GetAgainstPlayer.return_value = player

        ability.operation(effect, message)

        message.SetBeInstead.assert_called_once_with(effect)
        villain.DoSchemes.assert_called_once_with(player, effect)

    def test_stage_two_adds_boost_only_without_minion_and_expert_adds_overkill(self):
        standard = import_module(
            "cards.pack.fne.kingpin.60159b"
        ).GetAbilities()[0]
        expert = import_module(
            "cards.pack.fne.kingpin.60160b"
        ).GetAbilities()[0]
        player = MagicMock()
        player.GetEngagedMinions.return_value = []
        effect = MagicMock()
        attack = MagicMock(spec=Message.WhenUnitWouldAttack)
        message = MagicMock()
        message.GetToPlayer.return_value = player
        message.would_message = attack

        standard.operation(effect, message)
        expert.operation(effect, message)

        self.assertEqual(
            message.GiveAdditionalBoostCardForThisActivation.call_count,
            2,
        )
        attack.GainOverKill.assert_called_once_with(effect)

        message.reset_mock()
        attack.reset_mock()
        player.GetEngagedMinions.return_value = [MagicMock()]
        standard.operation(effect, message)
        expert.operation(effect, message)
        message.GiveAdditionalBoostCardForThisActivation.assert_not_called()
        attack.GainOverKill.assert_not_called()

    def test_setup_uses_considered_titles_for_unique_nemesis_replacement(self):
        module = import_module("cards.pack.fne.kingpin")
        minion = MagicMock()
        minion.name = "Black Cat"
        character = MagicMock()
        character.IsName.return_value = True
        player = MagicMock()
        effect = MagicMock()

        with (
            patch.object(module, "GetNemesisMinion", return_value=minion),
            patch.object(module.Worlds, "GetOnFieldCharacters", return_value=[character]),
            patch.object(module.Faces, "RemoveAllFromGame") as remove,
            patch.object(module, "RevealUnderlingNotInPlay") as reveal_underling,
        ):
            module.RevealSetupNemesis(player, effect)

        character.IsName.assert_called_once_with("Black Cat")
        remove.assert_called_once_with([minion], effect)
        reveal_underling.assert_called_once_with(player, effect)
        minion.Reveal.assert_not_called()

    def test_public_support_requires_two_per_player_plus_two(self):
        module = import_module("cards.pack.fne.kingpin.60163a")
        ability = module.GetAbilities()[1]
        support = MagicMock()
        effect = MagicMock()
        effect.this = support
        message = MagicMock()

        with patch.object(module.Worlds, "GetPlayerNumIcon", return_value=2):
            support.GetCounters.return_value = 5
            self.assertFalse(ability.conditions[-1](effect, message))
            support.GetCounters.return_value = 6
            self.assertTrue(ability.conditions[-1](effect, message))

    def test_public_support_high_only_cancels_enemy_boost_cards(self):
        module = import_module("cards.pack.fne.kingpin.60163b")
        ability = module.GetAbilities()[0]
        effect = MagicMock()
        effect.this.GetCounters.return_value = 1
        message = MagicMock()
        message.into_area.flags.is_attach_boost_area = True
        message.into_area.bind_card.face = MagicMock()

        with patch.object(module.Enemy, "IsType", side_effect=[False, True]):
            self.assertFalse(ability.conditions[-2](effect, message))
            self.assertTrue(ability.conditions[-2](effect, message))

    def test_public_support_high_accepts_any_card_as_the_enemy_boost(self):
        module = import_module("cards.pack.fne.kingpin.60163b")
        ability = module.GetAbilities()[0]
        effect = MagicMock()
        message = MagicMock()

        with patch(
            "game.ability.factory.card_move.Condition.CheckWhichCard",
            return_value=True,
        ) as check:
            self.assertTrue(ability.conditions[0](effect, message))

        check.assert_called_once_with(module.CardFace, message.trigger, effect)

    def test_scenario_hero_actions_can_be_used_by_any_player(self):
        public_support = import_module(
            "cards.pack.fne.kingpin.60161b"
        ).GetAbilities()[1]
        james_wesley = import_module(
            "cards.pack.fne.kingpin.60165"
        ).GetAbilities()[2]
        black_cat = import_module(
            "cards.pack.fne.kingpin.60169"
        ).GetAbilities()[0]

        for ability in (public_support, james_wesley, black_cat):
            with self.subTest(name=ability.name):
                self.assertTrue(ability.any_player_can_trigger_this_when)

    def test_scenario_hero_actions_affect_the_triggering_player(self):
        triggering_player = MagicMock(name="triggering_player")
        active_player = MagicMock(name="active_player")
        effect = MagicMock()
        effect.GetInitiator.return_value = triggering_player
        message = MagicMock()
        message.GetToPlayer.return_value = active_player
        kingpin = MagicMock()

        james = import_module("cards.pack.fne.kingpin.60165")
        with (
            patch.object(james, "GetKingpin", return_value=kingpin),
            patch.object(james.Faces, "DiscardAll"),
        ):
            james.GetAbilities()[2].operation(effect, message)
        kingpin.DoSchemes.assert_called_once_with(triggering_player, effect)

        kingpin.reset_mock()
        vanessa = import_module("cards.pack.fne.kingpin.60168")
        with (
            patch.object(vanessa, "GetKingpin", return_value=kingpin),
            patch.object(vanessa.Faces, "DiscardAll"),
        ):
            vanessa.GetAbilities()[2].operation(effect, message)
        kingpin.DoAttackYou.assert_called_once_with(triggering_player, effect)

        black_cat = import_module("cards.pack.fne.kingpin.60169")
        minion = MagicMock()
        minion.GetCounters.return_value = 4
        effect.this.CastTo.return_value = minion
        with (
            patch.object(black_cat.Faces, "PlaceCountersOn"),
            patch.object(black_cat.Faces, "TreatAsAlly") as treat_as_ally,
        ):
            black_cat.GetAbilities()[0].operation(effect, message)
        treat_as_ally.assert_called_once_with(
            minion,
            "kingpin_black_cat_ally",
            triggering_player,
            effect,
        )

    def test_cane_and_vanessa_use_actual_status_not_one_steady_status_card(self):
        cases = (
            ("60166", "IsStunned", "Stunned"),
            ("60168", "IsConfused", "Confused"),
        )

        for card_id, status_check, status_name in cases:
            with self.subTest(card_id=card_id):
                module = import_module(f"cards.pack.fne.kingpin.{card_id}")
                ability = module.GetAbilities()[-1]
                identity = MagicMock()
                player = MagicMock()
                player.GetIdentity.return_value = identity
                message = MagicMock()
                message.GetToPlayer.return_value = player
                effect = MagicMock()
                getattr(identity, status_check).return_value = False

                with patch.object(module.Faces, "GiveStatus") as give_status:
                    ability.operation(effect, message)

                give_status.assert_called_once_with([identity], status_name, effect)
                identity.TakeDamage.assert_not_called()
                effect.this.PlaceThreatOnSchemes.assert_not_called()

                give_status.reset_mock()
                getattr(identity, status_check).return_value = True
                ability.operation(effect, message)

                give_status.assert_not_called()
                if card_id == "60166":
                    identity.TakeDamage.assert_called_once_with(effect.this, 1, effect)
                else:
                    effect.this.PlaceThreatOnSchemes.assert_called_once_with(
                        "MainScheme",
                        1,
                        effect,
                    )

    def test_mountain_of_muscle_stores_damage_as_a_replacement(self):
        module = import_module("cards.pack.fne.kingpin.60167")
        ability = module.GetAbilities()[-1]
        attachment = MagicMock()
        attachment.GetCounters.return_value = 7
        effect = MagicMock()
        effect.this = attachment
        message = MagicMock()
        message.will_take_damage = 3

        with patch.object(module.Faces, "PlaceCountersOn") as place:
            ability.operation(effect, message)

        message.SetBeInstead.assert_called_once_with(effect)
        place.assert_called_once_with([attachment], 3, "damage", effect)
        message.PreventDamage.assert_not_called()

    def test_spot_redirects_attack_damage_to_the_attacker(self):
        module = import_module("cards.pack.fne.kingpin.60171")
        ability = module.GetAbilities()[-1]
        spot = MagicMock()
        spot.GetCounters.return_value = 1
        attacker = MagicMock()
        effect = MagicMock()
        effect.this.CastTo.return_value = spot
        message = MagicMock()
        message.attacker = attacker

        with patch.object(module.Faces, "RemoveCountersOn") as remove:
            ability.operation(effect, message)

        remove.assert_called_once_with([spot], 1, "spot", effect)
        message.ChangeDealtToTarget.assert_called_once_with(attacker, effect)

    def test_bag_of_tricks_surges_when_no_nemesis_card_can_be_revealed(self):
        ability = import_module(
            "cards.pack.fne.kingpin.60175"
        ).GetAbilities()[0]
        treachery = MagicMock()
        player = MagicMock()
        player.set_aside_nemesis_sets.Get.return_value = []
        effect = MagicMock()
        effect.this.CastTo.return_value = treachery
        message = MagicMock()
        message.GetToPlayer.return_value = player

        ability.operation(effect, message)

        treachery.GainSurge.assert_called_once_with(1, effect)


if __name__ == "__main__":
    unittest.main()
