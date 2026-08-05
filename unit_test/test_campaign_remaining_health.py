from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.pack.aoa.campaign_setup import ExpertCampaignEachPlayerMayHealAtMissionThreatCost
from game.ability.factory.campaign import AbilityFactoryCampaign
from game.message import Message


class TestCampaignRemainingHealth(unittest.TestCase):

    def test_remaining_health_is_applied_during_campaign_setup(self):
        ability = AbilityFactoryCampaign.CampaignSetPlayersHPToTheirRemainingHP(
            campaign_id="agents_of_shield",
        )
        identity = MagicMock()
        player = SimpleNamespace(
            player_id=0,
            GetIdentity=MagicMock(return_value=identity),
        )
        effect = SimpleNamespace()

        with patch(
            "game.operate.worlds.Worlds.GetPlayers",
            return_value=[player],
        ), patch(
            "game.operate.campaign_logs.CampaignLog.GetIntByPlayer",
            return_value=4,
        ):
            ability.operation(effect, SimpleNamespace())

        self.assertIs(ability.when, Message.WhenCampaignSetup)
        identity.SetHealth.assert_called_once_with(4, effect)

    def test_remaining_health_is_not_expert_only(self):
        ability = AbilityFactoryCampaign.CampaignSetPlayersHPToTheirRemainingHP(
            campaign_id="agents_of_shield",
        )
        effect = SimpleNamespace()
        message = SimpleNamespace()

        with patch(
            "game.operate.worlds.Worlds.IsCampaign",
            return_value=True,
        ), patch(
            "game.operate.worlds.Worlds.IsCampaignSelected",
            return_value=True,
        ), patch(
            "game.operate.worlds.Worlds.IsExpert",
            side_effect=AssertionError("standard setup must not check expert mode"),
        ):
            self.assertTrue(ability.conditions[0](effect, message))

    def test_aoa_standard_campaign_with_remaining_health_offers_heal(self):
        ability = ExpertCampaignEachPlayerMayHealAtMissionThreatCost()
        identity = MagicMock()
        player = SimpleNamespace(
            player_id=0,
            GetIdentity=MagicMock(return_value=identity),
            MayChooseOneAbility=MagicMock(),
        )
        effect = SimpleNamespace()

        with patch(
            "game.operate.worlds.Worlds.FindCardOnField",
            return_value=MagicMock(),
        ), patch(
            "game.operate.worlds.Worlds.GetPlayers",
            return_value=[player],
        ), patch(
            "game.operate.worlds.Worlds.IsExpert",
            return_value=False,
        ), patch(
            "game.operate.campaign_logs.CampaignLog.GetIntByPlayer",
            return_value=4,
        ):
            ability.operation(effect, SimpleNamespace())

        player.MayChooseOneAbility.assert_called_once()

    def test_aoa_standard_campaign_without_remaining_health_skips_heal(self):
        ability = ExpertCampaignEachPlayerMayHealAtMissionThreatCost()
        player = SimpleNamespace(
            player_id=0,
            GetIdentity=MagicMock(),
            MayChooseOneAbility=MagicMock(),
        )
        effect = SimpleNamespace()

        with patch(
            "game.operate.worlds.Worlds.FindCardOnField",
            return_value=MagicMock(),
        ), patch(
            "game.operate.worlds.Worlds.GetPlayers",
            return_value=[player],
        ), patch(
            "game.operate.worlds.Worlds.IsExpert",
            return_value=False,
        ), patch(
            "game.operate.campaign_logs.CampaignLog.GetIntByPlayer",
            return_value=0,
        ):
            ability.operation(effect, SimpleNamespace())

        player.MayChooseOneAbility.assert_not_called()


if __name__ == "__main__":
    unittest.main()
