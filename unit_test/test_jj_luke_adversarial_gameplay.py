"""Mixed-board and zone-transition regressions for every face in both packs.

These complement the card-specific outcome tests.  Rendering the real controller's
actions after every mutation forces its target predicates to see unrelated card
types, both identity forms, and cards belonging to another player.
"""
import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay
from game.scene import SceneLoader
from game.test.jj_luke_harness import load_pack_reference


class TestPackAdversarialGameplay(Gameplay, unittest.TestCase):
    pack = "jj"

    @staticmethod
    def with_spider_man(scene):
        # A third identity avoids illegal unique-name conflicts with either
        # pack's signature partner ally while exercising another controller.
        scene.players.append(SceneLoader.NewScene("rhino", None, ["spider_man"], 610620).players[0])

    @staticmethod
    def four_players(scene):
        scene.players.extend(SceneLoader.NewScene("rhino", None,
            ["luke_cage", "spider_man", "black_panther"], 610620).players)

    def mixed_board(self, cid):
        # Piecing ignores the side-scheme limit, so both sorts of side scheme
        # remain in play when the card under test is itself a player scheme.
        player_scheme = "61028" if cid == "61007" else "61007"
        return [
            'puzzle.ClearHand()',
            f'puzzle.PutIntoPlay("{player_scheme}")',
            'puzzle.PutIntoPlay("01107")',
            'puzzle.PutIntoPlay("01108")',
            'puzzle.FindOrCreateFace("01108").GainPermanent(1,DebugRule(hero))',
            'puzzle.PutIntoPlay("01102")',
            'puzzle.PutIntoPlay("01083")',
            'puzzle.PutIntoPlay("62012")' if cid != "62012" else 'puzzle.PutIntoPlay("62013")',
        ]

    def check_persistent_card(self, pack, card):
        self.pack = pack
        cid = card["card_id"]
        for multiplayer in (False, True):
            with self.subTest(card=cid, multiplayer=multiplayer):
                commands = self.mixed_board(cid)
                if multiplayer:
                    commands += ['puzzle.PutIntoPlayFor(1,"61038")',
                                 'puzzle.PutIntoPlayFor(1,"62032")']
                if cid == "62031":
                    commands += ['puzzle.PutIntoPlay("62029")']
                commands += [f'puzzle.PutIntoPlay("{cid}")']
                # Damage, status and form changes refresh passive modifiers and
                # target selection while all these different card types coexist.
                commands += ['puzzle.Damage(hero,1)', 'puzzle.Damage("01083",1)',
                             'puzzle.Exhaust(hero)', 'puzzle.Tough(hero)',
                             'puzzle.ChangeFormFor(0,"Hero")',
                             'puzzle.SetThreat("01107",4)',
                             'puzzle.ChangeFormFor(0,"Identity")']
                if cid != "61002":
                    commands += [f'puzzle.Discard("{cid}")', f'puzzle.PutIntoPlay("{cid}")']
                snapshots = self.play(commands,
                    configure_scene=self.with_spider_man if multiplayer else None)
                self.assertIn(cid, [f["cid"] for f in snapshots[-1]["field"]])
                self.assertIn("01107", snapshots[-1]["side_schemes"])
                self.assertIn("61028" if cid == "61007" else "61007",
                              snapshots[-1]["side_schemes"])

    def test_all_player_cards_offer_actions_on_mixed_boards_in_both_forms(self):
        for pack, cards in self.data.items():
            ids = [c["card_id"] for c in cards if "RES" in c["desc"]]
            self.pack = pack
            for multiplayer in (False, True):
                with self.subTest(pack=pack, multiplayer=multiplayer):
                    self.play([*self.mixed_board(""),
                        'puzzle.PutIntoPlay("61014")',
                        'puzzle.CreateHandCards(' + ','.join(repr(cid) for cid in ids) + ')',
                        'puzzle.ChangeFormFor(0,"Hero")',
                        'puzzle.Stun(hero)', 'puzzle.Confuse(hero)',
                        'puzzle.ChangeFormFor(0,"Identity")'],
                        configure_scene=self.with_spider_man if multiplayer else None)

    def test_hellcat_paid_reentry_does_not_inherit_free_entry_discard(self):
        for leave in ('puzzle.Gain("61025")', 'puzzle.Discard("61025")'):
            with self.subTest(leave=leave):
                s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.hand("61025"),
                    self.use("61025", "Action"), leave, 'puzzle.Gain("61025")',
                    'puzzle.CreateHandCards("62025","62026")', self.use("61025", "Play"),
                    'Message.WhenPhaseEnd(world.phase_id,"Player",world).Send()'])[-1]
                self.assertIn("61025", s["controlled"])

    def test_hellcat_free_reentry_still_discards_at_phase_end(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.hand("61025"),
            self.use("61025", "Action"), 'puzzle.Gain("61025")', self.use("61025", "Action"),
            'Message.WhenPhaseEnd(world.phase_id,"Player",world).Send()'])[-1]
        self.assertNotIn("61025", s["controlled"])
        self.assertIn("61025", s["discard"])

    def test_hellcat_returned_to_hand_is_not_discarded_at_phase_end(self):
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.hand("61025"),
            self.use("61025", "Action"), 'puzzle.Gain("61025")',
            'Message.WhenPhaseEnd(world.phase_id,"Player",world).Send()'])[-1]
        self.assertIn("61025", s["hand"])

    def test_hulk_cannot_thwart_even_when_righteous_purpose_buffs_him(self):
        s = self.play(['puzzle.PutIntoPlay("62020")', 'puzzle.Damage("62020",4)',
                       'puzzle.PutIntoPlay("62019")'])[-1]
        self.assertEqual(self.face(s,"62020")["atk"], 4)
        self.assertNotIn(("62020","Thwart"), s["actions"])

    @staticmethod
    def tower_defense(scene):
        scene.campaign = SceneLoader.NewScene("the_tower_defense", None, ["luke_cage"], 610620).campaign

    def test_sweet_christmas_only_hits_chosen_villain_and_own_minions(self):
        self.pack = "luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")', *self.tough(5),
            'puzzle.PutIntoPlay("62029")', *self.hand("62006"), self.use("62006")],
            configure_scene=self.tower_defense,
            choose_other=self.choices(names=("Choose a villain",), target="21095"))
        self.assertEqual(self.face(s[-1],"21092")["hp"], self.face(s[-2],"21092")["hp"])
        self.assertEqual(self.face(s[-2],"21095")["hp"] - self.face(s[-1],"21095")["hp"], 5)
        self.assertNotIn("62029", s[-1]["minions"])

    def test_observe_schemes_with_the_chosen_villain(self):
        self.pack = "luke_cage"
        s = self.play(['puzzle.ChangeFormFor(0,"Hero")',
            # Proxima is not the default active villain in this setup.
            'puzzle.Confuse("21092")', *self.hand("62035","62025"), self.use("62035")],
            configure_scene=self.tower_defense,
            choose_other=self.choices(names=("Choose a villain",), target="21092"))
        self.assertFalse(self.face(s[-1],"21092")["confused"])
        self.assertEqual(s[-1]["main_threat"], s[-2]["main_threat"])
        self.assertEqual(s[-1]["tough"], 1)

    def test_alias_can_defeat_an_affordable_nondefault_villain(self):
        # Isolate a legal two-villain board without Tower Defense's printed
        # prohibition on defeating either villain while the other has health.
        s = self.play(['puzzle.PutIntoPlay("01113")',
            'puzzle.FindOrCreateFace("01113").SetHealth(4,DebugRule(hero))',
            'puzzle.Counter("61002","evidence",2)', 'puzzle.PutIntoPlay("01107")',
            'puzzle.SetThreat("01107",2)', 'puzzle.ChangeFormFor(0,"Hero")',
            self.use("61001a","Thwart","01107")],
            choose_other=self.choices(responses=("61002",), names=("Spend evidence",)))
        self.assertEqual(s[-1]["evidence"], 0)
        self.assertEqual(self.face(s[-1],"01094")["hp"], self.face(s[-2],"01094")["hp"])
        self.assertNotIn("01113", [f["cid"] for f in s[-1]["field"]])

    def test_augmented_jaws_fallback_attaches_to_active_villain(self):
        self.pack = "luke_cage"
        self.play(['puzzle.Reveal("62031")'], configure_scene=self.tower_defense)
        jaws = next(c.face for c in self.last_game.world.object_manager.card_dict.values()
                    if c.face.paper.card_id == "62031" and c.face.IsInPlay())
        self.assertEqual(jaws.GetBindFace().paper.card_id, "21095")

    def test_run_them_to_ground_only_protects_chosen_villain(self):
        s = self.play(['puzzle.PutIntoPlay("61020")', 'puzzle.SetThreat("61020",1)',
            'puzzle.ChangeFormFor(0,"Hero")', self.use("61001a","Thwart","61020"),
            'puzzle.Damage("21092",1)', 'puzzle.Damage("21095",1)'],
            configure_scene=self.tower_defense,
            choose_other=self.choices(names=("Choose a villain",), target="21095"))
        self.assertEqual(self.face(s[-1],"21092")["hp"], 8)
        self.assertEqual(self.face(s[-1],"21095")["hp"], 8)

    @staticmethod
    def wrecking_crew(scene):
        scene.campaign = SceneLoader.NewScene("the_wrecking_crew", None, ["jessica_jones"], 610620).campaign

    def test_lay_the_trap_reprint_only_damages_active_wrecking_crew_villain(self):
        s = self.play(['puzzle.FindOrCreateFace("07017").SetActive(DebugRule(hero))',
            'puzzle.PutIntoPlay("61021")', 'puzzle.SetThreat("61021",1)',
            'puzzle.ChangeFormFor(0,"Hero")', self.use("61001a","Thwart","61021")],
            configure_scene=self.wrecking_crew)
        self.assertEqual(self.face(s[-2],"07017")["hp"] - self.face(s[-1],"07017")["hp"], 5)
        for cid in ("07002", "07032", "07046"):
            self.assertEqual(self.face(s[-2],cid)["hp"], self.face(s[-1],cid)["hp"])

    def test_lay_the_trap_defeating_player_chooses_villain(self):
        def setup(scene):
            self.tower_defense(scene)
            self.two_players(scene)
        chooser_ids = []
        choose_villain = self.choices(names=("Choose a villain",), target="21092")
        def choose(prompt):
            if any(o["name"] == "Choose_a_villain" for o in prompt.options):
                chooser_ids.append(prompt.player_id)
            return choose_villain(prompt)
        s = self.play(['puzzle.PutIntoPlay("61021")', 'puzzle.SetThreat("61021",2)',
            'END_TURN', 'puzzle.ChangeFormFor(1,"Hero")', self.use("62001a","Thwart","61021")],
            configure_scene=setup, choose_other=choose)
        self.assertEqual(chooser_ids, [1])
        self.assertEqual(self.face(s[-2],"21092")["hp"] - self.face(s[-1],"21092")["hp"], 10)

    def test_second_chance_four_players_choose_independently_with_stakeout_in_play(self):
        signature_cards = ("61004", "62004", "01002", "01042")
        accept = self.choices(names=("Shuffle all identity",))
        decline = self.choices()
        def choose(prompt):
            return accept(prompt) if prompt.player_id in (0, 2) else decline(prompt)
        commands = ['puzzle.PutIntoPlay("61014")', *self.hand("61028"), self.use("61028","Play")]
        for player_id, cid in enumerate(signature_cards):
            commands += [f'puzzle.CreateHandCardsFor({player_id},"{cid}","62025")',
                         f'puzzle.ClearHandFor({player_id})']
        commands += ['puzzle.SetThreat("61028",3)', 'puzzle.ChangeFormFor(0,"Hero")',
                     self.use("61001a","Thwart","61028")]
        s = self.play(commands, configure_scene=self.four_players, choose_other=choose)
        self.assertEqual(self.face(s[4],"61028")["threat"], 12)
        self.assertNotIn("61028", s[-1]["side_schemes"])
        self.assertIn("61014", s[-1]["controlled"])
        for player_id, player in enumerate(self.last_game.world.const_players):
            discarded = [f.paper.card_id for f in player.discard_pile.Get()]
            deck = [f.paper.card_id for f in player.player_deck.Get()]
            self.assertIn("62025", discarded)
            self.assertEqual(signature_cards[player_id] in discarded, player_id not in (0, 2))
            if player_id in (0, 2):
                self.assertIn(signature_cards[player_id], deck)

    def check_encounter_boost(self, pack, card):
        self.pack = pack
        self.play([*self.mixed_board(card["card_id"]),
            'puzzle.PutIntoPlay("61014")',
            f'puzzle.Boost("{card["card_id"]}")'], configure_scene=self.with_spider_man)


# Separate test names identify the exact card even when one candidate crashes.
for _pack, _cards in load_pack_reference().items():
    for _card in _cards:
        if _card["type"] in ("Ally", "Support", "Upgrade", "PlayerSideScheme", "Minion", "SideScheme", "Attachment", "Obligation"):
            def _test(self, pack=_pack, card=_card):
                self.check_persistent_card(pack, card)
            setattr(TestPackAdversarialGameplay, "test_mixed_board_" + _card["card_id"], _test)
        if "Boost" in _card["desc"]:
            def _boost_test(self, pack=_pack, card=_card):
                self.check_encounter_boost(pack, card)
            setattr(TestPackAdversarialGameplay, "test_mixed_board_boost_" + _card["card_id"], _boost_test)


if __name__ == "__main__":
    unittest.main()
