"""Regression coverage for pack activation checks and interrupted attacks."""
import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestPackFollowup(Gameplay, unittest.TestCase):
    pack = "luke_cage"

    def iron_fist_defense(self, prompt):
        if prompt.event_name == "WhenUnitBeingAttack":
            options = [o for o in prompt.options
                       if self.card_id(o) == "62012" and o["name"] == "Defense"]
            if options:
                return self.descriptor(options[0])
        return self.choices(responses=("62012",))(prompt)

    def test_iron_fist_prevention_survives_his_defeat_by_a_boost(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("62012")', 'puzzle.Damage("62012",2)',
            'puzzle.CreateEncounterDeck("01154")', 'puzzle.DoAttack("01094")'],
            choose_other=self.iron_fist_defense)[-1]
        self.assertNotIn("62012", s["allies"])
        # Concussive Blast deals 1 to Luke and defeats Iron Fist. The established
        # prevention still reduces Rhino's ensuing 2 attack damage to zero.
        self.assertEqual(s["health"], 9)

    def test_take_a_stand_cannot_be_spent_without_allies_to_improve(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            *self.hand("62015", "62016"), 'puzzle.CreateEncounterDeck("01104")',
            'puzzle.DoAttack("01094")'],
            choose_other=self.choices(responses=("62015",), names=("Defense",)))[-1]
        self.assertEqual(s["hand"], ["62015", "62016"])
        self.assertFalse(any(self.card_id(o) == "62015"
            for p in self.last_prompts if p.event_name == "AfterUnitDefendEnd"
            for o in p.options))

    def test_shakedown_does_not_exhaust_when_no_threat_can_be_removed(self):
        self.pack = "jj"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("61035")', 'puzzle.SetThreat("01097b",0)',
            'puzzle.PutIntoPlay("62029")', 'puzzle.Damage("62029",3)',
            self.use("61001a", "Attack", "62029")],
            choose_other=self.choices(responses=("61035",), names=("Remove threat equal",)))[-1]
        self.assertFalse(self.face(s, "61035")["exhausted"])

    def test_take_a_stand_cannot_use_another_players_allies(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlayFor(1,"62012")', *self.hand("62015", "62016"),
            'puzzle.CreateEncounterDeck("01104")', 'puzzle.DoAttack("01094")'],
            configure_scene=self.two_players,
            choose_other=self.choices(responses=("62015",), names=("Defense",)))[-1]
        self.assertEqual(s["hand"], ["62015", "62016"])
        self.assertEqual(self.face(s, "62012")["atk"], 2)

    def test_shakedown_can_remove_main_scheme_threat_despite_patrol(self):
        self.pack = "jj"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("61035")', 'puzzle.SetThreat("01097b",4)',
            'puzzle.PutIntoPlay("62032")',
            'puzzle.FindOrCreateFace("62032").GainPatrol(1,DebugRule(hero))',
            'puzzle.PutIntoPlay("62029")', 'puzzle.Damage("62029",3)',
            self.use("61001a", "Attack", "62029")],
            choose_other=self.choices(responses=("61035",), target="01097b"))[-1]
        self.assertEqual(s["main_threat"], 2)
        self.assertTrue(self.face(s, "61035")["exhausted"])

    def test_shakedown_cannot_target_main_scheme_through_crisis(self):
        self.pack = "jj"
        targets = []
        accept = self.choices(responses=("61035",), target="01108")
        def choose(prompt):
            if prompt.event_name == "AfterUnitDefeatedUnit":
                for option in prompt.options:
                    if self.card_id(option) == "61035":
                        targets.extend(option["all_legal_targets"])
            return accept(prompt)
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("61035")', 'puzzle.SetThreat("01097b",4)',
            'puzzle.PutIntoPlay("01108")', 'puzzle.SetThreat("01108",4)',
            'puzzle.PutIntoPlay("62029")', 'puzzle.Damage("62029",3)',
            self.use("61001a", "Attack", "62029")], choose_other=choose)[-1]
        self.assertEqual(targets, [self.face(s, "01108")["id"]])
        self.assertEqual(self.face(s, "01108")["threat"], 2)
        self.assertEqual(s["main_threat"], 4)

    def test_shakedown_does_not_exhaust_for_a_zero_scheme_minion(self):
        self.pack = "jj"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("61035")', 'puzzle.SetThreat("01097b",4)',
            'puzzle.PutIntoPlay("01101")', 'puzzle.Damage("01101",1)',
            self.use("61001a", "Attack", "01101")],
            choose_other=self.choices(responses=("61035",), names=("Remove threat equal",)))[-1]
        self.assertNotIn("01101", s["minions"])
        self.assertEqual(s["main_threat"], 4)
        self.assertFalse(self.face(s, "61035")["exhausted"])


if __name__ == "__main__":
    unittest.main()
