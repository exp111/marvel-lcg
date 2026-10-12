import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from engine import Engine
from engine.log import Log, Notify
from game.effect.effect_invoke import EffectInvoker
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


ROOT = Path(__file__).resolve().parents[1]


class TestResponsePreselection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which('node')
        compiler = shutil.which('tsc.cmd') or shutil.which('tsc')
        if not cls.node or not compiler:
            raise unittest.SkipTest('Node and TypeScript are required for the client regression')
        cls.output = tempfile.TemporaryDirectory(prefix='marvel-response-selection-')
        cls.addClassCleanup(cls.output.cleanup)
        result = subprocess.run([compiler, '-p', str(ROOT / 'public/js/tsconfig.json'),
                                 '--outDir', cls.output.name], cwd=ROOT,
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        initialize_database()

    def run_client(self, fixture=None):
        command = [self.node, str(ROOT / 'unit_test/response_preselection_ui.cjs'),
                   str(Path(self.output.name) / 'marvel')]
        if fixture:
            path = Path(self.output.name) / 'prompt.json'
            path.write_text(json.dumps(fixture), encoding='utf-8')
            command.append(str(path))
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def run_response(self, *, forced, accept=True, legacy=False):
        scene = SceneLoader.NewScene('rhino', None, ['she_hulk' if forced else 'black_widow'], 133)
        scene.rules = ['v16_all', 'no_v18_timing' if legacy else 'v18_timing']
        setup = iter([
            'puzzle.ClearHand()',
            *(['puzzle.ChangeFormFor(0, "Hero")',
               'p.PlayCardsLikeInTurn([puzzle.FindOrCreateFace("01028")], '
               'DebugRule(hero), ignore_resources_cost=True)'] if forced else [
                'p.PlayCardsLikeInTurn([puzzle.FindOrCreateFace("08010")], '
                'DebugRule(hero), ignore_resources_cost=True)',
            ]),
        ])
        response_card = '01028' if forced else '08001b'
        attacked = False
        offers, invocations, hand_before = [], [], []
        invoke = EffectInvoker.InvokeOperation

        def record(effect, message):
            if effect.this.paper.card_id == response_card and effect.ability.flags.is_response:
                invocations.append(effect.object_id)
            return invoke(effect, message)

        def choose(prompt):
            nonlocal attacked
            self.assertLess(len(devices.prompts), 35)
            world = Engine.game.world
            if prompt.event_name == 'WhenPlayerInTurn':
                command = next(setup, None)
                if command:
                    Engine.game.controller_manager.console.SetCommand(command, world)
                    return CommandDescriptor()
                if forced and not attacked:
                    attacked = True
                    attack = next(option for option in prompt.options
                                  if option['name'] == 'Attack' and option['bind_id'] == 1)
                    return CommandDescriptor(HeadlessDeviceManager._DescriptorId(attack),
                                             [str(attack['all_legal_targets'][0])])
                return None
            if prompt.ability_type == ('ForcedResponse' if forced else 'Response') and any(
                world.object_manager.card_dict[option['bind_id']].face.paper.card_id == response_card
                for option in prompt.options
            ):
                offers.append(prompt)
                self.assertEqual(len(prompt.options), 1)
                self.assertFalse(prompt.options[0]['automatic_submit'])
                self.assertEqual(invocations, [], 'The response must not resolve before confirmation')
                hand_before.append(len(world.GetFirstPlayer().hand_cards.Get()))
                fixture = {
                    'ask': dict(options_json=json.dumps(prompt.options), ability_type=prompt.ability_type,
                                event_name=prompt.event_name, show_cancel=prompt.show_cancel),
                    'cards': [dict(id=card.object_id, card_id=card.face.paper.card_id,
                                   control_player=0, card_type=card.face.paper.type,
                                   effects=[option['id'] for option in prompt.options
                                            if option['bind_id'] == card.object_id], resources=[])
                              for card in world.object_manager.card_dict.values()],
                    'accept': accept,
                }
                # The actual compiled client must produce no request while
                # opening/re-rendering, then exactly one request on OK or Pass.
                posted = self.run_client(fixture)
                self.assertEqual(invocations, [])
                return CommandDescriptor(posted.get('id', ''),
                                         [str(x) for x in posted.get('targets', [])],
                                         [str(x) for x in posted.get('resources', [])])
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (contextlib.redirect_stdout(io.StringIO()),
              patch('game.test.v18_timing_harness.initialize_database'),
              patch.object(EffectInvoker, 'InvokeOperation', record),
              patch.object(WorldRender, 'ErrorOccurred') as errors,
              patch.object(Log, 'Warn') as warnings, patch.object(Notify, 'Game') as notices,
              patch.object(Engine, 'SaveCrash')):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(len(offers), 0 if forced else 1, [(p.event_name, p.ability_type,
                                         [o['name'] for o in p.options]) for p in devices.prompts])
        self.assertEqual(len(invocations), int(accept))
        self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        if forced:
            self.assertTrue(game.world.GetScenario().area_villain.Get()[0].IsStunned())
            self.assertFalse(any(card.paper.card_id == '01028'
                                 for card in game.world.GetFirstPlayer().GetControlUpgrade()))
        else:
            self.assertEqual(len(game.world.GetFirstPlayer().hand_cards.Get()), hand_before[0] + int(accept))

    def test_mission_prep_confirms_or_passes_in_both_timing_modes(self):
        for legacy in (False, True):
            for accept in (False, True):
                with self.subTest(legacy=legacy, accept=accept):
                    self.run_response(forced=False, accept=accept, legacy=legacy)

    def test_superhuman_strength_without_a_prompt_keeps_existing_resolution(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                self.run_response(forced=True, legacy=legacy)

    def test_client_selection_safety_matrix(self):
        self.assertEqual(self.run_client(), {'ok': True})

    def run_energy_conversion(self, *, resource_count, accept, full_search, legacy):
        scene = SceneLoader.NewScene('rhino', None, ['bishop'], 139)
        scene.rules = ['v16_all', 'no_v18_timing' if legacy else 'v18_timing']
        resources = ('01088', '01089', '01088')[:resource_count]
        commands = iter([
            'puzzle.ClearHand()',
            'Faces.RemoveAllFromGame(p.discard_pile.Get(), DebugRule(hero))',
            f'puzzle.CreateHandCards({", ".join(repr(card) for card in (*resources, "01070"))})',
            'puzzle.ClearHand()',
            'puzzle.CreateHandCards("45009")',
            'puzzle.ChangeFormFor(0, "Hero")',
            'puzzle.DoAttack("01094")',
        ])
        offers, resource_ids = [], []

        def choose(prompt):
            self.assertLess(len(devices.prompts), 35)
            world = Engine.game.world
            player = world.GetFirstPlayer()
            player.GetController().SetShowDeckDuringFullSearch(full_search)
            if prompt.event_name == 'WhenPlayerInTurn':
                command = next(commands, None)
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, world)
                return CommandDescriptor()
            if prompt.event_name == 'WhenUnitWouldAttack' and any(
                world.object_manager.card_dict[option['bind_id']].face.paper.card_id == '45009'
                for option in prompt.options
            ):
                offers.append(prompt)
                self.assertEqual(len(offers), 1)
                self.assertEqual(len(prompt.options), 1)
                resource_ids.extend(face.card.object_id for face in player.discard_pile.Get()
                                    if face.paper.card_id in resources)
                option = prompt.options[0]
                self.assertEqual(len(resource_ids), resource_count)
                self.assertCountEqual(option['all_legal_targets'], resource_ids)
                self.assertFalse(option['automatic_submit'])
                fixture = {
                    'ask': dict(options_json=json.dumps(prompt.options), ability_type=prompt.ability_type,
                                event_name=prompt.event_name, show_cancel=prompt.show_cancel),
                    'cards': [dict(id=card.object_id, card_id=card.face.paper.card_id,
                                   control_player=0, card_type=card.face.paper.type,
                                   effects=[option['id'] for option in prompt.options
                                            if option['bind_id'] == card.object_id], resources=[])
                              for card in world.object_manager.card_dict.values()],
                    'accept': accept, 'full_search': full_search,
                    'expected_targets': option['all_legal_targets'],
                }
                posted = self.run_client(fixture)
                # Opening the client and confirming/passing there has not yet
                # executed any game effect on the server.
                self.assertEqual([face.card.object_id for face in player.discard_pile.Get()
                                  if face.paper.card_id in resources], resource_ids)
                self.assertTrue(player.hand_cards.FindCard(name='45009'))
                return CommandDescriptor(posted.get('id', ''),
                                         [str(x) for x in posted.get('targets', [])],
                                         [str(x) for x in posted.get('resources', [])])
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (contextlib.redirect_stdout(io.StringIO()),
              patch('game.test.v18_timing_harness.initialize_database'),
              patch.object(WorldRender, 'ErrorOccurred') as errors,
              patch.object(Log, 'Warn') as warnings, patch.object(Notify, 'Game') as notices,
              patch.object(Engine, 'SaveCrash')):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(len(offers), 1)
        self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        player = game.world.GetFirstPlayer()
        for card_id in resource_ids:
            card = game.world.object_manager.card_dict[card_id]
            self.assertIs(card.area, player.player_deck if accept else player.discard_pile)
        self.assertTrue(player.discard_pile.FindCard(name='01070'))
        event_area = player.discard_pile if accept else player.hand_cards
        self.assertTrue(event_area.FindCard(name='45009'))

    def test_energy_conversion_preselects_all_resources_and_confirms_or_passes(self):
        for legacy in (False, True):
            for full_search in (False, True):
                for accept in (False, True):
                    for resource_count in (0, 1, 3):
                        with self.subTest(legacy=legacy, full_search=full_search,
                                          accept=accept, resource_count=resource_count):
                            self.run_energy_conversion(resource_count=resource_count, accept=accept,
                                                       full_search=full_search, legacy=legacy)


if __name__ == '__main__':
    unittest.main()
