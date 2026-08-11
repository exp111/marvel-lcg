from pathlib import Path
import unittest


class TestReleaseDependencies(unittest.TestCase):

    def test_release_version_matches_patch_notes(self):
        project_root = Path(__file__).resolve().parents[1]
        build = (project_root / "build.py").read_text(encoding="utf-8")
        patch_notes = (project_root / "PATCH_NOTES.md").read_text(encoding="utf-8")
        marvel_html = (project_root / "public" / "marvel.html").read_text(
            encoding="utf-8"
        )

        for version_part in (
            "    MAJOR = 1",
            "    MINOR = 1",
            "    PATCH = 1",
            "    BUILD = 0",
        ):
            self.assertIn(version_part, build.splitlines())
        self.assertIn("Application version: **1.1.1r**", patch_notes)
        self.assertNotIn("1.0.0.5r", marvel_html)
        self.assertGreaterEqual(marvel_html.count("?v=1.1.1r"), 2)

    def test_main_menu_identifies_the_community_build_with_the_live_version(self):
        project_root = Path(__file__).resolve().parents[1]
        main_html = (project_root / "public" / "main.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("Community Build v${version}", main_html)
        self.assertIn("fetch('/get_version', { cache: 'no-store' })", main_html)
        self.assertNotIn("versionElement.innerHTML = `v${version}`", main_html)

    def test_packaged_build_opens_versioned_html_routes(self):
        project_root = Path(__file__).resolve().parents[1]
        launch = (project_root / "launch.json").read_text(encoding="utf-8")
        manager = (
            project_root / "engine" / "device" / "manager" / "web" / "manager.py"
        ).read_text(encoding="utf-8")
        main_html = (project_root / "public" / "main.html").read_text(
            encoding="utf-8"
        )

        self.assertIn('"open_browser_on_startup": true', launch)
        self.assertIn("/main?v={quote(version, safe='')}", manager)
        self.assertIn("webbrowser.open, url, new=2", manager)
        self.assertIn("destination.searchParams.set('v', version)", main_html)

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

    def test_release_uses_python_312_onedir_without_upx(self):
        project_root = Path(__file__).resolve().parents[1]
        release_spec = (
            project_root / "packaging" / "marvel-lcg-release.spec"
        ).read_text(encoding="utf-8")
        release_script = (
            project_root / "packaging" / "build_release.ps1"
        ).read_text(encoding="utf-8")
        workflow = (
            project_root / ".github" / "workflows" / "build-release.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("exclude_binaries=True", release_spec)
        self.assertIn("coll = COLLECT(", release_spec)
        self.assertEqual(release_spec.count("upx=False"), 2)
        self.assertIn('contents_directory="_internal"', release_spec)
        self.assertIn('Join-Path $projectRoot ".venv-release"', release_script)
        self.assertIn('$pythonVersion -ne "3.12"', release_script)
        self.assertIn('python-version: "3.12"', workflow)

    def test_release_executable_has_community_version_metadata(self):
        project_root = Path(__file__).resolve().parents[1]
        release_spec = (
            project_root / "packaging" / "marvel-lcg-release.spec"
        ).read_text(encoding="utf-8")

        self.assertIn('StringStruct("CompanyName", "Marvel Champions Digital Community")', release_spec)
        self.assertIn('StringStruct("ProductVersion", version_text)', release_spec)
        self.assertIn("version=version_info", release_spec)

    def test_release_excludes_developer_command_modules(self):
        project_root = Path(__file__).resolve().parents[1]
        release_spec = (
            project_root / "packaging" / "marvel-lcg-release.spec"
        ).read_text(encoding="utf-8")
        system = (project_root / "core" / "utility" / "system.py").read_text(
            encoding="utf-8"
        )

        for module in (
            '"editor"',
            '"engine.file.code_editor"',
            '"engine.security.command_validation"',
            '"game.world.cheat.cheat_cmd_helper"',
            '"unit_test"',
        ):
            self.assertIn(module, release_spec)
        self.assertNotIn("os.system", system)


if __name__ == "__main__":
    unittest.main()
