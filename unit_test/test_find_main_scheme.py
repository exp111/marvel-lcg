import unittest
from unittest.mock import Mock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.card.face.card_type import MainScheme
from game.effect.rule import GameRule
from game.message import Message
from game.operate.worlds import Worlds
from game.player import Player, Scenario


class TestFindMainScheme(unittest.TestCase):

    def setUp(self):
        self.scenario = Mock(spec=Scenario)
        self.player = Mock(spec=Player)
        self.face = Mock()
        self.face.GetOwner.return_value = self.scenario
        self.face.GetControlByOrOwner.return_value = self.scenario
        self.effect = GameRule(self.face)
        self.schemes = [self.make_scheme(self.scenario) for _ in range(2)]

        self.get_schemes = self.enterContext(
            patch.object(Worlds, "GetMainSchemes", return_value=self.schemes)
        )
        self.getting_message = self.enterContext(
            patch.object(Message, "GettingMainScheme")
        ).return_value
        self.getting_message.return_value = None

    @staticmethod
    def make_scheme(owner):
        scheme = object.__new__(MainScheme)
        scheme.card = Mock()
        scheme.card.GetOwner.return_value = owner
        return scheme

    def test_scenario_initiated_effect_falls_back_to_first_main_scheme(self):
        self.assertIs(Worlds.FindMainScheme(self.effect), self.schemes[0])

    def test_player_initiated_effect_selects_that_players_main_scheme(self):
        self.effect.context.initiator = self.player
        self.schemes[1].card.GetOwner.return_value = self.player

        self.assertIs(Worlds.FindMainScheme(self.effect), self.schemes[1])

    def test_explicit_against_player_takes_precedence_over_initiator(self):
        self.effect.context.initiator = Mock(spec=Player)
        self.schemes[0].card.GetOwner.return_value = self.effect.initiator
        self.schemes[1].card.GetOwner.return_value = self.player

        self.assertIs(
            Worlds.FindMainScheme(self.effect, against_player=self.player),
            self.schemes[1],
        )

    def test_scenario_override_takes_precedence_over_player_owned_scheme(self):
        self.effect.context.initiator = self.player
        self.schemes[0].card.GetOwner.return_value = self.player
        self.getting_message.return_value = self.schemes[1]

        self.assertIs(Worlds.FindMainScheme(self.effect), self.schemes[1])

    def test_scenario_initiated_effect_can_use_face_owners_scheme(self):
        self.face.GetOwner.return_value = self.player
        self.schemes[1].card.GetOwner.return_value = self.player

        self.assertIs(Worlds.FindMainScheme(self.effect), self.schemes[1])
        self.player.AskChooseFace.assert_not_called()

    def test_card_face_input_keeps_owner_based_selection(self):
        self.face.GetOwner.return_value = self.player
        self.schemes[1].card.GetOwner.return_value = self.player

        self.assertIs(Worlds.FindMainScheme(self.face), self.schemes[1])

    def test_single_main_scheme_needs_no_selection(self):
        self.get_schemes.return_value = self.schemes[:1]

        self.assertIs(Worlds.FindMainScheme(self.effect), self.schemes[0])
        self.getting_message.Send.assert_not_called()

    def test_no_main_scheme_returns_none(self):
        self.get_schemes.return_value = []

        self.assertIsNone(Worlds.FindMainScheme(self.effect))
        self.getting_message.Send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
