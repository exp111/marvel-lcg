from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability.factory import AbilityFactory
from game.ability.factory.asset_helper import (
    GiveKeywordToAttachWhenApplyThisInternal,
)
from game.message import Message, OnEvent
from game.scene.replay import OperationDescriptor
from game.scene.scene import ATTACHED_HEALTH_FLIP_RULE, Scene


class TestAttachedHealthFlip(unittest.TestCase):

    def test_while_valid_preserves_modifier_across_faces_of_same_card(self):
        class Card:
            def __init__(self):
                self.state = SimpleNamespace(is_leaving_play=False)

        class Face:
            def __init__(self, card):
                self.card = card

        identity_card = Card()
        old_face = Face(identity_card)
        new_face = Face(identity_card)

        registrations = []

        def registers(*abilities):
            registrations.append(abilities)
            return list(abilities)

        upgrade = SimpleNamespace(
            bind_face=old_face,
            card=SimpleNamespace(
                state=SimpleNamespace(
                    is_leaving_play=False,
                    is_flipping=False,
                ),
                ui=SimpleNamespace(ResetTempEffectBy=MagicMock()),
            ),
            effect=SimpleNamespace(
                Registers=MagicMock(side_effect=registers),
                RegisterTemp=MagicMock(),
            ),
            is_treat_as_if_blank=False,
            IsInPlay=MagicMock(return_value=True),
            IsFaceUp=MagicMock(return_value=True),
        )
        effect = SimpleNamespace(
            this=upgrade,
            context=SimpleNamespace(bind_message=None),
        )
        process = MagicMock()
        ability = AbilityFactory.WhileValid(
            OnEvent.AssetEffect(),
            lambda effect, message: True,
            lambda effect, last_value: 1,
            process,
            preserve_value_on_same_card_flip=True,
        )

        ability.operation(effect, SimpleNamespace())

        process.assert_called_once_with(effect, 1, 1)
        upgrade.bind_face = new_face
        gain_ability = next(
            registered
            for registered in registrations[0]
            if registered.when is Message.AfterCardGainUpgradeAbility
        )

        should_update = gain_ability.conditions[-1](
            effect,
            SimpleNamespace(),
        )

        self.assertFalse(should_update)
        process.assert_called_once_with(effect, 1, 1)

        different_card = Card()
        upgrade.bind_face = Face(different_card)

        should_update = gain_ability.conditions[-1](
            effect,
            SimpleNamespace(),
        )

        self.assertTrue(should_update)
        gain_ability.operation(effect, SimpleNamespace())
        self.assertEqual(process.call_count, 2)
        process.assert_called_with(effect, 1, 1)

    def test_attached_health_modifier_preserves_same_card_value(self):
        sentinel = object()
        with patch.object(
            AbilityFactory,
            "WhileValid",
            return_value=sentinel,
        ) as while_valid:
            result = GiveKeywordToAttachWhenApplyThisInternal(
                "You",
                ignore_flip=True,
                health=4,
            )

        self.assertIs(result, sentinel)
        self.assertTrue(
            while_valid.call_args.kwargs[
                "preserve_value_on_same_card_flip"
            ]
        )

    def test_legacy_save_crc_is_migrated_once_for_attached_health_fix(self):
        operation = OperationDescriptor(crc="inflated-health-state")
        scene = Scene(inputs=[operation])

        scene.MigrateAttachedHealthFlip()

        self.assertEqual(operation.crc, "")
        self.assertIn(ATTACHED_HEALTH_FLIP_RULE, scene.rules)

        operation.crc = "corrected-health-state"
        scene.MigrateAttachedHealthFlip()
        self.assertEqual(operation.crc, "corrected-health-state")


if __name__ == "__main__":
    unittest.main()
