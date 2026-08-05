from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestHerculesSonOfZeus(unittest.TestCase):

    def test_readies_hercules_and_chosen_identity_upgrade(self):
        module = import_module("cards.pack.hercules.hercules.59010")
        ability = module.GetAbilities()[0]
        identity = SimpleNamespace()
        upgrade = SimpleNamespace()
        player = SimpleNamespace(
            GetIdentity=MagicMock(return_value=identity),
            GetControlCards=MagicMock(return_value=[upgrade]),
            AskChooseOneText=MagicMock(return_value=upgrade),
        )
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        with patch.object(module, "CountGifts", return_value=1), patch.object(
            module.Faces,
            "ReadyAll",
        ) as ready_all:
            ability.operation(effect, SimpleNamespace())

        self.assertEqual(
            ready_all.call_args_list,
            [call([identity], effect), call([upgrade], effect)],
        )


if __name__ == "__main__":
    unittest.main()
