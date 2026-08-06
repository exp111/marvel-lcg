from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from engine.lib import Json
from game.game_run.campaign_settings import CampaignSettings


class TestCampaignSettingsPersistence(unittest.TestCase):

    def test_launch_updates_selected_campaign_and_preserves_others(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "campaign_settings.json")
            CampaignSettings.Update(
                "mutant_genesis",
                {"Reputation Track": "7"},
                path,
            )
            new_game = SimpleNamespace(
                campaign_json=Json.Dumps({
                    "campaign_id": "agents_of_shield",
                }),
                campaign_log={
                    "Evidence Seed": "123456789",
                    "Evidence Earned": "50185;50189",
                },
            )

            CampaignSettings.UpdateForLaunch(new_game, path)

            self.assertEqual(CampaignSettings.Load(path), {
                "mutant_genesis": {"Reputation Track": "7"},
                "agents_of_shield": {
                    "Evidence Seed": "123456789",
                    "Evidence Earned": "50185;50189",
                },
            })

    def test_relaunch_replaces_cleared_fields_for_that_campaign(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "campaign_settings.json")
            CampaignSettings.Update(
                "agents_of_shield",
                {
                    "Evidence Seed": "1",
                    "Chief Medical Officer Flipped": "Yes",
                },
                path,
            )

            CampaignSettings.Update(
                "agents_of_shield",
                {"Evidence Seed": "2"},
                path,
            )

            self.assertEqual(CampaignSettings.Load(path), {
                "agents_of_shield": {"Evidence Seed": "2"},
            })

    def test_campaign_settings_file_is_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "campaign_settings.json")
            CampaignSettings.Update("rise_of_red_skull", {"A": "B"}, path)

            self.assertEqual(
                json.loads(Path(path).read_text(encoding="utf-8")),
                {"rise_of_red_skull": {"A": "B"}},
            )


if __name__ == "__main__":
    unittest.main()
