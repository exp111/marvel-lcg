import json
from pathlib import Path
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
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
