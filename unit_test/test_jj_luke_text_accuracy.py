"""Printed-text regressions: partial resolution, timing, and effect boundaries."""
import unittest
from unittest.mock import patch

from unit_test.jj_luke_gameplay_helpers import Gameplay
from game.message import Message


class TestTextAccuracy(Gameplay, unittest.TestCase):
    pack = "jj"

    def test_snooping_without_threat_still_places_evidence_and_reveals_minion(self):
        s = self.play(['puzzle.SetThreat("01097b",0)',
            'puzzle.CreateEncounterDeck("01102")', *self.hand("61006"),
            self.use("61006")])[-1]
        self.assertEqual(s["main_threat"], 0)
        self.assertEqual(s["evidence"], 2)
        self.assertIn("01102", s["minions"])

    def test_stand_without_threat_still_gives_tough(self):
        self.pack = "luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.SetThreat("01097b",0)', *self.hand("62005","62025"),
            self.use("62005")])[-1]
        self.assertEqual(s["main_threat"], 0)
        self.assertEqual(s["tough"], 1)

    def test_both_bond_printings_can_heal_without_threat(self):
        for cid in ("61027", "62024"):
            with self.subTest(card=cid):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
                    'puzzle.PutIntoPlay("61003")', 'puzzle.Damage(hero,4)',
                    'puzzle.SetThreat("01097b",0)', *self.hand(cid,"01088"),
                    self.use(cid)])[-1]
                self.assertEqual(s["health"], 10)
                self.assertEqual(s["main_threat"], 0)

    def test_bond_cannot_be_played_when_neither_thwart_nor_heal_can_resolve(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("61003")', 'puzzle.SetThreat("01097b",0)',
            *self.hand("61027","01088")])[-1]
        self.assertFalse(any(cid == "61027" for cid, _ in s["actions"]))

    def test_iron_fist_prevents_before_tough_and_only_for_that_attack(self):
        self.pack = "luke_cage"
        response_windows = []
        accept = self.choices(responses=("62012",))
        def choose(prompt):
            if prompt.event_name == "WhenUnitBeingAttack":
                options = [o for o in prompt.options if self.card_id(o) == "62012"]
                if options:
                    return self.descriptor(options[0])
            if any(self.card_id(o) == "62012" and o["name"] != "Defense"
                   for o in prompt.options):
                response_windows.append(prompt.event_name)
            return accept(prompt)
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("62012")', 'puzzle.Tough("62012")',
            'puzzle.CreateEncounterDeck("01104")', 'puzzle.DoAttack("01094")',
            'puzzle.Damage("62012",1)', 'puzzle.Damage("62012",1)'],
            choose_other=choose)
        self.assertEqual(self.face(s[-3],"62012")["tough"], 1)
        self.assertEqual(self.face(s[-2],"62012")["hp"], 3)
        self.assertEqual(self.face(s[-1],"62012")["hp"], 2)
        self.assertEqual(response_windows, ["WhenUnitWouldDefend"])

    def test_bond_heals_each_character_in_one_instance(self):
        healed = []
        original = Message.AfterUnitHealHealth.Send
        def record(message):
            healed.append((message.trigger.paper.card_id, message.value))
            return original(message)
        with patch.object(Message.AfterUnitHealHealth, "Send", record):
            self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61003")',
                'puzzle.Damage(hero,4)', 'puzzle.SetThreat("01097b",4)',
                *self.hand("61027","01088"), self.use("61027")])
        self.assertEqual(healed, [("61001a",3)])

    def test_bond_must_heal_as_much_as_possible_when_less_than_three_is_damaged(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61003")',
            'puzzle.Damage(hero,2)', 'puzzle.SetThreat("01097b",0)',
            *self.hand("61027","01088"), self.use("61027")])[-1]
        self.assertEqual(s["health"], 11)

    def test_sweet_christmas_respects_serpent_society_attack_prohibition(self):
        self.pack = "luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.PutIntoPlay("62030")', 'puzzle.PutIntoPlay("62032")',
            *self.tough(5), *self.hand("62006"), self.use("62006")])
        self.assertEqual(self.face(s[-1],"62032")["hp"], self.face(s[-2],"62032")["hp"])
        self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 5)

    def test_ticked_off_respects_serpent_society_attack_prohibition(self):
        s = self.play(['puzzle.PutIntoPlay("61012")',
            'puzzle.PutIntoPlay("62030")', 'puzzle.PutIntoPlay("62032")',
            'puzzle.CreateEncounterDeck("01104")', 'DoScheme("01094")'])
        self.assertEqual(self.face(s[-1],"62032")["hp"], self.face(s[-2],"62032")["hp"])
        self.assertEqual(s[-2]["villain_health"] - s[-1]["villain_health"], 5)
        self.assertNotIn("61012", s[-1]["controlled"])

    def test_power_man_and_iron_fist_gives_tough_when_all_attacks_are_prohibited(self):
        self.pack = "luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62012")',
            'puzzle.PutIntoPlay("62030")', 'puzzle.PutIntoPlay("62029")',
            'puzzle.FindOrCreateFace("62029").GainGuard(1,DebugRule(hero))',
            *self.hand("62023"), self.use("62023")],
            choose_other=self.choices(names=("Give a character",), target="62012"))
        self.assertEqual(self.face(s[-1],"62012")["tough"], 1)
        self.assertEqual(self.face(s[-1],"62029")["hp"], 5)
        self.assertEqual(s[-2]["villain_health"], s[-1]["villain_health"])

    def test_joys_of_life_requires_a_resolvable_choice_before_payment(self):
        s = self.play([*self.hand("61026","01088")])[-1]
        self.assertFalse(any(cid == "61026" for cid, _ in s["actions"]))

    def test_sweet_christmas_guard_blocks_villain_even_when_guard_is_defeated(self):
        self.pack = "luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62029")',
            'puzzle.FindOrCreateFace("62029").GainGuard(1,DebugRule(hero))',
            *self.tough(5), *self.hand("62006"), self.use("62006")])
        self.assertNotIn("62029", s[-1]["minions"])
        self.assertEqual(s[-2]["villain_health"], s[-1]["villain_health"])

    def test_sweet_christmas_cannot_be_played_without_any_legal_attack_target(self):
        self.pack = "luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62030")',
            'puzzle.PutIntoPlay("62029")',
            'puzzle.FindOrCreateFace("62029").GainGuard(1,DebugRule(hero))',
            *self.tough(5), *self.hand("62006"), 'puzzle.Stun(hero)'])
        self.assertFalse(any(cid == "62006" for cid, _ in s[-2]["actions"]))
        self.assertTrue(any(cid == "62006" for cid, _ in s[-1]["actions"]))

    def test_bond_respects_crisis_and_still_heals(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("61003")',
            'puzzle.PutIntoPlay("01108")', 'puzzle.SetThreat("01108",2)',
            'puzzle.Damage(hero,3)', 'puzzle.SetThreat("01097b",4)',
            *self.hand("61027","01088"), self.use("61027")])[-1]
        self.assertEqual(s["health"], 11)
        self.assertEqual(s["main_threat"], 4)
        self.assertNotIn("01108", s["side_schemes"])

    def test_alias_then_does_not_spend_old_evidence_if_placement_is_prevented(self):
        original = Message.WhenCardWouldBePlacedCounter.Send
        def prevent(message):
            # Exercise the engine's actual replacement hook, preserving the
            # existing evidence so the post-then effect would otherwise work.
            if message.trigger.paper.card_id == "61002" and message.counters == 2:
                message.SetBeInstead(message.by_effect)
            return original(message)
        with patch.object(Message.WhenCardWouldBePlacedCounter,"Send",prevent):
            s = self.play(['puzzle.Counter("61002","evidence",10)',
                'puzzle.FindOrCreateFace("01094").SetHealth(4,DebugRule(hero))',
                'puzzle.PutIntoPlay("01107")', 'puzzle.SetThreat("01107",2)',
                'puzzle.ChangeFormFor(0,"Hero")', self.use("61001a","Thwart","01107")],
                choose_other=self.choices(responses=("61002",),names=("Spend evidence",)))[-1]
        self.assertEqual(s["evidence"], 10)
        self.assertEqual(self.face(s,"01094")["hp"], 4)

    def test_cruisin_engages_from_hand_or_deck_but_not_put_into_play(self):
        self.pack = "luke_cage"
        from game.scene import SceneLoader
        def two_players(scene):
            scene.players.append(SceneLoader.NewScene("rhino",None,["spider_man"],610620).players[0])
        for source in ("hand", "deck", "put"):
            with self.subTest(source=source):
                commands = ['puzzle.PutIntoPlayFor(1,"62029")', 'puzzle.ClearHand()']
                if source == "hand":
                    commands += ['puzzle.CreateHandCards("62009")', self.use("62009","Play","62029")]
                elif source == "deck":
                    commands += ['puzzle.CreatePlayerDeck("62009")',
                        'p.PlayCardsLikeInTurn([p.player_deck.GetTop()],DebugRule(hero),ignore_resources_cost=True)']
                else:
                    commands += ['puzzle.PutIntoPlay("62009")']
                s = self.play(commands,configure_scene=two_players,
                    choose_other=self.choices(responses=("62009",),pay_like_turn=True))[-1]
                self.assertEqual("62029" in s["players"][0]["minions"], source != "put")
                self.assertEqual("62029" in s["players"][1]["minions"], source == "put")


if __name__ == "__main__":
    unittest.main()
