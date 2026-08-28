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


def played_message(face, *, from_area=None):
    return SimpleNamespace(
        played_face=face,
        from_area=from_area,
        play_effect=SimpleNamespace(
            ability=SimpleNamespace(is_play=True),
        ),
    )


class TestEchoRegistration(unittest.TestCase):

    def test_starter_contains_complete_echo_deck_and_nemesis_set(self):
        starter = json.loads(
            (ROOT / "deck" / "starter" / "echo.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(starter["hero"], ["60037a,60037b"])
        self.assertEqual(len(starter["hero_deck"]), 15)
        self.assertEqual(starter["hero_deck"].count("60040a"), 2)
        self.assertEqual(starter["hero_deck"].count("60040b"), 2)
        self.assertEqual(starter["hero_deck"].count("60040c"), 2)
        self.assertEqual(starter["obligations"], ["60060"])
        self.assertEqual(
            starter["nemesis_set"],
            ["60061", "60062", "60063", "60063", "60064"],
        )
        self.assertEqual(len(starter["player_deck"]), 25)

    def test_every_echo_card_initializes_through_the_card_factory(self):
        Ver.Initialize()
        CardsDB.Initialize()
        world = MagicMock()
        world.GetPlayerNumIcon.return_value = 1
        card_ids = [
            "60037a",
            "60037b",
            "60038",
            "60039",
            "60040a",
            "60040b",
            "60040c",
            *[f"600{i:02d}" for i in range(41, 48)],
            *[f"600{i:02d}" for i in range(60, 65)],
        ]

        for card_id in card_ids:
            with self.subTest(card_id=card_id):
                paper = CardsDB.FindCardPaper(card_id)
                face = CardFactory.CreateFace(paper, world)
                self.assertEqual(face.paper.card_id, card_id)

    def test_photographic_reflexes_variants_keep_dash_cost_and_resources(self):
        cards = json.loads(
            (ROOT / "data" / "cards.json").read_text(encoding="utf-8")
        )
        papers = {paper["card_id"]: paper for paper in cards["fne"]}

        self.assertEqual(papers["60040a"]["desc"]["Cost"], "-")
        self.assertEqual(papers["60040a"]["desc"]["RES"], "Y")
        self.assertEqual(papers["60040b"]["desc"]["RES"], "B")
        self.assertEqual(papers["60040c"]["desc"]["RES"], "R")
        self.assertEqual(papers["60040b"]["ability_link"], "60040a")
        self.assertEqual(papers["60040c"]["ability_link"], "60040a")


class TestWatchAndLearnAndPhotographicReflexes(unittest.TestCase):

    def test_watch_and_learn_tucks_event_facedown_and_discards_overflow(self):
        module = import_module("cards.pack.fne.echo.60037a")
        ability = module.GetAbilities()[0]
        event = MagicMock()
        tucked = [MagicMock() for _ in range(4)]
        area = SimpleNamespace(GetAll=MagicMock(return_value=tucked))
        hero = SimpleNamespace(
            TuckCardUnderHere=MagicMock(return_value=True),
            GetPlacedCardArea=MagicMock(return_value=area),
        )
        player = SimpleNamespace(AskDiscardFaces=MagicMock())
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=hero)),
            GetInitiator=MagicMock(return_value=player),
        )

        ability.operation(effect, played_message(event))

        hero.TuckCardUnderHere.assert_called_once_with(event, effect)
        player.AskDiscardFaces.assert_called_once_with(tucked, (1, 1), effect)

    def test_watch_and_learn_rejects_event_played_from_echo_tuck_area(self):
        module = import_module("cards.pack.fne.echo.60037a")
        ability = module.GetAbilities()[0]
        area = MagicMock()
        effect = SimpleNamespace(
            this=SimpleNamespace(GetPlacedCardArea=MagicMock(return_value=area))
        )

        condition = ability.conditions[-2]
        self.assertFalse(condition(effect, SimpleNamespace(from_area=area)))
        self.assertTrue(condition(effect, SimpleNamespace(from_area=MagicMock())))

    def test_watch_and_learn_only_tucks_from_the_playing_players_discard(self):
        module = import_module("cards.pack.fne.echo.60037a")
        ability = module.GetAbilities()[0]
        discard_pile = MagicMock()
        event = SimpleNamespace(card=SimpleNamespace(area=discard_pile))
        player = SimpleNamespace(discard_pile=discard_pile)
        message = SimpleNamespace(
            played_face=event,
            GetToPlayer=MagicMock(return_value=player),
        )

        self.assertTrue(ability.conditions[-1](MagicMock(), message))
        event.card.area = MagicMock()
        self.assertFalse(ability.conditions[-1](MagicMock(), message))

    def test_reflexes_play_permission_uses_the_tucked_cards_normal_timing(self):
        module = import_module("cards.pack.fne.echo.60037a")
        ability = module.GetAbilities()[1]

        self.assertEqual(ability.when, module.Message.CheckIfFaceIsLikeInHand)
        self.assertFalse(ability.is_play)

    def test_reflexes_discount_only_applies_to_event_tucked_under_echo(self):
        module = import_module("cards.pack.fne.echo.60037a")
        ability = module.GetAbilities()[2]
        area = MagicMock()
        event = SimpleNamespace(card=SimpleNamespace(area=area))
        effect = SimpleNamespace(
            this=SimpleNamespace(GetPlacedCardArea=MagicMock(return_value=area)),
            GetInitiator=MagicMock(),
        )
        message = SimpleNamespace(check_effect=SimpleNamespace(this=event))

        with patch.object(module, "HasPhotographicReflexesInHand", return_value=True):
            self.assertTrue(ability.conditions[-1](effect, message))
            event.card.area = MagicMock()
            self.assertFalse(ability.conditions[-1](effect, message))

    def test_reflexes_discards_exactly_one_copy_when_tucked_event_is_played(self):
        module = import_module("cards.pack.fne.echo.60037a")
        ability = module.GetAbilities()[3]
        reflexes = [MagicMock(), MagicMock()]
        player = SimpleNamespace(AskDiscardFaces=MagicMock())
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        with patch.object(
            module,
            "GetPhotographicReflexesInHand",
            return_value=reflexes,
        ):
            ability.operation(effect, MagicMock())

        player.AskDiscardFaces.assert_called_once_with(
            reflexes,
            (1, 1),
            effect,
        )


