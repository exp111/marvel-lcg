from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
import json
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestGroundStomp(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.synthezoid.she_hulk.57010")
        self.player = MagicMock()
        self.effect = SimpleNamespace(this=MagicMock())

    def test_when_revealed_exhausts_every_ready_character(self):
        characters = [MagicMock(), MagicMock()]
        self.player.GetControlCharacters.return_value = characters
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=self.player))

        with patch.object(self.module.Faces, "ExhaustAll") as exhaust_all:
            self.module.GetAbilities()[0].operation(self.effect, message)

        exhaust_all.assert_called_once_with(characters, self.effect)

    def test_boost_exhausts_only_the_chosen_character(self):
        characters = [MagicMock(), MagicMock()]
        self.player.GetControlCharacters.return_value = characters
        self.player.AskChooseFace.return_value = characters[1]
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=self.player))

        with patch.object(self.module.Faces, "ExhaustAll") as exhaust_all:
            self.module.GetAbilities()[1].operation(self.effect, message)

        exhaust_all.assert_called_once_with([characters[1]], self.effect)


class TestPenance(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.synthezoid.thunderbolts.57019")
        self.card = MagicMock()
        self.effect = SimpleNamespace(this=self.card)
        self.player = MagicMock()
        self.message = SimpleNamespace(GetToPlayer=MagicMock(return_value=self.player))

    def test_damages_team_leader_before_considering_controlled_characters(self):
        leader = MagicMock()

        with patch.object(self.module.Worlds, "GetYourTeamLeader", return_value=leader):
            self.module.GetAbilities()[0].operation(self.effect, self.message)

        self.card.DealDamage.assert_called_once_with([leader], 2, self.effect)
        self.player.AskChooseFace.assert_not_called()

    def test_boost_falls_back_to_one_damage_on_a_chosen_character(self):
        character = MagicMock()
        self.player.GetControlCharacters.return_value = [character]
        self.player.AskChooseFace.return_value = character

        with patch.object(self.module.Worlds, "GetYourTeamLeader", return_value=None):
            self.module.GetAbilities()[1].operation(self.effect, self.message)

        self.card.DealDamage.assert_called_once_with([character], 1, self.effect)


class TestMimickedMove(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.synthezoid.taskmaster.57025")
        self.effect = SimpleNamespace(this=MagicMock())
        self.message = SimpleNamespace(GetToPlayer=MagicMock())

    def test_taskmaster_attacks_team_leader_when_both_are_in_play(self):
        taskmaster = MagicMock()

        with patch.object(
            self.module.Worlds, "GetOnFieldEnemies", return_value=[taskmaster]
        ), patch.object(self.module.Worlds, "GetYourTeamLeader", return_value=MagicMock()):
            self.module.GetAbilities()[0].operation(self.effect, self.message)

        taskmaster.DoAttackYou.assert_called_once()
        self.assertEqual(taskmaster.DoAttackYou.call_args.args[:2], ("YourLeader", self.effect))

    def test_otherwise_toughens_enemy_leader_and_gives_it_a_boost(self):
        leader = MagicMock()

        with patch.object(
            self.module.Worlds, "GetOnFieldEnemies", return_value=[]
        ), patch.object(self.module.Worlds, "GetYourTeamLeader", return_value=None), patch.object(
            self.module.Worlds, "GetEnemyLeader", return_value=leader
        ), patch.object(self.module.Faces, "GiveStatus") as give_status, patch.object(
            self.module.Faces, "GiveFacedownBoostCards"
        ) as give_boost:
            self.module.GetAbilities()[0].operation(self.effect, self.message)

        give_status.assert_called_once_with([leader], "Tough", self.effect)
        give_boost.assert_called_once_with([leader], 1, self.effect)


class TestJackOLantern(unittest.TestCase):

    def test_uses_a_minion_safe_script_and_places_threat_by_card_type_count(self):
        module = import_module("cards.pack.synthezoid.deadly_duo.57028")
        discarded = [MagicMock(), MagicMock(), MagicMock()]
        player = MagicMock()
        player.DiscardDeckTopCards.return_value = discarded
        card = MagicMock()
        effect = SimpleNamespace(this=card)
        message = SimpleNamespace(GetToPlayer=MagicMock(return_value=player))

        with patch.object(module.FacesCounter, "GetDifferentTypesCount", return_value=2):
            module.GetAbilities()[0].operation(effect, message)

        player.DiscardDeckTopCards.assert_called_once_with(3, effect)
        card.PlaceThreatOnSchemes.assert_called_once_with("MainScheme", 2, effect)
        card.CastTo.assert_not_called()

    def test_card_data_no_longer_links_to_the_treachery_implementation(self):
        cards_path = Path(__file__).parents[1] / "data" / "cards.json"
        cards = json.loads(cards_path.read_text(encoding="utf-8"))["synthezoid"]
        jack = next(card for card in cards if card["card_id"] == "57028")

        self.assertNotIn("ability_link", jack)


class TestMadJacksPlatform(unittest.TestCase):

    def test_grants_every_printed_modifier_to_attached_minion(self):
        module = import_module("cards.pack.cw.hells_kitchen.56191")

        with patch.object(
            module.AbilityFactory, "GiveKeywordToAttached", return_value=[]
        ) as give_keyword:
            module.GetAbilities()

        give_keyword.assert_called_once_with(
            module.Minion,
            attack=1,
            scheme=1,
            health=4,
            stalwart=1,
        )


class TestTaskmastersSword(unittest.TestCase):

    def test_piercing_uses_the_supported_attached_character_selector(self):
        module = import_module("cards.pack.synthezoid.taskmaster.57023")

        with patch.object(
            module.AbilityFactory,
            "UnitAttackGainKeyword",
            return_value=MagicMock(),
        ) as gain_keyword:
            module.GetAbilities()

        gain_keyword.assert_called_once_with(
            "AttachedCharacter",
            piercing=True,
        )


if __name__ == "__main__":
    unittest.main()
