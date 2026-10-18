"""Issue #142: Bodega affects local attackers, never the shared villain.

Fear No Evil's Separate Main Schemes rules (p. 13) explicitly exclude the
villain from every player's play area, even when it attacks that player.
"""
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


class TestBattleInTheBodega(Gameplay, unittest.TestCase):
    pack = 'luke_cage'

    @classmethod
    def setUpClass(cls):
        database = contextlib.ExitStack()
        cls.addClassCleanup(database.close)
        # Keep the original replay's IDs stable even after other test suites
        # initialize the card catalog (which appends linked reward cards).
        for name in ('papers', 'sets_cards', 'linked_papers', 'ability_cache',
                     'ability_link_cards', 'full_link_cards'):
            database.enter_context(patch.object(CardsDB, name, {}))
        initialize_database()

    @classmethod
    def tearDownClass(cls):
        pass  # The class cleanup restores the isolated catalog.

    @staticmethod
    def bodega_scene(scene, *, expert=True, multiplayer=False):
        scene.campaign.expert = expert
        scene.campaign.schemes = ['60134a,60134b']
        if multiplayer:
            Gameplay.two_players(scene)
            scene.campaign.schemes.append('60135a,60135b')

    def play_bodega(self, commands, *, expert=True, multiplayer=False):
        return self.play(commands, configure_scene=lambda scene:
                         self.bodega_scene(scene, expert=expert, multiplayer=multiplayer))

    def test_original_save_replays_without_a_missing_villain_response(self):
        scene = validate_file(Path(__file__).parent / 'fixtures/issue_142.json')
        devices = HeadlessDeviceManager(stop_when=lambda prompt: True)
        with (contextlib.redirect_stdout(io.StringIO()),
              patch('game.test.v18_timing_harness.initialize_database'),
              patch.object(WorldRender, 'ErrorOccurred') as errors,
              patch.object(Log, 'Warn') as warnings, patch.object(Notify, 'Game') as notices):
            game = run_scene_with_devices(scene, devices, load_type='InTesting')
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(game.controller_manager.replay.current_step_id, 12)
        self.assertEqual([entry.crc for entry in game.controller_manager.replay.history_inputs],
                         [entry.crc for entry in scene.inputs])
        self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        cards = game.world.object_manager.card_dict
        self.assertEqual((cards[54].face.paper.card_id, cards[54].face.threat), ('60134b', 2))
        self.assertEqual((cards[59].face.paper.card_id, cards[59].face.health), ('60087', 15))

    def test_villain_attack_does_not_damage_villain_or_add_threat(self):
        for expert in (False, True):
            with self.subTest(expert=expert):
                snapshots = self.play_bodega([
                    'puzzle.ChangeFormFor(0,"Hero")',
                    'puzzle.CreateEncounterDeck("01104")',
                    'puzzle.DoAttack("01094")',
                ], expert=expert)
                before, after = snapshots[-2:]
                self.assertLess(after['health'], before['health'])
                self.assertEqual(after['villain_health'], before['villain_health'])
                self.assertEqual(after['main_threat'], before['main_threat'])

    def test_hero_attack_damages_hero_and_places_threat(self):
        snapshots = self.play_bodega(['puzzle.ChangeFormFor(0,"Hero")',
                                    self.use('62001a', 'Attack', '01094')])
        before, after = snapshots[-2:]
        self.assertEqual(after['health'], before['health'] - 1)
        self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_ally_attack_takes_bodega_and_consequential_damage(self):
        snapshots = self.play_bodega(['puzzle.PutIntoPlay("62012")',
                                    self.use('62012', 'Attack', '01094')])
        before, after = snapshots[-2:]
        self.assertEqual(self.face(after, '62012')['hp'], self.face(before, '62012')['hp'] - 2)
        self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_engaged_minion_attack_damages_minion_and_places_threat(self):
        snapshots = self.play_bodega(['puzzle.ChangeFormFor(0,"Hero")',
                                    'puzzle.PutIntoPlay("01101")',
                                    'puzzle.DoAttack("01101")'])
        before, after = snapshots[-2:]
        self.assertEqual(self.face(after, '01101')['hp'], self.face(before, '01101')['hp'] - 1)
        self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_minion_in_another_play_area_does_not_trigger_bodega(self):
        snapshots = self.play_bodega([
            'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlayFor(1,"01101")',
            'puzzle.DoAttack("01101")',
        ], expert=False, multiplayer=True)
        before, after = snapshots[-2:]
        self.assertLess(after['health'], before['health'])
        self.assertEqual(self.face(after, '01101')['hp'], self.face(before, '01101')['hp'])
        self.assertEqual(after['main_threat'], before['main_threat'])

    def test_standard_once_per_phase_limit_and_expert_repeated_attacks(self):
        for expert, expected in ((False, 1), (True, 2)):
            with self.subTest(expert=expert):
                snapshots = self.play_bodega([
                    'puzzle.ChangeFormFor(0,"Hero")',
                    self.use('62001a', 'Attack', '01094'),
                    'puzzle.Ready(hero)',
                    self.use('62001a', 'Attack', '01094'),
                ], expert=expert)
                self.assertEqual(snapshots[-1]['main_threat'], expected)
                self.assertEqual(snapshots[-1]['health'], snapshots[0]['health'] - expected)


if __name__ == '__main__':
    unittest.main()
