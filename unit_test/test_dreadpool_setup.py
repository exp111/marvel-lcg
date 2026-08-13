import unittest
from unittest.mock import MagicMock

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.scene.replay.hero import HeroDescriptor
from game.world.world import IsUsingPoolAspect


def hero_descriptor(*, aspect="", aspect2=""):
    return HeroDescriptor(
        version="1.1.1",
        name="Hero",
        hero=["hero"],
        hero_deck=[],
        obligations=[],
        nemesis_set=[],
        player_deck=[],
        aspect=aspect,
        aspect2=aspect2,
    )


class TestDreadpoolSetup(unittest.TestCase):

    def test_off_aspect_pool_card_does_not_select_pool(self):
        player = MagicMock()
        hero = hero_descriptor(aspect="protection")

        self.assertFalse(IsUsingPoolAspect(hero, player))
        player.player_deck.FindCardSize.assert_not_called()

    def test_primary_or_secondary_pool_aspect_selects_pool(self):
        player = MagicMock()

        self.assertTrue(
            IsUsingPoolAspect(hero_descriptor(aspect="pool"), player)
        )
        self.assertTrue(
            IsUsingPoolAspect(hero_descriptor(
                aspect="leadership",
                aspect2="pool",
            ), player)
        )

    def test_legacy_deck_only_infers_pool_when_it_is_the_sole_aspect(self):
        player = MagicMock()
        player.player_deck.FindCardSize.side_effect = [1, 1]

        self.assertFalse(IsUsingPoolAspect(hero_descriptor(), player))

        player.player_deck.FindCardSize.side_effect = [1, 0]
        self.assertTrue(IsUsingPoolAspect(hero_descriptor(), player))


if __name__ == "__main__":
    unittest.main()
