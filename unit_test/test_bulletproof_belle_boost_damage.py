import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log
from game.message import Message
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)
from game.world.world_render import WorldRender


SAVE = Path(__file__).parent / "fixtures" / "issue119_bulletproof_belle.json"


class TestBulletproofBelleBoostDamage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Specialized Training's linked cards must retain the saved object IDs
        # even when another test initialized the database earlier in the run.
        linked_cards = patch.object(CardsDB, "linked_papers", {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    def play_saved_attack(self, *, remove_whirlwind=False):
        damage = []
        prevented = []
        attacks = []
        starting_state = []
        recording = False
        would_take_damage = Message.WhenUnitWouldTakeDamage.Send
        after_prevented = Message.AfterDamageBePrevented.Send
        attack_end = Message.AfterUnitAttackEnd.Send

        def record_damage(message):
            result = would_take_damage(message)
            if recording and message.trigger.paper.card_id == "38001a":
                damage.append((
                    message.source.paper.card_id,
                    message.IsFromAttack(),
                    message.property.damage,
                    message.total_prevent_damage,
                    message.is_be_instead,
                ))
            return result

        def record_prevention(message):
            if recording and message.prevent_by_effect.this.paper.card_id == "38008":
                prevented.append((
                    message.would_atk_message.attacker.paper.card_id,
                    message.prevent_damage,
                ))
            return after_prevented(message)

        def record_attack_end(message):
            result = attack_end(message)
            if recording and message.attacker.paper.card_id in {"01113", "01121"}:
                hero = message.world.const_players[0].GetIdentity()
                attacks.append((
                    message.attacker.paper.card_id,
                    [attack.taken_damage for attack in message.atk_messages],
                    hero.health,
                    hero.IsTough(),
                ))
            return result

        def choose(prompt):
            nonlocal recording
            if len(devices.prompts) > 30:
                return None
            if not recording:
                # The replay plays and pays for Bulletproof Belle, then stops
                # before Klaw's facedown boost cards turn faceup.
                hero = Engine.game.world.const_players[0].GetIdentity()
                starting_state.append((hero.health, hero.IsTough()))
                recording = True
                if remove_whirlwind:
                    # Compare the same saved attack with its star-ability boost
                    # card removed. Keep Klaw's other boost card and damage.
                    Engine.game.controller_manager.console.SetCommand(
                        'world.object_manager.card_dict[83].MoveToArea('
                        'world.aside_deck, DebugRule(hero))', Engine.game.world,
                    )
                    return CommandDescriptor()
            if prompt.event_name == "WhenPlayerInTurn":
                return None
            return (CommandDescriptor() if prompt.show_cancel
                    else HeadlessDeviceManager._DefaultChoice(prompt))

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(Message.WhenUnitWouldTakeDamage, "Send", record_damage),
            patch.object(Message.AfterDamageBePrevented, "Send", record_prevention),
            patch.object(Message.AfterUnitAttackEnd, "Send", record_attack_end),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(validate_file(SAVE), devices, load_type="InTesting")
        errors.assert_not_called()
        warnings.assert_not_called()
        self.assertEqual(starting_state, [(11, True)])
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.prompts[0].event_name, "WhenUnitBeingAttack")
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.round_id, 4)
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        self.assertEqual(prevented, [("01113", 1)])
        return game, damage, attacks

    def test_saved_boost_consumes_tough_but_klaws_attack_is_prevented(self):
        game, damage, attacks = self.play_saved_attack()
        # Boost damage is separate from attack damage. Tough stops Whirlwind,
        # Belle stops Klaw, then Weapons Runner deals its own attack damage.
        # Tough explicitly records the boost damage it prevents.
        self.assertEqual(damage, [
            ("01130", False, 1, 1, True),
            ("01113", True, 1, 1, False),
            ("01121", True, 1, 0, False),
        ])
        self.assertEqual(attacks, [
            ("01113", [0], 11, False),
            ("01121", [1], 10, False),
        ])
        self.assertEqual(game.world.const_players[0].GetIdentity().health, 10)

    def test_without_boost_damage_belle_keeps_tough_for_the_next_attack(self):
        game, damage, attacks = self.play_saved_attack(remove_whirlwind=True)
        self.assertEqual(damage, [
            ("01113", True, 1, 1, False),
            ("01121", True, 1, 1, True),
        ])
        self.assertEqual(attacks, [
            ("01113", [0], 11, True),
            ("01121", [0], 11, False),
        ])
        self.assertEqual(game.world.const_players[0].GetIdentity().health, 11)


if __name__ == "__main__":
    unittest.main()
