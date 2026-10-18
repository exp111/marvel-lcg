"""Issue #142: Bodega checks the attacked character's area, then hurts the attacker.

The printed card says "is attacked", not "attacks". The villain is outside
all player areas, but heroes, allies, and engaged minions can be local targets.
"""
import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log, Notify
from game.scene.replay.operation import CommandDescriptor
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

    def play_bodega(self, commands, *, expert=True, multiplayer=False, **kwargs):
        return self.play(commands, configure_scene=lambda scene:
                         self.bodega_scene(scene, expert=expert, multiplayer=multiplayer), **kwargs)

    def test_original_save_hero_attack_does_not_trigger_bodega(self):
        scene = validate_file(Path(__file__).parent / 'fixtures/issue_142.json')
        # The old save's next attack was followed by an erroneous Bodega
        # response. Keep the valid setup and perform that attack under the fix.
        scene.inputs = scene.inputs[:4]
        attacked = False

        def choose(prompt):
            nonlocal attacked
            if prompt.event_name == 'WhenPlayerInTurn':
                if attacked:
                    return None
                option = next(o for o in prompt.options
                              if o['bind_id'] == 1 and o['name'] == 'Attack')
                attacked = True
                return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option), ['59'], [])
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
        self.assertEqual([entry.crc for entry in game.controller_manager.replay.history_inputs[:4]],
                         [entry.crc for entry in scene.inputs])
        self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        cards = game.world.object_manager.card_dict
        self.assertEqual(cards[1].face.health, 11)  # Only Hammerhead's Retaliate 1.
        self.assertEqual((cards[54].face.paper.card_id, cards[54].face.threat), ('60134b', 0))
        self.assertEqual((cards[59].face.paper.card_id, cards[59].face.health), ('60087', 15))

    def test_villain_attacking_local_hero_takes_damage_and_places_threat(self):
        for expert in (False, True):
            with self.subTest(expert=expert):
                snapshots = self.play_bodega([
                    'puzzle.ChangeFormFor(0,"Hero")',
                    'puzzle.CreateEncounterDeck("01104")',
                    'puzzle.DoAttack("01094")',
                ], expert=expert)
                before, after = snapshots[-2:]
                self.assertLess(after['health'], before['health'])
                self.assertEqual(after['villain_health'], before['villain_health'] - 1)
                self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_hero_attacking_villain_does_not_trigger_bodega(self):
        snapshots = self.play_bodega(['puzzle.ChangeFormFor(0,"Hero")',
                                    self.use('62001a', 'Attack', '01094')])
        before, after = snapshots[-2:]
        self.assertEqual(after['health'], before['health'])
        self.assertEqual(after['main_threat'], before['main_threat'])

    def test_ally_attacking_villain_takes_only_consequential_damage(self):
        snapshots = self.play_bodega(['puzzle.PutIntoPlay("62012")',
                                    self.use('62012', 'Attack', '01094')])
        before, after = snapshots[-2:]
        self.assertEqual(self.face(after, '62012')['hp'], self.face(before, '62012')['hp'] - 1)
        self.assertEqual(after['main_threat'], before['main_threat'])

    def test_randall_survives_attacking_hammerhead_with_retaliate(self):
        def configure(scene):
            self.bodega_scene(scene)
            scene.campaign.villain = ['60087', '60088']

        snapshots = self.play(['puzzle.PutIntoPlay("45003")',
                               self.use('45003', 'Attack', '60087')], configure_scene=configure)
        before, after = snapshots[-2:]
        self.assertEqual(self.face(after, '45003')['hp'], 1)  # Retaliate + consequential.
        self.assertEqual(after['main_threat'], before['main_threat'])

    def test_attacking_a_local_minion_damages_attacker_and_places_threat(self):
        snapshots = self.play_bodega(['puzzle.ChangeFormFor(0,"Hero")',
                                    'puzzle.PutIntoPlay("60140")',
                                    self.use('62001a', 'Attack', '60140')])
        before, after = snapshots[-2:]
        self.assertEqual(after['health'], before['health'] - 1)
        self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_attacking_another_players_minion_does_not_trigger_bodega(self):
        snapshots = self.play_bodega(['puzzle.ChangeFormFor(0,"Hero")',
                                    'puzzle.PutIntoPlayFor(1,"60140")',
                                    self.use('62001a', 'Attack', '60140')],
                                    expert=False, multiplayer=True)
        before, after = snapshots[-2:]
        self.assertEqual(after['health'], before['health'])
        self.assertEqual(after['main_threat'], before['main_threat'])

    def test_engaged_minion_attack_damages_minion_and_places_threat(self):
        snapshots = self.play_bodega(['puzzle.ChangeFormFor(0,"Hero")',
                                    'puzzle.PutIntoPlay("01101")',
                                    'puzzle.DoAttack("01101")'])
        before, after = snapshots[-2:]
        self.assertEqual(self.face(after, '01101')['hp'], self.face(before, '01101')['hp'] - 1)
        self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_minion_in_another_play_area_attacking_local_hero_triggers_bodega(self):
        snapshots = self.play_bodega([
            'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlayFor(1,"01101")',
            'puzzle.DoAttack("01101")',
        ], expert=False, multiplayer=True)
        before, after = snapshots[-2:]
        self.assertLess(after['health'], before['health'])
        self.assertEqual(self.face(after, '01101')['hp'], self.face(before, '01101')['hp'] - 1)
        self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_villain_attacking_another_players_hero_does_not_trigger_bodega(self):
        snapshots = self.play_bodega([
            'puzzle.ChangeFormFor(1,"Hero")',
            'puzzle.CreateEncounterDeck("01104")',
            'puzzle.FindOrCreateFace("01094").DoAttackYou(world.const_players[1],DebugRule(hero))',
        ], expert=False, multiplayer=True)
        before, after = snapshots[-2:]
        self.assertLess(after['players'][1]['hp'], before['players'][1]['hp'])
        self.assertEqual(after['villain_health'], before['villain_health'])
        self.assertEqual(after['main_threat'], before['main_threat'])

    def test_attack_against_local_ally_triggers_even_when_tough_prevents_damage(self):
        def defend(prompt):
            options = [o for o in prompt.options
                       if self.card_id(o) == '45003' and o['name'] == 'Defense']
            return self.descriptor(options[0]) if options else NotImplemented

        snapshots = self.play_bodega([
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("45003")',
            'puzzle.Tough("45003")', 'puzzle.CreateEncounterDeck("01104")',
            'puzzle.DoAttack("01094")',
        ], choose_other=defend)
        before, after = snapshots[-2:]
        self.assertEqual(self.face(after, '45003')['hp'], 3)
        self.assertEqual(self.face(after, '45003')['tough'], 0)
        self.assertEqual(after['health'], before['health'])
        self.assertEqual(after['villain_health'], before['villain_health'] - 1)
        self.assertEqual(after['main_threat'], before['main_threat'] + 1)

    def test_standard_once_per_phase_limit_and_expert_repeated_attacks(self):
        for expert, expected in ((False, 1), (True, 2)):
            with self.subTest(expert=expert):
                snapshots = self.play_bodega([
                    'puzzle.ChangeFormFor(0,"Hero")',
                    'puzzle.PutIntoPlay("60140")',
                    'puzzle.DoAttack("60140")',
                    'puzzle.DoAttack("60140")',
                ], expert=expert)
                self.assertEqual(snapshots[-1]['main_threat'], expected)
                self.assertEqual(self.face(snapshots[-1], '60140')['hp'], 6 - expected)


if __name__ == '__main__':
    unittest.main()
