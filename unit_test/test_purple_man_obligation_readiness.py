from pathlib import Path
import unittest

from engine import Engine  # noqa: F401 - establishes project import order
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)


SAVE = Path(__file__).parent / "fixtures" / "issue117_purple_man.json"
COMMAND_IDS = {"60105", "60106", "60107"}


class TestPurpleManObligationReadiness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def play_to_round(self, stop_round, *, resolve_last_turn=False, legacy=False):
        # The reported save contains the scenario and seed, with no recorded
        # turns. Place its three command cards, then use their real UI options.
        scene = validate_file(SAVE)
        if legacy:
            scene.rules.remove("v18_timing")
            scene.rules.append("no_v18_timing")
        commands = [
            'ChangeForm(c1, "Hero")',
            'puzzle.PutIntoPlay("60105")',
            'puzzle.PutIntoPlay("60106")',
            'puzzle.PutIntoPlay("60107")',
        ]
        command_index = 0
        prepared_rounds = {1}
        selections = []
        command_faces = {}

        def choose(prompt):
            nonlocal command_index
            if len(devices.prompts) > 200:
                return None
            if prompt.event_name == "WhenPlayerInTurn":
                world = Engine.game.world
                if command_index < len(commands):
                    Engine.game.controller_manager.console.SetCommand(
                        commands[command_index], world,
                    )
                    command_index += 1
                    return CommandDescriptor()
                if world.round_id == stop_round and not resolve_last_turn:
                    return None
                if world.round_id not in prepared_rounds:
                    # Keep villain damage and scheme progress from ending a
                    # three-turn test before the obligations spend their uses.
                    prepared_rounds.add(world.round_id)
                    Engine.game.controller_manager.console.SetCommand(
                        '(puzzle.Heal("45001a", 100), '
                        'puzzle.SetThreat("60128b", 0))', world,
                    )
                    return CommandDescriptor()
                for option in prompt.options:
                    card = world.object_manager.card_dict.get(option.get("bind_id"))
                    if card and card.face.paper.card_id in COMMAND_IDS:
                        command_faces[card.face.paper.card_id] = card.face
                        selections.append((world.round_id, card.face.paper.card_id))
                        return CommandDescriptor(
                            HeadlessDeviceManager._DescriptorId(option),
                        )
                if world.round_id == stop_round:
                    return None
                return CommandDescriptor()
            if prompt.show_cancel:
                return CommandDescriptor()
            return HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        game = run_scene_with_devices(scene, devices, load_type="InTesting")
        self.assertEqual(command_index, len(commands))
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.round_id, stop_round)
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game, selections, command_faces

    def test_all_three_commands_ready_before_the_next_player_turn(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                game, selections, command_faces = self.play_to_round(2, legacy=legacy)
                self.assertEqual(selections, [(1, card_id) for card_id in sorted(COMMAND_IDS)])
                self.assertEqual(set(command_faces), COMMAND_IDS)
                player = game.world.const_players[0]
                self.assertEqual(len(player.obligations_area.Get()), 3)
                for face in command_faces.values():
                    self.assertTrue(face.card.IsReady(), face.name)
                    self.assertEqual(face.GetCounters("command"), 2)
                    self.assertNotIn(face, player.GetControlCards())

    def test_commands_resolve_once_each_turn_and_discard_after_three_uses(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                game, selections, command_faces = self.play_to_round(
                    3, resolve_last_turn=True, legacy=legacy,
                )
                self.assertEqual(selections, [
                    (round_id, card_id)
                    for round_id in (1, 2, 3)
                    for card_id in sorted(COMMAND_IDS)
                ])
                self.assertEqual(game.world.const_players[0].obligations_area.Get(), [])
                discarded = game.world.scenario.encounter_discard_pile.Get()
                for face in command_faces.values():
                    self.assertEqual(face.GetCounters("command"), 0)
                    self.assertFalse(face.IsInPlay())
                    self.assertIn(face, discarded)

    def test_end_phase_readies_only_that_players_cards_and_obligations(self):
        scene = SceneLoader.NewScene("rhino", None, ["bishop", "spider_man"], 117)
        commands = [
            'puzzle.PutIntoPlay("60107")',
            'CardFactory.GenerateCard("60106", world.aside_deck, world).face.PutIntoPlay('
            'p1, DebugRule(p1.GetIdentity()))',
            'puzzle.PutIntoPlayFor(0, "01091")',
            'puzzle.PutIntoPlay("02048")',
            'puzzle.Exhaust("60107", "60106", "01091", "02048", "45001b", "01001b")',
            'p.phase.EndPhase()',
        ]
        command_index = 0

        def choose(prompt):
            nonlocal command_index
            if prompt.event_name == "WhenPlayerInTurn":
                if command_index == len(commands):
                    return None
                Engine.game.controller_manager.console.SetCommand(
                    commands[command_index], Engine.game.world,
                )
                command_index += 1
                return CommandDescriptor()
            if prompt.show_cancel:
                return CommandDescriptor()
            return HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        game = run_scene_with_devices(scene, devices)
        self.assertEqual(command_index, len(commands))
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        bishop, spider_man = game.world.const_players
        self.assertTrue(bishop.obligations_area.Get()[0].card.IsReady())
        self.assertFalse(spider_man.obligations_area.Get()[0].card.IsReady())
        self.assertTrue(bishop.supports.Get()[0].card.IsReady())
        self.assertTrue(bishop.GetIdentity().GetInventoryDeck().Get()[0].card.IsReady())
        # All Tied Up still prevents Bishop's identity from readying; the
        # other player's identity waits for that player's end-phase step.
        self.assertFalse(bishop.GetIdentity().card.IsReady())
        self.assertFalse(spider_man.GetIdentity().card.IsReady())


if __name__ == "__main__":
    unittest.main()