class TestEchoIdentityAndCards(unittest.TestCase):

    def test_maya_searches_deck_for_aspect_or_basic_event(self):
        module = import_module("cards.pack.fne.echo.60037b")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        event = MagicMock()
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        with patch.object(module.Search, "PlayerCard", return_value=event) as search:
            ability.operation(effect, MagicMock())

        search.assert_called_once_with(
            effect,
            player,
            include_player_deck=True,
            card_type=module.Event,
            card_classes=["Aspect", "Basic"],
        )
        player.GainCard.assert_called_once_with(event, effect)

    def test_daredevil_discount_stacks_then_resets_at_round_end(self):
        common = import_module("cards.pack.fne.echo")
        module = import_module("cards.pack.fne.echo.60039")
        ability = module.GetAbilities()[0]
        buff = common.BuffDaredevilEventDiscount()
        identity = SimpleNamespace(GetBuff=MagicMock(return_value=buff))
        effect = SimpleNamespace(
            GetInitiator=MagicMock(
                return_value=SimpleNamespace(
                    GetIdentity=MagicMock(return_value=identity)
                )
            )
        )

        ability.operation(effect, MagicMock())
        ability.operation(effect, MagicMock())
        self.assertEqual(buff.discount, 2)

        buff.OnRoundEnd()
        self.assertEqual(buff.discount, 0)

    def test_study_the_tape_searches_all_discard_piles(self):
        module = import_module("cards.pack.fne.echo.60041")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        face = MagicMock()
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        with patch.object(module.Search, "PlayerCard", return_value=face) as search:
            ability.operation(effect, MagicMock())

        self.assertEqual(search.call_args.kwargs["include_discard_pile"], "All")
        self.assertFalse(search.call_args.kwargs["include_player_deck"])
        player.GainCard.assert_called_once_with(face, effect)

    def test_the_rez_heals_for_highest_tucked_printed_cost(self):
        module = import_module("cards.pack.fne.echo.60042")
        ability = module.GetAbilities()[0]
        costs = [1, 4, 2]
        tucked = [
            SimpleNamespace(
                CastTo=MagicMock(
                    return_value=SimpleNamespace(
                        printed_cost=SimpleNamespace(val=value)
                    )
                )
            )
            for value in costs
        ]
        identity = SimpleNamespace(
            GetPlacedCardArea=MagicMock(
                return_value=SimpleNamespace(GetAll=MagicMock(return_value=tucked))
            ),
            HealthUnits=MagicMock(),
        )
        player = SimpleNamespace(GetIdentity=MagicMock(return_value=identity))
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        ability.operation(effect, MagicMock())

        identity.HealthUnits.assert_called_once_with([identity], 4, effect)

    def test_choreography_draws_only_in_alter_ego(self):
        module = import_module("cards.pack.fne.echo.60044")
        ability = module.GetAbilities()[0]
        target = MagicMock()
        player = MagicMock()
        player.IsAlterEgo.return_value = True
        effect = SimpleNamespace(
            targets=[target],
            GetInitiator=MagicMock(return_value=player),
        )

        with patch.object(module.Faces, "ShuffleAllTo") as shuffle:
            ability.operation(effect, MagicMock())

        shuffle.assert_called_once_with([target], player.player_deck, effect)
        player.DrawUp.assert_called_once_with(1, effect)

    def test_american_sign_language_is_a_shared_event_resource(self):
        module = import_module("cards.pack.fne.echo.60043")
        ability = module.GetAbilities()[0]

        self.assertTrue(ability.CheckAnyPlayerCanTriggerThis(MagicMock()))
        self.assertEqual(len(ability.cost_funcs), 1)
        self.assertIsInstance(ability.cost_funcs[0], module.CostFunc.Exhaust)

    def test_katana_deals_printed_cost_damage_with_piercing(self):
        module = import_module("cards.pack.fne.echo.60045")
        ability = module.GetAbilities()[0]
        enemy = MagicMock()
        upgrade = MagicMock()
        event = SimpleNamespace(
            CastTo=MagicMock(
                return_value=SimpleNamespace(
                    printed_cost=SimpleNamespace(val=3)
                )
            )
        )
        effect = SimpleNamespace(
            targets=[enemy],
            this=SimpleNamespace(CastTo=MagicMock(return_value=upgrade)),
        )

        ability.operation(effect, played_message(event))

        self.assertEqual(upgrade.DealDamage.call_args.args[:3], ([enemy], 3, effect))
        self.assertTrue(upgrade.DealDamage.call_args.kwargs["property"].piercing)

    def test_improvisation_resolves_every_matching_trait_without_exhausting(self):
        module = import_module("cards.pack.fne.echo.60046")
        abilities = module.GetAbilities()
        identity = MagicMock()
        player = MagicMock()
        player.GetIdentity.return_value = identity
        source = MagicMock()
        source.CastTo.return_value = source
        target = MagicMock()
        effect = SimpleNamespace(
            this=source,
            GetInitiator=MagicMock(return_value=player),
        )
        event = MagicMock()
        event.CastTo.return_value = event
        event.HasTrait.side_effect = lambda trait: trait in {"ATTACK", "THWART"}
        message = played_message(event)

        def resolve_choice(by_effect, *choices, **kwargs):
            for choice in choices:
                choice.operation(
                    SimpleNamespace(
                        targets=[target],
                        GetPaidResources=MagicMock(),
                    ),
                    MagicMock(),
                )
            return []

        player.ChooseAbilities.side_effect = resolve_choice

        abilities[0].operation(effect, message)

        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].cost_funcs, [])
        self.assertEqual(abilities[0].name, "Improvisation")
        identity.HealthUnits.assert_called_once_with([identity], 1, effect)
        source.DealDamage.assert_called_once_with([target], 1, effect)
        source.RemoveThreatFromSchemes.assert_not_called()
        player.ChooseAbilities.assert_called_once()

    def test_muscle_memory_returns_selected_tucked_event_to_hand(self):
        module = import_module("cards.pack.fne.echo.60047")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        target = MagicMock()
        effect = SimpleNamespace(
            targets=[target],
            GetInitiator=MagicMock(return_value=player),
        )

        with patch.object(module.Faces, "AddToHand") as add_to_hand:
            ability.operation(effect, MagicMock())

        add_to_hand.assert_called_once_with([target], player, effect)


