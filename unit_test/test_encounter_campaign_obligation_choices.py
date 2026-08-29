from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestPaparazziChoice(unittest.TestCase):

    def test_exhaust_or_discard_choice_remains_forced(self):
        module = import_module("cards.pack.mojo.mojo.39030")
        ability = module.GetAbilities()[0]
        obligation = MagicMock()
        obligation.CastTo.return_value = obligation
        player = MagicMock()
        obligation.GetGaveToPlayer.return_value = player
        effect = SimpleNamespace(this=obligation)

        ability.operation(effect, SimpleNamespace())

        choices = player.ChooseAbilities.call_args.args[1:]
        self.assertEqual(len(choices), 2)
        self.assertTrue(all(len(choice.cost_funcs) == 1 for choice in choices))
        for choice in choices:
            self.assertNotIn("ForChoiceAbilityWithCost", choice.func_names)
            self.assertNotEqual(choice.GetName(False), "Otherwise")


class TestInnocentBystandersChoice(unittest.TestCase):

    def test_spend_or_threat_choice_remains_forced(self):
        module = import_module("cards.pack.aos.thunderbolts.50134")
        ability = module.GetAbilities()[0]
        obligation = MagicMock()
        obligation.CastTo.return_value = obligation
        player = MagicMock()
        attacker = MagicMock()
        attacker.GetControlByOrOwner.return_value.IsPlayer.return_value = True
        attacker.GetControlByPlayer.return_value = player
        effect = SimpleNamespace(this=obligation)
        message = SimpleNamespace(attacker=attacker, attacked=MagicMock())

        with patch.object(module.Worlds, "IsExpert", return_value=False), patch.object(
            module.Faces,
            "RemoveCountersOn",
        ):
            ability.operation(effect, message)

        choices = player.ChooseAbilities.call_args.args[1:]
        self.assertEqual(len(choices), 2)
        self.assertTrue(choices[0].NeedCost())
        for choice in choices:
            self.assertNotIn("ForChoiceAbilityWithCost", choice.func_names)
            self.assertNotEqual(choice.GetName(False), "Otherwise")


if __name__ == "__main__":
    unittest.main()
