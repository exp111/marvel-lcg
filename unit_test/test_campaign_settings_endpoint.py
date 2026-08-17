from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import json
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from engine.device.web.server.server_new_game import GameServerNewGame


class TestCampaignSettingsEndpoint(unittest.IsolatedAsyncioTestCase):

    async def test_save_campaign_settings_updates_without_starting_game(self):
        request = SimpleNamespace(json=AsyncMock(return_value={
            "campaign_id": "mutant_genesis",
            "campaign_log": {"Reputation Track": "7"},
        }))
        settings = {
            "mutant_genesis": {"Reputation Track": "7"},
        }

        with patch(
            "engine.device.web.server.server_new_game.CampaignSettings.Update",
            return_value=settings,
        ) as update:
            response = await GameServerNewGame.save_campaign_settings(None, request)

        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.text), {
            "result": "Campaign settings saved",
            "settings": settings,
        })
        update.assert_called_once_with(
            "mutant_genesis",
            {"Reputation Track": "7"},
        )

    async def test_save_campaign_settings_rejects_missing_campaign(self):
        request = SimpleNamespace(json=AsyncMock(return_value={
            "campaign_id": "",
            "campaign_log": {},
        }))

        response = await GameServerNewGame.save_campaign_settings(None, request)

        self.assertEqual(response.status, 400)
        self.assertEqual(
            json.loads(response.text),
            {"error": "No campaign selected"},
        )

    async def test_save_campaign_settings_rejects_non_object_log(self):
        request = SimpleNamespace(json=AsyncMock(return_value={
            "campaign_id": "mutant_genesis",
            "campaign_log": [],
        }))

        response = await GameServerNewGame.save_campaign_settings(None, request)

        self.assertEqual(response.status, 400)
        self.assertEqual(
            json.loads(response.text),
            {"error": "Invalid campaign log"},
        )


if __name__ == "__main__":
    unittest.main()
