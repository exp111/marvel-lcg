from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.database import CardsDB
from cards.pack.fne.campaign import (
    CAMPAIGN_ENVIRONMENTS,
    ApplyExpertPersistentDamageAndHealing,
    CampaignSetup,
    GetScenarioProgress,
    GetScenarioStatus,
    PutResolvedCampaignEnvironmentsIntoPlay,
    PutTyphoidMaryCampaignAllyIntoPlay,
    RemoveRecordedAlliesAndSupports,
    _apply_interchangeable_scenario_progress,
    _apply_kingpin_campaign_setup,
)
from core.utility.types import Types
from engine.lib.version import Ver
from game.card.factory import CardFactory
from game.message import Message


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_FACE_IDS = [
    f"{card_id}{side}"
    for card_id in range(60205, 60211)
    for side in "ab"
]


class TestFearNoEvilCampaignRegistration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Ver.Initialize()
        CardsDB.Initialize()

    def test_all_twelve_printed_faces_initialize_through_card_factory(self):
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1

        for card_id in CAMPAIGN_FACE_IDS:
            with self.subTest(card_id=card_id):
                face = CardFactory.CreateFace(CardsDB.FindCardPaper(card_id), world)
                self.assertEqual(face.paper.card_id, card_id)
                self.assertTrue(face.ability.abilities)

    def test_printed_metadata_matches_the_campaign_cards(self):
        papers = {
            paper["card_id"]: paper
            for paper in json.loads(
                (ROOT / "data" / "cards.json").read_text(encoding="utf-8")
            )["fne"]
        }

        expected_environment_text = {
            "60205a": "<b>Setup</b>: Give each identity a tough status card.",
            "60205b": (
                "<b>Setup</b>: Each player chooses to stun or confuse their "
                "identity (in expert mode, do both instead)."
            ),
            "60206a": (
                "<b>Setup</b>: After resolving mulligans, each player may search "
                "their deck and discard pile for an upgrade and add it to their "
                "hand. In expert mode, each player who did so discards 1 card "
                "from their hand."
            ),
            "60206b": (
                "In expert mode, attachments cannot be discarded from play "
                "during the first round.\n<b>Setup</b>: Each player searches the "
                "encounter deck for an attachment and reveals it. Deal a "
                "facedown encounter card to each player who could not."
            ),
            "60207a": (
                "<b>Setup</b>: After resolving mulligans, each player may search "
                "their deck and discard pile for a support and add it to their "
                "hand. In expert mode, each player who did so discards 1 card "
                "from their hand."
            ),
            "60207b": (
                "<b>Setup</b>: Each player chooses and discards 1 card from their "
                "hand (in expert mode, 2 cards instead)."
            ),
            "60208a": (
                "<b>Setup</b>: After resolving mulligans, each player may search "
                "their deck and discard pile for an ally and add it to their "
                "hand. In expert mode, each player who did so discards 1 card "
                "from their hand."
            ),
            "60208b": (
                "<b>Setup</b>: Shuffle each minion in The Raft Breakout encounter "
                "set into the encounter deck (in expert mode, deal 1 of those "
                "minions at random to each player as a facedown encounter card "
                "before shuffling in the rest)."
            ),
            "60209a": (
                "<b>Setup</b>: Each player puts 1 [[DAILY BUGLE]] support (that "
                "has not been removed from the campaign) into play from the Stop "
                "the Presses! encounter set."
            ),
            "60209b": (
                "<b>Setup</b>: Deal each player 1 facedown encounter card (in "
                "expert mode, 2 encounter cards instead)."
            ),
        }
        for card_id, text in expected_environment_text.items():
            with self.subTest(card_id=card_id):
                self.assertEqual(papers[card_id]["type"], "Environment")
                self.assertEqual(papers[card_id]["set_name"], "Fear No Evil Campaign")
                self.assertEqual(papers[card_id]["text"], text)

        self.assertEqual(
            papers["60210a"]["desc"],
            {
                "HP": "3", "ATK": "1*", "THW": "2*", "RES": "B",
                "Class": "Campaign", "Setup": "1", "Victory": "-1",
            },
        )
        self.assertEqual(
            papers["60210b"]["desc"],
            {
                "HP": "3", "ATK": "2*", "THW": "1*", "RES": "R",
                "Class": "Campaign", "Victory": "-1",
            },
        )
        for card_id in ("60210a", "60210b"):
            self.assertEqual(papers[card_id]["traits"], ["MUTANT", "PSIONIC"])
            self.assertTrue(papers[card_id]["name"].startswith("* "))

    def test_package_maximum_and_checksums_are_current(self):
        sets_info = json.loads(
            (ROOT / "data" / "sets_info.json").read_text(encoding="utf-8")
        )
        self.assertEqual(sets_info["60. Fear No Evil"]["max_id"], "60210")

        for filename in ("cards.json", "sets_info.json"):
            with self.subTest(filename=filename):
                data = json.loads(
                    (ROOT / "data" / filename).read_text(encoding="utf-8")
                )
                stored = data.pop("checksum")
                self.assertEqual(stored, Types.DictChecksum(data))

    def test_campaign_is_available_with_every_printed_log_field(self):
        html = (ROOT / "public" / "scene.html").read_text(encoding="utf-8")
        self.assertIn('fear_no_evil: {', html)
        self.assertIn('name: "Fear No Evil"', html)
        for scenario_name in CAMPAIGN_ENVIRONMENTS:
            self.assertIn(f'description: "{scenario_name} Status"', html)
            self.assertIn(f'description: "{scenario_name} Progress"', html)
            self.assertIn(f'description: "{scenario_name} Villain"', html)
        self.assertIn('description: "Trust Established?"', html)
        self.assertIn('description: "Mary Defeated?"', html)
        self.assertIn(
            'description: "Allies and Persona Supports Removed from the Campaign"',
            html,
        )

    def test_every_campaign_scenario_has_early_and_post_mulligan_setup(self):
        scripts = {
            "art_museum_heist/60121a.py": "Art Museum Heist",
            "the_getaway/60128a.py": "The Getaway",
            "protection_racket/60134a.py": "Protection Racket",
            "the_raft_breakout/60142a.py": "The Raft Breakout",
            "stop_the_presses/60151a.py": "Stop the Presses!",
            "kingpin/60161a.py": "Kingpin",
        }
        for relative_path, scenario_name in scripts.items():
            with self.subTest(scenario=scenario_name):
                source = (
                    ROOT / "cards" / "pack" / "fne" / relative_path
                ).read_text(encoding="utf-8")
                self.assertEqual(source.count(f'*CampaignSetup("{scenario_name}")'), 1)
                abilities = CampaignSetup(scenario_name)
                self.assertEqual(len(abilities), 2)
                self.assertIs(abilities[0].when, Message.WhenGameBeginSetup)
                self.assertIs(
                    abilities[1].when,
                    Message.AfterPlayersResolveMulligans,
                )

    def test_post_mulligan_message_is_scoped_to_fear_no_evil_campaign_games(self):
        source = (ROOT / "game" / "world" / "world.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('self.scene.campaign.campaign_id == "fear_no_evil"', source)
        self.assertEqual(source.count("Message.AfterPlayersResolveMulligans(self).Send()"), 1)


class TestFearNoEvilCampaignCardMechanics(unittest.TestCase):

    def test_art_museum_completed_gives_every_identity_tough(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60205a"
        )
        ability = module.GetAbilities()[0]
        identities = [MagicMock(), MagicMock()]
        players = [
            SimpleNamespace(GetIdentity=lambda identity=identity: identity)
            for identity in identities
        ]
        effect = SimpleNamespace()

        with patch.object(
            module.Worlds, "GetPlayers", return_value=players
        ), patch.object(module.Faces, "GiveStatus") as give_status:
            ability.operation(effect, MagicMock())

        give_status.assert_called_once_with(identities, "Tough", effect)

    def test_art_museum_failed_standard_chooses_one_status_and_expert_does_both(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60205b"
        )
        ability = module.GetAbilities()[0]
        identity = MagicMock()
        player = MagicMock()
        player.GetIdentity.return_value = identity
        effect = SimpleNamespace()

        with patch.object(
            module.Worlds, "GetPlayers", return_value=[player]
        ), patch.object(module.Worlds, "IsExpert", return_value=False):
            ability.operation(effect, MagicMock())
        choices = player.ChooseAbilities.call_args.args[1:]
        self.assertEqual([choice.name for choice in choices], [
            "Stun your identity", "Confuse your identity",
        ])

        player.reset_mock()
        with patch.object(
            module.Worlds, "GetPlayers", return_value=[player]
        ), patch.object(
            module.Worlds, "IsExpert", return_value=True
        ), patch.object(module.Faces, "GiveStatus") as give_status:
            ability.operation(effect, MagicMock())
        self.assertEqual(give_status.call_args_list, [
            call([identity], "Stunned", effect),
            call([identity], "Confused", effect),
        ])
        player.ChooseAbilities.assert_not_called()

    def test_completed_search_rewards_are_optional_and_expert_discards_after_gain(self):
        for card_id, card_type_name in (
            ("60206a", "Upgrade"),
            ("60207a", "Support"),
            ("60208a", "Ally"),
        ):
            with self.subTest(card_id=card_id):
                module = import_module(
                    f"cards.pack.fne.fear_no_evil_campaign.{card_id}"
                )
                ability = module.GetAbilities()[0]
                player = MagicMock()
                chosen = MagicMock()
                player.hand_cards.Get.return_value = [chosen]
                effect = SimpleNamespace()

                with patch.object(
                    module.Worlds, "GetPlayers", return_value=[player]
                ), patch.object(
                    module.Worlds, "IsExpert", return_value=True
                ), patch(
                    "cards.pack.fne.fear_no_evil_campaign.Search.PlayerCard",
                    return_value=chosen,
                ) as search:
                    ability.operation(effect, MagicMock())

                self.assertEqual(search.call_args.kwargs["may"], True)
                self.assertEqual(
                    search.call_args.kwargs["card_type"].__name__,
                    card_type_name,
                )
                self.assertTrue(search.call_args.kwargs["include_player_deck"])
                self.assertTrue(search.call_args.kwargs["include_discard_pile"])
                player.GainCard.assert_called_once_with(chosen, effect)
                player.AskDiscardFace.assert_called_once_with([chosen], effect)

    def test_getaway_failed_reveals_an_attachment_or_deals_a_facedown_card(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60206b"
        )
        ability = module.GetAbilities()[0]
        players = [MagicMock(), MagicMock()]
        attachment = MagicMock()
        effect = SimpleNamespace()

        with patch.object(module.Worlds, "GetPlayers", return_value=players), patch.object(
            module.Search,
            "EncounterCard",
            side_effect=[attachment, None],
        ) as search:
            ability.operation(effect, MagicMock())

        self.assertEqual(search.call_count, 2)
        self.assertFalse(search.call_args_list[0].kwargs["include_discard_pile"])
        attachment.Reveal.assert_called_once_with(players[0], effect)
        players[1].DealEncounterCards.assert_called_once_with(1, effect)

    def test_getaway_failed_attachment_lock_is_expert_first_round_only(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60206b"
        )
        lock = module.GetAbilities()[1]
        effect = SimpleNamespace(world=SimpleNamespace(round_id=1))
        message = MagicMock()

        with patch.object(module.Worlds, "IsExpert", return_value=True):
            self.assertTrue(lock.conditions[-2](effect, message))
            self.assertTrue(lock.conditions[-1](effect, message))
        effect.world.round_id = 2
        self.assertFalse(lock.conditions[-1](effect, message))
        with patch.object(module.Worlds, "IsExpert", return_value=False):
            self.assertFalse(lock.conditions[-2](effect, message))

    def test_protection_racket_failed_discards_the_printed_number(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60207b"
        )
        ability = module.GetAbilities()[0]
        player = MagicMock()
        cards = [MagicMock(), MagicMock(), MagicMock()]
        player.hand_cards.Get.return_value = cards
        effect = SimpleNamespace()

        with patch.object(module.Worlds, "GetPlayers", return_value=[player]), patch.object(
            module.Worlds, "IsExpert", return_value=True
        ):
            ability.operation(effect, MagicMock())
        player.AskDiscardFaces.assert_called_once_with(cards, (2, 2), effect)

    def test_raft_failed_expert_deals_random_prisoners_then_shuffles_the_rest(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60208b"
        )
        ability = module.GetAbilities()[0]
        players = [MagicMock(), MagicMock()]
        minions = [MagicMock() for _ in range(6)]
        effect = SimpleNamespace(world=MagicMock())

        with patch.object(module.Worlds, "GetPlayers", return_value=players), patch.object(
            module.Worlds, "IsExpert", return_value=True
        ), patch.object(
            module.CardFactory,
            "GenerateCard",
            side_effect=[SimpleNamespace(face=minion) for minion in minions],
        ), patch.object(
            module.Rand, "RandomChoice", side_effect=lambda choices, effect: choices[0]
        ), patch.object(module.Faces, "ShuffleAllTo") as shuffle:
            ability.operation(effect, MagicMock())

        players[0].DealEncounterCard.assert_called_once_with(minions[0], effect)
        players[1].DealEncounterCard.assert_called_once_with(minions[1], effect)
        shuffle.assert_called_once_with(minions[2:], "EncounterDeck", effect)

    def test_stop_the_presses_completed_assigns_available_supports_without_replacement(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60209a"
        )
        ability = module.GetAbilities()[0]
        players = [MagicMock(), MagicMock()]
        supports = [MagicMock(), MagicMock(), MagicMock()]
        for player, support in zip(players, supports):
            player.AskChooseFace.side_effect = lambda choices, effect, support=support, **kwargs: support
        effect = SimpleNamespace(world=MagicMock())
        papers = {
            "60153": SimpleNamespace(name="J. Jonah Jameson"),
            "60154": SimpleNamespace(name="Betty Brant"),
            "60155": SimpleNamespace(name="Ben Urich"),
            "60156": SimpleNamespace(name="Robbie Robertson"),
        }

        with patch.object(module.Worlds, "GetPlayers", return_value=players), patch.object(
            module, "_removed_campaign_titles", return_value={"Robbie Robertson"}
        ), patch.object(
            module.CardFactory,
            "FindCardPapers",
            side_effect=lambda card_id: [papers[card_id]],
        ), patch.object(
            module.CardFactory,
            "GenerateCard",
            side_effect=[
                SimpleNamespace(face=SimpleNamespace(CastTo=lambda card_type, face=face: face))
                for face in supports
            ],
        ):
            ability.operation(effect, MagicMock())

        supports[0].PutIntoPlay.assert_called_once_with(
            players[0], effect, under_control=True
        )
        supports[1].PutIntoPlay.assert_called_once_with(
            players[1], effect, under_control=True
        )
        self.assertNotIn(supports[0], players[1].AskChooseFace.call_args.args[0])

    def test_stop_the_presses_failed_deals_two_cards_in_expert(self):
        module = import_module(
            "cards.pack.fne.fear_no_evil_campaign.60209b"
        )
        ability = module.GetAbilities()[0]
        players = [MagicMock(), MagicMock()]
        effect = SimpleNamespace()

        with patch.object(module.Worlds, "GetPlayers", return_value=players), patch.object(
            module.Worlds, "IsExpert", return_value=True
        ):
            ability.operation(effect, MagicMock())
        for player in players:
            player.DealEncounterCards.assert_called_once_with(2, effect)

    def test_typhoid_mary_faces_heal_then_flip_on_their_printed_reveal(self):
        for card_id in ("60210a", "60210b"):
            with self.subTest(card_id=card_id):
                ability = import_module(
                    f"cards.pack.fne.fear_no_evil_campaign.{card_id}"
                ).GetAbilities()[0]
                ally = MagicMock()
                effect = MagicMock()
                effect.this.CastTo.return_value = ally
                message = MagicMock()

                ability.operation(effect, message)

                ally.HealHealth.assert_called_once_with("All", effect)
                ally.card.Flip.assert_called_once_with(effect)


class TestFearNoEvilCampaignSetup(unittest.TestCase):

    def test_post_mulligan_campaign_steps_resolve_in_printed_order(self):
        ability = CampaignSetup("Art Museum Heist")[1]
        effect = SimpleNamespace()
        resolved = []

        with patch(
            "cards.pack.fne.campaign.ApplyExpertPersistentDamageAndHealing",
            side_effect=lambda effect: resolved.append("persistent damage and heal"),
        ), patch(
            "cards.pack.fne.campaign.PutResolvedCampaignEnvironmentsIntoPlay",
            side_effect=lambda effect: resolved.append("environments"),
        ), patch(
            "cards.pack.fne.campaign.PutTyphoidMaryCampaignAllyIntoPlay",
            side_effect=lambda effect: resolved.append("mary"),
        ), patch(
            "cards.pack.fne.campaign.GetScenarioProgress", return_value=1
        ), patch(
            "cards.pack.fne.campaign._apply_interchangeable_scenario_progress",
            side_effect=lambda name, progress, effect: resolved.append("scenario"),
        ):
            ability.operation(effect, MagicMock())

        self.assertEqual(resolved, [
            "persistent damage and heal",
            "environments",
            "mary",
            "scenario",
        ])

    def test_status_and_progress_parsing_supports_the_campaign_log(self):
        effect = SimpleNamespace()
        values = {
            "The Getaway Status": "",
            "The Getaway Progress": "2",
            "Protection Racket Status": "Completed",
            "Protection Racket Progress": "3",
            "The Raft Breakout Status": "",
            "The Raft Breakout Progress": "3",
        }
        with patch(
            "game.operate.campaign_logs.CampaignLog.GetStrInternal",
            side_effect=lambda key, effect: values.get(key, ""),
        ):
            self.assertEqual(GetScenarioProgress("The Getaway", effect), 2)
            self.assertEqual(GetScenarioStatus("The Getaway", effect), "")
            self.assertEqual(
                GetScenarioStatus("Protection Racket", effect), "Completed"
            )
            self.assertEqual(
                GetScenarioStatus("The Raft Breakout", effect), "Failed"
            )

    def test_recorded_unique_allies_and_supports_are_removed_before_setup(self):
        ally = MagicMock()
        ally.name = "Mockingbird"
        ally.paper.is_unique = True
        ally.paper.card_id = "01083"
        ordinary = MagicMock()
        ordinary.name = "Energy"
        ordinary.paper.is_unique = False
        ordinary.paper.card_id = "01088"
        player = SimpleNamespace(
            player_deck=SimpleNamespace(Get=lambda: [ally, ordinary])
        )
        effect = SimpleNamespace()

        with patch(
            "game.operate.campaign_logs.CampaignLog.GetListInternal",
            side_effect=lambda key, effect: ["Mockingbird"] if key.startswith("Allies") else [],
        ), patch(
            "cards.pack.fne.campaign.Worlds.GetPlayers", return_value=[player]
        ), patch(
            "cards.pack.fne.campaign.Ally.IsType",
            side_effect=lambda face: face is ally,
        ), patch(
            "cards.pack.fne.campaign.Support.IsType", return_value=False
        ), patch(
            "cards.pack.fne.campaign.Faces.RemoveAllFromGame"
        ) as remove:
            RemoveRecordedAlliesAndSupports(effect)

        remove.assert_called_once_with([ally], effect)

    def test_expert_persistent_damage_and_optional_recovery_cost(self):
        identity = MagicMock()
        identity.max_health = 10
        alter_ego = MagicMock()
        alter_ego.recover = 4
        player = MagicMock()
        player.player_id = 0
        player.GetIdentity.return_value = identity
        player.GetAlterEgo.return_value = alter_ego
        effect = SimpleNamespace()

        with patch(
            "cards.pack.fne.campaign.Worlds.IsExpert", return_value=True
        ), patch(
            "cards.pack.fne.campaign.Worlds.GetPlayers", return_value=[player]
        ), patch(
            "game.operate.campaign_logs.CampaignLog.GetStrInternal",
            side_effect=lambda key, effect: "3" if "Remaining hit points" in key else "",
        ):
            ApplyExpertPersistentDamageAndHealing(effect)

        identity.SetHealth.assert_called_once_with(3, effect)
        choice = player.MayChooseOneAbility.call_args.args[1]
        choice_effect = SimpleNamespace(
            targets=[identity],
            GetPaidResources=lambda: MagicMock(),
        )
        choice.operation(choice_effect, MagicMock())
        player.DealEncounterCards.assert_called_once_with(1, effect)
        identity.HealHealth.assert_called_once_with(4, effect)

    def test_completed_and_failed_environment_faces_are_put_into_play(self):
        completed_face = MagicMock()
        completed_environment = MagicMock()
        completed_face.CastTo.return_value = completed_environment
        completed_card = SimpleNamespace(face=completed_face, back_faces=[MagicMock()])
        failed_face = MagicMock()
        failed_environment = MagicMock()
        failed_face.CastTo.return_value = failed_environment
        failed_back = MagicMock()
        failed_card = SimpleNamespace(face=failed_face, back_faces=[failed_back])
        first_player = MagicMock()
        effect = SimpleNamespace(world=MagicMock())
        statuses = {
            "Art Museum Heist": "Completed",
            "The Getaway": "Failed",
        }

        with patch(
            "cards.pack.fne.campaign.GetScenarioStatus",
            side_effect=lambda name, effect: statuses.get(name, ""),
        ), patch(
            "cards.pack.fne.campaign.CardFactory.GenerateCard",
            side_effect=[completed_card, failed_card],
        ) as generate, patch(
            "cards.pack.fne.campaign.Worlds.GetFirstPlayer",
            return_value=first_player,
        ):
            environments = PutResolvedCampaignEnvironmentsIntoPlay(effect)

        self.assertEqual(generate.call_args_list, [
            call("60205a,60205b", None, effect.world),
            call("60206a,60206b", None, effect.world),
        ])
        failed_face.FlipTo.assert_called_once_with(effect, card_face=failed_back)
        completed_environment.PutIntoPlay.assert_called_once_with(first_player, effect)
        failed_environment.PutIntoPlay.assert_called_once_with(first_player, effect)
        self.assertEqual(environments, [completed_environment, failed_environment])

    def test_trust_adds_mary_under_the_chosen_players_control(self):
        first_player = MagicMock()
        second_player = MagicMock()
        first_player.AskChooseOneText.return_value = second_player
        ally = MagicMock()
        generated_face = MagicMock()
        generated_face.CastTo.return_value = ally
        effect = SimpleNamespace(world=MagicMock())

        with patch(
            "cards.pack.fne.campaign._log_true",
            side_effect=lambda key, effect: key == "Trust Established?",
        ), patch(
            "cards.pack.fne.campaign.Worlds.GetFirstPlayer",
            return_value=first_player,
        ), patch(
            "cards.pack.fne.campaign.Worlds.GetPlayers",
            return_value=[first_player, second_player],
        ), patch(
            "cards.pack.fne.campaign.CardFactory.GenerateCard",
            return_value=SimpleNamespace(face=generated_face),
        ) as generate:
            result = PutTyphoidMaryCampaignAllyIntoPlay(effect)

        generate.assert_called_once_with("60210a,60210b", None, effect.world)
        ally.PutIntoPlay.assert_called_once_with(
            second_player, effect, under_control=True
        )
        self.assertIs(result, ally)

    def test_each_interchangeable_scenario_progress_effect(self):
        effect = MagicMock()
        effect.world = MagicMock()

        with patch(
            "cards.pack.fne.campaign.Worlds.IsExpert", return_value=False
        ), patch(
            "cards.pack.fne.campaign.Worlds.GetAllMainSchemes",
            return_value=["scheme-a", "scheme-b"],
        ):
            _apply_interchangeable_scenario_progress(
                "Protection Racket", 2, effect
            )
        effect.this.PlaceThreatOnSchemes.assert_called_once_with(
            ["scheme-a", "scheme-b"], 2, effect
        )

        tanker = MagicMock()
        effect.reset_mock()
        with patch(
            "cards.pack.fne.campaign.Worlds.GetFirstPlayer",
            return_value=MagicMock(),
        ), patch(
            "cards.pack.fne.campaign.Worlds.IsExpert", return_value=True
        ), patch(
            "cards.pack.fne.campaign.SetupCards.Reveal", return_value=tanker
        ):
            _apply_interchangeable_scenario_progress("The Getaway", 2, effect)
        effect.this.PlaceThreatOnSchemes.assert_called_once_with(
            [tanker], "2*", effect
        )

        prisoners = [MagicMock(), MagicMock()]
        with patch(
            "cards.pack.fne.campaign.Worlds.FindCardsOnField",
            return_value=prisoners,
        ), patch(
            "cards.pack.fne.campaign.Faces.GiveStatus"
        ) as tough, patch(
            "cards.pack.fne.campaign.Faces.GiveFacedownBoostCards"
        ) as boost:
            _apply_interchangeable_scenario_progress(
                "The Raft Breakout", 2, effect
            )
        tough.assert_called_once_with(prisoners, "Tough", effect)
        boost.assert_called_once_with(prisoners, 1, effect)

        supports = [MagicMock()]
        with patch(
            "cards.pack.fne.campaign.Worlds.FindCardsOnField",
            return_value=supports,
        ), patch(
            "cards.pack.fne.campaign.Faces.RemoveCountersOn"
        ) as remove:
            _apply_interchangeable_scenario_progress(
                "Stop the Presses!", 2, effect
            )
        remove.assert_called_once_with(supports, 2, "stamina", effect)

    def test_kingpin_thresholds_give_tough_and_reveal_james_wesley(self):
        effect = SimpleNamespace()
        minions = [MagicMock(), MagicMock()]
        first_player = MagicMock()

        with patch(
            "cards.pack.fne.campaign.GetScenarioStatus",
            return_value="Completed",
        ), patch(
            "cards.pack.fne.campaign.Worlds.FindCardsOnField",
            return_value=minions,
        ), patch(
            "cards.pack.fne.campaign.Worlds.GetFirstPlayer",
            return_value=first_player,
        ), patch(
            "cards.pack.fne.campaign.Faces.GiveStatus"
        ) as tough, patch(
            "cards.pack.fne.campaign.SetupCards.Reveal"
        ) as reveal:
            _apply_kingpin_campaign_setup(effect)

        tough.assert_called_once_with(minions, "Tough", effect)
        self.assertEqual(reveal.call_args.kwargs["name"], "James Wesley")
        self.assertIs(reveal.call_args.args[1], first_player)


if __name__ == "__main__":
    unittest.main()
