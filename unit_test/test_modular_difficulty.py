from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order

from cards.pack.mts.the_tower_defense import (
    SetupTowerDefenseModularDifficulty,
)
from cards.pack.mut_gen.project_wideawake import (
    SetupProjectWideawakeModularDifficulty,
)
from game.message import Message
from game.operate.modular_difficulty import ModularDifficulty


def make_effect(
    *,
    expert: bool = False,
    heroic: int = 0,
    skirmish: bool = False,
    players: int = 1,
):
    world = SimpleNamespace(
        rule=SimpleNamespace(
            mode_heroic=heroic,
            mode_skirmish=skirmish,
        ),
        scene=SimpleNamespace(
            campaign=SimpleNamespace(expert=expert),
        ),
        GetPlayerNumIcon=MagicMock(return_value=players),
    )
    return SimpleNamespace(
        world=world,
        this=SimpleNamespace(player_num_icon_override=None),
    )


class TestModularDifficultyValues(unittest.TestCase):
    def test_recommendation_follows_selected_mode(self):
        cases = [
            ("skirmish", make_effect(skirmish=True, players=2), 0),
            ("standard", make_effect(players=2), 2),
            ("expert", make_effect(expert=True, players=2), 4),
            (
                "heroic",
                make_effect(expert=True, heroic=1, players=2),
                6,
            ),
        ]

        for name, effect, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(
                    ModularDifficulty.GetRecommendedValue(
                        effect,
                        per_player=True,
                    ),
                    expected,
                )

    def test_non_scaling_recommendation_uses_mode_value(self):
        effect = make_effect(expert=True, players=4)

        self.assertEqual(
            ModularDifficulty.GetRecommendedValue(
                effect,
                per_player=False,
            ),
            2,
        )

    def test_recommended_setup_is_optional_and_executes_selected_action(self):
        effect = make_effect(expert=True, players=2)
        first_player = MagicMock()
        operation = MagicMock()

        with patch(
            "game.operate.worlds.Worlds.GetFirstPlayer",
            return_value=first_player,
        ):
            ModularDifficulty.MayApply(
                effect,
                description=lambda value: f"Apply {value}",
                operation=operation,
                per_player=True,
            )

        first_player.MayChooseOneAbility.assert_called_once()
        choice = first_player.MayChooseOneAbility.call_args.args[1]
        self.assertEqual(choice.name, "Apply 4")

        choice.operation(
            SimpleNamespace(
                targets=[],
                GetPaidResources=MagicMock(),
            ),
            SimpleNamespace(),
        )
        operation.assert_called_once_with(4)

    def test_skirmish_zero_does_not_show_a_prompt(self):
        effect = make_effect(skirmish=True)

        with patch(
            "game.operate.worlds.Worlds.GetFirstPlayer",
        ) as get_first_player:
            result = ModularDifficulty.MayApply(
                effect,
                description=lambda value: f"Apply {value}",
                operation=MagicMock(),
                per_player=True,
            )

        self.assertIsNone(result)
        get_first_player.assert_not_called()


class TestTowerDefenseModularDifficulty(unittest.TestCase):
    def test_tower_offer_scales_per_player_and_places_damage(self):
        effect = make_effect()

        with patch(
            "cards.pack.mts.the_tower_defense.ModularDifficulty.MayApply",
        ) as offer, patch(
            "cards.pack.mts.the_tower_defense.DealDamageToAvengersTower",
        ) as deal_damage:
            SetupTowerDefenseModularDifficulty(effect)

            offer.assert_called_once()
            self.assertTrue(offer.call_args.kwargs["per_player"])
            self.assertEqual(
                offer.call_args.kwargs["description"](4),
                "Place 4 damage on Avengers Tower (modular difficulty)",
            )
            offer.call_args.kwargs["operation"](4)

        deal_damage.assert_called_once_with(4, effect)

    def test_tower_prompt_runs_after_avengers_tower_enters_play(self):
        module = import_module(
            "cards.pack.mts.the_tower_defense.21098a"
        )
        order = []
        scheme = MagicMock()
        scheme.Reveal.side_effect = lambda *args: order.append("reveal")
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock()),
        )

        with patch.object(
            module.Worlds,
            "GetFirstPlayer",
            return_value=MagicMock(),
        ), patch.object(
            module.Worlds,
            "MainSchemesDeck",
            return_value=SimpleNamespace(
                Get=MagicMock(return_value=[scheme]),
            ),
        ), patch.object(
            module,
            "SetupTowerDefenseModularDifficulty",
            side_effect=lambda effect: order.append("modular"),
        ):
            setup = next(
                ability
                for ability in module.GetAbilities()
                if ability.when is Message.WhenCardSetup
            )
            setup.operation(effect, SimpleNamespace())

        self.assertEqual(order, ["reveal", "modular"])


