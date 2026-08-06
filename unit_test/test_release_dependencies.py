from pathlib import Path
import unittest


class TestReleaseDependencies(unittest.TestCase):

    def test_release_version_matches_patch_notes(self):
        project_root = Path(__file__).resolve().parents[1]
        build = (project_root / "build.py").read_text(encoding="utf-8")
        patch_notes = (project_root / "PATCH_NOTES.md").read_text(encoding="utf-8")

        self.assertIn("    BUILD = 3", build.splitlines())
        self.assertIn("Application version: **1.0.0.3r**", patch_notes)

    def test_scene_setup_metadata_bypasses_browser_cache(self):
        project_root = Path(__file__).resolve().parents[1]
        scene_html = (project_root / "public" / "scene.html").read_text(encoding="utf-8")
        server_get = (
            project_root / "engine" / "device" / "web" / "server" / "server_get.py"
        ).read_text(encoding="utf-8")

        self.assertIn("cache: 'no-store'", scene_html)
        self.assertGreaterEqual(server_get.count("headers=self.HeaderCache"), 2)
        for endpoint in (
            "get_sets_json?",
            "get_sets_custom_scenario?",
            "list_scenarios?",
            "list_encounter_sets?",
            "get_encounter_set_json?",
            "get_scenario_json?",
        ):
            self.assertIn(f"fetchFresh(`{endpoint}", scene_html)

    def test_numpy_is_installed_and_bundled_for_runtime_randomization(self):
        project_root = Path(__file__).resolve().parents[1]
        requirements = (project_root / "requirements.txt").read_text(encoding="utf-8")
        release_spec = (
            project_root / "packaging" / "marvel-lcg-release.spec"
        ).read_text(encoding="utf-8")

        self.assertIn("numpy==2.5.1", requirements.splitlines())
        self.assertIn('release_hiddenimports = ["numpy", *card_hiddenimports]', release_spec)
        self.assertIn("hiddenimports=release_hiddenimports", release_spec)


if __name__ == "__main__":
    unittest.main()
