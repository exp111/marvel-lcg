from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.pack.aos.campaign import (
    ResolveCampaignVictory,
    ResolveEarnedEvidenceSetup,
)
from cards.pack.aos.shield_executive_board import BoardMemberSecretThreshold
from game.message import Message


class TestAgentsOfShieldCampaign(unittest.TestCase):

    def test_board_member_threshold_uses_expert_encounter_set(self):
        effect = SimpleNamespace(
            world=SimpleNamespace(
                scene=SimpleNamespace(
                    campaign=SimpleNamespace(encounter_sets=["standard", "expert"]),
                ),
            ),
        )

        with patch("game.operate.worlds.Worlds.IsExpert", return_value=False):
            self.assertEqual(BoardMemberSecretThreshold(effect), 3)

        effect.world.scene.campaign.encounter_sets = ["standard"]
        with patch("game.operate.worlds.Worlds.IsExpert", return_value=False):
            self.assertEqual(BoardMemberSecretThreshold(effect), 4)

    def test_earned_evidence_setup_resolves_from_removed_area(self):
        evidence = MagicMock()
        removed = MagicMock()
        removed.FindCard.side_effect = lambda *, card_ids: (
            evidence if card_ids == ["50185"] else None
        )
        effect = SimpleNamespace(world=SimpleNamespace(area_removed=removed))
        ability = ResolveEarnedEvidenceSetup()

        with patch(
            "cards.pack.aos.campaign._campaign_list",
            return_value=["50185"],
        ), patch(
            "cards.pack.aos.campaign.Evidence.IsType",
            return_value=True,
        ):
            ability.operation(effect, SimpleNamespace())

        evidence.Setup.assert_called_once_with(False)
        self.assertIs(ability.when, Message.WhenCampaignSetup)

    def test_evidence_reward_is_after_win_checks_and_before_game_over_render(self):
        ability = ResolveCampaignVictory(1)

        self.assertIs(ability.when, Message.WhenGameOver)
        self.assertTrue(ability.conditions[0](None, SimpleNamespace(players_won=True)))
        self.assertFalse(ability.conditions[0](None, SimpleNamespace(players_won=False)))
        self.assertTrue(ability.ignore.out_of_play)

    def test_victory_reward_comes_from_shield_envelope(self):
        member = MagicMock()
        member.GetCounters.return_value = 0
        evidence = MagicMock()
        evidence.paper.card_id = "50185"
        envelope = SimpleNamespace(
            initialize=True,
            deck=MagicMock(),
        )
        envelope.deck.FindCards.return_value = [evidence]
        player = MagicMock()
        effect = SimpleNamespace(world=MagicMock())
        ability = ResolveCampaignVictory(5)

        with patch(
            "cards.pack.aos.campaign.Worlds.FindCardsOnField",
            return_value=[member],
        ), patch(
            "cards.pack.aos.campaign.Environment.IsType",
            return_value=True,
        ), patch(
            "cards.pack.aos.campaign.Worlds.ScenarioDeck",
            return_value=envelope,
        ) as scenario_deck, patch(
            "cards.pack.aos.campaign.Worlds.GetFirstPlayer",
            return_value=player,
        ), patch(
            "cards.pack.aos.campaign.Rand.RandomChoice",
            return_value=evidence,
        ), patch(
            "cards.pack.aos.campaign.Faces.LookAt",
        ) as look_at, patch(
            "cards.pack.aos.campaign.Faces.RemoveAllFromGame",
        ) as remove, patch(
            "cards.pack.aos.campaign._campaign_list",
            return_value=[],
        ), patch(
            "cards.pack.aos.campaign.CampaignLog.SetStr",
        ) as set_log:
            ability.operation(effect, SimpleNamespace(players_won=True))

        scenario_deck.assert_called_once_with(effect, "S.H.I.E.L.D.Envelope")
        look_at.assert_called_once_with([evidence], player, effect)
        remove.assert_called_once_with([evidence], effect)
        set_log.assert_called_once_with("Evidence Earned", "50185", effect.world)

    def test_campaign_setup_ui_has_board_member_flip_settings(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertIn('description: "Chief Medical Officer Flipped"', html)
        self.assertIn('description: "Chief Surveillance Officer Flipped"', html)
        self.assertIn('description: "Chief Tactical Officer Flipped"', html)


if __name__ == "__main__":
    unittest.main()
