from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.database import CardsDB
from engine.lib.version import Ver
from game.ability import AbilityType
from game.card.factory import CardFactory
from game.card.face import CanCrisis, MainScheme
from game.message import Message
from game.operate.worlds import Worlds


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ORDER = [
    "art_museum_heist",
    "the_getaway",
    "protection_racket",
    "the_raft_breakout",
    "stop_the_presses",
    "kingpin",
]
SCENARIO_CARD_IDS = (
    ["60128a", "60128b", "60129a", "60129b"]
    + [str(card_id) for card_id in range(60130, 60134)]
    + [f"{card_id}{side}" for card_id in range(60134, 60139) for side in "ab"]
    + [str(card_id) for card_id in range(60139, 60142)]
    + ["60142a", "60142b"]
    + [str(card_id) for card_id in range(60143, 60151)]
    + ["60151a", "60151b"]
    + [str(card_id) for card_id in range(60152, 60159)]
)


class TestFearNoEvilScenarioRegistration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Ver.Initialize()
        CardsDB.Initialize()

    def test_all_forty_printed_faces_initialize_through_card_factory(self):
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1

        for card_id in SCENARIO_CARD_IDS:
            with self.subTest(card_id=card_id):
                paper = CardsDB.FindCardPaper(card_id)
                face = CardFactory.CreateFace(paper, world)
                self.assertEqual(face.paper.card_id, card_id)
                self.assertTrue(face.ability.abilities)

    def test_scenarios_are_registered_in_printed_order(self):
        sets_info = json.loads(
            (ROOT / "data" / "sets_info.json").read_text(encoding="utf-8")
        )["60. Fear No Evil"]
        self.assertEqual(sets_info["scenarios"], SCENARIO_ORDER)
        self.assertEqual(sets_info["max_id"], "60204")

    def test_scenario_files_contain_printed_cards_and_recommended_modulars(self):
        expected = {
            "the_getaway": {
                "schemes": ["60128a,60128b"],
                "set_aside": ["60129a,60129b"],
                "encounters": ["60130", "60131", "60132", "60132", "60133", "60133"],
                "modular_sets": ["cops", "drive"],
            },
            "protection_racket": {
                "schemes": [f"{card_id}a,{card_id}b" for card_id in range(60134, 60139)],
                "set_aside": [],
                "encounters": ["60139", "60140", "60141", "60141"],
                "modular_sets": ["disasters", "tracksuit_mafia"],
            },
            "the_raft_breakout": {
                "schemes": ["60142a,60142b"],
                "set_aside": ["60143"],
                "encounters": [str(card_id) for card_id in range(60144, 60151)],
                "modular_sets": ["the_owl", "tombstone"],
            },
            "stop_the_presses": {
                "schemes": ["60151a,60151b"],
                "set_aside": [str(card_id) for card_id in range(60152, 60157)],
                "encounters": ["60157", "60158", "60158"],
                "modular_sets": ["tombstone", "tracksuit_mafia"],
            },
        }

        for slug, values in expected.items():
            with self.subTest(slug=slug):
                scenario = json.loads(
                    (ROOT / "data" / "scenarios" / f"{slug}.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(scenario["kind"], "main-scenario")
                self.assertEqual(scenario["villain"], [])
                for key, value in values.items():
                    self.assertEqual(scenario[key], value)

    def test_key_printed_values_traits_and_keywords_match_scans(self):
        papers = {
            paper["card_id"]: paper
            for paper in json.loads(
                (ROOT / "data" / "cards.json").read_text(encoding="utf-8")
            )["fne"]
        }

        self.assertEqual(papers["60128b"]["desc"]["EscalationThreat"], "2*")
        self.assertEqual(papers["60130"]["traits"], ["VEHICLE"])
        self.assertEqual(papers["60131"]["desc"]["Hinder"], "1*")
        for card_id in ("60134b", "60135b", "60136b", "60137b", "60138b"):
            self.assertEqual(papers[card_id]["desc"]["TargetThreat"], "10")
            self.assertEqual(papers[card_id]["desc"]["EscalationThreat"], "1")
        for card_id in range(60144, 60150):
            self.assertIn("PRISONER", papers[str(card_id)]["traits"])
        self.assertEqual(papers["60149"]["desc"]["Boost"], "4")
        for card_id in range(60153, 60157):
            self.assertEqual(papers[str(card_id)]["desc"]["Uses"], "3,stamina")
            self.assertIn("DAILY BUGLE", papers[str(card_id)]["traits"])


class TestTheGetawayMechanics(unittest.TestCase):

    def test_setup_uses_standard_or_expert_speed_and_attaches_out_front(self):
        module = import_module("cards.pack.fne.the_getaway.60128a")
        ability = module.GetAbilities()[0]
        scheme = MagicMock()
        villain = MagicMock()
        effect = MagicMock()
        effect.this.CastTo.return_value = scheme

        for expert, expected in ((False, 1), (True, 2)):
            with self.subTest(expert=expert):
                with (
                    patch.object(module.Worlds, "IsExpert", return_value=expert),
                    patch.object(module.Worlds, "FindVillain", return_value=villain),
                    patch.object(module.Faces, "PlaceCountersOn") as place,
                    patch.object(module.SetupCards, "AttachTo") as attach,
                ):
                    ability.operation(effect, MagicMock())
            place.assert_called_once_with([scheme], expected, "speed", effect)
            attach.assert_called_once_with(
                effect,
                villain,
                name="Out Front",
                card_type=module.Attachment,
                include_in_play=False,
            )

    def test_round_end_flips_alongside_or_adds_a_second_speed_counter(self):
        module = import_module("cards.pack.fne.the_getaway.60128b")
        abilities = module.GetAbilities()
        ability = abilities[0]
        scheme = MagicMock(threat=1)
        alongside = MagicMock()
        effect = MagicMock()
        effect.this.CastTo.return_value = scheme

        with (
            patch.object(module.Worlds, "FindCardOnField", return_value=alongside),
            patch.object(module.Faces, "PlaceCountersOn") as place,
        ):
            ability.operation(effect, MagicMock())
        place.assert_called_once_with([scheme], 1, "speed", effect)
        alongside.card.Flip.assert_called_once_with(effect)

        alongside.reset_mock()
        with (
            patch.object(module.Worlds, "FindCardOnField", return_value=None),
            patch.object(module.Faces, "PlaceCountersOn") as place,
        ):
            ability.operation(effect, MagicMock())
        self.assertEqual(place.call_count, 2)
        alongside.card.Flip.assert_not_called()

        scheme.threat = 0
        with patch.object(module.Faces, "PlaceCountersOn") as place:
            ability.operation(effect, MagicMock())
        place.assert_not_called()

    def test_out_front_replaces_all_damage_and_flips_after_any_last_threat_removal(self):
        module = import_module("cards.pack.fne.the_getaway.60129a")
        abilities = module.GetAbilities()
        scheme = MagicMock()
        effect = MagicMock()
        effect.this.card.face = effect.this
        damage_message = MagicMock()
        damage_message.PreventDamage.return_value = 4

        with patch.object(module, "GetGetawayScheme", return_value=scheme):
            abilities[2].operation(effect, damage_message)
        damage_message.PreventDamage.assert_called_once_with("All", effect)
        scheme.RemoveThreatFromSchemes.assert_called_once_with(
            [scheme], 4, effect, ignore_crisis=True
        )

        abilities[3].operation(effect, MagicMock())
        effect.this.card.Flip.assert_called_once_with(effect)

    def test_speed_based_treacheries_repeat_each_choice(self):
        for card_id in ("60132", "60133"):
            with self.subTest(card_id=card_id):
                module = import_module(f"cards.pack.fne.the_getaway.{card_id}")
                player = MagicMock()
                scheme = MagicMock()
                message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))
                with (
                    patch.object(module, "GetSpeed", return_value=4),
                    patch.object(module, "GetGetawayScheme", return_value=scheme),
                ):
                    module.GetAbilities()[0].operation(MagicMock(), message)
                self.assertEqual(player.ChooseAbilities.call_count, 4)


