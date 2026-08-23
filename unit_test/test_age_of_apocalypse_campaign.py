import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.pack.aoa.campaign import (
    MakeMissionAttempt,
    PlayAllyToMission,
    _resolve_overseer_discard_effects,
    _mission_cards_child_first,
)
from cards.pack.aoa.campaign_setup import (
    AddPreviousMissionRewardsAndPenalties,
    ResolveCampaignVictory,
    SetupMission,
)
from game.ability.factory import AbilityFactory
from game.card.card_finder import CardFinder
from game.card.face.base import Friend
from game.card.face.card_type import Ally
from game.element.resources import Resources
from game.operate.worlds import Worlds
from game.selector import Select


class TestAgeOfApocalypseCampaign(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]

    def test_mission_stats_are_per_player(self):
        cards = json.loads(
            (self.project_root / "data" / "cards.json").read_text(
                encoding="utf-8"
            )
        )["aoa"]
        by_id = {card["card_id"]: card for card in cards}

        for card_id in ("45166a", "45167a", "45168a", "45169a", "45170a"):
            with self.subTest(mission=card_id):
                self.assertEqual(
                    by_id[card_id]["desc"]["StartingThreat"],
                    "5*",
                )

        for card_id in ("45179a", "45180a", "45181a", "45182a", "45183a"):
            with self.subTest(overseer=card_id):
                self.assertEqual(by_id[card_id]["desc"]["HP"], "5*")

    def test_generic_side_scheme_queries_exclude_missions(self):
        game_area = SimpleNamespace()
        deck = MagicMock()
        world = SimpleNamespace(area_schemes_side=deck)
        game_area.world = world

        regular_scheme = MagicMock()
        regular_scheme.card.GetGameArea.return_value = game_area
        regular_scheme.HasTrait.return_value = False

        mission_scheme = MagicMock()
        mission_scheme.card.GetGameArea.return_value = game_area
        mission_scheme.HasTrait.side_effect = lambda trait: trait == "MISSION"

        deck.Get.return_value = [regular_scheme, mission_scheme]

        with patch(
            "game.operate.worlds.EncounterSideScheme.IsType",
            return_value=True,
        ), patch(
            "game.operate.worlds.PlayerSideScheme.IsType",
            return_value=False,
        ):
            self.assertEqual(
                Worlds.GetSideSchemes(game_area),
                [regular_scheme],
            )
            self.assertEqual(
                Worlds.GetSideSchemes(game_area, include_missions=True),
                [regular_scheme, mission_scheme],
            )
            self.assertEqual(
                Worlds.GetAllSideSchemes(world),
                [regular_scheme],
            )
            self.assertEqual(
                Worlds.GetAllSideSchemes(world, include_missions=True),
                [regular_scheme, mission_scheme],
            )

    def test_generic_field_queries_exclude_missions(self):
        empty_area = MagicMock()
        empty_area.GetAll.return_value = []
        side_scheme_area = MagicMock()

        world = SimpleNamespace(
            area_schemes_main=empty_area,
            area_schemes_side=side_scheme_area,
            area_environment=empty_area,
            scenario=SimpleNamespace(area_villain=empty_area),
        )
        game_area = SimpleNamespace(world=world)

        regular_scheme = MagicMock()
        regular_scheme.card.game_area = game_area
        regular_scheme.IsFaceUp.return_value = True
        regular_scheme.HasTrait.return_value = False
        regular_scheme.GetInventoryDeck.return_value.GetAll.return_value = []
        regular_scheme.GetPlacedCardArea.return_value.GetAll.return_value = []

        mission_scheme = MagicMock()
        mission_scheme.card.game_area = game_area
        mission_scheme.IsFaceUp.return_value = True
        mission_scheme.HasTrait.side_effect = lambda trait: trait == "MISSION"
        mission_scheme.GetInventoryDeck.return_value.GetAll.return_value = []
        mission_scheme.GetPlacedCardArea.return_value.GetAll.return_value = []

        side_scheme_area.GetAll.return_value = [regular_scheme, mission_scheme]

        with patch.object(Worlds, "GetPlayers", return_value=[]), patch(
            "game.operate.worlds.EncounterSideScheme.IsType",
            return_value=True,
        ):
            self.assertEqual(
                Worlds.GetOnFieldCards(game_area),
                [regular_scheme],
            )
            self.assertEqual(
                Worlds.GetOnFieldCards(game_area, include_missions=True),
                [regular_scheme, mission_scheme],
            )

    def test_prelates_are_defined_as_double_sided_overseer_cards(self):
        encounter_set = json.loads(
            (self.project_root / "data" / "encounter_sets" / "prelates.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            encounter_set["encounters"],
            [
                "45179b,45179a",
                "45180b,45180a",
                "45181b,45181a",
                "45182b,45182a",
                "45183b,45183a",
            ],
        )

    def test_only_ally_upgrade_selectors_gain_the_mission_target_source(self):
        ally_upgrade = AbilityFactory.CanPlayThisUpgradeCard(Ally)
        trait_ally_upgrade = AbilityFactory.CanPlayThisUpgradeCard(
            CardFinder(traits=["X-MEN"], card_type=Ally)
        )
        your_ally_upgrade = AbilityFactory.CanPlayThisUpgradeCard(
            Select.From(
                "YourAlly",
                finder=CardFinder(card_class="IdentitySpecific"),
            )
        )
        friendly_upgrade = AbilityFactory.CanPlayThisUpgradeCard(Friend)
        identity_upgrade = AbilityFactory.CanPlayThisUpgradeCard()

        self.assertEqual(
            len(ally_upgrade.selectors[0].selector_target.additional_get_targets_fns),
            1,
        )
        self.assertEqual(
            len(
                trait_ally_upgrade.selectors[0]
                .selector_target.additional_get_targets_fns
            ),
            1,
        )
        self.assertEqual(
            len(your_ally_upgrade.selectors[0].selector_target.additional_get_targets_fns),
            0,
        )
        self.assertEqual(
            len(identity_upgrade.selectors[0].selector_target.additional_get_targets_fns),
            0,
        )
        self.assertEqual(
            len(friendly_upgrade.selectors[0].selector_target.additional_get_targets_fns),
            0,
        )

        mission_ally = MagicMock()
        get_targets = (
            ally_upgrade.selectors[0]
            .selector_target.additional_get_targets_fns[0]
        )
        effect = SimpleNamespace()
        with patch(
            "cards.pack.aoa.campaign.HasActiveMission",
            return_value=True,
        ), patch(
            "cards.pack.aoa.campaign.GetMissionAllies",
            return_value=[mission_ally],
        ):
            self.assertEqual(get_targets(effect), [mission_ally])

    def test_mission_ally_is_blanked_before_enter_play_callbacks_complete(self):
        ally = MagicMock()
        player = MagicMock()
        effect = SimpleNamespace()
        mission_area = MagicMock()

        with patch(
            "cards.pack.aoa.campaign.GetMissionArea",
            return_value=mission_area,
        ), patch(
            "cards.pack.aoa.campaign.Faces.MoveAllTo",
        ) as move_all:
            PlayAllyToMission(ally, player, effect)

        ally.card.SetOwner.assert_called_once_with(player)
        move_all.assert_called_once()
        before_enter_play = move_all.call_args.kwargs["before_enter_play"]
        before_enter_play(ally)
        ally.TreatAsIfBlankInternal.assert_called_once_with(1, effect)

    def test_shadow_king_counts_the_entire_discard_for_his_response(self):
        cards = [
            SimpleNamespace(printed_resource_internal=Resources("B")),
            SimpleNamespace(printed_resource_internal=Resources("BB")),
        ]
        overseer = MagicMock()
        overseer.IsName.side_effect = lambda name: name == "The Shadow King"
        mission_area = MagicMock()
        mission_area.FindCards.return_value = [overseer]
        mission = MagicMock()
        effect = SimpleNamespace()

        with patch(
            "cards.pack.aoa.campaign.GetMissionArea",
            return_value=mission_area,
        ):
            remaining = _resolve_overseer_discard_effects(
                cards,
                MagicMock(),
                mission,
                effect,
            )

        self.assertEqual(remaining, cards)
        mission.PlaceThreatOnSchemes.assert_called_once_with(
            [mission], 6, effect
        )

    def test_mission_attempt_uses_upgraded_ally_attack(self):
        ally = MagicMock()
        ally.attack = 3
        ally.thwart = 0
        card = MagicMock()
        minion = MagicMock()
        minion.HasTrait.return_value = False
        mission = MagicMock()
        mission.IsInPlay.return_value = False
        player = MagicMock()
        player.DiscardDeckTopCards.return_value = [card]
        player.AskChooseFace.side_effect = (
            lambda faces, *args, **kwargs: faces[0]
        )
        effect = SimpleNamespace(this=MagicMock())

        with patch(
            "cards.pack.aoa.campaign.GetMissionScheme",
            side_effect=[mission, None],
        ), patch(
            "cards.pack.aoa.campaign.GetMissionAllies",
            return_value=[ally],
        ), patch(
            "cards.pack.aoa.campaign.GetMissionMinions",
            return_value=[minion],
        ), patch(
            "cards.pack.aoa.campaign._resolve_overseer_discard_effects",
            return_value=[card],
        ), patch(
            "cards.pack.aoa.campaign._matching_resources",
            return_value=["R"],
        ):
            MakeMissionAttempt(player, effect)

        self.assertEqual(minion.TakeDamage.call_count, 3)

    def test_scenario_five_win_becomes_loss_while_mission_is_unresolved(self):
        ability = ResolveCampaignVictory(5)
        message = MagicMock()
        effect = SimpleNamespace()

        with patch(
            "cards.pack.aoa.campaign_setup.GetMissionScheme",
            return_value=MagicMock(),
        ):
            ability.operation(effect, message)

        message.SetPlayerLost.assert_called_once_with(effect)

    def test_desperate_measures_future_reward_is_optional(self):
        ability = AddPreviousMissionRewardsAndPenalties(2)
        player = SimpleNamespace(
            player_id=0,
            MayChooseOneAbility=MagicMock(),
        )
        effect = SimpleNamespace()

        def log_list(key, check_effect):
            if key == "Mission Side Schemes Defeated":
                return ["45166a"]
            return []

        with patch(
            "cards.pack.aoa.campaign_setup._log_list",
            side_effect=log_list,
        ), patch(
            "cards.pack.aoa.campaign_setup.Worlds.GetPlayers",
            return_value=[player],
        ), patch(
            "cards.pack.aoa.campaign_setup._generate_into_player_deck",
        ) as generate:
            ability.operation(effect, SimpleNamespace())

        player.MayChooseOneAbility.assert_called_once()
        generate.assert_not_called()

    def test_active_prelate_reverse_is_unavailable_as_scenario_three_overseer(self):
        ability = SetupMission(3)
        prelate = MagicMock()
        mission_team = MagicMock()
        generated = SimpleNamespace(face=mission_team)
        effect = SimpleNamespace(world=MagicMock())
        selections = []

        def select(key, all_ids, unavailable, check_effect):
            selections.append((key, list(unavailable)))
            return ""

        with patch(
            "cards.pack.aoa.campaign_setup._log_list",
            return_value=[],
        ), patch(
            "cards.pack.aoa.campaign_setup._selected_or_random",
            side_effect=select,
        ), patch(
            "cards.pack.aoa.campaign_setup._printed_overseer_id",
            return_value="45179a",
        ), patch(
            "cards.pack.aoa.campaign_setup.Worlds.FindCardsOnField",
            return_value=[prelate],
        ), patch(
            "cards.pack.aoa.campaign_setup.Worlds.GetFirstPlayer",
            return_value=MagicMock(),
        ), patch(
            "game.operate.campaign_logs.CampaignLog.SetStr",
        ), patch(
            "cards.pack.aoa.campaign_setup.CardFactory.GenerateCard",
            return_value=generated,
        ):
            ability.operation(effect, SimpleNamespace())

        self.assertEqual(len(selections), 2)
        self.assertIn("45179a", selections[1][1])

    def test_abyss_removes_every_wild_card_before_assignment(self):
        wild_one = MagicMock()
        wild_one.printed_resource_internal = Resources("G")
        wild_two = MagicMock()
        wild_two.printed_resource_internal = Resources("RG")
        physical = MagicMock()
        physical.printed_resource_internal = Resources("R")
        cards = [wild_one, physical, wild_two]
        overseer = MagicMock()
        overseer.IsName.side_effect = lambda name: name == "Abyss"
        inventory = MagicMock()
        overseer.GetInventoryDeck.return_value = inventory
        mission_area = MagicMock()
        mission_area.FindCards.return_value = [overseer]
        effect = SimpleNamespace()

        with patch(
            "cards.pack.aoa.campaign.GetMissionArea",
            return_value=mission_area,
        ), patch(
            "cards.pack.aoa.campaign.Faces.MoveAllTo",
            return_value=[wild_one, wild_two],
        ) as move_all, patch(
            "cards.pack.aoa.campaign.Faces.FlipAllTo",
        ) as flip_all:
            remaining = _resolve_overseer_discard_effects(
                cards,
                MagicMock(),
                MagicMock(),
                effect,
            )

        self.assertEqual(remaining, [physical])
        move_all.assert_called_once_with(
            [wild_one, wild_two], inventory, effect
        )
        flip_all.assert_called_once_with([wild_one, wild_two], False, effect)

    def test_mister_sinister_restricts_assignment_by_all_actual_icons(self):
        allies = [MagicMock(), MagicMock()]
        for ally in allies:
            ally.attack = 0
            ally.thwart = 0
        first_card = MagicMock()
        first_card.printed_resource_internal = Resources("RB")
        second_card = MagicMock()
        second_card.printed_resource_internal = Resources("R")
        sinister = MagicMock()
        sinister.HasTrait.side_effect = lambda trait: trait == "OVERSEER"
        sinister.IsName.side_effect = lambda name: name == "Mister Sinister"
        mission = MagicMock()
        mission.IsInPlay.return_value = False
        player = MagicMock()
        player.DiscardDeckTopCards.return_value = [first_card, second_card]
        player.AskChooseFace.side_effect = (
            lambda faces, *args, **kwargs: faces[0]
        )
        effect = SimpleNamespace(this=MagicMock())

        with patch(
            "cards.pack.aoa.campaign.GetMissionScheme",
            side_effect=[mission, None],
        ), patch(
            "cards.pack.aoa.campaign.GetMissionAllies",
            return_value=allies,
        ), patch(
            "cards.pack.aoa.campaign.GetMissionMinions",
            return_value=[sinister],
        ), patch(
            "cards.pack.aoa.campaign._resolve_overseer_discard_effects",
            return_value=[first_card, second_card],
        ), patch(
            "cards.pack.aoa.campaign._matching_resources",
            return_value=["R"],
        ):
            MakeMissionAttempt(player, effect)

        self.assertEqual(player.AskChooseFace.call_count, 1)

    def test_nested_player_cards_are_found_child_first_for_mission_cleanup(self):
        upgrade = MagicMock()
        placed_card = MagicMock()
        ally = MagicMock()
        for nested in [upgrade, placed_card]:
            nested.GetInventoryDeck.return_value.Get.return_value = []
            nested.GetPlacedCardArea.return_value.Get.return_value = []
        ally.GetInventoryDeck.return_value.Get.return_value = [upgrade]
        ally.GetPlacedCardArea.return_value.Get.return_value = [placed_card]
        mission_area = MagicMock()
        mission_area.Get.return_value = [ally]
        effect = SimpleNamespace()

        with patch(
            "cards.pack.aoa.campaign.GetMissionArea",
            return_value=mission_area,
        ):
            cards = _mission_cards_child_first(effect)

        self.assertEqual(cards, [upgrade, placed_card, ally])


if __name__ == "__main__":
    unittest.main()
