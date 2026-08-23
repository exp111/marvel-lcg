import json
from importlib import import_module
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestMagog(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]
    mojomania_modular_sets = [
        "crime",
        "fantasy",
        "horror",
        "sci_fi",
        "sitcom",
        "western",
    ]

    def test_scenarios_offer_every_mojomania_modular_set(self):
        for filename in ("magog.json", "magog_expert.json"):
            with self.subTest(scenario=filename):
                scenario = json.loads(
                    (
                        self.project_root / "data" / "scenarios" / filename
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    scenario["modular_sets"],
                    self.mojomania_modular_sets,
                )

    def test_setup_keeps_one_random_modular_set(self):
        module = import_module("cards.pack.mojo.magog.39002a")
        select_random_modular_set = module.GetAbilities()[0]

        effect = Mock()
        message = Mock()
        message.encounter_set_names = [
            "standard",
            "expert",
            *self.mojomania_modular_sets,
        ]

        with patch.object(
            module.Rand,
            "RandomChoice2",
            return_value=["horror"],
        ) as choose_random:
            select_random_modular_set.operation(effect, message)

        choose_random.assert_called_once_with(
            self.mojomania_modular_sets,
            1,
            effect,
        )
        self.assertEqual(
            message.encounter_set_names,
            ["standard", "expert", "horror"],
        )

    def test_melee_completion_places_ratings_and_resets_threat(self):
        module = import_module("cards.pack.mojo.magog.39002b")
        melee_in_the_mojo_seum = module.GetAbilities()[0]

        effect = Mock()
        main_scheme = Mock()
        main_scheme.threat = 9
        message = Mock()
        champion = Mock()
        effect.this.CastTo.return_value = main_scheme

        with patch.object(
            module,
            "FindTheChampion",
            return_value=champion,
        ), patch.object(
            module.Faces,
            "PlaceCountersOn",
        ) as place_counters:
            melee_in_the_mojo_seum.operation(effect, message)

        message.SetBeInstead.assert_called_once_with(effect)
        place_counters.assert_called_once_with(
            [champion],
            "2*",
            "ratings",
            effect,
        )
        main_scheme.RemoveThreatFromSchemes.assert_called_once_with(
            [main_scheme],
            9,
            effect,
        )

    def test_crime_scene_allows_main_scheme_completion_resets_only(self):
        module = import_module("cards.pack.mojo.crime.39037")
        cannot_remove_threat = module.GetAbilities()[0]
        exception_condition = cannot_remove_threat.conditions[-1]

        effect = Mock()
        main_scheme = Mock()
        other_main_scheme = Mock()
        player_card = Mock()
        completion_message = Mock()
        completion_message.is_be_instead = True
        source_effect = Mock()
        source_effect.this = main_scheme
        source_effect.ability.when = (
            module.Message.WhenMainSchemeStageWouldBeCompleted
        )
        source_effect.bind_message = completion_message
        message = Mock()
        message.trigger = main_scheme
        message.by_effect = source_effect

        with patch.object(
            module.MainScheme,
            "IsType",
            side_effect=lambda face: face in (main_scheme, other_main_scheme),
        ):
            self.assertFalse(exception_condition(effect, message))

            source_effect.this = other_main_scheme
            message.trigger = other_main_scheme
            self.assertFalse(exception_condition(effect, message))

            completion_message.is_be_instead = False
            self.assertTrue(exception_condition(effect, message))

            completion_message.is_be_instead = True
            source_effect.this = player_card
            self.assertTrue(exception_condition(effect, message))

            source_effect.this = other_main_scheme
            source_effect.ability.when = module.Message.WhenPlayerInTurn
            self.assertTrue(exception_condition(effect, message))

    def test_stage_fright_requires_challengers_to_have_more_ratings(self):
        module = import_module("cards.pack.mojo.magog.39011")
        stage_fright = module.GetAbilities()[0]

        for challengers_ratings, champion_ratings, expected_threat in (
            (0, 0, 2),
            (2, 2, 2),
            (1, 2, 2),
            (2, 1, 4),
        ):
            with self.subTest(
                challengers=challengers_ratings,
                champion=champion_ratings,
            ):
                effect = Mock()
                treachery = Mock()
                player = Mock()
                identity = Mock()
                message = Mock()
                champion = Mock()
                challengers = Mock()
                main_scheme = Mock()
                effect.this.CastTo.return_value = treachery
                message.GetToPlayer.return_value = player
                player.GetIdentity.return_value = identity
                champion.GetCounters.return_value = champion_ratings
                challengers.GetCounters.return_value = challengers_ratings

                with patch.object(
                    module,
                    "FindTheChampion",
                    return_value=champion,
                ), patch.object(
                    module,
                    "FindTheChallengers",
                    return_value=challengers,
                ), patch.object(
                    module.Worlds,
                    "FindMainScheme",
                    return_value=main_scheme,
                ), patch.object(module.Faces, "GiveStatus"):
                    stage_fright.operation(effect, message)

                treachery.PlaceThreatOnSchemes.assert_called_once_with(
                    [main_scheme],
                    expected_threat,
                    effect,
                )


if __name__ == "__main__":
    unittest.main()