class TestEchoObligationAndNemesis(unittest.TestCase):

    def test_obligation_finds_kingpin_and_tracks_removed_threat(self):
        module = import_module("cards.pack.fne.echo.60060")
        abilities = module.GetAbilities()
        self.assertEqual(abilities[2].type, module.AbilityType.Response)
        player = MagicMock()
        effect = MagicMock()
        reveal_message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        with patch.object(module.Find, "FindAndPutIntoPlay") as find:
            abilities[1].operation(effect, reveal_message)

        find.assert_called_once_with(
            effect,
            player,
            name="Kingpin",
            card_type=module.Minion,
        )

        obligation = MagicMock()
        obligation.GetTokens.return_value = 4
        effect.this.CastTo.return_value = obligation
        with patch.object(module.Faces, "PlaceTokensOn") as place, patch.object(
            module.Faces,
            "RemoveAllFromGame",
        ) as remove:
            abilities[2].operation(
                effect,
                SimpleNamespace(total_remove_threat=3),
            )

        place.assert_called_once_with([obligation], 3, "threat", effect)
        remove.assert_called_once_with([obligation], effect)

    def test_kingpin_replaces_attack_against_maya_with_scheme(self):
        module = import_module("cards.pack.fne.echo_nemesis.60061")
        ability = module.GetAbilities()[0]
        kingpin = MagicMock()
        player = MagicMock()
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=kingpin))
        )
        message = SimpleNamespace(
            against_player=player,
            SetBeInstead=MagicMock(),
        )

        ability.operation(effect, message)

        message.SetBeInstead.assert_called_once_with(effect)
        kingpin.DoSchemes.assert_called_once_with(player, effect)

    def test_master_manipulator_boost_reveals_only_while_kingpin_is_in_play(self):
        module = import_module("cards.pack.fne.echo_nemesis.60062")
        ability = module.GetAbilities()[2]
        effect = MagicMock()

        with patch.object(module.Worlds, "FindCardOnField", return_value=MagicMock()):
            self.assertTrue(ability.conditions[-1](effect, MagicMock()))
        with patch.object(module.Worlds, "FindCardOnField", return_value=None):
            self.assertFalse(ability.conditions[-1](effect, MagicMock()))

    def test_pawn_hero_can_damage_any_hero_using_your_hero_attack(self):
        module = import_module("cards.pack.fne.echo_nemesis.60064")
        ability = module.GetAbilities()[1]
        revealing_hero = SimpleNamespace(attack=3)
        chosen_hero = MagicMock()
        player = SimpleNamespace(GetHero=MagicMock(return_value=revealing_hero))
        treachery = MagicMock()
        effect = SimpleNamespace(this=treachery, targets=[chosen_hero])
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        ability.operation(effect, message)

        treachery.DealDamage.assert_called_once_with([chosen_hero], 3, effect)
        self.assertEqual(len(ability.selectors), 1)

    def test_pawn_alter_ego_makes_kingpin_scheme_or_gains_surge(self):
        module = import_module("cards.pack.fne.echo_nemesis.60064")
        ability = module.GetAbilities()[0]
        player = MagicMock()
        kingpin = MagicMock()
        kingpin.CastTo.return_value = kingpin
        effect = MagicMock()
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        with patch.object(module.Worlds, "FindCardOnField", return_value=kingpin):
            ability.operation(effect, message)
        kingpin.DoSchemes.assert_called_once_with(player, effect)

        with patch.object(module.Worlds, "FindCardOnField", return_value=None), patch.object(
            module,
            "ThisCardGainSurge",
        ) as surge:
            ability.operation(effect, message)
        surge.assert_called_once_with(effect)

    def test_henchman_keeps_kingpin_from_taking_damage(self):
        module = import_module("cards.pack.fne.echo_nemesis.60063")
        ability = module.GetAbilities()[0]

        self.assertEqual(ability.when, module.Message.WhenUnitWouldTakeDamage)
        self.assertEqual(ability.type, module.AbilityType.NonKeyword)


if __name__ == "__main__":
    unittest.main()
