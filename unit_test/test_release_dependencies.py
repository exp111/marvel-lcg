from pathlib import Path
import unittest


class TestReleaseDependencies(unittest.TestCase):

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
