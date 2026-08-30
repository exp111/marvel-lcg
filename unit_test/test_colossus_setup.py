from __future__ import annotations

import importlib
import unittest
from unittest.mock import patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class _Identity:
    def CastTo(self, _card_type):
        return self


class _Effect:
    def __init__(self) -> None:
        self.this = _Identity()
        self.initiator = object()

    def GetInitiator(self):
        return self.initiator


class TestColossusSetup(unittest.TestCase):

    def test_organic_steel_searches_only_the_player_deck(self):
        module = importlib.import_module("cards.pack.mut_gen.colossus.32001b")
        setup_ability = module.GetAbilities()[0]
        effect = _Effect()

        with patch.object(module.Search, "PlayerCard", return_value=None) as search:
            setup_ability.operation(effect, object())

        self.assertEqual(search.call_args.args[:2], (effect, effect.initiator))
        self.assertTrue(search.call_args.kwargs["include_player_deck"])
        self.assertFalse(search.call_args.kwargs.get("include_discard_pile", False))
        self.assertEqual(search.call_args.kwargs["name"], "Organic Steel")
        self.assertIs(search.call_args.kwargs["card_type"], module.Upgrade)


if __name__ == "__main__":
    unittest.main()
