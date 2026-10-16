import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay
from game.scene.replay.operation import CommandDescriptor


class TestJessicaNemesisGameplay(Gameplay, unittest.TestCase):
    pack = "jj"

    def test_work_life_balance_form_change_pays_hand_card(self):
        s = self.play(['puzzle.PutIntoPlay("61030")', *self.hand("01088"),
                      self.use("61001b", "Change_Form")])
        self.assertEqual(s[-1]["face"], "61001a")
        self.assertEqual(s[-1]["hand"], [])

    def test_work_life_balance_blocks_form_change_without_payment(self):
        s = self.play(['puzzle.PutIntoPlay("61030")', 'puzzle.ClearHand()',
                      self.use("61001b", "Change_Form")])[-1]
        self.assertEqual(s["face"], "61001b")

    def test_work_life_balance_confuse_to_discard(self):
        s = self.play(['puzzle.PutIntoPlay("61030")', self.use("61030", "Alter-Ego_Action")],
                      choose_other=self.choices(names=("Confuse your identity",)))[-1]
        self.assertTrue(s["confused"])
        self.assertFalse(any(f["cid"] == "61030" for f in s["field"]))

    def test_work_life_balance_removes_ally_and_obligation(self):
        s = self.play(['puzzle.PutIntoPlay("61003")', 'puzzle.PutIntoPlay("61030")',
                      self.use("61030", "Alter-Ego_Action")],
                      choose_other=self.choices(names=("Remove an ally",)))[-1]
        self.assertNotIn("61003", s["allies"])
        self.assertNotIn("61003", s["discard"])
        self.assertFalse(any(f["cid"] == "61030" for f in s["field"]))
        self.assertFalse(s["confused"])

    def test_purple_man_copies_highest_stats_and_updates_when_cards_leave(self):
        s = self.play(['puzzle.PutIntoPlay("61031")', 'puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("01050")', 'puzzle.Discard("01050")'])
        self.assertEqual((self.face(s[1],"61031")["atk"], self.face(s[1],"61031")["sch"]), (2,1))
        self.assertEqual((self.face(s[2],"61031")["atk"], self.face(s[2],"61031")["sch"]), (2,3))
        self.assertEqual(self.face(s[3],"61031")["atk"], 3)
        self.assertEqual(self.face(s[-1],"61031")["atk"], 2)

    def test_indomitable_will_reveal_hinder_and_counters_on_existing_suggestion(self):
        s = self.play(['puzzle.PutIntoPlay("61033a")', self.use("61033a","Forced_Action"), 'puzzle.Reveal("61032")'],
                      choose_other=self.choices(names=("Place 2 threat",)))
        self.assertEqual(self.face(s[-1],"61032")["threat"], 5)
        self.assertEqual(self.face(s[2],"61033a")["pheromone"], 2)
        self.assertEqual(self.face(s[-1],"61033a")["pheromone"], 4)

    def test_indomitable_will_adds_counters_to_new_suggestion(self):
        s = self.play(['puzzle.PutIntoPlay("61032")', 'puzzle.PutIntoPlay("61033b")',
                      self.use("61033b","Forced_Action")],
                      choose_other=self.choices(names=("Place 2 threat",)))[-1]
        self.assertEqual(self.face(s,"61033b")["pheromone"], 4)

    def test_suggestions_exhaust_spend_counter_and_add_threat(self):
        for cid in ("61033a", "61033b", "61033c"):
            with self.subTest(cid=cid):
                s = self.play(['puzzle.ClearHand()', f'puzzle.PutIntoPlay("{cid}")', self.use(cid,"Forced_Action")],
                              choose_other=self.choices(names=("Place 2 threat",)))[-1]
                self.assertEqual(s["main_threat"], 2)
                self.assertEqual(self.face(s,cid)["pheromone"], 2)
                self.assertTrue(self.face(s,cid)["exhausted"])

    def test_suggestion_can_play_matching_printed_resource_and_pays_cost(self):
        # Hero upgrades: Y Reluctant Flier, B Camcorder, R Now I'm Ticked Off.
        for cid, upgrade in (("61033a","61013"), ("61033b","61009"), ("61033c","61012")):
            with self.subTest(cid=cid):
                s = self.play([*self.hand(upgrade,"01088"), f'puzzle.PutIntoPlay("{cid}")', self.use(cid,"Forced_Action")],
                    choose_other=self.choices(names=("Play a card with",), target=upgrade, pay_like_turn=True))[-1]
                self.assertIn(upgrade,s["controlled"])
                self.assertEqual(s["main_threat"],0)
                self.assertEqual(s["hand"],[])

    def test_suggestion_disappears_after_last_use(self):
        s = self.play(['puzzle.ClearHand()', 'puzzle.PutIntoPlay("61033a")',
            self.use("61033a","Forced_Action"), 'puzzle.Ready("61033a")',
            self.use("61033a","Forced_Action"), 'puzzle.Ready("61033a")', self.use("61033a","Forced_Action")],
            choose_other=self.choices(names=("Place 2 threat",)))[-1]
        self.assertEqual(s["main_threat"], 6)
        self.assertFalse(any(f["cid"] == "61033a" for f in s["field"]))

    def test_suggestion_does_not_allow_canceling_payment_to_avoid_both_penalties(self):
        choose_play=self.choices(names=("Play a card with",),target="61013")
        def choose(prompt):
            if prompt.event_name=="WhenPlayerLikeInTurn":
                return CommandDescriptor()
            return choose_play(prompt)
        s = self.play([*self.hand("61013","01088"), 'puzzle.PutIntoPlay("61033a")',
                      self.use("61033a","Forced_Action")],choose_other=choose)[-1]
        self.assertNotIn("61013",s["controlled"])
        self.assertEqual(s["main_threat"],2)

    def test_suggestion_with_unaffordable_matching_card_must_add_threat(self):
        choose_play=self.choices(names=("Play a card with",),target="61012")
        def choose(prompt):
            if prompt.event_name=="WhenPlayerLikeInTurn":
                # The UI offers no payment; decline the unavailable play.
                for option in prompt.options:
                    for payment in option["target_payment"].values():
                        self.assertEqual(payment["payment"],[])
                return CommandDescriptor()
            return choose_play(prompt)
        s = self.play([*self.hand("61012"), 'puzzle.PutIntoPlay("61033c")',
                      self.use("61033c","Forced_Action")],
                      choose_other=choose)[-1]
        self.assertNotIn("61012",s["controlled"])
        self.assertEqual(s["main_threat"],2)
        self.assertEqual(s["hand"],["61012"])

    def test_suggestion_wrong_printed_resource_cannot_be_selected(self):
        s = self.play([*self.hand("61013","01088"), 'puzzle.PutIntoPlay("61033b")',
                      self.use("61033b","Forced_Action")],
                      choose_other=self.choices(names=("Place 2 threat",)))[-1]
        self.assertEqual(s["main_threat"],2)
        self.assertEqual(s["hand"],["61013","01088"])
        choices=[o for p in self.last_prompts if p.event_name=="WhenPlayerChooseAbility"
                 for o in p.options if "matching_printed" in o["name"]]
        self.assertEqual(choices,[])

    def test_suggestion_must_be_used_before_ending_turn(self):
        self.play(['puzzle.ClearHand()', 'puzzle.PutIntoPlay("61033a")'])
        self.assertFalse(self.last_prompts[-1].show_cancel)


