import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.card.face import Ally
from game.player.model.player_ask import PlayerAsk
from game.selector import Select


class _Player:

    def __init__(self, selected):
        self.AskChooseFaces = MagicMock(return_value=selected)


class _AskPlayer(PlayerAsk):

    def __init__(self, selected):
        self.AskChooseSelect = MagicMock(return_value=selected)

    def GetPlayer(self):
        return self


class _Face:

    def __init__(self, *traits):
        self.traits = set(traits)

    def HasTrait(self, *traits):
        return any(trait in self.traits for trait in traits)

    def IsInDeck(self):
        return False


class TestMutantMayhem(unittest.TestCase):

    def test_alliance_rule_rejects_two_allies_with_the_same_required_trait(self):
        rule = Select.Alliance(["X-FORCE", "X-MEN"], Ally).selector_rule
        effect = SimpleNamespace(failures=MagicMock())

        self.assertFalse(rule.AfterSelectTargets(
            effect,
            [_Face("X-MEN"), _Face("X-MEN")],
            (2, 2),
        ))
        self.assertTrue(rule.AfterSelectTargets(
            effect,
            [_Face("X-MEN"), _Face("X-FORCE")],
            (2, 2),
        ))

    def test_alliance_rule_requires_both_traits_to_be_available(self):
        selector = Select.Alliance(["X-FORCE", "X-MEN"], Ally)
        effect = SimpleNamespace(failures=MagicMock())

        self.assertEqual(
            selector.selector_rule.Process(
                [_Face("X-MEN"), _Face("X-MEN")],
                effect,
                selector.selector_range,
            ),
            [],
        )

    def test_choose_faces_exposes_the_preserved_rule_to_the_client(self):
        selected = [_Face("X-MEN"), _Face("X-FORCE")]
        player = _AskPlayer(selected)
        effect = SimpleNamespace()

        self.assertEqual(player.AskChooseFaces(
            selected,
            (2, 2),
            effect,
            select_rule="MustIncludeTraits",
            target_must_include_traits=["X-FORCE", "X-MEN"],
        ), selected)

        choice_selector = player.AskChooseSelect.call_args.args[0]
        self.assertEqual(
            choice_selector.selector_rule.raw_select_rule,
            "MustIncludeTraits",
        )
        self.assertEqual(
            choice_selector.selector_rule.target_must_include_traits,
            ["X-FORCE", "X-MEN"],
        )

    def test_cost_choice_preserves_the_alliance_rule_for_the_client(self):
        module = importlib.import_module("cards.pack.jubilee.47028")
        cost = module.GetAbilities()[0].cost_funcs[0]
        selected = [_Face("X-MEN"), _Face("X-FORCE")]
        player = _Player(selected)
        effect = SimpleNamespace(
            ability=SimpleNamespace(
                flags=SimpleNamespace(is_check_pay=False),
            ),
        )

        cost.selector.GetAllLegalTargets = MagicMock(return_value=selected)
        cost.selector.GetTargetRange = MagicMock(return_value=(2, 2))
        cost.selector.AfterSelectTargets = MagicMock(return_value=True)
        cost.call_fn = MagicMock(return_value=True)

        with patch("game.player.Player", _Player):
            self.assertTrue(cost.PayCost(effect, player))

        player.AskChooseFaces.assert_called_once_with(
            selected,
            (2, 2),
            effect,
            prompt="Pay cost ReturnToHand",
            select_rule="MustIncludeTraits",
            target_must_include_traits=["X-FORCE", "X-MEN"],
        )


if __name__ == "__main__":
    unittest.main()
