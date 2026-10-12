import contextlib
import io
import unittest
from unittest.mock import patch

from engine import Engine
from engine.log import Log, Notify
from game.message import Message
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


class TestFormChangeLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()

    def run_commands(self, identity, commands, *, scheme=None, timing='v18_timing',
                     expert=False, scenario='rhino', accept_form_responses=False,
                     expected_loss=False):
        scene = SceneLoader.NewScene(scenario, None, [identity], 106115)
        scene.rules = ['v16_all', timing]
        scene.campaign.expert = expert
        if scheme:
            scene.campaign.schemes = [scheme]
        commands = iter(commands)
        snapshots = []
        entries = []
        entry_send = Message.AfterCardEnterPlay.Send

        def after_entry(message):
            if snapshots:
                entries.append(message.trigger.paper.card_id)
            return entry_send(message)

        def choose(prompt):
            if len(devices.prompts) > 70:
                raise AssertionError('Unexpected repeated prompt')
            if prompt.event_name == 'WhenPlayerInTurn':
                world = Engine.game.world
                player = world.GetFirstPlayer()
                face = player.GetIdentity()
                snapshots.append({
                    'card': face.card,
                    'face': face.paper.card_id,
                    'health': face.health,
                    'max_health': face.max_health,
                    'stunned': face.IsStunned(),
                    'confused': face.IsConfused(),
                    'tough': face.IsTough(),
                    'exhausted': face.IsExhaust(),
                    'threat': world.area_schemes_main.Get()[0].threat,
                    'attack': getattr(face, 'attack', None),
                    'defense': getattr(face, 'defense', None),
                    'upgrades': sorted(upgrade.paper.card_id for upgrade in player.GetControlUpgrade()),
                    'tucked': sorted(card.paper.card_id for card in face.GetPlacedCardArea().Get()),
                    'counters': face.GetCounters('charge'),
                })
                command = next(commands, None)
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, world)
                return CommandDescriptor()
            if accept_form_responses and prompt.event_name == 'AfterUnitChangeForm':
                return HeadlessDeviceManager._DefaultChoice(prompt)
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch('game.test.v18_timing_harness.initialize_database'),
            patch.object(Message.AfterCardEnterPlay, 'Send', new=after_entry),
            patch.object(WorldRender, 'ErrorOccurred') as errors,
            patch.object(Log, 'Warn') as warnings,
            patch.object(Notify, 'Game') as notices,
            patch.object(Engine, 'SaveCrash'),
        ):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        if expected_loss:
            self.assertEqual(game.world.game_over.reason, 'Players Lost')
            self.assertFalse(game.world.game_over.players_won)
        else:
            self.assertIsNotNone(devices.stopped_prompt)
            self.assertEqual(devices.stopped_prompt.event_name, 'WhenPlayerInTurn')
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game.world, snapshots, entries

    def test_identity_form_changes_are_not_entries(self):
        for identity in ('captain_marvel', 'ant_man', 'wasp', 'vision', 'colossus', 'shadowcat', 'echo', 'daredevil'):
            with self.subTest(identity=identity):
                _, snapshots, entries = self.run_commands(identity, [
                    'puzzle.ChangeFormFor(0, "Hero")',
                    'puzzle.ChangeFormFor(0, "Identity")',
                ])
                self.assertEqual(entries, [])
                self.assertEqual(len(snapshots), 3)
                self.assertTrue(all(s['card'] is snapshots[0]['card'] for s in snapshots))

    def test_mass_form_does_not_trigger_pawn_shop_showdown(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            with self.subTest(timing=timing):
                _, snapshots, entries = self.run_commands('vision', [
                    'puzzle.Flip("26002a")',
                    'puzzle.Flip("26002b")',
                ], scheme='60137a,60137b', timing=timing)
                self.assertEqual([s['threat'] for s in snapshots], [snapshots[0]['threat']] * 3)
                self.assertEqual(entries, [])

    def test_actual_allies_and_minions_still_enter_play(self):
        _, _, entries = self.run_commands('captain_marvel', [
            'puzzle.PutIntoPlay("01067")',
            'puzzle.PutIntoPlay("01172")',
        ])
        self.assertEqual(entries, ['01067', '01172'])

    def test_form_changes_preserve_character_state_and_attached_health(self):
        setup = [
            'puzzle.PutIntoPlay("05023")',  # Endurance, +3 health
            'puzzle.PutIntoPlay("01081")',  # Armored Vest
            'puzzle.Damage(hero, 3)',
            'hero.GainStatus("Stunned", DebugRule(hero))',
            'hero.GainStatus("Confused", DebugRule(hero))',
            'hero.GainStatus("Tough", DebugRule(hero))',
            'puzzle.Exhaust(hero)',
            'hero.TuckCardUnderHere(puzzle.FindOrCreateFace("01089"), DebugRule(hero))',
            'puzzle.Counter(hero, "charge", 2)',
        ]
        for identity in ('captain_marvel', 'ant_man', 'wasp'):
            with self.subTest(identity=identity):
                _, snapshots, entries = self.run_commands(identity, setup + ['puzzle.Flip(hero)'] * 6)
                stable = snapshots[len(setup):]
                for state in stable:
                    for key in ('card', 'health', 'max_health', 'stunned', 'confused', 'tough',
                                'exhausted', 'upgrades', 'tucked', 'counters'):
                        self.assertEqual(state[key], stable[0][key], key)
                self.assertEqual(entries, ['05023', '01081'])

    def test_mass_form_modifiers_refresh_after_each_flip(self):
        _, snapshots, entries = self.run_commands('vision', [
            'puzzle.ChangeFormFor(0, "Hero")',
            'puzzle.Flip("26002a")',
            'puzzle.ChangeFormFor(0, "Identity")',
            'puzzle.ChangeFormFor(0, "Hero")',
            'puzzle.Flip("26002b")',
        ])
        self.assertEqual([(s['attack'], s['defense']) for s in snapshots[1:]],
                         [(0, 0), (2, 2), (None, None), (2, 2), (0, 0)])
        self.assertEqual(entries, [])

    def test_printed_form_change_response_still_resolves(self):
        _, snapshots, entries = self.run_commands('ant_man', [
            'puzzle.SetThreat("01097b", 3)',
            'puzzle.ChangeFormFor(0, "Hero")',
        ], accept_form_responses=True)
        self.assertEqual(snapshots[-1]['threat'], 2)
        self.assertEqual(entries, [])

    def test_setup_mode_flip_initializes_uses_once_on_final_face(self):
        for expert, incoming, expected_face, expected_counters in (
            (False, '27174b,27174a', '27174a', 2),
            (True, '27174a,27174b', '27174b', 3),
        ):
            with self.subTest(expert=expert):
                world, _, entries = self.run_commands('captain_marvel', [
                    f'puzzle.PutIntoPlay("{incoming}")',
                ], expert=expert)
                card = next(face for face in world.FindCardsOnField(name='Public Outcry'))
                self.assertEqual(card.paper.card_id, expected_face)
                self.assertEqual(card.GetCounters('notoriety'), expected_counters)
                self.assertEqual(entries, [expected_face])

    def test_later_flips_do_not_refill_uses(self):
        world, _, entries = self.run_commands('captain_marvel', [
            'puzzle.PutIntoPlay("27174a,27174b")',
            'puzzle.Counter("27174a", "notoriety", -1)',
            'puzzle.Flip("27174a")',
            'puzzle.Flip("27174b")',
        ])
        card = next(face for face in world.FindCardsOnField(name='Public Outcry'))
        self.assertEqual(card.GetCounters('notoriety'), 1)
        self.assertEqual(entries, ['27174a'])

    def test_collector_recovers_health_when_flipping_at_round_end(self):
        world, snapshots, entries = self.run_commands('captain_marvel', [
            'puzzle.Damage("16080a", 100)',
            'Message.WhenRoundEnd(world).Send()',
        ], scenario='escape_the_museum')
        collector = next(face for face in world.FindCardsOnField(name='Collector'))
        self.assertEqual(collector.paper.card_id, '16080a')
        self.assertEqual(collector.health, collector.printed_health)
        self.assertEqual(snapshots[-1]['threat'], snapshots[0]['threat'] - 3)
        self.assertEqual(entries, [])

    def test_campaign_environments_initialize_counters_when_earned(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            for card_id, counter in (('40190', 'assembly'), ('40191', 'safehouse'),
                                     ('40192', 'pouch'), ('40193', 'prep')):
                with self.subTest(timing=timing, card_id=card_id):
                    world, _, entries = self.run_commands('captain_marvel', [
                        f'puzzle.PutIntoPlay("{card_id}a,{card_id}b")',
                        f'hero.RemoveThreatFromSchemes([puzzle.FindOrCreateFace("{card_id}a")], '
                        '"All", DebugRule(hero))',
                    ], timing=timing)
                    environment = next(face for face in world.FindCardsOnField()
                                       if face.paper.card_id == card_id + 'b')
                    self.assertEqual(environment.GetCounters(counter), 1)
                    self.assertEqual(entries, [card_id + 'a'])

    def test_campaign_environments_initialize_counters_once_when_already_earned(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            for card_id, counter in (('40190', 'assembly'), ('40191', 'safehouse'),
                                     ('40192', 'pouch'), ('40193', 'prep')):
                with self.subTest(timing=timing, card_id=card_id):
                    world, _, entries = self.run_commands('captain_marvel', [
                        f'puzzle.PutIntoPlay("{card_id}b,{card_id}a")',
                    ], timing=timing)
                    environment = next(face for face in world.FindCardsOnField()
                                       if face.paper.card_id == card_id + 'b')
                    self.assertEqual(environment.GetCounters(counter), 1)
                    self.assertEqual(entries, [card_id + 'b'])

    def test_prepared_defenses_modifier_activates_after_campaign_scheme_flips(self):
        world, snapshots, entries = self.run_commands('captain_marvel', [
            'puzzle.ChangeFormFor(0, "Hero")',
            'puzzle.PutIntoPlay("40195a,40195b")',
            'hero.RemoveThreatFromSchemes([puzzle.FindOrCreateFace("40195a")], '
            '"All", DebugRule(hero))',
            'puzzle.ChangeFormFor(0, "Identity")',
            'puzzle.ChangeFormFor(0, "Hero")',
        ])
        self.assertEqual(snapshots[3]['defense'], snapshots[1]['defense'] + 1)
        self.assertEqual(snapshots[5]['defense'], snapshots[3]['defense'])
        self.assertEqual(world.GetFirstPlayer().GetIdentity().retaliate, 1)
        self.assertEqual(entries, ['40195a'])

    def test_spdr_swapping_identity_preserves_state_without_entries(self):
        setup = [
            'puzzle.PutIntoPlay("05023")',
            'puzzle.Damage(hero, 3)',
            'hero.GainStatus("Stunned", DebugRule(hero))',
            'hero.GainStatus("Confused", DebugRule(hero))',
            'hero.GainStatus("Tough", DebugRule(hero))',
            'puzzle.Counter(hero, "charge", 2)',
        ]
        for timing in ('v18_timing', 'no_v18_timing'):
            with self.subTest(timing=timing):
                _, snapshots, entries = self.run_commands('sp_dr', setup + [
                    'puzzle.ChangeFormFor(0, "Identity")',
                ] * 6, timing=timing)
                stable = snapshots[len(setup):]
                self.assertEqual([s['face'] for s in stable],
                                 ['31002a', '31001a', '31002a', '31001a',
                                  '31002a', '31001a', '31002a'])
                for state in stable:
                    for key in ('health', 'max_health', 'stunned', 'confused', 'tough', 'counters'):
                        self.assertEqual(state[key], stable[0][key], key)
                self.assertEqual(entries, ['05023'])

    def test_second_symbiote_environment_ends_venom_goblin_game(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            for first, second in (('27117', '27118'), ('27118', '27119'),
                                  ('27119', '27117')):
                with self.subTest(timing=timing, first=first, second=second):
                    world, snapshots, entries = self.run_commands('captain_marvel', [
                        f'hero.PlaceThreatOnSchemes([puzzle.FindOrCreateFace("{first}a")], '
                        '20, DebugRule(hero))',
                        f'hero.PlaceThreatOnSchemes([puzzle.FindOrCreateFace("{second}a")], '
                        '20, DebugRule(hero))',
                    ], scenario='venom_goblin', timing=timing, expected_loss=True)
                    self.assertEqual(len(snapshots), 2)
                    self.assertEqual(sorted(face.paper.card_id for face in world.FindCardsOnField()
                                            if face.HasTrait('SYMBIOTE') and face.paper.type == 'Environment'),
                                     sorted([first + 'b', second + 'b']))
                    self.assertEqual(entries, [])

    def test_black_swan_gets_toughness_when_scheme_flips_to_minion(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            with self.subTest(timing=timing):
                world, _, entries = self.run_commands('captain_marvel', [
                    'puzzle.PutIntoPlay("21182a,21182b")',
                    'hero.RemoveThreatFromSchemes([puzzle.FindOrCreateFace("21182a")], '
                    '"All", DebugRule(hero))',
                ], timing=timing)
                swan = world.FindCardsOnField(name='Black Swan')[0]
                self.assertIs(swan.GetEngagedPlayer(), world.GetFirstPlayer())
                self.assertTrue(swan.IsTough())
                self.assertEqual(entries, ['21182a'])

    def test_rescued_strong_inhuman_gets_toughness(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            with self.subTest(timing=timing):
                world, _, _ = self.run_commands('captain_marvel', [
                    'puzzle.Counter("Holding Cell", "lock", -2)',
                ] * 4, scenario='modok', timing=timing)
                allies = world.GetFirstPlayer().GetControlAllies()
                self.assertEqual(len(allies), 4)
                strong = next(ally for ally in allies if ally.paper.card_id == '50108b')
                self.assertEqual(strong.health, 7)
                self.assertTrue(strong.IsTough())

    def test_apocalypse_new_stage_gets_toughness_after_flip(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            with self.subTest(timing=timing):
                world, _, _ = self.run_commands('captain_marvel', [
                    'hero.PlaceThreatOnSchemes(world.area_schemes_main.Get(), 20, DebugRule(hero))',
                    'puzzle.Damage("Apocalypse", 1)',
                    'hero.PlaceThreatOnSchemes(world.area_schemes_main.Get(), 20, DebugRule(hero))',
                ], scenario='apocalypse', timing=timing)
                villain = world.scenario.area_villain.Get()[0]
                self.assertEqual(villain.paper.card_id, '45102b')
                self.assertTrue(villain.IsTough())


if __name__ == '__main__':
    unittest.main()