class TestProtectionRacketMechanics(unittest.TestCase):

    def test_scenario_area_crisis_blocks_every_personal_main_scheme(self):
        owner_one = MagicMock()
        owner_two = MagicMock()
        area_one = MagicMock()
        area_two = MagicMock()
        world = MagicMock(game_areas=[area_one, area_two])
        crisis = MagicMock()
        crisis.card.world = world
        crisis.card.GetGameArea.return_value = area_one

        schemes = []
        for owner in (owner_one, owner_two):
            scheme = MagicMock()
            scheme.paper.set_name = "Protection Racket"
            scheme.card.GetOwner.return_value = owner
            scheme.card.world = world
            schemes.append(scheme)

        with (
            patch.object(
                Worlds,
                "GetCrisisFaces",
                side_effect=lambda game_area: [crisis] if game_area is area_one else [],
            ),
            patch.object(Worlds, "GetPlayAreaPlayer", return_value=None),
        ):
            self.assertEqual(
                Worlds.GetCrisisFacesAffectingMainScheme(schemes[0]),
                [crisis],
            )
            self.assertEqual(
                Worlds.GetCrisisFacesAffectingMainScheme(schemes[1]),
                [crisis],
            )

        with (
            patch.object(Worlds, "GetMainSchemes", return_value=[]),
            patch.object(Worlds, "GetAllMainSchemes", return_value=schemes),
            patch.object(Worlds, "GetPlayAreaPlayer", return_value=None),
        ):
            self.assertEqual(
                Worlds.GetMainSchemesAffectedByCrisis(crisis),
                schemes,
            )

    def test_player_area_crisis_only_blocks_its_owned_main_scheme(self):
        owner_one = MagicMock()
        owner_two = MagicMock()
        game_area = MagicMock()
        world = MagicMock(game_areas=[game_area])
        local_crisis = MagicMock()

        schemes = []
        for owner in (owner_one, owner_two):
            scheme = MagicMock()
            scheme.paper.set_name = "Protection Racket"
            scheme.card.GetOwner.return_value = owner
            scheme.card.world = world
            schemes.append(scheme)

        with (
            patch.object(Worlds, "GetCrisisFaces", return_value=[local_crisis]),
            patch.object(Worlds, "GetPlayAreaPlayer", return_value=owner_one),
        ):
            self.assertEqual(
                Worlds.GetCrisisFacesAffectingMainScheme(schemes[0]),
                [local_crisis],
            )
            self.assertEqual(
                Worlds.GetCrisisFacesAffectingMainScheme(schemes[1]),
                [],
            )

    def test_main_scheme_threat_removal_uses_protection_racket_crisis_scope(self):
        scheme = MagicMock()
        effect = MagicMock()
        effect.IsIgnoreKeyword.return_value = False
        crisis = MagicMock()
        icon_message = MagicMock()

        with (
            patch.object(
                Worlds,
                "GetCrisisFacesAffectingMainScheme",
                return_value=[crisis],
            ) as get_crisis,
            patch.object(Message, "IconsActivate_Text", return_value=icon_message),
        ):
            removed = MainScheme.RemoveThreatInternal(
                scheme,
                MagicMock(),
                3,
                effect,
            )

        self.assertEqual(removed, 0)
        get_crisis.assert_called_once_with(scheme)
        icon_message.Send.assert_called_once_with()

    def test_crisis_ui_marks_every_affected_personal_main_scheme(self):
        crisis = MagicMock()
        crisis.IsInPlay.return_value = True
        schemes = [MagicMock(), MagicMock()]

        with patch.object(
            Worlds,
            "GetMainSchemesAffectedByCrisis",
            return_value=schemes,
        ) as get_schemes:
            CanCrisis.SetCrisisEffectedBy(crisis, 1)

        get_schemes.assert_called_once_with(crisis)
        for scheme in schemes:
            scheme.card.ui.SetEffectedBy.assert_called_once()

    def test_play_area_helper_handles_controlled_cards_minions_and_attachments(self):
        module = import_module("cards.pack.fne.protection_racket")
        owner = MagicMock(spec=module.Player)
        effect = MagicMock()
        effect.this.card.GetOwner.return_value = owner

        minion = MagicMock()
        minion.CastTo.return_value.engaged_player = owner
        with patch.object(module.Minion, "IsType", return_value=True):
            self.assertTrue(module.IsInThisPlayArea(minion, effect))

        controlled = MagicMock()
        controlled.card.area.play_area = owner
        with patch.object(module.Minion, "IsType", return_value=False):
            self.assertTrue(module.IsInThisPlayArea(controlled, effect))

        attachment = MagicMock()
        attachment.card.area.play_area = None
        attachment.CastTo.return_value.GetBindFace.return_value = controlled
        with (
            patch.object(module.Minion, "IsType", return_value=False),
            patch.object(module.Attachment, "IsType", return_value=True),
        ):
            self.assertTrue(module.IsInThisPlayArea(attachment, effect))

    def test_all_location_operations_apply_their_printed_damage_heal_and_threat(self):
        effect = MagicMock()
        attacker = MagicMock()

        battle = import_module("cards.pack.fne.protection_racket.60134b")
        battle.GetAbilities()[0].operation(effect, SimpleNamespace(attacker=attacker))
        effect.this.DealDamage.assert_called_once_with([attacker], 1, effect)

        bull = import_module("cards.pack.fne.protection_racket.60135b")
        with patch.object(bull, "PlaceThreatHere") as place:
            bull.GetAbilities()[0].operation(effect, SimpleNamespace(excess_damage=3))
        place.assert_called_once_with(effect, 3)

        dry = import_module("cards.pack.fne.protection_racket.60136b")
        character = MagicMock()
        with patch.object(dry, "PlaceThreatHere") as place:
            dry.GetAbilities()[0].operation(effect, SimpleNamespace(trigger=character))
        effect.this.DealDamage.assert_called_with([character], 1, effect)
        place.assert_called_once_with(effect, 1)

        pizza = import_module("cards.pack.fne.protection_racket.60138b")
        killer = MagicMock()
        with patch.object(pizza, "PlaceThreatHere") as place:
            with patch.object(pizza.Condition, "CheckWhichCard", return_value=True):
                pizza.GetAbilities()[0].operation(
                    effect,
                    SimpleNamespace(target=MagicMock(), attacker=killer),
                )
            delayed = effect.this.effect.RegisterTemp.call_args.args[0]
            delayed.operation(effect, SimpleNamespace(killer=killer))
        effect.this.HealthUnits.assert_called_once_with([killer], 1, effect)
        place.assert_called_once_with(effect, 1)

    def test_shop_proprietor_enters_under_control_surges_and_penalizes_owner(self):
        module = import_module("cards.pack.fne.protection_racket.60139")
        abilities = module.GetAbilities()
        ally = MagicMock()
        player = MagicMock(spec=module.Player)
        scheme = MagicMock()
        effect = MagicMock()
        effect.this.CastTo.return_value = ally
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))
        with patch.object(module, "ThisCardGainSurge") as surge:
            abilities[0].operation(effect, message)
        ally.card.SetOwner.assert_called_once_with(player)
        ally.PutIntoPlay.assert_called_once_with(player, effect, under_control=True)
        surge.assert_called_once_with(effect)

        leaving = MagicMock()
        leaving.trigger.GetControlBy.return_value = player
        with patch.object(module, "GetProtectionRacketScheme", return_value=scheme):
            abilities[1].operation(effect, leaving)
        scheme.PlaceThreatOnSchemes.assert_called_once_with([scheme], 4, effect)

    def test_man_bull_counts_excess_and_boost_registers_for_that_attack(self):
        module = import_module("cards.pack.fne.protection_racket.60140")
        scheme = MagicMock()
        player = MagicMock()
        effect = MagicMock()
        attacks = [SimpleNamespace(excess_damage=2), SimpleNamespace(), SimpleNamespace(excess_damage=1)]
        with patch.object(module, "GetProtectionRacketScheme", return_value=scheme):
            module.PlaceAttackExcess(effect, player, attacks)
        scheme.PlaceThreatOnSchemes.assert_called_once_with([scheme], 3, effect)

        boost_message = MagicMock()
        boost_message.would_atk_message = MagicMock()
        module.GetAbilities()[1].operation(effect, boost_message)
        effect.this.effect.RegisterTemp.assert_called_once()
        registered = effect.this.effect.RegisterTemp.call_args.args[0]
        self.assertEqual(registered.when, Message.AfterUnitAttackEnd)

    def test_change_of_venue_swaps_and_transfers_threat(self):
        module = import_module("cards.pack.fne.protection_racket")
        player = MagicMock()
        effect = MagicMock()
        old = MagicMock(threat=6)
        new_face = MagicMock()
        new_face.card.face.printed_target_threat = 10
        new_scheme = MagicMock()
        new_face.card.face.CastTo.return_value = new_scheme
        with (
            patch.object(module, "GetProtectionRacketScheme", return_value=old),
            patch.object(module.Worlds, "GetSetAsideAreaCards", return_value=[new_face]),
            patch.object(module.Rand, "RandomChoice", return_value=new_face),
            patch.object(module.Worlds, "AsideDeck", return_value=MagicMock()),
            patch.object(module.Faces, "MoveAllTo"),
        ):
            self.assertTrue(module.SwapProtectionRacketScheme(player, effect))
        new_face.card.SetOwner.assert_called_once_with(player)
        new_scheme.PutIntoPlay.assert_called_once_with(player, effect)
        new_scheme.PlaceThreatOnSchemes.assert_called_once_with([new_scheme], 6, effect)


