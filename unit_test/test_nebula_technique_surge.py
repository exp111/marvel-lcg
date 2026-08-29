import importlib
from types import SimpleNamespace
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from cards.pack.gmw.nebula import (
    TheFirstTechniqueAttachmentRevealedEachRoundGainsSurge,
)
from game.ability.condition import Condition
from game.world.world_stat import WorldStat


class TestNebulaTechniqueSurge(unittest.TestCase):

    def test_first_technique_limit_is_global_across_players(self):
        for card_id in ("16088", "16089", "16090"):
            with self.subTest(card_id=card_id):
                card_module = importlib.import_module(
                    f"cards.pack.gmw.nebula.{card_id}"
                )
                ability = card_module.GetAbilities()[0]
                stat = WorldStat()
                effect = SimpleNamespace(
                    ability=ability,
                    world=SimpleNamespace(stat=stat),
                )

                self.assertIn(Condition.LimitOncePerRound, ability.conditions)
                self.assertNotIn(
                    Condition.LimitOncePerRoundPerPlayer,
                    ability.conditions,
                )
                self.assertTrue(Condition.LimitOncePerRound(effect, None))

                stat.RecordEffect(effect)

                self.assertFalse(Condition.LimitOncePerRound(effect, None))

    def test_first_technique_limit_resets_next_round(self):
        ability = TheFirstTechniqueAttachmentRevealedEachRoundGainsSurge()
        stat = WorldStat()
        effect = SimpleNamespace(
            ability=ability,
            world=SimpleNamespace(stat=stat),
        )
        stat.RecordEffect(effect)

        stat.OnRoundEnd()

        self.assertTrue(Condition.LimitOncePerRound(effect, None))


if __name__ == "__main__":
    unittest.main()
