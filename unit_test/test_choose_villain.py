import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.operate.worlds import Worlds


class TestChooseVillain(unittest.TestCase):

    def setUp(self):
        self.player = MagicMock()
        self.effect = MagicMock()
        self.effect.GetInitiator.return_value = self.player
        self.effect.world.GetScenario.return_value.name = "The Tower Defense"

    def test_returns_only_villain_without_prompting(self):
        villain = MagicMock(name="Proxima")

        with patch.object(Worlds, "GetVillains", return_value=[villain]):
            result = Worlds.ChooseVillain(self.effect)

        self.assertIs(result, villain)
        self.player.AskChooseFace.assert_not_called()

    def test_prompts_for_one_of_multiple_villains(self):
        villains = [MagicMock(name="Proxima"), MagicMock(name="Corvus")]
        self.player.AskChooseFace.return_value = villains[1]

        with patch.object(Worlds, "GetVillains", return_value=villains):
            result = Worlds.ChooseVillain(
                self.effect,
                prompt="Choose the attacking villain",
            )

        self.assertIs(result, villains[1])
        self.player.AskChooseFace.assert_called_once_with(
            villains,
            self.effect,
            prompt="Choose the attacking villain",
        )

    def test_returns_none_when_no_villain_matches_filter(self):
        finder = MagicMock()

        with patch.object(Worlds, "GetVillains", return_value=[]) as get_villains:
            result = Worlds.ChooseVillain(self.effect, finder)

        self.assertIsNone(result)
        get_villains.assert_called_once_with(self.effect, finder)
        self.player.AskChooseFace.assert_not_called()

    def test_wrecking_crew_uses_only_the_active_villain(self):
        active_villain = MagicMock(name="Wrecker")
        self.effect.world.GetScenario.return_value.name = "The Wrecking Crew"

        with patch.object(Worlds, "FindVillain", return_value=active_villain), patch.object(
            Worlds,
            "GetVillains",
        ) as get_villains:
            result = Worlds.ChooseVillain(self.effect)

        self.assertIs(result, active_villain)
        get_villains.assert_not_called()
        self.player.AskChooseFace.assert_not_called()


if __name__ == "__main__":
    unittest.main()
