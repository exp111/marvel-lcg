"""Issue #144: Harlem's Hero can ready only characters its player controls."""
import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log, Notify
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices, validate_file
from game.world.world_render import WorldRender
from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestHarlemsHeroTargets(Gameplay, unittest.TestCase):
    pack = 'luke_cage'

    @classmethod
    def setUpClass(cls):
        database = contextlib.ExitStack()
        cls.addClassCleanup(database.close)
        for name in ('papers', 'sets_cards', 'linked_papers', 'ability_cache',
                     'ability_link_cards', 'full_link_cards'):
            database.enter_context(patch.object(CardsDB, name, {}))
        initialize_database()

    @classmethod
    def tearDownClass(cls):
        pass  # The class cleanup restores the isolated catalog.

    def ready_options(self, prompt):
        return [option for option in prompt.options
                if option['name'] == 'Ready_a_character_you_control']

    def test_saved_position_only_offers_luke_and_jessica_and_finishes_legally(self):
        scene = validate_file(Path(__file__).parent / 'fixtures/issue_144.json')
        # The final two recorded choices include the illegal Power Man target.
        # Replay all earlier inputs unchanged, then make legal ready choices.
        scene.inputs = scene.inputs[:16]
        targets = []

        def choose(prompt):
            options = self.ready_options(prompt)
            if not options:
                return None
            targets.append(options[0]['all_legal_targets'])
            return HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (contextlib.redirect_stdout(io.StringIO()),
              patch('game.test.v18_timing_harness.initialize_database'),
              patch.object(WorldRender, 'ErrorOccurred') as errors,
              patch.object(Log, 'Warn') as warnings, patch.object(Notify, 'Game') as notices):
            game = run_scene_with_devices(scene, devices, load_type='InTesting')
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        history = game.controller_manager.replay.history_inputs
        self.assertEqual([entry.crc for entry in history[:16]], [entry.crc for entry in scene.inputs])
        # Once Luke is ready, Jessica is the only legal target and resolves
        # automatically without another prompt.
        self.assertEqual(targets, [[1, 8]])
        self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        cards = game.world.object_manager.card_dict
        self.assertFalse(cards[1].face.IsExhaust())
        self.assertFalse(cards[8].face.IsExhaust())
        self.assertTrue(cards[22].face.IsExhaust())
        self.assertEqual(cards[1].face.tough, 2)

    def test_excludes_upgrades_supports_enemies_and_other_players_characters(self):
        target_sets = []

        def choose(prompt):
            options = self.ready_options(prompt)
            if not options:
                return NotImplemented
            cards = Engine.game.world.object_manager.card_dict
            target_sets.append({cards[target].face.paper.card_id
                                for target in options[0]['all_legal_targets']})
            return self.descriptor(options[0])

        result = self.play([
            'puzzle.ChangeFormFor(0,"Hero")', *self.tough(1),
            'puzzle.PutIntoPlay("01083")', 'puzzle.PutIntoPlay("62011")',
            'puzzle.PutIntoPlay("62007")', 'puzzle.PutIntoPlay("01101")',
            'puzzle.PutIntoPlayFor(1,"62012")',
            'puzzle.Exhaust(hero,"01083","62011","62007","01101","62012","61001b")',
            *self.hand('62003', '01088'), self.use('62003'),
        ], configure_scene=self.two_players, choose_other=choose)[-1]
        self.assertEqual(target_sets, [{'62001a', '01083'}])
        self.assertFalse(result['exhausted'])
        self.assertFalse(self.face(result, '01083')['exhausted'])
        for cid in ('62011', '62007', '01101', '62012', '61001b'):
            self.assertTrue(self.face(result, cid)['exhausted'], cid)

    def test_extra_tough_does_not_spend_remaining_readies_on_upgrades(self):
        result = self.play([
            'puzzle.ChangeFormFor(0,"Hero")', *self.tough(2),
            'puzzle.PutIntoPlay("62011")', 'puzzle.Exhaust(hero,"62011")',
            *self.hand('62003', '01088'), self.use('62003'),
        ], choose_other=self.choices(names=('Ready a character',)))[-1]
        self.assertEqual(result['tough'], 3)
        self.assertFalse(result['exhausted'])
        self.assertTrue(self.face(result, '62011')['exhausted'])
        # The sole legal character readies automatically; surplus readies
        # have no target and must not produce an upgrade-only prompt.
        self.assertFalse(any(self.ready_options(p) for p in self.last_prompts))

    def test_all_ready_characters_still_gain_tough_without_readying_power_man(self):
        result = self.play([
            'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("62011")', 'puzzle.Exhaust("62011")',
            *self.hand('62003', '01088'), self.use('62003'),
        ], choose_other=self.choices(names=('Ready a character',)))[-1]
        self.assertEqual(result['tough'], 1)
        self.assertTrue(self.face(result, '62011')['exhausted'])
        self.assertFalse(any(self.ready_options(p) for p in self.last_prompts))


if __name__ == '__main__':
    unittest.main()
