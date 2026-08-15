from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability import AbilityType, TimingPriority
from game.card.face.attribute.can_defense import CanDefense
from game.effect.effect_invoke import EffectInvoker
from game.message import Message


shadowcat_forms = import_module("cards.pack.mut_gen.shadowcat")
solid = import_module("cards.pack.mut_gen.shadowcat.32031a")
phased = import_module("cards.pack.mut_gen.shadowcat.32031b")
powerful_punch = import_module("cards.pack.mut_gen.32014")
toe_to_toe = import_module("cards.pack.hlk.10015")


class TestShadowcatFormTiming(unittest.TestCase):

    @staticmethod
    def mass_form_response(module):
        return next(
            ability
            for ability in module.GetAbilities()
            if isinstance(
                object.__new__(Message.AfterUnitAttackEnd),
                ability.when,
            )
        )

    def resolve_mass_form_window(self, current_form, completion_message):
        module = phased if current_form == "Phased" else solid
        ability = self.mass_form_response(module)
        effect = MagicMock()
        scheduled_callbacks = []

        with patch.object(
            shadowcat_forms.RunAt,
            "AfterEventEnd",
            side_effect=lambda effect, message, callback: scheduled_callbacks.append(
                callback
            ),
        ):
            ability.operation(effect, completion_message)

        self.assertEqual(len(scheduled_callbacks), 1)
        effect.GetInitiator.return_value.form.ChangeMassForm.assert_not_called()
        scheduled_callbacks[0]()
        change_form = effect.GetInitiator.return_value.form.ChangeMassForm
        next_form = change_form.call_args.kwargs["name"]
        return next_form, not ability.flags.is_forced

    def test_both_mass_forms_listen_to_attack_and_defense_completion(self):
        attack_end = object.__new__(Message.AfterUnitAttackEnd)
        defend_end = object.__new__(Message.AfterUnitDefendEnd)

        for module in (solid, phased):
            with self.subTest(module=module.__name__):
                ability = self.mass_form_response(module)
                self.assertIsInstance(attack_end, ability.when)
                self.assertIsInstance(defend_end, ability.when)

    def test_phased_flip_is_forced_but_solid_flip_is_optional(self):
        phased_response = self.mass_form_response(phased)
        solid_response = self.mass_form_response(solid)

        self.assertEqual(phased_response.type, AbilityType.ForcedResponse)
        self.assertEqual(phased_response.priority, TimingPriority.ForcedResponse)
        self.assertTrue(phased_response.flags.is_forced)

        self.assertEqual(solid_response.type, AbilityType.Response)
        self.assertEqual(solid_response.priority, TimingPriority.Response)
        self.assertFalse(solid_response.flags.is_forced)

    def test_form_change_waits_until_end_of_its_completion_window(self):
        effect = MagicMock()
        effect.this.CastTo.return_value = MagicMock()
        initiator = effect.GetInitiator.return_value
        completion_message = object()

        with patch.object(shadowcat_forms.RunAt, "AfterEventEnd") as after_event_end:
            shadowcat_forms.FlipSolidPhased(
                effect,
                completion_message,
                "Solid",
            )

        initiator.form.ChangeMassForm.assert_not_called()
        after_event_end.assert_called_once()
        scheduled_effect, scheduled_message, callback = after_event_end.call_args.args
        self.assertIs(scheduled_effect, effect)
        self.assertIs(scheduled_message, completion_message)

        callback()

        initiator.form.ChangeMassForm.assert_called_once_with(
            effect,
            name="Solid",
        )

    def test_powerful_punch_is_both_an_attack_and_a_defense(self):
        ability = powerful_punch.GetAbilities()[0]

        self.assertEqual(ability.type, AbilityType.HeroInterrupt)
        self.assertEqual(ability.labels, ["attack", "defense"])
        self.assertTrue(ability.is_like_attack)
        self.assertTrue(ability.is_like_defense)

    def test_powerful_punch_flips_and_flips_back_from_either_form(self):
        windows = (
            ("Powerful Punch attack ends", object.__new__(Message.AfterUnitAttackEnd)),
            ("Shadowcat defense ends", object.__new__(Message.AfterUnitDefendEnd)),
        )

        for starting_form in ("Phased", "Solid"):
            with self.subTest(starting_form=starting_form):
                current_form = starting_form
                prompt_windows = []
                for window_name, message in windows:
                    current_form, prompts_player = self.resolve_mass_form_window(
                        current_form,
                        message,
                    )
                    if prompts_player:
                        prompt_windows.append(window_name)

                self.assertEqual(current_form, starting_form)
                expected_prompt = windows[1 if starting_form == "Phased" else 0][0]
                self.assertEqual(prompt_windows, [expected_prompt])

    def test_defense_is_established_before_powerful_punch_resolves(self):
        class FakePlayer:
            def __init__(self, defender):
                self.defender = defender

            def GetIdentity(self):
                return self.defender

        order = []
        defender = MagicMock()
        defender.SpecialDefense.side_effect = lambda message, effect: order.append(
            "establish defense"
        )
        player = FakePlayer(defender)
        ability = powerful_punch.GetAbilities()[0]
        effect = MagicMock()
        effect.ability = ability
        effect.initiator = player
        effect.world = MagicMock()
        effect.this = MagicMock()
        effect.this.GetControlBy.return_value = player
        effect.GetInitiator.return_value = player
        effect.ProcessSelfCost.return_value = True
        effect.is_unregister_after_exec = False
        effect.cost_func.GetAll.return_value = []
        engine_game = MagicMock()

        message = object.__new__(Message.WhenUnitWouldAttack)
        message.send_resolve_message = False

        with patch("game.player.Player", FakePlayer), \
            patch.object(CanDefense, "IsType", return_value=True), \
            patch("game.effect.effect_invoke.Build.release", True), \
            patch.object(Engine, "game", engine_game, create=True), \
            patch.object(
                EffectInvoker,
                "InvokeOperation",
                side_effect=lambda effect, message: order.append(
                    "resolve Powerful Punch attack"
                ),
            ):
            resolved = EffectInvoker.ResolveSelfInternal(
                effect,
                message,
                None,
                effect,
            )

        self.assertTrue(resolved)
        self.assertEqual(
            order,
            ["establish defense", "resolve Powerful Punch attack"],
        )

    def test_toe_to_toe_finishes_enemy_attack_before_its_attack_damage(self):
        order = []
        player = object()
        enemy = MagicMock()
        enemy.CastTo.return_value = enemy
        enemy.DoAttackYou.side_effect = lambda initiator, effect: order.append(
            "enemy attack and defense completion"
        )
        event = MagicMock()
        event.DealDamage.side_effect = lambda targets, damage, effect: order.append(
            "Toe to Toe attack completion"
        )
        effect = MagicMock()
        effect.this.CastTo.return_value = event
        effect.GetInitiator.return_value = player
        effect.targets = [enemy]

        ability = toe_to_toe.GetAbilities()[0]
        ability.operation(effect, SimpleNamespace())

        self.assertEqual(ability.labels, ["attack"])
        self.assertEqual(
            order,
            [
                "enemy attack and defense completion",
                "Toe to Toe attack completion",
            ],
        )
        enemy.DoAttackYou.assert_called_once_with(player, effect)
        event.DealDamage.assert_called_once_with([enemy], 5, effect)

    def test_toe_to_toe_flips_and_flips_back_from_either_form(self):
        windows = (
            ("Shadowcat defense ends", object.__new__(Message.AfterUnitDefendEnd)),
            ("Toe to Toe attack ends", object.__new__(Message.AfterUnitAttackEnd)),
        )

        for starting_form in ("Phased", "Solid"):
            with self.subTest(starting_form=starting_form):
                current_form = starting_form
                prompt_windows = []
                for window_name, message in windows:
                    current_form, prompts_player = self.resolve_mass_form_window(
                        current_form,
                        message,
                    )
                    if prompts_player:
                        prompt_windows.append(window_name)

                self.assertEqual(current_form, starting_form)
                expected_prompt = windows[1 if starting_form == "Phased" else 0][0]
                self.assertEqual(prompt_windows, [expected_prompt])


if __name__ == "__main__":
    unittest.main()