class TestLukeNemesisGameplay(Gameplay, unittest.TestCase):
    pack = "luke_cage"

    def test_internal_injury_player_phase_end_ignores_tough(self):
        s = self.play(['puzzle.PutIntoPlay("62028")', *self.tough(2),
            'puzzle.CreateEncounterDeck("62010","01088")', 'END_TURN'])[-1]
        self.assertEqual(s["round"], 2)
        self.assertEqual((s["tough"],s["health"]), (2,7))

    def test_internal_injury_removed_after_basic_recovery(self):
        s = self.play(['puzzle.PutIntoPlay("62028")', 'puzzle.Damage(hero,5)',
                      self.use("62001b", "Recover")], choose_other=self.choices(responses=("62028",)))[-1]
        self.assertEqual(s["health"],9)
        self.assertFalse(any(f["cid"] == "62028" for f in s["field"]))

    def test_internal_injury_not_removed_after_nonbasic_healing(self):
        s = self.play(['puzzle.PutIntoPlay("62028")', 'puzzle.Damage(hero,5)',
                      'puzzle.Heal(hero,4)'], choose_other=self.choices(responses=("62028",)))[-1]
        self.assertTrue(any(f["cid"] == "62028" for f in s["field"]))

    def test_asp_schemes_and_stuns(self):
        s = self.play(['puzzle.PutIntoPlay("62032")', 'DoScheme("62032")'])[-1]
        self.assertEqual(s["main_threat"],1)
        self.assertTrue(s["stunned"])

    def test_asp_boost_stuns_and_venomous_whispers_boost_confuses(self):
        for cid, status in (("62032","stunned"),("62030","confused")):
            with self.subTest(cid=cid):
                s = self.play([f'puzzle.Boost("{cid}")'])[-1]
                self.assertTrue(s[status])

    def test_augmented_jaws_fallback_villain_and_paid_removal(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62031")',
                      *self.hand("01089"), self.use("62031")])
        self.assertEqual(self.face(s[-2],"01094")["atk"],3)
        self.assertEqual(self.face(s[-1],"01094")["atk"],2)
        self.assertEqual(s[-1]["hand"],[])
        self.assertFalse(any(f["cid"] == "62031" for f in s[-1]["field"]))

    def test_augmented_jaws_cannot_be_paid_with_wrong_resource(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62031")',
                      *self.hand("01088"), self.use("62031")])[-1]
        self.assertTrue(any(f["cid"] == "62031" for f in s["field"]))
        self.assertEqual(s["hand"], ["01088"])

    def test_venomous_whispers_blocks_attacks_but_not_nonattack_damage(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62029")',
                      'puzzle.PutIntoPlay("62030")', 'puzzle.Damage("62029",2)'])[-1]
        attack = next(o for o in self.last_prompts[-1].options if o["name"] == "Attack")
        self.assertNotIn(self.face(s,"62029")["id"],attack["all_legal_targets"])
        self.assertEqual(self.face(s,"62029")["hp"],3)

    def test_venomous_whispers_defeat_searches_and_reveals_serpent(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62030")',
            'puzzle.SetThreat("62030",2)', 'puzzle.CreateEncounterDeck("62032","01106")',
            self.use("62001a", "Thwart", "62030")])[-1]
        self.assertNotIn("62030",s["side_schemes"])
        self.assertIn("62032",s["minions"])

    def test_sidewinder_only_escapes_for_boost_star(self):
        for top, escapes in (("62030", True), ("01106",False), ("01088",False)):
            with self.subTest(top=top):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62033")',
                    f'puzzle.CreateEncounterDeck("{top}")', self.use("62001a", "Attack", "62033")])[-1]
                self.assertEqual("62033" in s["encounters"], escapes)
                if not escapes:
                    self.assertEqual(self.face(s,"62033")["hp"], 1)

    def test_sidewinder_quickstrike_only_attacks_hero(self):
        for hero in (False, True):
            with self.subTest(hero=hero):
                s = self.play([*(['puzzle.ChangeFormFor(0,"Hero")'] if hero else []),
                              'puzzle.Reveal("62033")'])[-1]
                self.assertEqual(s["health"],8 if hero else 10)

    def test_cottonmouth_repeats_against_defending_ally_until_it_is_defeated(self):
        def defend(prompt):
            if prompt.event_name=="WhenUnitBeingAttack":
                for option in prompt.options:
                    if self.card_id(option)=="01083" and option["name"]=="Defense":
                        return self.descriptor(option)
            return NotImplemented
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("01083")',
                      'puzzle.PutIntoPlay("62029")', 'puzzle.DoAttack("62029")'],
                      choose_other=defend)[-1]
        self.assertEqual(s["health"],10)
        self.assertNotIn("01083",s["allies"])


if __name__ == "__main__":
    unittest.main()