class TestRaftBreakoutMechanics(unittest.TestCase):

    def test_setup_attaches_key_and_searches_one_prisoner_per_player(self):
        module = import_module("cards.pack.fne.the_raft_breakout.60142a")
        ability = module.GetAbilities()[0]
        villain = MagicMock()
        players = [MagicMock(), MagicMock()]
        prisoner = MagicMock()
        effect = MagicMock()
        with (
            patch.object(module.Worlds, "FindVillain", return_value=villain),
            patch.object(module.Worlds, "GetPlayers", return_value=players),
            patch.object(
                module.Worlds,
                "DiscardEncounterCardsUntil",
                side_effect=[prisoner, None],
            ) as search,
            patch.object(module.SetupCards, "AttachTo") as attach,
        ):
            ability.operation(effect, MagicMock())
        attach.assert_called_once_with(
            effect,
            villain,
            name="Master Key",
            card_type=module.Attachment,
            include_in_play=False,
        )
        self.assertEqual(search.call_count, 2)
        prisoner.Reveal.assert_called_once_with(players[0], effect)

    def test_prisoner_defeat_removes_one_or_two_threat_without_bypassing_crisis(self):
        module = import_module("cards.pack.fne.the_raft_breakout.60142b")
        abilities = module.GetAbilities()
        scheme = MagicMock()
        effect = MagicMock()
        effect.this.CastTo.return_value = scheme
        minion = MagicMock()
        for elite, expected in ((False, 1), (True, 2)):
            minion.HasTrait.return_value = elite
            abilities[0].operation(effect, SimpleNamespace(trigger=minion))
            scheme.RemoveThreatFromSchemes.assert_called_with(
                [scheme], expected, effect
            )

    def test_absorbing_man_tucks_top_card_and_counts_distinct_resources(self):
        module = import_module("cards.pack.fne.the_raft_breakout.60144")
        minion = MagicMock()
        player = MagicMock()
        top = MagicMock()
        player.player_deck.GetTop.return_value = top
        message = MagicMock()
        message.GetAgainstPlayer.return_value = player
        effect = MagicMock()
        effect.this.CastTo.return_value = minion
        with patch.object(module.FacesCounter, "GetPrintedResourcesTypes", return_value=3):
            module.GetAbilities()[0].operation(effect, message)
        minion.TuckCardUnderHere.assert_called_once_with(top, effect)
        message.GainATKForThisAttack.assert_called_once_with(3, effect)

    def test_baron_zemo_converts_existing_threatened_allies_and_new_targets(self):
        module = import_module("cards.pack.fne.the_raft_breakout.60145")
        abilities = module.GetAbilities()
        ally = MagicMock()
        ally.IsInPlay.return_value = True
        ally.GetCounters.return_value = 1
        player = MagicMock()
        ally.GetControlByPlayer.return_value = player
        candidate = MagicMock()
        candidate.GetCounters.return_value = 1
        candidate.CastTo.return_value = ally
        effect = MagicMock()
        with (
            patch.object(module.Worlds, "GetOnFieldCharacters", return_value=[candidate]),
            patch.object(module.Ally, "IsType", return_value=True),
            patch("game.ability.factory.treat.TreatAsMinion") as treat,
        ):
            abilities[0].operation(effect, MagicMock())
        treat.assert_called_once()
        self.assertIs(treat.call_args.args[0], ally)
        self.assertEqual(treat.call_args.args[1], "Minion")
        self.assertIs(treat.call_args.args[2], player)
        self.assertEqual(treat.call_args.kwargs["while_counter"], "threat")

    def test_drang_barrage_increases_each_time_and_deals_indirect_damage(self):
        module = import_module("cards.pack.fne.the_raft_breakout.60146")
        minion = MagicMock()
        minion.GetCounters.side_effect = [1, 2]
        player = MagicMock()
        message = MagicMock()
        message.GetAgainstPlayer.return_value = player
        effect = MagicMock()
        effect.this.CastTo.return_value = minion
        with patch.object(module.Faces, "PlaceCountersOn"):
            ability = module.GetAbilities()[0]
            ability.operation(effect, message)
            ability.operation(effect, message)
        self.assertEqual(player.GetIdentity.return_value.TakeIndirectDamage.call_count, 2)
        player.GetIdentity.return_value.TakeIndirectDamage.assert_has_calls(
            [call(minion, 1, effect), call(minion, 2, effect)]
        )

    def test_master_key_and_mysterio_capture_only_their_printed_boost_types(self):
        cases = (
            ("60143", "AfterUnitSchemeEnd", "boost_cards"),
            ("60147", "AfterUnitAttackEnd", "atk_messages"),
        )
        for card_id, _, field in cases:
            with self.subTest(card_id=card_id):
                module = import_module(f"cards.pack.fne.the_raft_breakout.{card_id}")
                player = MagicMock()
                message = MagicMock()
                message.GetAgainstPlayer.return_value = player
                wanted = MagicMock()
                other = MagicMock()
                if field == "boost_cards":
                    message.boost_cards = [wanted, other]
                    with patch.object(module.Minion, "IsType", side_effect=lambda face: face is wanted):
                        module.GetAbilities()[-1].operation(MagicMock(), message)
                else:
                    with (
                        patch.object(module, "ActivationBoostCards", return_value=[wanted, other]),
                        patch.object(module.Treachery, "IsType", side_effect=lambda face: face is wanted),
                    ):
                        module.GetAbilities()[0].operation(MagicMock(), message)
                player.DealEncounterCard.assert_called_once()
                self.assertIs(player.DealEncounterCard.call_args.args[0], wanted)

    def test_proxima_offers_threat_or_attack_and_rhino_boost_targets_activator(self):
        proxima = import_module("cards.pack.fne.the_raft_breakout.60148")
        player = MagicMock()
        scheme = MagicMock()
        message = MagicMock()
        message.GetAgainstPlayer.return_value = player
        with patch.object(proxima.Worlds, "FindMainScheme", return_value=scheme):
            proxima.GetAbilities()[0].operation(MagicMock(), message)
        self.assertEqual(len(player.ChooseAbilities.call_args.args[1:]), 2)

        rhino = import_module("cards.pack.fne.the_raft_breakout.60149")
        activator = MagicMock()
        with patch.object(rhino.Faces, "GiveStatus") as give:
            rhino.GetAbilities()[1].operation(
                MagicMock(), SimpleNamespace(activating_enemy=activator)
            )
        give.assert_called_once_with([activator], "Tough", unittest.mock.ANY)

    def test_imprisoned_has_both_discard_costs_and_all_three_restrictions(self):
        module = import_module("cards.pack.fne.the_raft_breakout.60150")
        abilities = module.GetAbilities()
        self.assertEqual(len(abilities), 7)
        self.assertEqual(abilities[4].flags.ability_type, AbilityType.HeroAction)
        self.assertEqual(abilities[5].flags.ability_type, AbilityType.HeroAction)
        self.assertIsNotNone(abilities[4].cost_fn)
        self.assertEqual(len(abilities[5].cost_funcs), 1)


