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
from cards.database import CardsDB
from engine.log import Log, Notify
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


ROOT = Path(__file__).resolve().parents[1]


class TestOptionalDiscardAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        linked_cards = patch.object(CardsDB, 'linked_papers', {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    @staticmethod
    def command(option, targets=None):
        if targets is None:
            targets = option.get('automatic_targets') or option['all_legal_targets'][:option['target_num_range'][0]]
        return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option), [str(target) for target in targets])

    def run_action(self, hero, setup_commands, action_card, action_name, decide, *, legacy=False,
                   pay_card=None, before_action=None, scenario='rhino', debug_action=None):
        scene = SceneLoader.NewScene(scenario, None, [hero], 131)
        scene.rules = ['v16_all', 'no_v18_timing' if legacy else 'v18_timing']
        setup = iter(setup_commands)
        acted = []

        def choose(prompt):
            world = Engine.game.world
            if len(devices.prompts) > 40:
                return None
            if prompt.event_name == 'WhenPlayerInTurn':
                command = next(setup, None)
                if command:
                    Engine.game.controller_manager.console.SetCommand(command, world)
                    return CommandDescriptor()
                if acted:
                    return None
                if before_action:
                    before_action(world)
                if debug_action:
                    acted.append(debug_action)
                    Engine.game.controller_manager.console.SetCommand(debug_action, world)
                    return CommandDescriptor()
                option = next(option for option in prompt.options
                              if world.object_manager.card_dict[option['bind_id']].face.paper.card_id == action_card
                              and (action_name is None or option['name'] == action_name))
                acted.append(option)
                command = self.command(option)
                if pay_card:
                    entries = next(iter(option['target_payment'].values()))['payment']
                    payment_id = next(payment_id for entry in entries for payment_id in entry
                                      if world.object_manager.paying_effect_dict[int(payment_id)].this.paper.card_id == pay_card)
                    command.resources = [str(payment_id)]
                return command
            result = decide(prompt, world)
            if result is not None:
                return result
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch('game.test.v18_timing_harness.initialize_database'),
            patch.object(WorldRender, 'ErrorOccurred') as errors,
            patch.object(Log, 'Warn') as warnings,
            patch.object(Notify, 'Game') as notices,
            patch.object(Engine, 'SaveCrash'),
        ):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(len(acted), 1)
        self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game.world

    @staticmethod
    def fixture(prompt, world, *, optional_count=False):
        ids = {option['bind_id'] for option in prompt.options}
        ids.update(target for option in prompt.options for target in option['all_legal_targets'])
        cards = []
        for object_id in ids:
            card = world.object_manager.card_dict[object_id]
            rendered = card.Render()
            cards.append({'id': object_id, 'card_id': rendered.card_id, 'name': rendered.name,
                          'control_player': 0, 'card_type': rendered.card_type, 'info': rendered.info,
                          'effects': rendered.effects, 'resources': rendered.resources, 'traits': rendered.traits})
        return {'ask': {'options_json': json.dumps(prompt.options), 'ability_type': prompt.ability_type,
                        'event_name': prompt.event_name, 'show_cancel': prompt.show_cancel},
                'cards': cards, 'optional_count': optional_count}

    def melinda_discard(self, accept, legacy=False):
        offers = []
        looked_at = []

        def decide(prompt, world):
            if prompt.event_name == 'WhenPlayerChooseAbility' and prompt.options[0]['name'] == 'Discard':
                offers.append(self.fixture(prompt, world, optional_count=True))
                looked_at.extend(prompt.options[0]['all_legal_targets'])
                return self.command(prompt.options[0], looked_at if accept else [])
            option = next((option for option in prompt.options
                           if world.object_manager.card_dict[option['bind_id']].face.paper.card_id == '50023'), None)
            return self.command(option) if option else None

        world = self.run_action('spider_man', [
            'ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)', 'puzzle.PutIntoPlay("50023")',
        ], '50023', 'Attack', decide, legacy=legacy)
        self.assertEqual(len(offers), 1)
        self.assertEqual(len(looked_at), 1)
        face = world.object_manager.card_dict[looked_at[0]].face
        self.assertEqual(face in world.GetScenario().encounter_discard_pile.Get(), accept)
        self.assertEqual(face in world.GetScenario().encounter_deck.Get(), not accept)
        return offers[0]

    def weapons_training(self, accept, legacy=False):
        offers = []

        def decide(prompt, world):
            option = next((option for option in prompt.options
                           if world.object_manager.card_dict[option['bind_id']].face.paper.card_id == '41011'), None)
            if option:
                offers.append(self.fixture(prompt, world))
                return self.command(option) if accept else CommandDescriptor()
            return None

        world = self.run_action('psylocke', [
            'ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)', 'puzzle.PutIntoPlay("41011")',
            'Faces.ExhaustAll(p.GetControlUpgrade(), DebugRule(c1))',
        ], '41001a', 'Attack', decide, legacy=legacy)
        self.assertEqual(len(offers), 1)
        weapons = [face for face in world.GetFirstPlayer().GetControlUpgrade() if face.HasTrait('WEAPON')]
        self.assertEqual(len(weapons), 2)
        self.assertTrue(all(face.IsExhaust() != accept for face in weapons))
        upgrade = next(card.face for card in world.object_manager.card_dict.values()
                       if card.face.paper.card_id == '41011')
        self.assertEqual(upgrade.IsInPlay(), not accept)
        self.assertEqual(upgrade in world.GetFirstPlayer().discard_pile.Get(), accept)
        return offers[0]

    def test_melinda_may_can_keep_or_discard_the_encounter_card(self):
        for legacy in (False, True):
            for accept in (False, True):
                with self.subTest(legacy=legacy, accept=accept):
                    fixture = self.melinda_discard(accept, legacy)
                    self.assertTrue(fixture['ask']['show_cancel'])
                    self.assertFalse(json.loads(fixture['ask']['options_json'])[0]['automatic_submit'])

    def test_weapons_training_is_kept_until_its_response_is_accepted(self):
        for legacy in (False, True):
            for accept in (False, True):
                with self.subTest(legacy=legacy, accept=accept):
                    self.weapons_training(accept, legacy)

    def test_optional_discards_wait_for_a_choice_in_the_real_client(self):
        node = shutil.which('node')
        compiler = shutil.which('tsc.cmd') or shutil.which('tsc')
        if not node or not compiler:
            self.skipTest('Node and TypeScript are required for the client regression')
        fixtures = [self.weapons_training(False), self.melinda_discard(False)]
        with tempfile.TemporaryDirectory(prefix='marvel-discard-audit-') as output:
            result = subprocess.run(
                [compiler, '-p', str(ROOT / 'public/js/tsconfig.json'), '--outDir', output],
                cwd=ROOT, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            fixture = Path(output) / 'prompts.json'
            fixture.write_text(json.dumps(fixtures), encoding='utf-8')
            result = subprocess.run(
                [node, str(ROOT / 'unit_test/optional_discard_audit_ui.cjs'), str(Path(output) / 'marvel'), str(fixture)],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_mobile_bunker_recipient_can_decline_before_drawing_or_discarding(self):
        for legacy in (False, True):
            for accept in (False, True):
                with self.subTest(legacy=legacy, accept=accept):
                    offers = []
                    discards = []
                    before = []

                    def decide(prompt, world):
                        if prompt.options[0]['name'] == 'Draw_2_cards,_then_discard_2_cards':
                            player = world.GetFirstPlayer()
                            offers.append((player.hand_cards.GetSize(), player.player_deck.GetSize()))
                            return self.command(prompt.options[0] if accept else prompt.options[-1])
                        if prompt.options[0]['name'] == 'Discard':
                            discards.append(prompt.options[0])
                            return self.command(prompt.options[0])
                        return None

                    def snapshot(world):
                        player = world.GetFirstPlayer()
                        before.append((player.hand_cards.GetSize(), player.player_deck.GetSize()))

                    world = self.run_action('nova', [
                        'ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)',
                        'puzzle.CreateHandCardsFor(0, "01088", "01089", "01090")',
                        'puzzle.PutIntoPlay("28020")',
                    ], '28020', None, decide, legacy=legacy, before_action=snapshot)
                    player = world.GetFirstPlayer()
                    self.assertEqual(offers, before)
                    self.assertEqual(player.hand_cards.GetSize(), 3)
                    self.assertEqual(player.player_deck.GetSize(), before[0][1] - (2 if accept else 0))
                    self.assertEqual(len(discards), int(accept))
                    if accept:
                        self.assertEqual(discards[0]['target_num_range'], [2, 2])

    def test_warlock_events_still_require_at_least_one_discard_to_pay_the_cost(self):
        for legacy in (False, True):
            for card_id in ('21038', '21039'):
                with self.subTest(legacy=legacy, card_id=card_id):
                    choices = []
                    before = []

                    def decide(prompt, world):
                        if all(option['name'].isdigit() for option in prompt.options):
                            choices.append([option['name'] for option in prompt.options])
                            return self.command(next(option for option in prompt.options if option['name'] == '1'))
                        return None

                    def snapshot(world):
                        before.append((world.GetFirstPlayer().player_deck.GetSize(),
                                       world.GetScenario().area_villain.Get()[0].health))

                    world = self.run_action('adam_warlock', [
                        'ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)',
                        f'puzzle.CreateHandCardsFor(0, "{card_id}", "01088")',
                        'puzzle.SetThreat("01097b", 6)',
                    ], card_id, 'Play', decide, legacy=legacy, pay_card='01088', before_action=snapshot)
                    self.assertEqual(choices, [['1', '2', '3', '4']])
                    self.assertEqual(world.GetFirstPlayer().player_deck.GetSize(), before[0][0] - 1)
                    if card_id == '21038':
                        self.assertIn(world.GetScenario().area_villain.Get()[0].health,
                                      (before[0][1] - 4, before[0][1] - 5))
                    else:
                        self.assertIn(world.area_schemes_main.Get()[0].threat, (2, 3))

    def test_goldballs_can_use_his_base_attack_or_choose_the_discard_bonus(self):
        for legacy in (False, True):
            for count in (0, 3):
                with self.subTest(legacy=legacy, count=count):
                    choices = []
                    before = []

                    def decide(prompt, world):
                        if all(option['name'].isdigit() for option in prompt.options):
                            choices.append([option['name'] for option in prompt.options])
                            return self.command(next(option for option in prompt.options if option['name'] == str(count)))
                        option = next((option for option in prompt.options
                                       if world.object_manager.card_dict[option['bind_id']].face.paper.card_id == '45041'), None)
                        return self.command(option) if option and count else None

                    def snapshot(world):
                        ally = next(face for face in world.GetFirstPlayer().GetControlAllies()
                                    if face.paper.card_id == '45041')
                        before.append((world.GetFirstPlayer().player_deck.GetSize(),
                                       world.GetScenario().area_villain.Get()[0].health, ally.attack))

                    world = self.run_action('spider_man', [
                        'ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)', 'puzzle.PutIntoPlay("45041")',
                    ], '45041', 'Attack', decide, legacy=legacy, before_action=snapshot)
                    self.assertEqual(choices, [['1', '2', '3']] if count else [])
                    self.assertEqual(world.GetFirstPlayer().player_deck.GetSize(), before[0][0] - count)
                    self.assertEqual(world.GetScenario().area_villain.Get()[0].health, before[0][1] - before[0][2] - count)

    def test_declining_stryfes_discard_still_places_the_required_threat(self):
        for legacy in (False, True):
            for accept in (False, True):
                with self.subTest(legacy=legacy, accept=accept):
                    discards = []

                    def decide(prompt, world):
                        if prompt.options[0]['name'] == 'Discard':
                            discards.append(prompt)
                            return self.command(prompt.options[0], prompt.options[0]['all_legal_targets'][:1]) \
                                if accept else CommandDescriptor()
                        return None

                    world = self.run_action('spider_man', [
                        'ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)',
                        'puzzle.CreateHandCardsFor(0, "01088", "01089", "01090")',
                        'puzzle.SetThreat("40166b", 0)',
                    ], None, None, decide, legacy=legacy, scenario='stryfe', debug_action=
                        'Message.AfterResolveVillainPhaseStep(1, Message.WhenVillainPhaseStepStart(1, world)).Send()')
                    self.assertEqual(len(discards), 1)
                    self.assertTrue(discards[0].show_cancel)
                    self.assertFalse(discards[0].options[0]['automatic_submit'])
                    self.assertEqual(world.GetFirstPlayer().hand_cards.GetSize(), 3 - int(accept))
                    scheme = next(face for face in world.area_schemes_main.Get() if face.paper.card_id == '40166b')
                    self.assertEqual(scheme.threat, 3 - int(accept))

    def test_magnetic_missile_can_take_the_damage_without_discarding(self):
        for legacy in (False, True):
            for accept in (False, True):
                with self.subTest(legacy=legacy, accept=accept):
                    discards = []
                    before = []

                    def decide(prompt, world):
                        if prompt.options[0]['name'] == 'Discard':
                            discards.append(prompt)
                            return self.command(prompt.options[0], prompt.options[0]['all_legal_targets']) \
                                if accept else CommandDescriptor()
                        return None

                    world = self.run_action('spider_man', [
                        'ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)',
                        'puzzle.CreateHandCardsFor(0, "01088", "01089", "01090")',
                        'puzzle.PutIntoPlay("32101")',
                    ], None, None, decide, legacy=legacy, debug_action='puzzle.Reveal("32155")',
                        before_action=lambda world: before.append(world.GetFirstPlayer().GetHero().health))
                    self.assertEqual(len(discards), 1)
                    self.assertTrue(discards[0].show_cancel)
                    self.assertFalse(discards[0].options[0]['automatic_submit'])
                    player = world.GetFirstPlayer()
                    self.assertEqual(player.hand_cards.GetSize(), 0 if accept else 3)
                    self.assertEqual(player.GetHero().health, before[0] - (2 if accept else 5))
                    sentinel = next(card.face for card in world.object_manager.card_dict.values()
                                    if card.face.paper.card_id == '32101')
                    self.assertFalse(sentinel.IsInPlay())


if __name__ == '__main__':
    unittest.main()
