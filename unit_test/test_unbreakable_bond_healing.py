"""Issue #145: unrelated allies must not hide Unbreakable Bond's healing targets."""
import contextlib
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log, Notify
from game.operate.referential import Referential
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices, validate_file
from game.world.world_render import WorldRender
from unit_test.jj_luke_gameplay_helpers import Gameplay


def issue_145_scene():
    scene = validate_file(Path(__file__).parent / 'fixtures/issue_145.json')
    # Issue #144 now automatically readies the sole remaining legal character.
    # Remove only that redundant confirmation, preserving all other choices.
    obsolete = scene.inputs.pop(55)
    assert obsolete.effect.id == 'e1 Ready_a_character_you_control c1 62001a'
    assert obsolete.effect.targets == ['c1 62001a']
    for index, operation in enumerate(scene.inputs):
        operation.step = index
    return scene


class TestUnbreakableBondHealing(Gameplay, unittest.TestCase):
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
        pass

    def test_reported_save_offers_three_healing_and_resolves_the_allocation(self):
        scene = issue_145_scene()
        healing_prompts = []

        def choose(prompt):
            options = [o for o in prompt.options if o['name'] == 'Distribute_3_healing']
            if not options:
                return None
            healing_prompts.append(options[0])
            command = self.descriptor(options[0])
            command.targets = ['1', '8', '8']
            return command

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (contextlib.redirect_stdout(io.StringIO()),
              patch('game.test.v18_timing_harness.initialize_database'),
              patch.object(WorldRender, 'ErrorOccurred') as errors,
              patch.object(Log, 'Warn') as warnings, patch.object(Notify, 'Game') as notices):
            game = run_scene_with_devices(scene, devices, load_type='InTesting')
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual([entry.crc for entry in game.controller_manager.replay.history_inputs[:62]],
                         [entry.crc for entry in scene.inputs])
        self.assertEqual(len(healing_prompts), 1)
        self.assertEqual(healing_prompts[0]['target_num_range'], [3, 3])
        self.assertCountEqual(healing_prompts[0]['all_legal_targets'], [1, 1, 1, 8, 8])
        self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        cards = game.world.object_manager.card_dict
        self.assertEqual(cards[1].face.health, 7)
        self.assertEqual(cards[8].face.health, 3)
        self.assertEqual(cards[23].face.health, 1)
        self.assertEqual(cards[48].face.threat, 0)

    def split_healing(self, prompt):
        options = [o for o in prompt.options if o['name'] == 'Distribute_3_healing']
        if not options:
            return NotImplemented
        option = options[0]
        hero = self.descriptor(option, '62001a').targets[0]
        ally = self.descriptor(option, '62002').targets[0]
        command = self.descriptor(option)
        command.targets = [hero, hero, ally]
        return command

    def test_both_printings_heal_with_an_unrelated_healthy_or_damaged_ally(self):
        for cid in ('61027', '62024'):
            for damage in (0, 1):
                with self.subTest(card=cid, unrelated_ally_damage=damage):
                    result = self.play([
                        'puzzle.ChangeFormFor(0,"Hero")',
                        'puzzle.PutIntoPlay("62002")', 'puzzle.PutIntoPlay("62012")',
                        'puzzle.Damage(hero,4)', 'puzzle.Damage("62002",2)',
                        f'puzzle.Damage("62012",{damage})', 'puzzle.SetThreat("01097b",5)',
                        *self.hand(cid, '01088'), self.use(cid),
                    ], choose_other=self.split_healing)[-1]
                    self.assertEqual(result['health'], 8)
                    self.assertEqual(self.face(result, '62002')['hp'], 2)
                    self.assertEqual(self.face(result, '62012')['hp'], 3 - damage)
                    self.assertEqual(result['main_threat'], 2)

    def test_unrelated_ally_does_not_block_play_when_only_healing_can_resolve(self):
        result = self.play([
            'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("62002")', 'puzzle.PutIntoPlay("62012")',
            'puzzle.Damage(hero,4)', 'puzzle.SetThreat("01097b",0)',
            *self.hand('62024', '01088'), self.use('62024'),
        ])[-1]
        self.assertEqual(result['health'], 9)
        self.assertEqual(result['main_threat'], 0)

    def test_identity_specific_references_keep_priority_over_other_printings(self):
        def face(cid):
            return SimpleNamespace(paper=CardsDB.FindCardPaper(cid),
                                   card=SimpleNamespace(IsAsOtherCard=lambda: False))

        hero, other_ally = face('62001a'), face('61003')
        candidates = [other_ally, hero]
        # A Luke identity card still refers to its own Luke Cage. A basic
        # card's empty set name cannot make unrelated basic cards a set.
        self.assertEqual(Referential.BelongToSameIdentityEncounterSet(
            ['Luke Cage'], face('62003'), candidates), [hero])
        self.assertEqual(Referential.BelongToSameIdentityEncounterSet(
            ['Luke Cage'], face('62024'), candidates), candidates)


if __name__ == '__main__':
    unittest.main()
