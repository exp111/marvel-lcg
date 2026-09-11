import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from engine.log import Log, Notify
from game.message import Message
from game.operate.worlds import Worlds
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)
from game.world.world_render import WorldRender


FIXTURE = Path(__file__).parent / "fixtures" / "issue_97_deadly_sai.json"


class TestDeadlySai(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def run_replay(self, devices):
        scene = validate_file(FIXTURE)
        attacks = []
        original_send = Message.AfterUnitAttackUnit.Send

        def after_attack(message, *args, **kwargs):
            if message.attacker.paper.card_id == "60065":
                attack = message.would_atk_unit_message
                attacks.append({
                    "attack": message.attacker.attack,
                    "damage": message.taken_damage,
                    "boost_cards": [face.paper.card_id for face in message.boost_faces],
                    "ranged": attack.IsRanged(),
                    "piercing": attack.IsPiercing(),
                })
            return original_send(message, *args, **kwargs)

        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch.object(Message.AfterUnitAttackUnit, "Send", new=after_attack),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Notify, "Game") as notices,
        ):
            game = run_scene_with_devices(scene, devices, load_type="InTesting")

        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(
            [operation.crc for operation in game.controller_manager.replay.history_inputs[:12]],
            [operation.crc for operation in scene.inputs],
        )
        return game, attacks

    def test_reported_save_counts_only_printed_boost_icons_plus_bullseyes_bonus(self):
        devices = HeadlessDeviceManager(stop_when=lambda prompt: True)
        game, attacks = self.run_replay(devices)

        self.assertEqual(attacks, [{
            "attack": 4,  # 1 base ATK + 2 printed boost icons + Bullseye's 1.
            "damage": 1,  # Daredevil defended with 3 DEF.
            "boost_cards": ["60070"],
            "ranged": True,
            "piercing": False,
        }])
        villain = Worlds.GetAllVillains(game.world)[0]
        self.assertEqual(villain.attack, 1)
        sai = villain.encounter_discard_pile.FindCard(name="60070")
        self.assertIsNotNone(sai)
        self.assertIsNone(sai.bind_face)
        self.assertEqual(game.controller_manager.replay.current_step_id, 12)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")

    def test_revealed_sai_still_attaches_and_modifies_attack_and_keywords(self):
        commands = iter((
            'Reveal("Deadly Sai")',
            'puzzle.CreateEncounterDeck("01186")',  # Advance has no printed boost icons.
            'DoAttack("Bullseye")',
        ))

        def choose(prompt):
            if prompt.event_name == "WhenPlayerInTurn":
                command = next(commands, None)
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, Engine.game.world)
                return CommandDescriptor()
            if prompt.show_cancel:
                return CommandDescriptor()  # Leave the follow-up attack undefended.
            return HeadlessDeviceManager._DefaultChoice(prompt)

        game, attacks = self.run_replay(HeadlessDeviceManager(choice_provider=choose))

        self.assertEqual(len(attacks), 2)
        self.assertEqual(attacks[1], {
            "attack": 4,  # 1 base + 2 attached Sai + Bullseye's 1.
            "damage": 4,
            "boost_cards": ["01186"],
            "ranged": False,
            "piercing": True,
        })
        villain = Worlds.GetAllVillains(game.world)[0]
        sai = game.world.FindCardsOnField(name="Deadly Sai")[0]
        self.assertIs(sai.bind_face, villain)
        self.assertEqual(villain.attack, 3)


if __name__ == "__main__":
    unittest.main()
