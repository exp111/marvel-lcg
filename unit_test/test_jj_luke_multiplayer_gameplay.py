import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestHeroMultiplayerGameplay(Gameplay, unittest.TestCase):
    pack = "jj"

    def play(self, commands, **kwargs):
        kwargs.setdefault("configure_scene", self.two_players)
        return super().play(commands, **kwargs)

    def test_now_im_ticked_off_hits_activated_players_minions(self):
        s = self.play(['puzzle.PutIntoPlay("61012")', 'puzzle.PutIntoPlay("62029")',
            'puzzle.PutIntoPlayFor(1,"62032")', 'puzzle.CreateEncounterDeck("01088")',
            'puzzle.FindOrCreateFace("01094").DoSchemes(world.const_players[1],DebugRule(hero))'])
        self.assertEqual(s[-1]["players"][0]["face"], "61001a")
        self.assertIn("62029",s[-1]["players"][0]["minions"])
        self.assertNotIn("62032",s[-1]["players"][1]["minions"])
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],5)

    def test_cottonmouth_boost_dealt_to_luke_in_other_seat(self):
        s = self.play(['puzzle.Boost("62029")'])[-1]
        self.assertIn("62029",s["players"][1]["encounters"])
        self.assertNotIn("62029",s["players"][0]["encounters"])

    def test_boost_status_applies_to_activated_player(self):
        for cid, status in (("62032","IsStunned"),("62030","IsConfused")):
            with self.subTest(cid=cid):
                self.play([f'puzzle.CreateEncounterDeck("{cid}")',
                    'puzzle.FindOrCreateFace("01094").DoSchemes(world.const_players[1],DebugRule(hero))'])
                players=self.last_game.world.const_players
                self.assertFalse(getattr(players[0].GetIdentity(),status)())
                self.assertTrue(getattr(players[1].GetIdentity(),status)())

    def test_alias_and_piecing_reward_other_player_defeating_scheme(self):
        s = self.play(['puzzle.PutIntoPlay("61007")', 'puzzle.SetThreat("61007",2)',
            'END_TURN', 'puzzle.ChangeFormFor(1,"Hero")',
            self.use("62001a","Thwart","61007")], choose_other=self.choices(responses=("61002",)))
        self.assertEqual(s[-1]["evidence"],2)
        self.assertEqual(len(s[-1]["players"][1]["hand"])-len(s[-2]["players"][1]["hand"]),3)
        self.assertEqual(s[-1]["players"][0]["hand"],s[-2]["players"][0]["hand"])

    def test_stakeout_rewards_jessica_for_lukes_basic_thwart(self):
        s = self.play(['puzzle.PutIntoPlay("01107")', 'puzzle.SetThreat("01107",4)',
            'puzzle.PutIntoPlay("61014")', self.use("61014",target="01107"),
            'END_TURN', 'puzzle.ChangeFormFor(1,"Hero")', self.use("62001a","Thwart","01107")],
            choose_other=self.choices(responses=("61014",)))
        self.assertNotIn("01107",s[-1]["side_schemes"])
        self.assertEqual(s[-1]["evidence"],2)

    def test_fogwells_gym_can_ready_other_players_defender(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlayFor(1,"62007")',
            'puzzle.Tough(hero)', 'puzzle.Exhaust(hero)', 'puzzle.Damage(hero,2)'],
            choose_other=self.choices(responses=("62007",)))[-1]
        self.assertFalse(s["exhausted"])
        self.assertTrue(self.face(s,"62007")["exhausted"])

    def test_cruisin_engages_minion_from_other_player_on_paid_play(self):
        self.pack="luke_cage"
        s = self.play(['puzzle.PutIntoPlayFor(1,"62029")', *self.hand("62009"),
                      self.use("62009","Play","62029")],
                      choose_other=self.choices(responses=("62009",)))[-1]
        self.assertIn("62029",s["players"][0]["minions"])
        self.assertNotIn("62029",s["players"][1]["minions"])

    def test_cruisin_bonus_applies_to_other_players_attack(self):
        self.pack="luke_cage"
        s = self.play(['puzzle.PutIntoPlay("62029")', 'puzzle.Damage("62029",3)',
            *self.hand("62009"), self.use("62009","Play","62029"), 'END_TURN',
            'puzzle.ChangeFormFor(1,"Hero")', self.use("61001a","Attack","62029")])
        self.assertNotIn("62029",s[-1]["players"][0]["minions"])
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],2)

    def test_sweet_christmas_does_not_damage_other_players_minions(self):
        self.pack="luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.tough(5),
            'puzzle.PutIntoPlay("62029")', 'puzzle.PutIntoPlayFor(1,"62032")',
            *self.hand("62006"), self.use("62006")])[-1]
        self.assertNotIn("62029",s["players"][0]["minions"])
        self.assertIn("62032",s["players"][1]["minions"])
        self.assertEqual(self.face(s,"62032")["hp"],4)

    def test_breakthrough_only_responds_to_owners_alias(self):
        # Give the other seat the event to isolate its ownership check.
        s = self.play(['puzzle.ClearHandFor(1)', 'puzzle.CreateHandCardsFor(1,"61005")',
            'puzzle.Exhaust(world.const_players[1].GetIdentity())', 'puzzle.Counter("61002","evidence",1)'],
            choose_other=self.choices(responses=("61005",)))[-1]
        self.assertEqual(s["players"][1]["hand"],["61005"])
        self.assertTrue(self.face(s,"62001b")["exhausted"])

    def test_indomitable_will_hinder_scales_per_player(self):
        s = self.play(['puzzle.Reveal("61032")'])[-1]
        self.assertEqual(self.face(s,"61032")["threat"],10)

    def test_work_life_balance_reveal_given_to_jessica_from_lukes_turn(self):
        self.play(['END_TURN', 'puzzle.Reveal("61030")'])
        obligation=self.last_game.world.const_players[0].obligations_area.Get()[0]
        self.assertEqual(obligation.paper.card_id,"61030")
        self.assertEqual(obligation.GetGaveToPlayer(),self.last_game.world.const_players[0])


if __name__ == "__main__":
    unittest.main()
