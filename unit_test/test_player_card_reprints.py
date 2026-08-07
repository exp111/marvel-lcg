import json
from pathlib import Path
import unittest


class TestPlayerCardReprints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "data" / "cards.json").read_text(encoding="utf-8"))
        cls.cards = {
            card["card_id"]: card
            for pack in data.values()
            if isinstance(pack, list)
            for card in pack
        }

    def test_wonder_man_reprints_use_the_original_cards(self):
        expected = {
            "58017": "42029",  # Bombs Away
            "58023": "01088",  # Energy
        }

        for card_id, original_id in expected.items():
            with self.subTest(card_id=card_id):
                self.assertEqual(
                    self.cards[card_id],
                    {"card_id": card_id, "full_link": original_id},
                )

    def test_hercules_reprints_use_the_original_cards(self):
        expected = {
            "59021": "06032",  # Teamwork
            "59022": "40018",  # Call for Backup
            "59027": "31023",  # Limitless Stamina
            "59029": "01088",  # Energy
            "59030": "01089",  # Genius
            "59031": "01090",  # Strength
            "59032": "58034",  # Avengers Compound
            "59033": "01092",  # Helicarrier
            "59034": "08023",  # Quincarrier
        }

        for card_id, original_id in expected.items():
            with self.subTest(card_id=card_id):
                self.assertEqual(
                    self.cards[card_id],
                    {"card_id": card_id, "full_link": original_id},
                )


if __name__ == "__main__":
    unittest.main()
