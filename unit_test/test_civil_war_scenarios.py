"""Custom Civil War setup and printed main scheme behavior through the game engine."""
import contextlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from game.scene import SceneLoader
from game.test.v18_timing_harness import initialize_database
from unit_test.jj_luke_gameplay_helpers import Gameplay

ROOT = Path(__file__).resolve().parents[1]
LEADERS = ('iron_man', 'captain_marvel', 'captain_america', 'spider_woman', 'she_hulk', 'vision')

def preset(name):
    return json.loads((ROOT / 'data/scenarios' / (name + '.json')).read_text(encoding='utf-8'))


class TestCivilWarScenarios(Gameplay, unittest.TestCase):
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

    def observe(self, world, player, prompt):
        state = super().observe(world, player, prompt)
        for entry in state['field']:
            face = world.object_manager.card_dict[entry['id']].face
            entry.update(guard=getattr(face, 'guard', None), steady=getattr(face, 'steady', None),
                         target_threat=getattr(face, 'target_threat', None),
                         escalation=getattr(face, 'escalation_threat', None))
        for entry, seat in zip(state['players'], world.const_players):
            entry['deck_size'] = seat.player_deck.GetSize()
            entry['discard_size'] = seat.discard_pile.GetSize()
        return state

    def play_civil(self, leader, first, second, commands, *, players=1, **kwargs):
        def configure(scene):
            campaign = SceneLoader.NewScene(leader, None, ['luke_cage'], 125).campaign
            campaign.schemes = [f'{cid}a,{cid}b' for cid in (first, second)]
            scene.campaign = campaign
            if players > 1:
                scene.players.extend(SceneLoader.NewScene(
                    leader, [], ['jessica_jones', 'spider_man', 'captain_marvel'][:players-1], 125
                ).players)
        return self.play(commands, configure_scene=configure, **kwargs)

    @staticmethod
    def advance(first):
        return f'puzzle.FindOrCreateFace("{first}b").Advance(None,DebugRule(hero))'

    @staticmethod
    def end_step(step=1):
        return f'Message.AfterResolveVillainPhaseStep({step},Message.WhenVillainPhaseStepStart({step},world)).Send()'

    def test_all_stage_combinations_setup_and_advance_in_solo_and_multiplayer(self):
        for leader in ('iron_man', 'captain_america', 'she_hulk', 'vision'):
            options = preset(leader)['scheme_options']
            for first in options[0]:
                for second in options[1]:
                    for players in (1, 2):
                        with self.subTest(leader=leader, first=first, second=second, players=players):
                            a, b = first[:5], second[:5]
                            states = self.play_civil(leader, a, b, [self.advance(a)], players=players)
                            self.assertEqual(self.face(states[0], a+'b')['threat'], 0 if players == 1 else 4)
                            self.assertEqual(self.face(states[-1], b+'b')['threat'], 0)
                            self.assertEqual(self.face(states[0], a+'b')['target_threat'], 7 * players)
                            self.assertEqual(self.face(states[-1], b+'b')['target_threat'], 9 * players)
                            self.assertEqual(self.face(states[0], a+'b')['escalation'], players)
                            self.assertEqual(self.face(states[-1], b+'b')['escalation'], players)
                            self.assertTrue(any(
                                c['cid'] != a+'b' and c['threat'] is not None and
                                CardsDB.FindCardPaper(c['cid']).set_name == CardsDB.FindCardPaper(preset(leader)['villain'][0]).set_name
                                for c in states[0]['field']), 'Every stage 1 must reveal the chosen leader\'s side scheme')
                            if a in ('56096', '56141'):
                                self.assertTrue(all(len(p['encounters']) == 1 for p in states[0]['players']))
                            self.assertNotIn(a+'b', [c['cid'] for c in states[-1]['field']])

    def test_all_leaders_and_expert_stages_keep_their_own_setup_side_scheme(self):
        for name in LEADERS:
            data = preset(name)
            # Civil War leaders use Synthezoid schemes and vice versa.
            option = 0 if name in ('she_hulk', 'vision') else -1
            first, second = (stage[option][:5] for stage in data['scheme_options'])
            for suffix in ('', '_expert'):
                with self.subTest(leader=name+suffix):
                    state = self.play_civil(name+suffix, first, second, [])[-1]
                    side_schemes = [c for c in state['field'] if c['threat'] is not None and c['cid'] != first+'b']
                    self.assertTrue(any(CardsDB.FindCardPaper(c['cid']).set_name == CardsDB.FindCardPaper(preset(name)['villain'][0]).set_name for c in side_schemes))
                    if name == 'vision':
                        self.assertIn('57046a', [c['cid'] for c in state['field']], 'Vision retains his mass form with Civil War schemes')

    def test_going_underground_reveals_spider_womans_side_scheme(self):
        state = self.play_civil('spider_woman', '56200', '57045', [])[-1]
        self.assertIn('56179', state['side_schemes'])
        self.assertEqual(self.face(state, '56179')['threat'], 3)
        self.assertIn('56174', [c['cid'] for c in state['field']], 'Finesse still attaches during leader setup')

    def test_new_scene_uses_preconstructed_modules_and_schemes(self):
        for leader in LEADERS:
            for suffix in ('', '_expert'):
                name = leader + suffix
                config = preset(name)
                for seed in range(4):
                    with self.subTest(leader=name, seed=seed):
                        scene = SceneLoader.NewScene(name, None, ['luke_cage'], seed)
                        again = SceneLoader.NewScene(name, None, ['luke_cage'], seed)
                        self.assertEqual(scene.campaign.encounter_sets, config['encounter_sets'] + config['modular_sets'])
                        self.assertEqual(len(config['modular_sets']), 4)
                        self.assertEqual(scene.campaign.schemes, again.campaign.schemes)
                        self.assertEqual(scene.campaign.schemes, config['default_schemes'])
                        self.assertEqual(len(scene.campaign.schemes), 2)
                        self.assertEqual(config['schemes'], [])
                        for stage, scheme in enumerate(scene.campaign.schemes):
                            self.assertIn(scheme, config['scheme_options'][stage])
                            self.assertEqual(len(config['scheme_options'][stage]), 5)

    def test_explicit_custom_modules_remain_unrestricted_including_empty_selection(self):
        for leader in LEADERS:
            for selected in ([], ['bomb_scare'], ['mighty_avengers', 'new_avengers']):
                with self.subTest(leader=leader, modules=selected):
                    scene = SceneLoader.NewScene(leader, selected, ['luke_cage'], 125)
                    self.assertEqual(scene.campaign.encounter_sets, ['standard', *selected])

    def test_explicit_scheme_choices_override_preconstructed_defaults(self):
        hero_json = (ROOT / 'deck/starter/luke_cage.json').read_text(encoding='utf-8')
        for leader in LEADERS:
            for suffix in ('', '_expert'):
                with self.subTest(leader=leader + suffix):
                    config = preset(leader + suffix)
                    config['schemes'] = [next(s for s in options if s != default)
                                         for options, default in zip(config['scheme_options'], config['default_schemes'])]
                    scene = SceneLoader.NewFromJson(json.dumps(config), [], [hero_json], 125, [], {})
                    self.assertEqual(scene.campaign.schemes, config['schemes'])

    def test_guerilla_warfare_counts_each_status_on_only_the_enemy_leader(self):
        states = self.play_civil('spider_woman', '56172', '56201', [
            self.advance('56172'), 'puzzle.Tough("56168")',
            'puzzle.Stun("56168")', 'puzzle.Confuse("56168")',
            'puzzle.FindOrCreateFace("56168").GainStatus("Tough",DebugRule(hero))', 'puzzle.Tough(hero)',
            'puzzle.PutIntoPlay("01101")', 'puzzle.Tough("01101")',
        ])
        self.assertEqual([s['main_threat'] for s in states], [0, 0, 1, 2, 3, 3, 3, 3, 3])

    def test_superhero_jailbreak_puts_discarded_minions_into_play_for_each_player(self):
        states = self.play_civil('spider_woman', '56172', '56202', [
            self.advance('56172'), 'puzzle.CreateEncounterDeck("01104","01101","56083")',
            self.end_step(2), self.end_step(),
        ], players=2)
        self.assertEqual(states[-2]['players'][0]['minions'], [])
        self.assertEqual(states[-2]['players'][1]['minions'], [])
        self.assertEqual(states[-1]['players'][0]['minions'], ['56083'])
        self.assertEqual(states[-1]['players'][1]['minions'], ['01101'])
        self.assertNotIn('56084', [f['cid'] for f in states[-1]['field']], 'Putting Maria Hill into play must not reveal her')

    def test_superhero_jailbreak_leaves_non_minions_discarded(self):
        states = self.play_civil('spider_woman', '56172', '56202', [
            self.advance('56172'), 'puzzle.CreateEncounterDeck("01101","01104")', self.end_step(),
        ])
        self.assertEqual(states[-1]['minions'], [])

    def test_side_scheme_search_handles_fewer_schemes_than_players(self):
        for leader, first, second in (('iron_man', '56063', '56123'), ('spider_woman', '56172', '56173')):
            with self.subTest(scheme=second):
                states = self.play_civil(leader, first, second, [
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_deck.Get(),DebugRule(hero)))',
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_discard_pile.Get(),DebugRule(hero)))',
                    'puzzle.CreateEncounterDeck("01101","01104")', self.advance(first),
                ], players=2)
                self.assertEqual(states[-1]['players'][0]['encounters'], [])
                self.assertEqual(states[-1]['players'][1]['encounters'], [])

    def test_negative_zone_prison_only_captures_allies_defeated_by_enemy_attacks(self):
        for attack in (False, True):
            with self.subTest(attack=attack):
                def defend(prompt):
                    options = [o for o in prompt.options if self.card_id(o) == '45003' and o['name'] == 'Defense']
                    return self.descriptor(options[0]) if options else NotImplemented
                commands = [self.advance('56063'), 'puzzle.ChangeFormFor(0,"Hero")',
                            'puzzle.PutIntoPlay("45003")',
                            'puzzle.FindOrCreateFace("45003").SetHealth(1,DebugRule(hero))']
                if attack:
                    commands += ['puzzle.CreateEncounterDeck("01104")', 'puzzle.DoAttack("56059")']
                else:
                    commands += ['puzzle.FindOrCreateFace("45003").TakeDamage(puzzle.FindOrCreateFace("56059"),3,DebugRule(hero))']
                self.play_civil('iron_man', '56063', '56064', commands, choose_other=defend)
                scheme = next(s for s in self.last_game.world.area_schemes_main.Get() if s.paper.card_id == '56064b')
                self.assertEqual(scheme.GetPlacedCardArea().GetSize(), int(attack))
                self.assertEqual(scheme.target_threat, 9 - int(attack))

    def test_treachery_threat_limit_is_per_player_and_resets_each_phase(self):
        for leader, first, second in (('iron_man', '56063', '56124'), ('spider_woman', '56172', '56142')):
            with self.subTest(scheme=first):
                states = self.play_civil(leader, first, second, [
                    'puzzle.Reveal("01122")', 'puzzle.Reveal("01122")',
                    'puzzle.FindOrCreateFace("01122").Reveal(world.players[1],DebugRule(hero))',
                    'puzzle.FindOrCreateFace("01122").Reveal(world.players[1],DebugRule(hero))',
                    'world.stat.OnPhaseEnd()', 'puzzle.Reveal("01122")',
                    self.advance(first), 'puzzle.Reveal("01122")',
                ], players=2)
                self.assertEqual([s['main_threat'] for s in states], [4, 5, 5, 6, 6, 6, 7, 0, 0])

    def test_guard_applies_to_new_minions_and_expires_with_stage_one(self):
        for leader, first, second in (('iron_man', '56121', '56124'), ('spider_woman', '56199', '56142')):
            with self.subTest(scheme=first):
                states = self.play_civil(leader, first, second, [
                    'puzzle.PutIntoPlay("01103")', self.advance(first),
                ])
                self.assertEqual(self.face(states[-2], '01103')['guard'], 1)
                self.assertEqual(self.face(states[-1], '01103')['guard'], 0)

    def test_guard_actually_blocks_only_the_engaged_players_attacks_on_the_leader(self):
        for leader, first, second, villain in (('iron_man', '56121', '56124', '56059'),
                                               ('spider_woman', '56199', '56142', '56168')):
            with self.subTest(scheme=first):
                legal = []
                def observe_attack(prompt):
                    option = next(o for o in prompt.options if self.card_id(o) == '62001a' and o['name'] == 'Attack')
                    legal.append([Engine.game.world.object_manager.card_dict[int(t.get('id', t) if isinstance(t, dict) else t)].face.paper.card_id
                                  for t in option['all_legal_targets']])
                    Engine.game.controller_manager.console.SetCommand('puzzle.Ready(hero)', Engine.game.world)
                    from game.scene.replay.operation import CommandDescriptor
                    return CommandDescriptor()
                self.play_civil(leader, first, second, [
                    'puzzle.ChangeFormFor(0,"Hero")',
                    'puzzle.CreateCard("01103").PutIntoPlay(world.players[1],DebugRule(hero))', observe_attack,
                    'puzzle.PutIntoPlay("01103")', observe_attack,
                    self.advance(first), observe_attack,
                ], players=2)
                self.assertIn(villain, legal[0], 'A minion engaged with another player does not block this hero')
                self.assertNotIn(villain, legal[1])
                self.assertIn(villain, legal[2], 'The granted guard must stop blocking after stage one leaves')

    def test_going_underground_steady_applies_only_to_leader_and_expires(self):
        states = self.play_civil('spider_woman', '56200', '56142', [
            'puzzle.PutIntoPlay("01103")',
            'puzzle.FindOrCreateFace("56168").GainStatus("Stunned",DebugRule(hero))',
            'puzzle.FindOrCreateFace("56168").GainStatus("Stunned",DebugRule(hero))',
            self.advance('56200'),
        ])
        self.assertEqual(self.face(states[0], '56168')['steady'], 1)
        self.assertEqual(self.face(states[1], '01103')['steady'], 0)
        self.assertEqual(self.face(states[-1], '56168')['steady'], 0)

    def test_enforce_the_law_steady_survives_leader_advance_then_expires(self):
        states = self.play_civil('iron_man', '57005', '56124', [
            'puzzle.PutIntoPlay("01103")',
            'puzzle.FindOrCreateFace("56059").GainStatus("Stunned",DebugRule(hero))',
            'puzzle.Damage("56059",100)',
            'puzzle.FindOrCreateFace("56060").GainStatus("Stunned",DebugRule(hero))',
            self.advance('57005'),
        ])
        self.assertEqual(self.face(states[0], '56059')['steady'], 1)
        self.assertEqual(self.face(states[1], '01103')['steady'], 0)
        self.assertEqual(self.face(states[3], '56060')['steady'], 2, 'Iron Man II also has printed steady')
        self.assertEqual(self.face(states[4], '56060')['stunned'], 2)
        self.assertEqual(self.face(states[5], '56060')['steady'], 1, 'Printed steady remains after the scheme advances')

    def test_every_scheme_scales_for_three_and_four_players(self):
        for leader in ('iron_man', 'spider_woman'):
            stages = preset(leader)['scheme_options']
            for first, second in zip(*stages):
                for players in (3, 4):
                    with self.subTest(first=first, second=second, players=players):
                        a, b = first[:5], second[:5]
                        states = self.play_civil(leader, a, b, [self.advance(a)], players=players)
                        self.assertEqual(self.face(states[0], a+'b')['threat'], 2*players)
                        self.assertEqual(self.face(states[0], a+'b')['target_threat'], 7*players)
                        self.assertEqual(self.face(states[0], a+'b')['escalation'], players)
                        self.assertEqual(self.face(states[-1], b+'b')['target_threat'], 9*players)
                        self.assertEqual(self.face(states[-1], b+'b')['escalation'], players)
                        if a in ('56096', '56141'):
                            self.assertTrue(all(len(p['encounters']) == 1 for p in states[0]['players']))
                        if b in ('56123', '56173'):
                            self.assertTrue(all(len(end['encounters']) == len(start['encounters'])+1
                                for start, end in zip(states[0]['players'], states[-1]['players'])))

    def test_hunting_rebel_heroes_only_damages_heroes_when_another_card_is_revealed(self):
        states = self.play_civil('iron_man', '56063', '56097', [
            self.advance('56063'), 'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.Reveal("56120")', 'puzzle.Reveal("56106")',
            'puzzle.ChangeFormFor(1,"Hero")',
            'puzzle.CreateCard("56106").Reveal(world.players[1],DebugRule(hero))',
        ], players=2)
        self.assertNotIn('UNREGISTERED', self.face(states[1], '62001b')['traits'])
        self.assertIn('UNREGISTERED', self.face(states[2], '62001a')['traits'])
        initial = [p['hp'] for p in states[2]['players']]
        self.assertEqual([p['hp'] for p in states[3]['players']], [initial[0]-2, initial[1]])
        self.assertEqual([p['hp'] for p in states[4]['players']], [initial[0]-4, initial[1]])
        self.assertEqual([p['hp'] for p in states[5]['players']], [initial[0]-4, initial[1]])
        self.assertEqual([p['hp'] for p in states[6]['players']], [initial[0]-4, initial[1]-2])

    def test_no_going_back_exhausts_only_new_allies_and_allows_readying(self):
        for leader, first, second in (('iron_man', '56063', '56124'), ('spider_woman', '56172', '57045')):
            with self.subTest(scheme=second):
                states = self.play_civil(leader, first, second, [
                    'puzzle.PutIntoPlay("45003")', self.advance(first),
                    'puzzle.PutIntoPlay("01041")', 'puzzle.Ready("01041")',
                    'puzzle.CreateCard("01011").PutIntoPlay(world.players[1],DebugRule(hero))',
                ], players=2)
                self.assertFalse(self.face(states[2], '45003')['exhausted'])
                self.assertTrue(self.face(states[3], '01041')['exhausted'])
                self.assertFalse(self.face(states[4], '01041')['exhausted'])
                self.assertTrue(self.face(states[5], '01011')['exhausted'])

    def test_public_outrage_discards_three_per_player_only_after_step_one(self):
        for leader, first, second in (('iron_man', '56122', '56124'), ('spider_woman', '57044', '57045')):
            with self.subTest(scheme=first):
                states = self.play_civil(leader, first, second, [
                    self.end_step(2), self.end_step(), self.advance(first), self.end_step(),
                ], players=4)
                initial = [p['deck_size'] for p in states[0]['players']]
                self.assertEqual([p['deck_size'] for p in states[1]['players']], initial)
                for state in states[2:]:
                    self.assertEqual([p['deck_size'] for p in state['players']], [size-3 for size in initial])

    def test_secret_avengers_boost_is_two_undefended_or_one_defended(self):
        for second, defend in ((second, defend) for second in ('56142', '57006') for defend in (False, True)):
            with self.subTest(scheme=second, defended=defend):
                def choose(prompt):
                    options = [o for o in prompt.options if o['name'] == 'Defense' and self.card_id(o) == '62001a']
                    return self.descriptor(options[0]) if defend and options else NotImplemented
                states = self.play_civil('spider_woman', '56172', second, [
                    self.advance('56172'), 'puzzle.ChangeFormFor(0,"Hero")',
                    'puzzle.CreateEncounterDeck("01104")', 'puzzle.DoAttack("56168")',
                ], choose_other=choose)
                self.assertEqual(states[-2]['health'] - states[-1]['health'], 2 if defend else 4)

    def test_attack_bonus_only_applies_to_the_leader_and_ally_defense_counts(self):
        for second in ('56142', '57006'):
            with self.subTest(scheme=second):
                def defend(prompt):
                    options = [o for o in prompt.options if o['name'] == 'Defense' and self.card_id(o) == '01041']
                    return self.descriptor(options[0]) if options else NotImplemented
                states = self.play_civil('spider_woman', '56172', second, [
                    self.advance('56172'), 'puzzle.ChangeFormFor(0,"Hero")',
                    'puzzle.PutIntoPlay("01101")', 'puzzle.DoAttack("01101")',
                    'puzzle.PutIntoPlay("01041")',
                    'puzzle.FindOrCreateFace("01041").Gain(effect=DebugRule(hero),diff=1,health=5)',
                    'puzzle.FindOrCreateFace("01041").SetHealth(8,DebugRule(hero))',
                    'puzzle.CreateEncounterDeck("01104")', 'puzzle.DoAttack("56168")',
                ], choose_other=defend)
                self.assertEqual(states[3]['health']-states[4]['health'], 1)
                self.assertEqual(self.face(states[-2], '01041')['hp']-self.face(states[-1], '01041')['hp'], 3)
                self.assertEqual(self.face(states[-1], '56168')['atk'], 2)

    def test_step_one_advance_stops_old_discard_and_triggers_new_jailbreak(self):
        states = self.play_civil('spider_woman', '57044', '56202', [
            'puzzle.SetThreat("57044b",6)', 'puzzle.CreateEncounterDeck("01104","01101")',
            'puzzle.FindOrCreateFace("57044b").Phase()', self.end_step(),
        ])
        self.assertEqual(states[-1]['main_threat'], 0)
        self.assertEqual(states[0]['players'][0]['deck_size'], states[-1]['players'][0]['deck_size'])
        self.assertEqual(states[-1]['minions'], ['01101'])

    def test_search_schemes_deal_from_deck_and_discard_without_revealing(self):
        for leader, first, second in (('iron_man', '56063', '56123'), ('spider_woman', '56172', '56173')):
            with self.subTest(scheme=second):
                states = self.play_civil(leader, first, second, [
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_deck.Get(),DebugRule(hero)))',
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_discard_pile.Get(),DebugRule(hero)))',
                    'puzzle.CreateEncounterDeck("01104","01107")',
                    'puzzle.CreateEncounterDiscardPile("01109")', self.advance(first),
                ], players=2)
                dealt = [p['encounters'] for p in states[-1]['players']]
                self.assertTrue(all(len(cards) == 1 for cards in dealt))
                self.assertEqual({cid for cards in dealt for cid in cards}, {'01107', '01109'})
                self.assertFalse({'01107', '01109'} & set(states[-1]['side_schemes']))

    def test_hunting_rebel_heroes_does_not_trigger_for_put_into_play_or_form_changes(self):
        states = self.play_civil('iron_man', '56063', '56097', [
            'puzzle.ChangeFormFor(0,"Hero")', self.advance('56063'),
            'puzzle.PutIntoPlay("56120")', 'puzzle.ChangeFormFor(0,"Identity")',
            'puzzle.ChangeFormFor(0,"Hero")',
        ])
        self.assertEqual([s['health'] for s in states], [10] * 6)

    def test_hunting_rebel_heroes_hits_each_affected_hero_once_after_reveal_finishes(self):
        from game.card.face.model.face_on_event import ModelOnEvent
        from game.card.face.card_face import CardFace
        events = []
        original_end = ModelOnEvent.OnAfterCardRevealedEnd
        original_damage = CardFace.DealDamage

        def end(face, message):
            if face.paper.card_id == '56120':
                events.append('reveal end')
            return original_end(face, message)

        def damage(face, units, amount, effect, **kwargs):
            if face.paper.card_id == '56097b':
                events.append([unit.paper.card_id for unit in units])
            return original_damage(face, units, amount, effect, **kwargs)

        with patch.object(ModelOnEvent, 'OnAfterCardRevealedEnd', end), patch.object(CardFace, 'DealDamage', damage):
            states = self.play_civil('iron_man', '56063', '56097', [
                'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.ChangeFormFor(1,"Hero")',
                'puzzle.ChangeFormFor(2,"Hero")', self.advance('56063'),
                'puzzle.Reveal("56120")',
            ], players=4)
        self.assertEqual(events[0], 'reveal end')
        self.assertEqual(len(events), 2, 'All affected heroes take damage in one response to the reveal')
        self.assertCountEqual(events[1], ['62001a', '61001a', '01001a'])
        before, after = states[-2]['players'], states[-1]['players']
        self.assertEqual([a['hp']-b['hp'] for a,b in zip(before,after)], [2,2,2,0])

    def test_negative_zone_captures_minion_attack_victims_and_returns_threshold_when_card_leaves(self):
        def defend(prompt):
            options = [o for o in prompt.options if self.card_id(o) == '45003' and o['name'] == 'Defense']
            return self.descriptor(options[0]) if options else NotImplemented
        states = self.play_civil('iron_man', '56063', '56064', [
            self.advance('56063'), 'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("45003")', 'puzzle.FindOrCreateFace("45003").SetHealth(1,DebugRule(hero))',
            'puzzle.PutIntoPlay("01101")', 'puzzle.DoAttack("01101")',
            'len(Faces.MoveAllTo(puzzle.FindOrCreateFace("56064b").GetPlacedCardArea().Get(),player.hand_cards,DebugRule(hero)))',
        ], choose_other=defend, players=2)
        self.assertEqual(self.face(states[-2], '56064b')['target_threat'], 17)
        self.assertEqual(self.face(states[-1], '56064b')['target_threat'], 18)

    def test_reducing_target_threat_can_advance_stage_one_without_placing_threat(self):
        states = self.play_civil('iron_man', '56063', '56124', [
            'puzzle.CreateCard("06031").AttachTo2(puzzle.FindOrCreateFace("56063b"),DebugRule(hero))',
            'puzzle.SetThreat("56063b",8)',
            'puzzle.Discard("06031")',
        ])
        self.assertEqual(self.face(states[1], '56063b')['target_threat'], 11)
        self.assertNotIn('56063b', [f['cid'] for f in states[-1]['field']])
        self.assertEqual(self.face(states[-1], '56124b')['threat'], 0)

    def test_losing_threshold_upgrade_during_completion_does_not_advance_twice(self):
        states = self.play_civil('iron_man', '56063', '56124', [
            'puzzle.CreateCard("06031").AttachTo2(puzzle.FindOrCreateFace("56063b"),DebugRule(hero))',
            'puzzle.SetThreat("56063b",11)',
        ])
        self.assertEqual(self.face(states[-1], '56124b')['threat'], 0)
        self.assertNotIn('06031', [f['cid'] for f in states[-1]['field']])

    def test_jailbreak_finishes_each_players_discard_before_putting_minions_into_play(self):
        from game.card.face.card_type import Minion
        from game.operate.worlds import Worlds
        events = []
        original_discard = Worlds.DiscardEncounterTopCard
        original_enter = Minion.PutIntoPlay

        def discard(effect):
            face = original_discard(effect)
            if effect.this.paper.card_id == '56202b':
                events.append(('discard', face.paper.card_id))
            return face

        def enter(face, player, effect, *args, **kwargs):
            if effect.this.paper.card_id == '56202b':
                events.append(('enter', face.paper.card_id))
            return original_enter(face, player, effect, *args, **kwargs)

        with patch.object(Worlds, 'DiscardEncounterTopCard', side_effect=discard), patch.object(Minion, 'PutIntoPlay', enter):
            self.play_civil('spider_woman', '56172', '56202', [
                self.advance('56172'), 'puzzle.CreateEncounterDeck("01104","01101","56083")', self.end_step(),
            ], players=2)
        self.assertEqual(events, [('discard', '56083'), ('discard', '01101'), ('enter', '56083'), ('enter', '01101')])

    def test_minion_search_uses_only_the_deck_and_handles_a_shortfall(self):
        for leader, first, second in (('iron_man', '56096', '56124'), ('spider_woman', '56141', '56142')):
            with self.subTest(scheme=first):
                states = self.play_civil(leader, first, second, [
                    'len(Faces.RemoveAllFromGame([f for p in world.players for f in p.dealt_encounter_cards.Get()],DebugRule(hero)))',
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_discard_pile.Get(),DebugRule(hero)))',
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_deck.Get(),DebugRule(hero)))',
                    'puzzle.CreateEncounterDeck("01104","01101")',
                    'puzzle.CreateEncounterDiscardPile("01103")', f'puzzle.Reveal("{first}b")',
                ], players=2)
                self.assertEqual([cid for p in states[-1]['players'] for cid in p['encounters']], ['01101'])
                self.assertFalse(any(p['minions'] for p in states[-1]['players']))

    def test_side_scheme_search_deals_the_only_available_card(self):
        for leader, first, second in (('iron_man', '56063', '56123'), ('spider_woman', '56172', '56173')):
            with self.subTest(scheme=second):
                states = self.play_civil(leader, first, second, [
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_discard_pile.Get(),DebugRule(hero)))',
                    'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_deck.Get(),DebugRule(hero)))',
                    'puzzle.CreateEncounterDeck("01104")',
                    'puzzle.CreateEncounterDiscardPile("01109")', self.advance(first),
                ], players=2)
                self.assertEqual([p['encounters'] for p in states[-1]['players']], [['01109'], []])

    def test_public_outrage_stops_discarding_at_an_empty_player_deck(self):
        states = self.play_civil('iron_man', '56122', '56124', [
            'len(Faces.RemoveAllFromGame(player.discard_pile.Get(),DebugRule(hero)))',
            'len(Faces.RemoveAllFromGame(player.player_deck.Get(),DebugRule(hero)))',
            'CardFactory.GenerateCard("01088",player.player_deck,world)',
            'CardFactory.GenerateCard("01089",player.player_deck,world)', self.end_step(),
        ])
        self.assertEqual(states[-1]['players'][0]['deck_size'], 2)
        self.assertEqual(states[-1]['players'][0]['discard_size'], 0)
        self.assertEqual(len(states[-1]['encounters']), len(states[-2]['encounters'])+1)

    def test_jailbreak_resolves_enter_play_keywords_but_not_reveal_keywords(self):
        for cid, damage, tough in (('04116', 2, 0), ('01120', 0, 1), ('04056', 0, 0)):
            with self.subTest(minion=cid):
                states = self.play_civil('spider_woman', '56172', '56202', [
                    self.advance('56172'), 'puzzle.ChangeFormFor(0,"Hero")',
                    f'puzzle.CreateEncounterDeck("01104","{cid}")', self.end_step(),
                ])
                self.assertEqual(states[-2]['health']-states[-1]['health'], damage)
                self.assertEqual(self.face(states[-1], cid)['tough'], tough)
                self.assertEqual(states[-1]['main_threat'], 0, 'Incite must not trigger on put into play')

    def test_jailbreak_triggers_during_the_real_villain_phase(self):
        states = self.play_civil('spider_woman', '56172', '56202', [
            self.advance('56172'), 'puzzle.Confuse("56168")',
            'puzzle.CreateEncounterDeck("01104","01122","04116")', 'END_TURN',
        ])
        self.assertIn('04116', states[-1]['minions'])
        self.assertEqual(states[-1]['round'], states[-2]['round']+1)

    def test_guerilla_warfare_counts_steady_status_cards_but_not_failed_placements(self):
        states = self.play_civil('spider_woman', '56172', '56201', [
            self.advance('56172'),
            'puzzle.FindOrCreateFace("56168").Gain(effect=DebugRule(hero),diff=1,steady=1)',
            'puzzle.FindOrCreateFace("56168").GainStatus("Stunned",DebugRule(hero))',
            'puzzle.FindOrCreateFace("56168").GainStatus("Stunned",DebugRule(hero))',
            'puzzle.FindOrCreateFace("56168").GainStatus("Stunned",DebugRule(hero))',
            'puzzle.FindOrCreateFace("56168").Gain(effect=DebugRule(hero),diff=1,stalwart=1)',
            'puzzle.FindOrCreateFace("56168").GainStatus("Confused",DebugRule(hero))',
        ])
        self.assertEqual([s['main_threat'] for s in states], [0, 0, 0, 1, 2, 2, 2, 2])

    def test_guerilla_warfare_does_not_count_status_cards_carried_to_the_next_leader_stage(self):
        states = self.play_civil('spider_woman', '56172', '56201', [
            self.advance('56172'), 'puzzle.Stun("56168")', 'puzzle.Damage("56168",100)',
        ])
        self.assertEqual(states[-1]['main_threat'], 1)
        self.assertEqual(self.face(states[-1], '56169')['stunned'], 1)

    def test_jailbreak_can_put_a_discarded_minion_into_play_after_encounter_deck_reset(self):
        states = self.play_civil('spider_woman', '56172', '56202', [
            self.advance('56172'),
            'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_discard_pile.Get(),DebugRule(hero)))',
            'len(Faces.RemoveAllFromGame(Worlds.GetAllVillains(world)[0].encounter_deck.Get(),DebugRule(hero)))',
            'puzzle.CreateEncounterDeck("01104","01101")', self.end_step(),
        ], players=2)
        self.assertEqual([p['minions'] for p in states[-1]['players']], [['01101'], []])

    def assert_civil_defeat(self, leader, first, second, commands, *, choose_other=None, players=1):
        import io
        from engine.log import Log, Notify
        from game.scene.replay.operation import CommandDescriptor
        from game.test.headless import HeadlessDeviceManager
        from game.test.v18_timing_harness import run_scene_with_devices, V18_RULES
        from game.world.world_render import WorldRender

        scene = SceneLoader.NewScene(leader, None,
            ['luke_cage', 'jessica_jones', 'spider_man', 'captain_marvel'][:players], 125)
        scene.rules = V18_RULES[:]
        scene.campaign.schemes = [f'{cid}a,{cid}b' for cid in (first, second)]
        commands = iter(commands)

        def choose(prompt):
            if prompt.event_name == 'WhenPlayerInTurn':
                command = next(commands, None)
                if command is None:
                    return None
                Engine.game.controller_manager.console.SetCommand(command, Engine.game.world)
                return CommandDescriptor()
            if choose_other:
                choice = choose_other(prompt)
                if choice is not NotImplemented:
                    return choice
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (contextlib.redirect_stdout(io.StringIO()),
              patch('game.test.v18_timing_harness.initialize_database'),
              patch.object(WorldRender, 'ErrorOccurred') as errors,
              patch.object(Log, 'Warn') as warnings,
              patch.object(Notify, 'Game') as notices,
              patch.object(Engine, 'SaveCrash')):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertIsNone(devices.stopped_prompt, 'The scheme must complete before another player action')
        self.assertEqual(game.world.game_over.reason, 'The Main Scheme was Completed')
        self.assertFalse(game.world.game_over.players_won)
        return game

    def test_every_final_scheme_loses_the_game_at_its_printed_threshold(self):
        for leader in ('iron_man', 'spider_woman'):
            config = preset(leader)
            for scheme in config['scheme_options'][1]:
                with self.subTest(scheme=scheme):
                    first, second = config['scheme_options'][0][0][:5], scheme[:5]
                    self.assert_civil_defeat(leader, first, second, [
                        self.advance(first), f'puzzle.SetThreat("{second}b",9)',
                    ])

    def test_negative_zone_prison_completes_as_soon_as_capture_lowers_target_to_current_threat(self):
        def defend(prompt):
            options = [o for o in prompt.options if self.card_id(o) == '45003' and o['name'] == 'Defense']
            return self.descriptor(options[0]) if options else NotImplemented

        self.assert_civil_defeat('iron_man', '56063', '56064', [
            self.advance('56063'), 'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.SetThreat("56064b",8)', 'puzzle.PutIntoPlay("45003")',
            'puzzle.FindOrCreateFace("45003").SetHealth(1,DebugRule(hero))',
            'puzzle.CreateEncounterDeck("01104")', 'puzzle.DoAttack("56059")',
        ], choose_other=defend)


if __name__ == '__main__':
    unittest.main()
