import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestJessicaPlayerCards(Gameplay, unittest.TestCase):
    pack = "jj"

    def test_captain_marvel_counts_energy_icons_and_confuses_at_two(self):
        for tops,threat,confused in ((["01089"]*4,6,False),
                (["61015","01089","01089","01089"],4,False),
                (["01088","01089","01089","01089"],4,True)):
            with self.subTest(tops=tops):
                s=self.play(['puzzle.SetThreat("01097b",6)',
                    'puzzle.CreatePlayerDeck('+','.join(repr(cid) for cid in tops)+')',
                    'puzzle.PutIntoPlay("61015")'],choose_other=self.choices(responses=("61015",),
                    names=("Remove 2 threat","Confuse an enemy")))[-1]
                self.assertEqual(s["main_threat"],threat)
                self.assertEqual(bool(self.face(s,"01094")["confused"]),confused)

    def test_spider_woman_gains_counters_on_hero_and_ally_thwarts(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.SetThreat("01097b",6)',
            'puzzle.PutIntoPlay("61016")',self.use("61001a","Thwart","01097b"),
            self.use("61016","Thwart","01097b")],choose_other=self.choices(responses=("61016",)))[-1]
        self.assertEqual(self.face(s,"61016")["limb"],2)
        self.assertEqual(self.face(s,"61016")["hp"],1)

    def test_spider_woman_eight_counter_cap_and_discard_damage(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.SetThreat("01097b",6)',
            'puzzle.PutIntoPlay("61016")','puzzle.Counter("61016","limb",8)',
            self.use("61001a","Thwart","01097b")],choose_other=self.choices(responses=("61016",),
            names=("Discard Spider-Woman",)))
        self.assertNotIn("61016",s[-1]["allies"])
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],8)

    def test_spider_woman_event_thwart_also_counts(self):
        s=self.play(['puzzle.PutIntoPlay("61016")','puzzle.SetThreat("01097b",6)',
            *self.hand("61006"),'puzzle.CreateEncounterDeck("01104")',self.use("61006",target="01097b")],
            choose_other=self.choices(responses=("61016",)))[-1]
        self.assertEqual(self.face(s,"61016")["limb"],1)

    def test_squirrel_girl_counts_hand_after_payment_with_cap(self):
        for extras,count in ((0,0),(2,2),(5,4)):
            with self.subTest(extras=extras):
                def pay_energy(prompt):
                    option=next(o for o in prompt.options if self.card_id(o)=="61017" and o["name"]=="Play")
                    choice=self.descriptor(option)
                    choice.resources=choice.resources[:1]
                    return choice
                s=self.play([*self.hand("61017","01088",*(["61004"]*extras)),pay_energy],
                    choose_other=self.choices(responses=("61017",)))[-1]
                self.assertEqual(self.face(s,"61017")["squirrel"],count)
                self.assertEqual(len(s["hand"]),extras)

    def test_squirrel_girl_no_counters_when_put_into_play(self):
        s=self.play(['puzzle.PutIntoPlay("61017")'],choose_other=self.choices(responses=("61017",)))[-1]
        self.assertEqual(self.face(s,"61017")["squirrel"],0)

    def test_squirrel_girl_removes_threat_without_exhausting_until_empty(self):
        s=self.play(['puzzle.PutIntoPlay("61017")','puzzle.Counter("61017","squirrel",2)',
            'puzzle.SetThreat("01097b",3)',self.use("61017","Action","01097b"),
            self.use("61017","Action","01097b")])[-1]
        self.assertEqual(s["main_threat"],1)
        self.assertEqual(self.face(s,"61017")["squirrel"],0)
        self.assertFalse(self.face(s,"61017")["exhausted"])
        self.assertNotIn(("61017","Action"),s["actions"])

    def test_strategy_session_hero_thwarts_only_player_side_scheme(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61007")',
            *self.hand("61019","01088"),self.use("61019",target="61007")])[-1]
        self.assertEqual(self.face(s,"61007")["threat"],3)
        self.assertEqual(s["hand"],[])

    def test_strategy_session_alter_ego_searches_and_adds_scheme(self):
        s=self.play(['puzzle.CreatePlayerDeck("61007")',*self.hand("61019","01088"),self.use("61019")],
            choose_other=self.choices(names=("Search",),target="61007"))[-1]
        self.assertEqual(s["hand"],["61007"])
        self.assertNotIn("61007",s["side_schemes"])

    def test_lay_down_the_law_reprint_mental_resource_bonus(self):
        for resource,remaining in (("01088",3),("01089",2)):
            with self.subTest(resource=resource):
                s=self.play(['puzzle.SetThreat("01097b",6)',*self.hand("61018",resource),
                    self.use("61001b","Change_Form")],choose_other=self.choices(responses=("61018",)))[-1]
                self.assertEqual(s["main_threat"],remaining)
                self.assertEqual(s["hand"],[])

    def test_lay_the_trap_reprint_damage_when_defeated(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61021")',
            self.use("61001a","Thwart","61021")])
        self.assertNotIn("61021",s[-1]["side_schemes"])
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],5)

    def test_determination_reprint_only_removes_threat_in_hero_form(self):
        for hero in (False,True):
            with self.subTest(hero=hero):
                s=self.play([*(['puzzle.ChangeFormFor(0,"Hero")'] if hero else []),
                    'puzzle.SetThreat("01097b",3)',*self.hand("61024","61022"),self.use("61024","Play")],
                    choose_other=self.choices(responses=("61022",)))[-1]
                self.assertEqual(s["main_threat"],2 if hero else 3)
                self.assertEqual(s["hand"],[])

    def test_hellcat_free_action_requires_defender_and_expires_at_phase_end(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")',*self.hand("61025"),
            self.use("61025","Action"),'puzzle.CreateEncounterDeck("01105","01104")','END_TURN'])
        self.assertIn("61025",s[4]["allies"])
        self.assertNotIn("61025",s[-1]["allies"])
        self.assertIn("61025",s[-1]["discard"])

    def test_hellcat_free_action_unavailable_to_civilian_alter_ego(self):
        s=self.play(self.hand("61025"))[-1]
        self.assertNotIn(("61025","Action"),s["actions"])

    def test_hellcat_paid_play_does_not_expire(self):
        s=self.play([*self.hand("61025","01088","01089"),self.use("61025","Play"),
            'puzzle.ChangeFormFor(0,"Hero")','puzzle.CreateEncounterDeck("01105","01104")','END_TURN'])[-1]
        self.assertIn("61025",s["allies"])

    def test_joys_of_life_both_exhaust_ready_choices(self):
        for forward in (False,True):
            with self.subTest(forward=forward):
                s=self.play(['puzzle.PutIntoPlay("01083")',
                    'puzzle.Exhaust("01083")' if forward else 'puzzle.Exhaust(hero)',
                    *self.hand("61026"),self.use("61026")],choose_other=self.choices(
                    names=("Exhaust a Civilian" if forward else "Exhaust a hero",)))[-1]
                self.assertEqual(s["exhausted"],forward)
                self.assertEqual(self.face(s,"01083")["exhausted"],not forward)

    def test_innate_aggression_and_perception_apply_only_to_hero(self):
        s=self.play(['puzzle.PutIntoPlay("61034")','puzzle.PutIntoPlay("61036")',
            'puzzle.ChangeFormFor(0,"Hero")','puzzle.Discard("61034")','puzzle.Discard("61036")'])
        self.assertEqual((self.face(s[3],"61001a")["atk"],self.face(s[3],"61001a")["thw"]),(3,4))
        self.assertEqual((self.face(s[-1],"61001a")["atk"],self.face(s[-1],"61001a")["thw"]),(2,3))

    def test_innate_inspiration_affects_existing_and_new_allies_and_cleans_up(self):
        s=self.play(['puzzle.PutIntoPlay("01083")','puzzle.PutIntoPlay("61037")',
            'puzzle.PutIntoPlay("61016")','puzzle.Discard("61037")'])
        self.assertEqual(self.face(s[-2],"01083")["max_hp"],4)
        self.assertEqual(self.face(s[-2],"61016")["max_hp"],4)
        self.assertEqual(self.face(s[-1],"61016")["max_hp"],3)

    def test_shakedown_only_triggers_on_exact_attack_defeat(self):
        for damage,attack,remaining in ((3,True,4),(4,True,6),(3,False,6)):
            with self.subTest(damage=damage,attack=attack):
                s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61035")',
                    'puzzle.SetThreat("01097b",6)','puzzle.PutIntoPlay("62029")',f'puzzle.Damage("62029",{damage})',
                    self.use("61001a","Attack","62029") if attack else 'puzzle.Damage("62029",2)'],
                    choose_other=self.choices(responses=("61035",),names=("Remove threat equal",)))[-1]
                self.assertEqual(s["main_threat"],remaining)
                self.assertEqual(self.face(s,"61035")["exhausted"],remaining==4)

    def test_echo_reduces_enemy_attack_by_current_hero_defense(self):
        for jacket,health in ((False,2),(True,3)):
            with self.subTest(jacket=jacket):
                def defend(prompt):
                    if prompt.event_name=="WhenUnitBeingAttack":
                        return self.descriptor(next(o for o in prompt.options if self.card_id(o)=="61038"))
                    return NotImplemented
                s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61038")',
                    *(['puzzle.PutIntoPlay("61011")'] if jacket else []),
                    'puzzle.CreateEncounterDeck("01104")','puzzle.DoAttack("01094")'],choose_other=defend)[-1]
                self.assertEqual(self.face(s,"61038")["hp"],health)

    def test_echo_does_not_reduce_nonattack_damage(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61038")','puzzle.Damage("61038",2)'])[-1]
        self.assertEqual(self.face(s,"61038")["hp"],1)

    def test_lay_low_flips_and_heals_by_recovery_without_exhausting(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.Damage(hero,5)',
            'puzzle.PutIntoPlay("61039")',self.use("61001a","Thwart","61039")],
            accept_events=("WhenPlayerChooseAbility",))[-1]
        self.assertEqual(s["face"],"61001b")
        self.assertEqual(s["health"],10)
        self.assertTrue(s["exhausted"])


if __name__=="__main__":
    unittest.main()
