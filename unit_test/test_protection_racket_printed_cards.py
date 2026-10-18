"""Gameplay checks against printed Protection Racket cards 135-138.

China Shop interrupts excess damage to local allies (also minions in expert).
Pizza Dough requires defeating *another* character or a side scheme.
"""
import contextlib
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from game.message import Message
from game.test.v18_timing_harness import initialize_database
from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestProtectionRacketPrintedCards(Gameplay, unittest.TestCase):
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

    def play_scheme(self, card, commands, *, expert=False, multiplayer=False,
                    timing='v18_timing', **kwargs):
        def configure(scene):
            scene.campaign.expert = expert
            scene.campaign.schemes = [f'{card}a,{card}b']
            scene.rules = ['v16_all', timing, 'fix_attached_health_flip']
            if multiplayer:
                self.two_players(scene)
                scene.campaign.schemes.append('60134a,60134b')
        return self.play(commands, configure_scene=configure, **kwargs)

    @staticmethod
    def damage(source, target, amount):
        return (f'puzzle.FindOrCreateFace("{target}").TakeDamage('
                f'puzzle.FindOrCreateFace("{source}"),{amount},DebugRule(hero))')

    def test_china_shop_counts_excess_damage_to_local_allies_from_any_source(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            for source in ('01094', '60135b'):
                with self.subTest(timing=timing, source=source):
                    states = self.play_scheme('60135', [
                        'puzzle.PutIntoPlay("45003")', self.damage(source, '45003', 5),
                    ], timing=timing)
                    self.assertEqual(states[-1]['main_threat'], 2)
                    self.assertNotIn('45003', states[-1]['controlled'])

    def test_china_shop_only_counts_minions_in_expert(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            for expert, threat in ((False, 0), (True, 2)):
                with self.subTest(timing=timing, expert=expert):
                    states = self.play_scheme('60135', [
                        'puzzle.PutIntoPlay("01101")', self.damage('62001b', '01101', 5),
                    ], expert=expert, timing=timing)
                    self.assertEqual(states[-1]['main_threat'], threat)
                    self.assertNotIn('01101', states[-1]['minions'])

    def test_china_shop_does_not_count_exact_lethal_nonlethal_or_prevented_damage(self):
        for amount, tough in ((2, False), (3, False), (5, True)):
            with self.subTest(amount=amount, tough=tough):
                states = self.play_scheme('60135', [
                    'puzzle.PutIntoPlay("45003")',
                    *(['puzzle.Tough("45003")'] if tough else []),
                    self.damage('01094', '45003', amount),
                ])
                self.assertEqual(states[-1]['main_threat'], 0)

    def test_china_shop_ignores_characters_in_another_play_area(self):
        states = self.play_scheme('60135', [
            'puzzle.PutIntoPlayFor(1,"45003")', self.damage('01094', '45003', 5),
        ], multiplayer=True)
        self.assertEqual(states[-1]['main_threat'], 0)

    def test_china_shop_counts_an_enemy_attack_against_a_defending_ally(self):
        def defend(prompt):
            options = [o for o in prompt.options
                       if self.card_id(o) == '45003' and o['name'] == 'Defense']
            return self.descriptor(options[0]) if options else NotImplemented

        for overkill, excess in ((False, 1), (True, 4)):
            with self.subTest(overkill=overkill):
                states = self.play_scheme('60135', [
                    'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("45003")',
                    'puzzle.FindOrCreateFace("45003").SetHealth(1,DebugRule(hero))',
                    *(['puzzle.PutIntoPlay("01099")'] if overkill else []),
                    'puzzle.CreateEncounterDeck("01104")', 'puzzle.DoAttack("01094")',
                ], choose_other=defend)
                self.assertEqual(states[-1]['main_threat'], excess)
                self.assertNotIn('45003', states[-1]['controlled'])
                self.assertEqual(states[-1]['health'], 10 - (excess if overkill else 0))

    def test_china_shop_forced_interrupt_precedes_follow_through_interrupt(self):
        # Both trigger on excess damage. The mandatory interrupt resolves
        # before Follow Through can increase the excess with its optional one.
        excess = []
        original_send = Message.AfterUnitDefeatedUnit.Send

        def observe(message):
            if message.target.paper.card_id == '01101':
                excess.append(message.excess_damage)
            return original_send(message)

        with patch.object(Message.AfterUnitDefeatedUnit, 'Send', observe):
            states = self.play_scheme('60135', [
                'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("01101")',
                'puzzle.FindOrCreateFace("01101").SetHealth(1,DebugRule(hero))',
                'puzzle.PutIntoPlay("16045")', self.use('62001a', 'Attack', '01101'),
            ], expert=True, choose_other=self.choices(responses=('16045',)))
        self.assertEqual(states[-1]['main_threat'], 1)
        self.assertEqual(excess, [2])

    def test_china_shop_interrupt_places_threat_before_the_character_is_defeated(self):
        observed = []
        original_send = Message.WhenUnitBeDefeated.Send

        def observe(message):
            if message.trigger.paper.card_id == '45003':
                scheme = next(s for s in Engine.game.world.area_schemes_main.Get()
                              if s.paper.card_id == '60135b')
                observed.append((scheme.threat, message.trigger.IsInPlay()))
            return original_send(message)

        with patch.object(Message.WhenUnitBeDefeated, 'Send', observe):
            self.play_scheme('60135', [
                'puzzle.PutIntoPlay("45003")', self.damage('01094', '45003', 5),
            ])
        self.assertEqual(observed, [(2, True)])

    def test_pizza_dough_does_not_reward_an_ally_defeating_itself(self):
        for timing in ('v18_timing', 'no_v18_timing'):
            with self.subTest(timing=timing):
                states = self.play_scheme('60138', [
                    'puzzle.PutIntoPlay("45003")',
                    'puzzle.FindOrCreateFace("45003").SetHealth(1,DebugRule(hero))',
                    self.use('45003', 'Attack', '01094'),
                ], timing=timing)
                self.assertNotIn('45003', states[-1]['controlled'])
                self.assertEqual(states[-1]['main_threat'], 0)

    def test_pizza_dough_heals_a_local_hero_defeating_a_character_in_either_area(self):
        for player_id in (0, 1):
            with self.subTest(player_id=player_id):
                states = self.play_scheme('60138', [
                    'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Damage(hero,2)',
                    f'puzzle.PutIntoPlayFor({player_id},"01101")',
                    self.damage('62001a', '01101', 3),
                ], multiplayer=True)
                self.assertEqual(states[-1]['health'], 9)
                self.assertEqual(self.face(states[-1], '60138b')['threat'], 1)

    def test_pizza_dough_heals_the_local_minion_that_defeats_an_ally(self):
        states = self.play_scheme('60138', [
            'puzzle.PutIntoPlay("01101")', 'puzzle.PutIntoPlay("45003")',
            'puzzle.Damage("01101",1)', self.damage('01101', '45003', 3),
        ])
        self.assertEqual(self.face(states[-1], '01101')['hp'], 3)
        self.assertEqual(states[-1]['main_threat'], 1)

    def test_pizza_dough_does_not_reward_the_shared_villain(self):
        states = self.play_scheme('60138', [
            'puzzle.PutIntoPlay("45003")', 'puzzle.Damage("01094",2)',
            self.damage('01094', '45003', 3),
        ])
        self.assertEqual(states[-1]['villain_health'], states[-2]['villain_health'])
        self.assertEqual(states[-1]['main_threat'], 0)

    def test_pizza_dough_does_not_reward_a_character_from_another_area(self):
        states = self.play_scheme('60138', [
            'puzzle.PutIntoPlayFor(1,"45003")', 'puzzle.Damage("45003",1)',
            'puzzle.PutIntoPlay("01101")', self.damage('45003', '01101', 3),
        ], multiplayer=True)
        self.assertEqual(self.face(states[-1], '45003')['hp'], 2)
        self.assertEqual(self.face(states[-1], '60138b')['threat'], 0)

    def test_pizza_dough_rewards_defeating_a_side_scheme(self):
        states = self.play_scheme('60138', [
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Damage(hero,2)',
            'puzzle.PutIntoPlay("01107")', 'puzzle.SetThreat("01107",1)',
            self.use('62001a', 'Thwart', '01107'),
        ])
        self.assertEqual(states[-1]['health'], 9)
        self.assertEqual(states[-1]['main_threat'], 1)

    def test_pizza_dough_still_places_threat_when_the_defeating_character_is_uninjured(self):
        states = self.play_scheme('60138', [
            'puzzle.PutIntoPlay("01101")', self.damage('62001b', '01101', 3),
        ])
        self.assertEqual(states[-1]['health'], 10)
        self.assertEqual(states[-1]['main_threat'], 1)

    def test_pizza_dough_can_trigger_more_than_once_per_phase(self):
        states = self.play_scheme('60138', [
            'puzzle.Damage(hero,3)',
            'puzzle.PutIntoPlay("01101")', self.damage('62001b', '01101', 3),
            'puzzle.PutIntoPlay("60140")', self.damage('62001b', '60140', 6),
        ])
        self.assertEqual(states[-1]['health'], 9)
        self.assertEqual(states[-1]['main_threat'], 2)

    def test_pizza_dough_heals_a_defeating_ally_before_consequential_damage(self):
        states = self.play_scheme('60138', [
            'puzzle.PutIntoPlay("45003")', 'puzzle.PutIntoPlay("01101")',
            'puzzle.FindOrCreateFace("45003").SetHealth(1,DebugRule(hero))',
            'puzzle.FindOrCreateFace("01101").SetHealth(1,DebugRule(hero))',
            self.use('45003', 'Attack', '01101'),
        ])
        self.assertEqual(self.face(states[-1], '45003')['hp'], 1)
        self.assertEqual(states[-1]['main_threat'], 1)

    def test_hung_out_to_dry_tough_prevents_damage_but_not_threat(self):
        states = self.play_scheme('60136', ['puzzle.PutIntoPlay("01102")'])
        self.assertEqual(self.face(states[-1], '01102')['hp'], 4)
        self.assertEqual(self.face(states[-1], '01102')['tough'], 0)
        self.assertEqual(states[-1]['main_threat'], 1)

    def test_hung_out_to_dry_ignores_non_character_entries(self):
        states = self.play_scheme('60136', ['puzzle.PutIntoPlay("01081")'])
        self.assertEqual(states[-1]['main_threat'], 0)

    def test_hung_out_to_dry_does_not_treat_a_minion_moving_areas_as_entering_play(self):
        states = self.play_scheme('60136', [
            'puzzle.PutIntoPlayFor(1,"01101")',
            'puzzle.FindOrCreateFace("01101").EngagePlayer(world.const_players[0],DebugRule(hero))',
        ], multiplayer=True)
        self.assertEqual(self.face(states[-1], '01101')['hp'], 3)
        self.assertEqual(self.face(states[-1], '60136b')['threat'], 0)

    def test_pawn_shop_counts_attachments_on_local_minions_only(self):
        for player_id in (0, 1):
            with self.subTest(player_id=player_id):
                states = self.play_scheme('60137', [
                    f'puzzle.PutIntoPlayFor({player_id},"62029")',
                    'puzzle.PutIntoPlay("62031")',
                ], multiplayer=True)
                self.assertEqual(self.face(states[-1], '60137b')['threat'], int(player_id == 0))

    def test_pawn_shop_ignores_attachments_on_the_shared_villain(self):
        states = self.play_scheme('60137', ['puzzle.PutIntoPlay("62031")'])
        self.assertEqual(states[-1]['main_threat'], 0)


if __name__ == '__main__':
    unittest.main()