class TestProjectWideawakeModularDifficulty(unittest.TestCase):
    def test_project_wideawake_chooses_a_deck_for_each_captured_card(self):
        effect = make_effect()
        chooser = MagicMock()
        players = [
            SimpleNamespace(name="Player 1"),
            SimpleNamespace(name="Player 2"),
        ]

        with patch(
            "cards.pack.mut_gen.project_wideawake.ModularDifficulty.MayApply",
        ) as offer, patch(
            "cards.pack.mut_gen.project_wideawake.Worlds.GetFirstPlayer",
            return_value=chooser,
        ), patch(
            "cards.pack.mut_gen.project_wideawake.Worlds.GetPlayers",
            return_value=players,
        ), patch(
            "cards.pack.mut_gen.project_wideawake.PlaceDeckTopCardFacedownUnderOperationZeroTolerance",
        ) as place_card:
            SetupProjectWideawakeModularDifficulty(effect)

            offer.assert_called_once()
            self.assertFalse(offer.call_args.kwargs["per_player"])
            offer.call_args.kwargs["operation"](2)

            self.assertEqual(chooser.ChooseAbilities.call_count, 2)
            first_choice = chooser.ChooseAbilities.call_args_list[0].args[1]
            first_choice.operation(
                SimpleNamespace(
                    targets=[],
                    GetPaidResources=MagicMock(),
                ),
                SimpleNamespace(),
            )

        place_card.assert_called_once_with(players[0], effect)

    def test_project_wideawake_prompt_runs_after_side_schemes_are_revealed(self):
        module = import_module(
            "cards.pack.mut_gen.project_wideawake.32087a"
        )
        order = []
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock()),
        )

        with patch.object(
            module.SetupCards,
            "Reveal",
            side_effect=lambda *args, **kwargs: order.append("reveal"),
        ), patch.object(
            module,
            "SetupProjectWideawakeModularDifficulty",
            side_effect=lambda effect: order.append("modular"),
        ):
            setup = next(
                ability
                for ability in module.GetAbilities()
                if ability.when is Message.WhenCardSetup
            )
            setup.operation(effect, SimpleNamespace())

        self.assertEqual(order, ["reveal", "reveal", "modular"])


class TestInfinitesModularDifficulty(unittest.TestCase):
    def test_gene_pool_offers_per_player_threat_during_setup(self):
        module = import_module("cards.pack.aoa.infinites.45071")
        gene_pool = MagicMock()
        effect = SimpleNamespace(
            this=SimpleNamespace(
                CastTo=MagicMock(return_value=gene_pool),
            ),
        )
        setup = next(
            ability
            for ability in module.GetAbilities()
            if ability.when is Message.WhenCardSetup
        )

        with patch.object(
            module.ModularDifficulty,
            "MayApply",
        ) as offer:
            setup.operation(effect, SimpleNamespace())

            offer.assert_called_once()
            self.assertTrue(offer.call_args.kwargs["per_player"])
            self.assertEqual(
                offer.call_args.kwargs["description"](3),
                "Place 3 threat on Gene Pool (modular difficulty)",
            )
            offer.call_args.kwargs["operation"](3)

        gene_pool.PlaceThreatOnSchemes.assert_called_once_with(
            [gene_pool],
            3,
            effect,
        )


if __name__ == "__main__":
    unittest.main()
