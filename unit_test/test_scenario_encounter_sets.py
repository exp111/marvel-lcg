import json
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from engine.lib import Json, Ver
from game.game_run.game_new import NewGameDescriptor
from game.game_run.game_session import GameSession
from game.scene.scene import Scene
from game.scene.loader import SceneLoader


class TestScenarioEncounterSets(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]

    def test_required_sets_are_restored_when_client_omits_them(self):
        merged = SceneLoader.MergeEncounterSets(
            ["prelates", "standard"],
            ["standard"],
        )

        self.assertEqual(merged, ["prelates", "standard"])

    def test_selected_modular_sets_are_retained_without_duplicates(self):
        merged = SceneLoader.MergeEncounterSets(
            ["prelates", "standard"],
            ["standard", "dark_riders", "infinites"],
        )

        self.assertEqual(
            merged,
            ["prelates", "standard", "dark_riders", "infinites"],
        )

    def test_selected_standard_variant_replaces_the_scenario_default(self):
        merged = SceneLoader.MergeEncounterSets(
            ["prelates", "standard", "expert"],
            ["standard_iii", "expert", "dark_riders", "infinites"],
        )

        self.assertEqual(
            merged,
            ["prelates", "standard_iii", "expert", "dark_riders", "infinites"],
        )

    def test_selected_expert_variant_replaces_the_scenario_default(self):
        merged = SceneLoader.MergeEncounterSets(
            ["standard", "expert"],
            ["standard", "expert_ii"],
        )

        self.assertEqual(merged, ["standard", "expert_ii"])

    def test_only_the_last_selected_variant_from_each_family_is_retained(self):
        merged = SceneLoader.MergeEncounterSets(
            ["prelates", "standard", "expert"],
            ["standard", "standard_iii", "expert", "expert_ii"],
        )

        self.assertEqual(merged, ["prelates", "standard_iii", "expert_ii"])

    def test_opt_out_can_remove_either_or_both_difficulty_sets_only(self):
        for selected, expected in (
            ([], ["prelates"]),
            (["standard_iii"], ["prelates", "standard_iii"]),
            (["expert_ii"], ["prelates", "expert_ii"]),
            (["standard", "standard_iii", "expert", "expert_ii", "dark_riders"],
             ["prelates", "standard", "standard_iii", "expert", "expert_ii", "dark_riders"]),
            (["standard", "standard_ii", "standard_iii", "standard_ii", "expert", "expert_ii", "prelates"],
             ["prelates", "standard", "standard_ii", "standard_iii", "expert", "expert_ii"]),
        ):
            with self.subTest(selected=selected):
                self.assertEqual(SceneLoader.MergeEncounterSets(
                    ["prelates", "standard", "expert"], selected,
                    remove_standard_set_restriction=True,
                ), expected)

    def test_restriction_requires_explicit_boolean_opt_out(self):
        for enabled in (False, None, "false", "true", 1):
            with self.subTest(enabled=enabled):
                self.assertEqual(SceneLoader.MergeEncounterSets(
                    ["standard", "expert"], [],
                    remove_standard_set_restriction=enabled,
                ), ["standard", "expert"])

    def test_launch_and_save_keep_expert_villain_without_difficulty_sets(self):
        campaign_json = (self.project_root / "data/scenarios/rhino_expert.json").read_text()
        payload = dict(campaign_json=campaign_json, encounter_set_names=["bomb_scare"],
                       hero_json=[], seed=133, timeout=0, challenges=[], rules=[], campaign_log={})
        # Old clients omit the new field: their existing restriction must remain.
        for enabled in (None, False, True):
            with self.subTest(enabled=enabled), patch.object(Ver, "version", Ver("1.3.3"), create=True):
                request = dict(payload)
                if enabled is not None:
                    request["remove_standard_set_restriction"] = enabled
                descriptor = Json.LoadsAs(json.dumps(request), NewGameDescriptor)
                self.assertEqual(descriptor.remove_standard_set_restriction, enabled is True)
                session = GameSession(SimpleNamespace(state=Mock()))
                session.NewGame(descriptor)
                scene = session.scene
                expected = ["bomb_scare"] if enabled else ["standard", "expert", "bomb_scare"]
                self.assertEqual(scene.campaign.encounter_sets, expected)
                self.assertEqual(scene.campaign.villain, ["01095", "01096"])
                self.assertTrue(scene.campaign.expert)
                saved = Json.Dumps(scene)
                self.assertNotIn("remove_standard_set_restriction", saved)
                restored = Json.LoadsAs(saved, Scene)
                restored.UpdateVersion()
                self.assertEqual(restored.campaign.encounter_sets, expected)

    def test_unspecified_selection_keeps_scenario_defaults_even_with_opt_out(self):
        campaign_json = (self.project_root / "data/scenarios/rhino_expert.json").read_text()
        with patch.object(Ver, "version", Ver("1.3.3"), create=True):
            scene = SceneLoader.NewFromJson(campaign_json, None, [], 133, [], {},
                                           remove_standard_set_restriction=True)
        self.assertEqual(scene.campaign.encounter_sets, ["standard", "expert", "bomb_scare"])

    def test_combined_difficulty_sets_survive_launch_and_save(self):
        selected = ["standard", "standard_ii", "standard_iii", "expert", "expert_ii", "bomb_scare"]
        campaign_json = (self.project_root / "data/scenarios/rhino_expert.json").read_text()
        with patch.object(Ver, "version", Ver("1.3.3"), create=True):
            scene = SceneLoader.NewFromJson(campaign_json, selected, [], 133, [], {},
                                           remove_standard_set_restriction=True)
            self.assertEqual(scene.campaign.encounter_sets, selected)
            restored = Json.LoadsAs(Json.Dumps(scene), Scene)
            restored.UpdateVersion()
        self.assertEqual(restored.campaign.encounter_sets, selected)
        self.assertEqual(restored.campaign.villain, ["01095", "01096"])

    def test_all_scenarios_preserve_valid_required_encounter_sets(self):
        sets_info = json.loads(
            (self.project_root / "data" / "sets_info.json").read_text(
                encoding="utf-8"
            )
        )
        listed_sets = {
            encounter_set
            for pack in sets_info.values()
            if isinstance(pack, dict)
            for encounter_set in pack.get("encounters", [])
        }
        encounter_sets_folder = self.project_root / "data" / "encounter_sets"
        scenario_files = sorted(
            (self.project_root / "data" / "scenarios").glob("*.json")
        )

        self.assertGreater(len(scenario_files), 0)
        for scenario_file in scenario_files:
            with self.subTest(scenario=scenario_file.name):
                scenario = json.loads(scenario_file.read_text(encoding="utf-8"))
                required = scenario.get("encounter_sets", [])
                selected_standard_sets = [
                    encounter_set
                    for encounter_set in required
                    if encounter_set.startswith(("standard", "expert"))
                ]
                merged = SceneLoader.MergeEncounterSets(
                    required,
                    selected_standard_sets,
                )

                self.assertTrue(set(required).issubset(merged))
                for encounter_set in required:
                    self.assertIn(encounter_set, listed_sets)
                    encounter_set_file = encounter_sets_folder / f"{encounter_set}.json"
                    self.assertTrue(encounter_set_file.is_file())
                    encounter_set_data = json.loads(
                        encounter_set_file.read_text(encoding="utf-8")
                    )
                    self.assertTrue(encounter_set_data.get("encounters"))


if __name__ == "__main__":
    unittest.main()
