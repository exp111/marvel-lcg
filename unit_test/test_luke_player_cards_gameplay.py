import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestLukePlayerCards(Gameplay, unittest.TestCase):
    pack = "luke_cage"

    def defense(self, cid, responses=()):
        other = self.choices(responses=responses)
        used = set()
        def choose(prompt):
            if prompt.event_name == "WhenUnitBeingAttack":
                options=[o for o in prompt.options if self.card_id(o)==cid]
                if options: return self.descriptor(options[0])
                return NotImplemented
            if any(self.card_id(o)=="62015" for o in prompt.options):
                if "62015" in used: return NotImplemented
                used.add("62015")
            return other(prompt)
        return choose

    def test_iron_fist_prevents_attack_damage_only_while_defending(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("62012")',
            'puzzle.CreateEncounterDeck("01104")','puzzle.DoAttack("01094")','puzzle.Damage("62012",1)'],
            choose_other=self.defense("62012",("62012",)))
        self.assertEqual(self.face(s[-2],"62012")["hp"],3)
        self.assertEqual(self.face(s[-1],"62012")["hp"],2)
        self.assertTrue(self.face(s[-1],"62012")["exhausted"])

    def test_misty_knight_tough_bonus_and_consequential_damage(self):
        s=self.play(['puzzle.PutIntoPlay("62013")','puzzle.SetThreat("01097b",6)',
            self.use("62013","Thwart","01097b"),'puzzle.Tough("62013")'])
        self.assertEqual(self.face(s[1],"62013")["tough"],1)
        self.assertEqual(s[-2]["main_threat"],3)
        self.assertEqual(self.face(s[-2],"62013")["hp"],2)
        self.assertEqual(self.face(s[-2],"62013")["thw"],1)
        self.assertEqual(self.face(s[-1],"62013")["thw"],3)

    def test_valkyrie_paid_play_enters_with_toughness(self):
        s=self.play([*self.hand("62014","62025","62016"),self.use("62014","Play")])[-1]
        self.assertEqual(self.face(s,"62014")["tough"],1)
        self.assertEqual(s["hand"],[])

    def test_valkyrie_prevents_another_ally_defeat_and_heals_to_one(self):
        for accept in (False,True):
            with self.subTest(accept=accept):
                s=self.play(['puzzle.PutIntoPlay("62014")','puzzle.PutIntoPlay("62012")',
                    'puzzle.Damage("62012",5)'],choose_other=self.choices(responses=("62014",) if accept else ())) [-1]
                self.assertEqual("62012" in s["allies"],accept)
                self.assertEqual("62014" in s["allies"],not accept)
                if accept: self.assertEqual(self.face(s,"62012")["hp"],1)

    def test_valkyrie_can_save_consequential_defeat_but_not_herself(self):
        s=self.play(['puzzle.PutIntoPlay("62014")','puzzle.PutIntoPlay("62012")',
            'puzzle.Damage("62012",2)',self.use("62012","Attack","01094")],
            choose_other=self.choices(responses=("62014",))) [-1]
        self.assertEqual(self.face(s,"62012")["hp"],1)
        self.assertNotIn("62014",s["allies"])
        s=self.play(['puzzle.PutIntoPlay("62014")','puzzle.Damage("62014",1)',
            'puzzle.Damage("62014",4)'],choose_other=self.choices(responses=("62014",))) [-1]
        self.assertNotIn("62014",s["allies"])

    def test_take_a_stand_after_player_phase_defense_expires_at_phase_end(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("62012")',
            *self.hand("62015","62016"),'puzzle.CreateEncounterDeck("01104")',
            'puzzle.DoAttack("01094")','puzzle.CreateEncounterDeck("01105","01104")','END_TURN'],
            choose_other=self.defense("62001a",("62015",)))
        self.assertEqual(self.face(s[-3],"62012")["atk"],3)
        self.assertEqual(self.face(s[-1],"62012")["atk"],2)

    def test_take_a_stand_villain_phase_defense_lasts_through_next_player_phase(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("62012")',
            *self.hand("62015","62016"),'puzzle.CreateEncounterDeck("01105","01104")',
            'END_TURN','puzzle.CreateEncounterDeck("01105","01104")','END_TURN'],
            choose_other=self.defense("62001a",("62015",)))
        self.assertEqual(self.face(s[-3],"62012")["atk"],3)
        self.assertEqual(self.face(s[-1],"62012")["atk"],2)

    def test_innovation_heals_owned_ally_only_in_hero_form(self):
        for hero in (False,True):
            with self.subTest(hero=hero):
                s=self.play([*(['puzzle.ChangeFormFor(0,"Hero")'] if hero else []),
                    'puzzle.PutIntoPlay("62012")','puzzle.Damage("62012",2)',
                    *self.hand("61024","62016"),self.use("61024","Play")],
                    choose_other=self.choices(responses=("62016",))) [-1]
                self.assertEqual(self.face(s,"62012")["hp"],2 if hero else 1)

    def test_power_of_leadership_pays_two_for_leadership_support(self):
        s=self.play([*self.hand("62018","62017"),self.use("62018","Play")])[-1]
        self.assertIn("62018",s["controlled"])
        self.assertEqual(s["hand"],[])

    def test_power_of_leadership_only_generates_one_for_other_aspect(self):
        captured=[]
        def inspect(prompt):
            option=next(o for o in prompt.options if self.card_id(o)=="61023")
            captured.append(option["target_payment"])
            return self.descriptor(next(o for o in prompt.options if self.card_id(o)=="62001b" and o["name"]=="Change_Form"))
        self.play([*self.hand("61023","62017"),inspect])
        self.assertTrue(captured)
        self.assertTrue(all(list(g.values())==["G"] for p in captured[0].values() for g in p["payment"]))

    def test_defensive_formation_charges_exhaustion_and_last_use_discard(self):
        s=self.play(['puzzle.PutIntoPlay("62018")','puzzle.PutIntoPlay("62012")',
            self.use("62018","Action","62012"),'puzzle.Damage("62012",1)','puzzle.Ready("62018")',
            self.use("62018","Action","62012"),'puzzle.Damage("62012",1)','puzzle.Ready("62018")',
            self.use("62018","Action","62012")])
        self.assertEqual(self.face(s[3],"62018")["block"],2)
        self.assertTrue(self.face(s[3],"62018")["exhausted"])
        self.assertNotIn(("62018","Action"),s[3]["actions"])
        self.assertNotIn("62018",s[-1]["controlled"])
        self.assertEqual(self.face(s[-1],"62012")["tough"],1)

    def test_defensive_formation_cannot_target_nondefender_or_already_tough(self):
        s=self.play(['puzzle.PutIntoPlay("62018")','puzzle.PutIntoPlay("01083")',
            'puzzle.PutIntoPlay("62013")'])[-1]
        self.assertNotIn(("62018","Action"),s["actions"])

    def test_righteous_purpose_paid_support_tracks_exactly_one_hp(self):
        s=self.play(['puzzle.PutIntoPlay("62012")','puzzle.Damage("62012",2)',
            *self.hand("62019","62025"),self.use("62019","Play"),
            'puzzle.Heal("62012",1)','puzzle.Damage("62012",1)','puzzle.Discard("62019")'])
        self.assertIn("62019",s[-4]["controlled"])
        self.assertEqual(self.face(s[-4],"62012")["atk"],4)
        self.assertEqual(self.face(s[-3],"62012")["atk"],2)
        self.assertEqual(self.face(s[-2],"62012")["thw"],3)
        self.assertEqual(self.face(s[-1],"62012")["thw"],1)

    def test_hulk_gains_rage_after_villain_attack_not_minion_attack(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("62020")',
            'puzzle.CreateEncounterDeck("01104")','puzzle.DoAttack("01094")',
            'puzzle.PutIntoPlay("01102")','puzzle.DoAttack("01102")',
            self.use("62020","Attack","01094")],choose_other=self.choices(responses=("62020",)))
        self.assertEqual(self.face(s[-1],"62020")["rage"],1)
        self.assertEqual(self.face(s[-1],"62020")["atk"],3)
        self.assertEqual(self.face(s[-1],"62020")["hp"],3)
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],3)

    def test_she_hulk_toughness_and_entry_gives_luke_additional_tough(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")',*self.tough(1),
            'puzzle.PutIntoPlay("62021")'],choose_other=self.choices(responses=("62021",))) [-1]
        self.assertEqual(s["tough"],2)
        self.assertEqual(self.face(s,"62021")["tough"],1)

    def test_native_double_resource_reprints_each_pay_two(self):
        for resource in ("62025","62026","62027"):
            with self.subTest(resource=resource):
                s=self.play([*self.hand("62018",resource),self.use("62018","Play")])[-1]
                self.assertIn("62018",s["controlled"])
                self.assertEqual(s["hand"],[])

    def test_size_advantage_compares_remaining_health_strictly(self):
        for injury,damage in ((0,6),(3,3),(4,3)):
            with self.subTest(injury=injury):
                s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.Damage("01094",7)',f'puzzle.Damage(hero,{injury})',
                    *self.hand("62034","62025"),self.use("62034",target="01094")])
                self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],damage)

    def test_size_advantage_giant_overrides_health_comparison(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.Damage(hero,8)',
            'hero.GainTraits(1,"GIANT",DebugRule(hero))',*self.hand("62034","62025"),
            self.use("62034",target="01094")])
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],6)

    def test_observe_schemes_then_gives_tough_even_if_confused(self):
        for confused in (False,True):
            with self.subTest(confused=confused):
                s=self.play(['puzzle.ChangeFormFor(0,"Hero")',
                    *(['puzzle.Confuse("01094")'] if confused else []),
                    'puzzle.CreateEncounterDeck("01104")',*self.hand("62035","62025"),self.use("62035")])[-1]
                self.assertEqual(s["main_threat"],0 if confused else 1)
                self.assertEqual(s["tough"],1)
                self.assertFalse(self.face(s,"01094")["confused"])

    def test_toughen_up_requires_basic_recovery_reaching_base_health(self):
        for injury,expected in ((4,1),(8,0)):
            with self.subTest(injury=injury):
                s=self.play(['puzzle.PutIntoPlay("62036")',f'puzzle.Damage(hero,{injury})',
                    self.use("62001b","Recover")],choose_other=self.choices(responses=("62036",))) [-1]
                self.assertEqual(s["tough"],expected)
                self.assertEqual(self.face(s,"62036")["exhausted"],bool(expected))

    def test_toughen_up_nonbasic_heal_does_not_trigger(self):
        s=self.play(['puzzle.PutIntoPlay("62036")','puzzle.Damage(hero,4)','puzzle.Heal(hero,4)'],
            choose_other=self.choices(responses=("62036",))) [-1]
        self.assertEqual(s["tough"],0)
        self.assertFalse(self.face(s,"62036")["exhausted"])

    def test_black_belt_requires_controlled_martial_artist_and_grants_trait_health(self):
        s=self.play([*self.hand("62037"),'puzzle.PutIntoPlay("62012")',self.use("62037","Play","62001b"),
            'puzzle.ChangeFormFor(0,"Hero")','puzzle.Discard("62037")'])
        self.assertNotIn(("62037","Play"),s[2]["actions"])
        self.assertIn("MARTIAL ARTIST",self.face(s[-3],"62001b")["traits"])
        self.assertEqual(self.face(s[-3],"62001b")["max_hp"],11)
        self.assertIn("MARTIAL ARTIST",self.face(s[-2],"62001a")["traits"])
        self.assertEqual(self.face(s[-1],"62001a")["max_hp"],10)
        self.assertNotIn("MARTIAL ARTIST",self.face(s[-1],"62001a")["traits"])


if __name__ == "__main__":
    unittest.main()
