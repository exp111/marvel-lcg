from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.card.face.model.face_action import ModelAction
from game.message import Message


class TestTemporaryRecoveryGain(unittest.TestCase):

    def test_gain_until_phase_end_forwards_recovery_and_phase_expiration(self):
        model = MagicMock()
        effect = MagicMock()

        ModelAction.GainUntilPhaseEnd(model, effect, recover=2)

        args = model.TemporaryGain.call_args.args
        kwargs = model.TemporaryGain.call_args.kwargs
        self.assertEqual(args, (effect, None, Message.WhenPhaseEnd))
        self.assertEqual(kwargs["recover"], 2)
        self.assertTrue(kwargs["ignore_flip"])
        self.assertTrue(kwargs["render_ui"])


class TestJarvis(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.wonder_man.58024")
        self.ability = self.module.GetAbilities()[0]
        self.identity = MagicMock()
        self.status = MagicMock()
        self.identity.components.status.GetDeck.return_value.GetAll.return_value = [self.status]
        self.trigger = SimpleNamespace(
            CastTo=MagicMock(return_value=self.identity),
        )
        self.player = MagicMock()
        self.effect = SimpleNamespace(
            GetInitiator=MagicMock(return_value=self.player),
        )
        self.message = SimpleNamespace(trigger=self.trigger)

    def test_recovery_choice_grants_two_recovery_until_phase_end(self):
        self.ability.operation(self.effect, self.message)
        recovery_choice = self.player.ChooseAbilities.call_args.args[1]
        choice_effect = SimpleNamespace(
            targets=[],
            GetPaidResources=MagicMock(),
        )

        recovery_choice.operation(choice_effect, SimpleNamespace())

        self.identity.GainUntilPhaseEnd.assert_called_once_with(
            self.effect,
            recover=2,
        )

    def test_status_choice_discards_the_selected_status(self):
        self.ability.operation(self.effect, self.message)
        status_choice = self.player.ChooseAbilities.call_args.args[2]
        choice_effect = SimpleNamespace(
            targets=[self.status],
            GetPaidResources=MagicMock(),
        )

        with patch.object(self.module.Faces, "DiscardAll") as discard_all:
            status_choice.operation(choice_effect, SimpleNamespace())

        discard_all.assert_called_once_with([self.status], self.effect)


if __name__ == "__main__":
    unittest.main()
