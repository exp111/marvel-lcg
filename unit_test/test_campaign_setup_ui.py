from pathlib import Path
import unittest


class TestCampaignSetupUI(unittest.TestCase):

    def test_player_campaign_rows_update_without_regeneration(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertIn("function updateCampaignPlayerRows()", html)
        self.assertIn("row.dataset.playerNumber = playerNumber", html)
        self.assertIn("row.hidden = parseInt(row.dataset.playerNumber) > visiblePlayers", html)
        self.assertIn("SetHero(j, i)", html)
        self.assertGreaterEqual(html.count("updateCampaignPlayerRows()"), 3)


if __name__ == "__main__":
    unittest.main()
