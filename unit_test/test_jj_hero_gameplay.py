import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestJessicaHeroGameplay(Gameplay, unittest.TestCase):
    pack = "jj"

    def test_big_mistake_base_paid_attack(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.hand("61004", "01088"),
                       self.use("61004", target="01094")])
        self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 3)
        self.assertEqual(s[-1]["hand"], [])
        self.assertCountEqual(s[-1]["discard"][-2:], ["61004", "01088"])

    def test_big_mistake_evidence_overkill_and_piercing(self):
        for keyword in ("Overkill", "Piercing"):
            with self.subTest(keyword=keyword):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Counter("61002","evidence",2)',
                    'puzzle.PutIntoPlay("62029")', 'puzzle.Damage("62029",3)',
                    *(['puzzle.Tough("62029")'] if keyword == "Piercing" else []),
                    *self.hand("61004", "01088"), self.use("61004", target="62029")],
                    choose_other=self.choices(names=("Remove 1 evidence", keyword)))
                self.assertNotIn("62029", s[-1]["minions"])
                self.assertEqual(s[-1]["evidence"], 1)
                self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 3 if keyword == "Overkill" else 0)

    def test_big_mistake_stunned_cancels_evidence_spend_and_attack(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Stun(hero)',
            'puzzle.Counter("61002","evidence",2)', *self.hand("61004", "01088"),
            self.use("61004")], choose_other=self.choices(names=("Remove 1 evidence",)))
        self.assertFalse(s[-1]["stunned"])
        self.assertEqual(s[-1]["evidence"], 2)
        self.assertEqual(s[-1]["villain_health"], s[-2]["villain_health"])

    def test_breakthrough_readies_and_shuffles_after_basic_attack(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.hand("61005"),
                      self.use("61001a", "Attack", "01094")],
                      choose_other=self.choices(responses=("61001a", "61005")))
        self.assertEqual(s[-1]["evidence"], 1)
        self.assertFalse(s[-1]["exhausted"])
        self.assertNotIn("61005", s[-1]["hand"])
        self.assertEqual(s[-1]["discard"].count("61005"), s[-2]["discard"].count("61005"))
        self.assertEqual(s[-1]["deck"].count("61005"), s[-2]["deck"].count("61005") + 1)

    def test_snooping_around_thwarts_and_reveals_only_minions_and_schemes(self):
        for top in ("62029", "01107", "01106"):
            with self.subTest(top=top):
                s = self.play(['puzzle.SetThreat("01097b",6)', *self.hand("61006"),
                    'puzzle.CreateEncounterDeck("'+top+'")', self.use("61006", target="01097b")])
                self.assertEqual(s[-1]["main_threat"], 2)
                self.assertEqual(s[-1]["evidence"], 2)
                self.assertEqual(top in s[-1]["minions"] + s[-1]["side_schemes"], top != "01106")

    def test_snooping_confused_cancels_all_effects(self):
        s = self.play(['puzzle.SetThreat("01097b",6)', 'puzzle.Confuse(hero)',
                      *self.hand("61006"), 'puzzle.CreateEncounterDeck("62029")',
                      self.use("61006")])
        self.assertFalse(s[-1]["confused"])
        self.assertEqual(s[-1]["main_threat"], 6)
        self.assertEqual(s[-1]["evidence"], 0)
        self.assertNotIn("62029", s[-1]["minions"])

    def test_piecing_it_all_together_draws_three_when_defeated(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.hand("61007"),
            self.use("61007", "Play"), 'puzzle.SetThreat("61007",3)',
            self.use("61001a", "Thwart", "61007")])
        self.assertEqual(len(s[-1]["hand"]) - len(s[-2]["hand"]), 3)
        self.assertNotIn("61007", s[-1]["side_schemes"])

    def test_camcorder_uses_remaining_health_and_discards_without_defeating(self):
        for damage, counters, remaining in ((0,3,0), (3,0,0), (2,2,1)):
            with self.subTest(damage=damage):
                s = self.play(['puzzle.PutIntoPlay("61009")', 'puzzle.PutIntoPlay("61010")',
                    'puzzle.PutIntoPlay("62029")', f'puzzle.Damage("62029",{damage})',
                    f'puzzle.Counter("61002","evidence",{counters})',
                    self.use("61009", target="62029")], choose_other=self.choices(responses=("61010",)))
                self.assertNotIn("62029", s[-1]["minions"])
                self.assertEqual(s[-1]["evidence"], remaining)
                self.assertTrue(self.face(s[-1], "61009")["exhausted"])
                self.assertFalse(self.face(s[-1], "61010")["exhausted"])

    def test_camcorder_cannot_afford_undamaged_minion_without_evidence(self):
        s = self.play(['puzzle.PutIntoPlay("61009")', 'puzzle.PutIntoPlay("62029")', 'puzzle.ClearHand()'])[-1]
        self.assertFalse(any(cid == "61009" for cid, name in s["actions"]))

    def test_circumstantial_evidence_rewards_enemy_defeat_once(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61010")',
            'puzzle.PutIntoPlay("62029")', 'puzzle.Damage("62029",3)',
            self.use("61001a", "Attack", "62029")], choose_other=self.choices(responses=("61010", "61001a")))
        self.assertEqual(s[-1]["evidence"], 2)
        self.assertTrue(self.face(s[-1], "61010")["exhausted"])

    def test_now_im_ticked_off_after_scheme_damages_villain_and_minions(self):
        s = self.play(['puzzle.PutIntoPlay("61012")', 'puzzle.PutIntoPlay("62029")',
                      'puzzle.CreateEncounterDeck("01088")', 'DoScheme("01094")'])
        self.assertEqual(s[-1]["face"], "61001a")
        self.assertNotIn("62029", s[-1]["minions"])
        self.assertNotIn("61012", s[-1]["controlled"])
        self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 5)

    def test_now_im_ticked_off_does_not_trigger_in_hero_form(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61012")',
                      'puzzle.CreateEncounterDeck("01088")', 'puzzle.DoAttack("01094")'])
        self.assertIn("61012", s[-1]["controlled"])
        self.assertEqual(s[-1]["villain_health"], s[-2]["villain_health"])

    def test_stakeout_does_not_reward_nonlethal_thwart(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("01107")',
            'puzzle.SetThreat("01107",6)', 'puzzle.PutIntoPlay("61014")',
            self.use("61014", target="01107"), self.use("61001a", "Thwart", "01107")],
            choose_other=self.choices(responses=("61014",)))
        self.assertEqual(self.face(s[-1], "01107")["threat"], 1)
        self.assertEqual(s[-1]["evidence"], 0)

    def test_stakeout_applies_to_event_thwart(self):
        s = self.play(['puzzle.PutIntoPlay("01107")', 'puzzle.SetThreat("01107",6)',
            'puzzle.PutIntoPlay("61014")', self.use("61014", target="01107"),
            *self.hand("61006"), 'puzzle.CreateEncounterDeck("01108")', self.use("61006", target="01107")],
            choose_other=self.choices(responses=("61014",)))
        self.assertNotIn("01107", s[-1]["side_schemes"])
        self.assertEqual(s[-1]["evidence"], 4)

    def test_alias_threshold_spends_evidence_to_advance_villain_stage(self):
        for spend in (False, True):
            with self.subTest(spend=spend):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Damage("01094",10)',
                    'puzzle.Counter("61002","evidence",2)', 'puzzle.PutIntoPlay("01107")',
                    'puzzle.SetThreat("01107",2)', self.use("61001a", "Thwart", "01107")],
                    choose_other=self.choices(responses=("61002",), names=("Spend evidence",) if spend else ()))
                self.assertEqual(s[-1]["evidence"], 0 if spend else 4)
                self.assertTrue(self.face(s[-1], "61002")["exhausted"])
                self.assertEqual(any(f["cid"] == "01095" for f in s[-1]["field"]), spend)

    def test_luke_ally_toughness_consequential_damage_and_action(self):
        s = self.play(['puzzle.PutIntoPlay("61003")', 'puzzle.ChangeFormFor(0,"Hero")',
            self.use("61003", "Attack", "01094"), 'puzzle.Ready("61003")', self.use("61003", "Action")])
        self.assertEqual(s[1]["allies"]["61003"], (2,2,3,1))
        self.assertEqual(s[3]["allies"]["61003"], (2,2,3,0))
        self.assertEqual(s[-1]["allies"]["61003"], (2,2,2,1))
        self.assertTrue(self.face(s[-1], "61003")["exhausted"])

    def test_luke_ally_does_not_return_after_lethal_action_cost(self):
        s = self.play(['puzzle.PutIntoPlay("61003")', 'puzzle.Tough("61003")',
            'puzzle.Damage("61003",2)', self.use("61003", "Action")])[-1]
        self.assertNotIn("61003", s["allies"])

    def test_leather_jacket_basic_defense_adds_two_evidence(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61011")',
            'puzzle.CreateEncounterDeck("01106")', 'puzzle.DoAttack("01094")'],
            choose_other=self.choices(responses=("61001a", "61011"), names=("Defense",)))
        self.assertEqual(self.face(s[-1], "61001a")["defense"], 3)
        self.assertEqual(s[-1]["health"], 11)
        self.assertEqual(s[-1]["evidence"], 2)
        self.assertTrue(s[-1]["exhausted"])

    def test_reluctant_flier_threshold_and_defense_response(self):
        for boost, triggers, health in (("01088",False,9), ("01106",True,10)):
            with self.subTest(boost=boost):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61011")',
                    'puzzle.PutIntoPlay("61013")', f'puzzle.CreateEncounterDeck("{boost}")',
                    'puzzle.DoAttack("01094")'],
                    choose_other=self.choices(responses=("61011", "61013")))
                self.assertEqual(s[-1]["health"], health)
                self.assertEqual("61013" not in s[-1]["controlled"], triggers)
                self.assertEqual(s[-1]["evidence"], int(triggers))
                self.assertFalse(s[-1]["exhausted"])

    def test_reluctant_flier_does_not_prevent_nonattack_damage(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61013")',
                      'puzzle.Damage(hero,3)'], choose_other=self.choices(responses=("61013",)))[-1]
        self.assertEqual(s["health"], 8)
        self.assertIn("61013", s["controlled"])

    def test_calling_in_favors_searches_deck_and_pays_discounted_cost(self):
        s = self.play(['puzzle.PutIntoPlay("61008")', 'puzzle.Counter("61002","evidence",2)',
                      *self.hand("01088"), 'puzzle.CreatePlayerDeck("61003")',
                      self.use("61008", "Alter-Ego_Action")],
                      choose_other=self.choices(names=("Search",), target="61003", pay_like_turn=True))
        self.assertIn("61003", s[-1]["allies"])
        self.assertEqual(s[-1]["evidence"], 0)
        self.assertTrue(self.face(s[-1], "61008")["exhausted"])
        self.assertEqual(s[-1]["hand"], [])
        costs = [o["target_payment"] for p in self.last_prompts if p.event_name == "WhenPlayerLikeInTurn" for o in p.options]
        self.assertTrue(costs)
        self.assertEqual(next(iter(costs[0].values()))["cost"], "1")

    def test_now_im_ticked_off_resolves_independent_sentences_if_form_change_blocked(self):
        s = self.play(['puzzle.PutIntoPlay("61012")', 'puzzle.PutIntoPlay("61030")',
                      'puzzle.ClearHand()', 'puzzle.CreateEncounterDeck("01088")', 'DoScheme("01094")'])
        self.assertEqual(s[-1]["face"], "61001b")
        # The damage/discard are independent sentences, with no "then".
        self.assertNotIn("61012", s[-1]["controlled"])
        self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 5)

    def test_circumstantial_evidence_also_rewards_alias_nondamage_defeat(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61010")',
            'puzzle.Damage("01094",10)', 'puzzle.Counter("61002","evidence",2)',
            'puzzle.PutIntoPlay("01107")', 'puzzle.SetThreat("01107",2)',
            self.use("61001a","Thwart","01107")],
            choose_other=self.choices(responses=("61002","61010"), names=("Spend evidence",)))[-1]
        self.assertEqual(s["evidence"],1)
        self.assertTrue(self.face(s,"61010")["exhausted"])

    def test_camcorder_cannot_discard_elite_minions(self):
        s = self.play(['puzzle.PutIntoPlay("61009")', 'puzzle.Counter("61002","evidence",20)',
            'puzzle.PutIntoPlay("01102")', 'puzzle.ClearHand()'])[-1]
        self.assertTrue(any(f["cid"]=="01102" for f in s["field"]))
        self.assertFalse(any(cid=="61009" for cid,name in s["actions"]))

    def test_breakthrough_does_not_trigger_when_evidence_is_removed(self):
        s = self.play(['puzzle.Counter("61002","evidence",2)', *self.hand("61005"),
            'puzzle.Exhaust(hero)', 'puzzle.FindOrCreateFace("61002").RemoveCountersInternal(1,"evidence",DebugRule(hero),forced=True)'],
            choose_other=self.choices(responses=("61005",)))[-1]
        self.assertTrue(s["exhausted"])
        self.assertEqual(s["hand"],["61005"])

    def test_calling_in_favors_cannot_play_unaffordable_ally_for_free(self):
        s = self.play(['puzzle.PutIntoPlay("61008")', 'puzzle.Counter("61002","evidence",2)',
            'puzzle.ClearHand()', 'puzzle.CreatePlayerDeck("61003")', self.use("61008","Alter-Ego_Action")],
            choose_other=self.choices(names=("Search",),target="61003",pay_like_turn=True))[-1]
        self.assertNotIn("61003",s["allies"])
        self.assertEqual(s["hand"],[])
        self.assertIn("61003",s["deck"])
        self.assertEqual(s["evidence"],0)

    def test_incognito_form_lock_expires_through_real_villain_phase(self):
        s = self.play([self.use("61001b","Incognito_Mode"),
            'puzzle.CreateEncounterDeck("01105","01104")', 'END_TURN',
            self.use("61001a","Change_Form")])[-1]
        self.assertEqual(s["round"],2)
        self.assertEqual(s["face"],"61001b")
        self.assertEqual(s["health"],9)

    def test_stunned_now_im_ticked_off_is_replaced_without_flipping_or_discarding(self):
        s = self.play(['puzzle.PutIntoPlay("61012")', 'puzzle.Stun(hero)',
            'puzzle.CreateEncounterDeck("01104")', 'DoScheme("01094")'])
        self.assertFalse(s[-1]["stunned"])
        self.assertEqual(s[-1]["face"],"61001b")
        self.assertIn("61012",s[-1]["controlled"])
        self.assertEqual(s[-1]["villain_health"],s[-2]["villain_health"])


if __name__ == "__main__":
    unittest.main()