class TestStopThePressesMechanics(unittest.TestCase):

    def test_setup_assigns_distinct_random_supports_and_removes_the_rest(self):
        module = import_module("cards.pack.fne.stop_the_presses.60151a")
        players = [MagicMock(), MagicMock()]
        supports = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        selected = supports[:2]
        leftovers = supports[2:]
        effect = MagicMock()
        with (
            patch.object(module.SetupCards, "PutIntoPlay") as put_environment,
            patch.object(module.Worlds, "GetSetAsideAreaCards", return_value=supports),
            patch.object(module.Worlds, "GetPlayers", return_value=players),
            patch.object(module.Rand, "RandomChoice", side_effect=lambda cards, effect: cards[0]),
            patch.object(module.Faces, "RemoveAllFromGame") as remove,
        ):
            module.GetAbilities()[0].operation(effect, MagicMock())
        put_environment.assert_called_once_with(
            effect,
            name="Daily Bugle",
            card_type=module.Environment,
        )
        selected[0].PutIntoPlay.assert_called_once_with(players[0], effect, under_control=True)
        selected[1].PutIntoPlay.assert_called_once_with(players[1], effect, under_control=True)
        remove.assert_called_once_with(leftovers, effect)

    def test_undefended_attack_offers_stamina_when_available_and_expert_threat(self):
        module = import_module("cards.pack.fne.stop_the_presses.60151b")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        support = MagicMock()
        support.GetCounters.return_value = 1
        effect = MagicMock()
        message = SimpleNamespace(attacked_you=player)
        with (
            patch.object(module, "GetDailyBugleSupports", return_value=[support]),
            patch.object(module.Worlds, "IsExpert", return_value=True),
        ):
            ability.operation(effect, message)
        choices = player.ChooseAbilities.call_args.args[1:]
        self.assertEqual(len(choices), 2)
        self.assertIn("3 threat", choices[0].name)

    def test_daily_bugle_support_leaving_play_causes_a_loss(self):
        module = import_module("cards.pack.fne.stop_the_presses.60151b")
        loss = next(
            ability
            for ability in module.GetAbilities()
            if ability.when == Message.AfterCardsMoved
        )
        support = MagicMock()
        old_area = MagicMock()
        old_area.flags.is_in_play = True
        support.card.area.flags.is_in_play = False
        effect = MagicMock()
        with (
            patch.object(module.DAILY_BUGLE_SUPPORT, "Check", return_value=True),
            patch.object(module.Worlds, "SetGameOver") as game_over,
        ):
            loss.operation(effect, SimpleNamespace(face_areas={support: old_area}))
        game_over.assert_called_once_with(False, effect)

        support.card.area.flags.is_in_play = True
        game_over.reset_mock()
        with (
            patch.object(module.DAILY_BUGLE_SUPPORT, "Check", return_value=True),
            patch.object(module.Worlds, "SetGameOver") as game_over,
        ):
            loss.operation(effect, SimpleNamespace(face_areas={support: old_area}))
        game_over.assert_not_called()

    def test_daily_bugle_environment_restores_the_support_it_exhausted(self):
        module = import_module("cards.pack.fne.stop_the_presses.60152")
        support = MagicMock()
        cost = SimpleNamespace(return_exhausted_cards=[support])
        effect = MagicMock()
        effect.cost_func.Get.return_value = cost
        with patch.object(module.Faces, "PlaceCountersOn") as place:
            module.GetAbilities()[0].operation(effect, MagicMock())
        place.assert_called_once_with([support], 1, "stamina", effect)

    def test_betty_cancels_both_boost_parts_and_deals_replacement(self):
        module = import_module("cards.pack.fne.stop_the_presses.60154")
        enemy = MagicMock()
        would_message = SimpleNamespace(trigger=MagicMock())
        would_message.trigger.CastTo.return_value = enemy
        message = MagicMock(would_message=would_message)
        effect = MagicMock()
        module.GetAbilities()[0].operation(effect, message)
        message.CancelAllBoostIcons.assert_called_once_with(effect)
        message.CancelBoostAbility.assert_called_once_with(effect)
        enemy.GiveFacedownBoostCardsInternal.assert_called_once_with(
            1, effect, would_message
        )

    def test_robbie_can_discard_the_dealt_card_and_replace_it(self):
        module = import_module("cards.pack.fne.stop_the_presses.60156")
        face = MagicMock()
        player = MagicMock()
        initiator = MagicMock()
        effect = MagicMock()
        effect.GetInitiator.return_value = initiator
        message = SimpleNamespace(
            GetToPlayer=MagicMock(return_value=player),
            would_message=SimpleNamespace(face=face),
        )
        with patch.object(module.Faces, "LookAt"):
            module.GetAbilities()[0].operation(effect, message)
        choice = initiator.MayChooseOneAbility.call_args.args[1]
        with patch.object(module.Faces, "DiscardAll") as discard:
            choice.operation(MagicMock(targets=[face]), MagicMock())
        discard.assert_called_once_with([face], effect)
        player.DealEncounterCards.assert_called_once_with(1, effect)

    def test_exclusive_interview_exhausts_all_daily_bugle_supports(self):
        module = import_module("cards.pack.fne.stop_the_presses.60157")
        supports = [MagicMock(), MagicMock()]
        with (
            patch.object(module, "GetDailyBugleSupports", return_value=supports),
            patch.object(module.Faces, "ExhaustAll") as exhaust,
        ):
            module.GetAbilities()[-1].operation(MagicMock(), MagicMock())
        exhaust.assert_called_once_with(supports, unittest.mock.ANY)

    def test_breaking_news_uses_one_support_for_both_costs_and_boost_exhausts(self):
        module = import_module("cards.pack.fne.stop_the_presses.60158")
        support = MagicMock()
        support.CanExhaust.return_value = True
        support.GetCounters.return_value = 2
        player = MagicMock()
        player.AskChooseFace.return_value = support
        scheme = MagicMock()
        effect = MagicMock()
        revealed_message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))
        with (
            patch.object(module, "GetDailyBugleSupports", return_value=[support]),
            patch.object(module.Worlds, "FindMainScheme", return_value=scheme),
        ):
            module.GetAbilities()[0].operation(effect, revealed_message)
        choices = player.ChooseAbilities.call_args.args[1:]
        self.assertEqual(len(choices), 2)
        self.assertEqual(len(choices[0].cost_funcs), 1)

        boost_message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))
        with (
            patch.object(module, "GetDailyBugleSupports", return_value=[support]),
            patch.object(module.Faces, "ExhaustAll") as exhaust,
        ):
            module.GetAbilities()[1].operation(effect, boost_message)
        exhaust.assert_called_once_with([support], effect)


if __name__ == "__main__":
    unittest.main()
