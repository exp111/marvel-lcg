from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.world.world import (
    DoesIdentitySpecificAllyMatchPlayer,
    FindTeamUpAllyRemovalCandidates,
    IsTeamUpForPlayers,
    World,
)


class FakePlayer:
    def __init__(self, names, deck=()):
        self.names = set(names)
        self.player_deck = SimpleNamespace(GetAll=lambda: list(deck))
        self.identity = MagicMock()

    def IsName(self, *names):
        return any(name in self.names for name in names)

    def GetIdentity(self):
        return self.identity


class TestTeamUpAllyReplacement(unittest.TestCase):

    def test_team_up_requires_the_two_players_in_opposite_groups(self):
        team_up = SimpleNamespace(team_up=[["Hercules"], ["Thor"]])
        thor = FakePlayer(["Thor", "Odinson"])
        hercules = FakePlayer(["Hercules"])
        wasp = FakePlayer(["Wasp", "Nadia Van Dyne"])

        self.assertTrue(IsTeamUpForPlayers(team_up, thor, hercules))
        self.assertTrue(IsTeamUpForPlayers(team_up, hercules, thor))
        self.assertFalse(IsTeamUpForPlayers(team_up, thor, wasp))

    def test_ally_can_match_the_other_players_alter_ego_name(self):
        shuri_ally = MagicMock()
        shuri_ally.name = "Shuri"
        shuri_ally.printed_subtitle = ""
        shuri_ally.CanCoexistWith.return_value = True
        shuri = FakePlayer(["Black Panther", "Shuri"])

        self.assertTrue(
            DoesIdentitySpecificAllyMatchPlayer(shuri_ally, shuri)
        )

    def test_finds_only_matching_identity_specific_ally_once(self):
        team_up = MagicMock(
            kind="team_up",
            team_up=[["Hercules"], ["Thor"]],
        )
        hercules_ally = MagicMock(
            kind="ally",
            paper=SimpleNamespace(card_id="06011"),
        )
        hercules_ally.name = "Hercules"
        hercules_ally.printed_subtitle = ""
        hercules_ally.IsClass.return_value = True
        hercules_ally.CanCoexistWith.return_value = False
        basic_ally = MagicMock(
            kind="ally",
            paper=SimpleNamespace(card_id="basic"),
        )
        basic_ally.name = "Hercules"
        basic_ally.printed_subtitle = ""
        basic_ally.IsClass.return_value = False
        thor = FakePlayer(
            ["Thor", "Odinson"],
            [team_up, team_up, hercules_ally, basic_ally],
        )
        hercules = FakePlayer(["Hercules"])

        with (
            patch(
                "game.world.world.HasTeamUp.IsType",
                side_effect=lambda face: face.kind == "team_up",
            ),
            patch(
                "game.world.world.Ally.IsType",
                side_effect=lambda face: face.kind == "ally",
            ),
            patch(
                "game.world.world.ClassCard.IsType",
                side_effect=lambda face: face.kind == "ally",
            ),
        ):
            candidates = FindTeamUpAllyRemovalCandidates(
                [thor, hercules],
            )

        self.assertEqual(candidates, {thor: [hercules_ally]})

    @patch("game.operate.faces.Faces.RemoveAllFromGame")
    @patch("game.effect.rule.GameRule")
    def test_pre_opening_draw_choice_only_considers_allies_still_in_deck(
        self,
        game_rule,
        remove_all_from_game,
    ):
        player = MagicMock()
        player_deck = player.player_deck

        keep_ally = MagicMock(name="keep_ally")
        keep_ally.name = "Hercules"
        keep_ally.card.area = player_deck
        remove_ally = MagicMock(name="remove_ally")
        remove_ally.name = "Shuri"
        remove_ally.card.area = player_deck
        setup_moved_ally = MagicMock(name="setup_moved_ally")
        setup_moved_ally.name = "Wasp"
        setup_moved_ally.card.area = object()

        player.AskChooseOneText.side_effect = [False, True]
        identity = player.GetIdentity.return_value
        world = SimpleNamespace(
            const_players=[player],
        )

        World.ResolveTeamUpAllyRemovalChoices(
            world,
            {player: [keep_ally, remove_ally, setup_moved_ally]},
        )

        # An ally moved under a scheme (or anywhere else) by setup is skipped.
        self.assertEqual(player.AskChooseOneText.call_count, 2)
        game_rule.assert_called_once_with(identity)
        remove_all_from_game.assert_called_once_with(
            [remove_ally],
            game_rule.return_value,
        )


if __name__ == "__main__":
    unittest.main()
