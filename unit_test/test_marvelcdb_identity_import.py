import json
from pathlib import Path
import unittest

from engine.file import FileManager


class TestMarvelCDBIdentityImport(unittest.TestCase):

    def test_duplicate_black_panther_names_resolve_by_identity_code(self):
        project_root = Path(__file__).resolve().parents[1]
        expected_decks = {
            "01040a": "black_panther.json",
            "51001a": "black_panther_shuri.json",
        }

        for identity_code, expected_file in expected_decks.items():
            with self.subTest(identity_code=identity_code):
                path = FileManager.FindStarterDeckJsonPathByIdentityCode(identity_code)

                self.assertIsNotNone(path)
                self.assertEqual(Path(path).name, expected_file)

                deck = json.loads((project_root / path).read_text(encoding="utf-8"))
                self.assertIn(identity_code, deck["hero"][0].split(","))

    def test_marvelcdb_import_passes_the_identity_code_to_the_lookup(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "deck.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "await set_hero(json_data['hero_name'], json_data['hero_code'])",
            html,
        )
        self.assertIn("getHeroJson(hero_code || name)", html)


if __name__ == "__main__":
    unittest.main()
