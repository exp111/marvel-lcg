import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestLukeHeroGameplay(Gameplay, unittest.TestCase):
    pack = "luke_cage"

    def test_stand_with_me_tough_and_thwart_cap(self):
        for tough, removed in ((0,1), (3,4), (4,5), (6,5)):
            with self.subTest(tough=tough):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.tough(tough),
                    'puzzle.SetThreat("01097b",6)', *self.hand("62005", "01088"),
                    self.use("62005", target="01097b")])[-1]
                self.assertEqual(s["tough"], tough + 1)
                self.assertEqual(s["main_threat"], 6 - removed)
                self.assertEqual(s["hand"], [])

    def test_confused_stand_does_not_gain_tough(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Confuse(hero)',
            'puzzle.SetThreat("01097b",6)', *self.hand("62005", "01088"), self.use("62005")])[-1]
        self.assertFalse(s["confused"])
        self.assertEqual((s["tough"], s["main_threat"]), (0,6))

    def test_knuckle_sandwich_optional_return_pays_tough_damage(self):
        for take_back in (False, True):
            with self.subTest(take_back=take_back):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.tough(2),
                    *self.hand("62004", "01088"), self.use("62004", target="01094")],
                    choose_other=self.choices(names=("Discard 1 tough",) if take_back else ()))
                self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 3)
                self.assertEqual(s[-1]["tough"], 1 if take_back else 2)
                self.assertEqual(s[-1]["health"], 9 if take_back else 10)
                self.assertEqual(s[-1]["hand"], ["62004"] if take_back else [])

    def test_stunned_knuckle_sandwich_spends_no_tough_and_stays_discarded(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Stun(hero)', *self.tough(1),
            *self.hand("62004", "01088"), self.use("62004")],
            choose_other=self.choices(names=("Discard 1 tough",)))
        self.assertFalse(s[-1]["stunned"])
        self.assertEqual((s[-1]["tough"], s[-1]["health"], s[-1]["hand"]), (1,10,[]))
        self.assertEqual(s[-1]["villain_health"], s[-2]["villain_health"])

    def test_sweet_christmas_cost_reduction_and_area_damage(self):
        for tough, cost in ((0,"5"), (3,"2"), (5,"0"), (7,"0")):
            with self.subTest(tough=tough):
                funds = ("01088", "01089", "01090") if tough == 0 else (("01088",) if tough == 3 else ())
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.tough(tough),
                    'puzzle.PutIntoPlay("62029")', 'puzzle.PutIntoPlay("62032")',
                    *self.hand("62006", *funds), self.use("62006")])
                self.assertEqual(s[-2]["costs"]["62006"], [cost])
                self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 5)
                self.assertEqual(s[-1]["minions"], [])
                self.assertEqual(s[-1]["tough"], tough)

    def test_stunned_sweet_christmas_cancels_entire_multi_target_attack(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.tough(5), 'puzzle.Stun(hero)',
            'puzzle.PutIntoPlay("62029")', *self.hand("62006"), self.use("62006")])
        self.assertFalse(s[-1]["stunned"])
        self.assertEqual(self.face(s[-1], "62029")["hp"], 5)
        self.assertEqual(s[-1]["villain_health"], s[-2]["villain_health"])

    def test_harlem_hero_readies_hero_and_allies_up_to_tough_count(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.tough(2),
            'puzzle.PutIntoPlay("62002")', 'puzzle.PutIntoPlay("01083")',
            'puzzle.Exhaust(hero)', 'puzzle.Exhaust("62002")', 'puzzle.Exhaust("01083")',
            *self.hand("62003", "01088"), self.use("62003")],
            choose_other=self.choices(names=("Ready a character",)))
        self.assertEqual(s[-1]["tough"], 3)
        self.assertFalse(s[-1]["exhausted"])
        for cid in ("62002", "01083"):
            self.assertFalse(self.face(s[-1], cid)["exhausted"])

    def test_jessica_ally_thwart_updates_and_caps_at_four_bonus(self):
        s = self.play(['puzzle.PutIntoPlay("62002")', *self.tough(6),
                      'puzzle.ChangeFormFor(0,"Hero")', 'hero.DiscardTough(DebugRule(hero),rule="All")'])
        self.assertEqual(s[1]["allies"]["62002"][1], 1)
        self.assertEqual(s[4]["allies"]["62002"][1], 4)
        self.assertEqual(s[-2]["allies"]["62002"][1], 5)
        self.assertEqual(s[-1]["allies"]["62002"][1], 1)
        self.assertEqual(s[-1]["health"], 4)

    def test_burstein_cannot_activate_in_hero_form(self):
        s = self.play(['puzzle.PutIntoPlay("62008")', 'puzzle.ChangeFormFor(0,"Hero")',
                      'puzzle.ClearHand()'])[-1]
        self.assertFalse(any(cid == "62008" for cid, name in s["actions"]))

    def test_fogwells_gym_readies_defender_after_tough_loss(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62007")',
            *self.tough(2), 'puzzle.Exhaust(hero)', 'puzzle.Damage(hero,3)'],
            choose_other=self.choices(responses=("62007",)))
        self.assertFalse(s[-1]["exhausted"])
        self.assertTrue(self.face(s[-1], "62007")["exhausted"])
        self.assertEqual((s[-1]["tough"], s[-1]["health"]), (1,9))

    def test_power_man_draws_only_once_until_readied(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62011")',
            *self.tough(3), 'puzzle.ClearHand()', 'puzzle.Damage(hero,2)', 'puzzle.Damage(hero,2)'],
            choose_other=self.choices(responses=("62011",)))
        self.assertEqual(len(s[-1]["hand"]), 1)
        self.assertTrue(self.face(s[-1], "62011")["exhausted"])
        self.assertEqual((s[-1]["tough"], s[-1]["health"]), (1,8))

    def test_power_man_does_not_draw_in_alter_ego(self):
        s = self.play(['puzzle.PutIntoPlay("62011")', *self.tough(1),
                      'puzzle.ClearHand()', 'puzzle.Damage(hero,2)'],
                      choose_other=self.choices(responses=("62011",)))[-1]
        self.assertEqual((s["health"], s["hand"]), (10,[]))
        self.assertFalse(self.face(s, "62011")["exhausted"])

    def test_cruisin_paid_play_adds_attack_damage_and_overkill(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62029")',
            'puzzle.Damage("62029",3)', *self.hand("62009"), self.use("62009", "Play", "62029"),
            self.use("62001a", "Attack", "62029")])
        self.assertNotIn("62029", s[-1]["minions"])
        self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 2)

    def test_cruisin_does_not_increase_nonattack_damage(self):
        s = self.play(['puzzle.PutIntoPlay("62029")', *self.hand("62009"),
            self.use("62009", "Play", "62029"), 'puzzle.Damage("62029",1)'])[-1]
        self.assertEqual(self.face(s, "62029")["hp"], 4)

    def test_two_metal_bracers_stack_retaliate(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            *self.hand("62010", "01088"), self.use("62010", "Play"),
            *self.hand("62010", "01089"), self.use("62010", "Play"),
            'puzzle.CreateEncounterDeck("01088")', 'puzzle.DoAttack("01094")'])
        self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 2)

    def test_piercing_attack_still_consumes_only_one_tough_in_both_forms(self):
        for form in ("Hero", "Identity"):
            with self.subTest(form=form):
                s = self.play([*(['puzzle.ChangeFormFor(0,"Hero")'] if form == "Hero" else []), *self.tough(3),
                    'puzzle.PutIntoPlay("62029")',
                    'puzzle.FindOrCreateFace("62029").GainKeyword(1,"Piercing",DebugRule(hero))',
                    'puzzle.DoAttack("62029")'])[-1]
                # Cottonmouth attacks three times; none pierce through Luke's Tough.
                self.assertEqual(s["tough"], 0)
                self.assertEqual(s["health"], 7 if form == "Hero" else 10)

    def test_burstein_identity_searches_deck_and_discard_once_per_phase(self):
        for zone in ("CreatePlayerDeck", "CreatePlayerDiscardPile"):
            with self.subTest(zone=zone):
                s = self.play(['puzzle.ClearHand()', f'puzzle.{zone}("62008")',
                    self.use("62001b", "Action")], choose_other=self.choices(names=("Search",),target="62008"))[-1]
                self.assertEqual(s["hand"], ["62008"])
                self.assertNotIn(("62001b", "Action"), s["actions"])

    def test_burstein_identity_search_limit_resets_next_phase(self):
        s = self.play(['puzzle.ClearHand()', 'puzzle.CreatePlayerDeck("62008")',
            self.use("62001b", "Action"), 'puzzle.CreateEncounterDeck("62010","01088")',
            'END_TURN'], choose_other=self.choices(names=("Search",),target="62008"))[-1]
        self.assertEqual(s["round"], 2)
        self.assertIn(("62001b", "Action"), s["actions"])

    def test_unpreventable_tough_loss_does_not_offer_metal_bracer(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62010")',
            *self.tough(2), 'hero.DiscardTough(DebugRule(hero),rule=1)'],
            choose_other=self.choices(responses=("62010",)))[-1]
        self.assertEqual((s["health"], s["tough"]), (9,1))
        self.assertFalse(self.face(s,"62010")["exhausted"])

    def test_harlem_hero_with_one_tough_readies_exactly_one_character(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62002")',
            'puzzle.Exhaust(hero)', 'puzzle.Exhaust("62002")', *self.hand("62003","01088"),
            self.use("62003")], choose_other=self.choices(names=("Ready a character",),target="62002"))[-1]
        self.assertTrue(s["exhausted"])
        self.assertFalse(self.face(s,"62002")["exhausted"])
        self.assertEqual(s["tough"],1)

    def test_cruisin_also_modifies_attack_event(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62029")',
            'puzzle.Damage("62029",3)', *self.hand("62009"), self.use("62009","Play","62029"),
            *self.hand("62004","01088"), self.use("62004",target="62029")])
        self.assertNotIn("62029",s[-1]["minions"])
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],3)

    def test_power_man_and_gym_ready_and_trigger_again_across_full_round(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62011")',
            'puzzle.PutIntoPlay("62007")', *self.tough(3), 'puzzle.Exhaust(hero)',
            'puzzle.Damage(hero,2)', 'puzzle.CreateEncounterDeck("01105","01104")',
            'END_TURN', 'puzzle.Exhaust(hero)', 'puzzle.Damage(hero,2)'],
            choose_other=self.choices(responses=("62011","62007")))
        self.assertEqual(s[-1]["round"],2)
        self.assertEqual((s[-1]["health"],s[-1]["tough"]),(7,0))
        self.assertFalse(s[-1]["exhausted"])
        self.assertEqual(len(s[-1]["hand"])-len(s[-2]["hand"]),0)
        # The villain's attack already used this round's newly readied Power Man.
        self.assertTrue(self.face(s[-1],"62011")["exhausted"])


if __name__ == "__main__":
    unittest.main()
