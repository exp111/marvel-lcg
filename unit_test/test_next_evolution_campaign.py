from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.pack.next_evol.campaign import RevealTeleportedAwayWithCampaignThreat


class TestNextEvolutionCampaign(unittest.TestCase):

    def test_teleported_away_adds_one_threat_per_campaign_environment(self):
        scheme = MagicMock()
        effect = SimpleNamespace(
            world=MagicMock(),
            this=MagicMock(),
        )
        ability = RevealTeleportedAwayWithCampaignThreat()

        with patch(
            "cards.pack.next_evol.campaign.SetupCards.Reveal",
            return_value=scheme,
        ), patch(
            "cards.pack.next_evol.campaign._earned_environment_ids",
            return_value=["40190b", "40191b", "40195b"],
        ):
            ability.operation(effect, SimpleNamespace())

        effect.this.PlaceThreatOnSchemes.assert_called_once_with(
            [scheme],
            3,
            effect,
        )


if __name__ == "__main__":
    unittest.main()
