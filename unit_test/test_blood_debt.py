from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability.factory.on_while import AbilityFactoryWhile


class TestBloodDebt(unittest.TestCase):

    def test_hunted_refreshes_after_the_attached_identity_changes_form(self):
        module = import_module("cards.pack.synthezoid.royal_guard.57072")
        marker_ability = MagicMock()

        with patch.object(
            module.AbilityFactory,
            "GiveKeywordToAttached",
            return_value=[marker_ability],
        ) as give_keyword:
            abilities = module.GetAbilities()

        self.assertIn(marker_ability, abilities)
        give_keyword.assert_called_once()
        self.assertIs(give_keyword.call_args.args[0], module.Identity)
        self.assertEqual(give_keyword.call_args.kwargs["trait"], "HUNTED")
        form_event = give_keyword.call_args.kwargs["ex_change_on_event"]
        self.assertIsInstance(form_event, module.OnEvent.Form)
        self.assertEqual(form_event.which_card, "AttachedIdentity")

    def test_while_valid_reapplies_when_the_bound_face_changes(self):
        captured = {}
        process = MagicMock()
        first_face = MagicMock(name="hero")
        second_face = MagicMock(name="alter_ego")
        shared_card = MagicMock()
        first_face.card = shared_card
        second_face.card = shared_card
        shared_card.state.is_leaving_play = False

        this = MagicMock()
        this.bind_face = first_face
        this.IsInPlay.return_value = True
        this.is_treat_as_if_blank = False
        this.card.state.is_leaving_play = False
        this.card.state.is_flipping = False
        effect = SimpleNamespace(
            this=this,
            context=SimpleNamespace(bind_message=None),
        )

        def capture_event_abilities(_event, _ability_type, condition, operation):
            captured["condition"] = condition
            captured["operation"] = operation
            return []

        with patch(
            "game.ability.factory.on_while.Condition.GetEventAbilities",
            side_effect=capture_event_abilities,
        ), patch(
            "game.ability.factory.AbilityFactory.WhileThisStateUpdate",
            return_value=MagicMock(),
        ):
            ability = AbilityFactoryWhile.WhileValid(
                MagicMock(),
                lambda effect, message: True,
                lambda effect, last_value: 1,
                process,
            )
            ability.operation(effect, MagicMock())

        process.assert_called_once_with(effect, 1, 1)

        this.bind_face = second_face
        message = MagicMock()
        self.assertTrue(captured["condition"](effect, message))
        captured["operation"](effect, message)

        self.assertEqual(process.call_count, 2)
        process.assert_called_with(effect, 1, 1)


if __name__ == "__main__":
    unittest.main()
