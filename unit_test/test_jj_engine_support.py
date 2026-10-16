import unittest

from engine import Engine
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.jj_luke_harness import build_scene
from unit_test import test_jj_luke_first_pass as fixtures


class TestJessicaEngineSupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.TestFirstPassPacks.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixtures.TestFirstPassPacks.tearDownClass.__func__(cls)

    run_commands = fixtures.TestFirstPassPacks.run_commands

    def observe(self, world, player, prompt):
        faces = [card.face for card in world.object_manager.card_dict.values()
                 if card.face.IsInPlay()]
        return {
            "round": world.round_id,
            "phase": world.phase_id,
            "skip_pending": world.phase.skip_next_villain_phase,
            "thwart": getattr(player.GetIdentity(), "thwart", None),
            "confused": player.GetIdentity().IsConfused(),
            "icons": {f.paper.card_id: tuple(f.GetKeyword(k) for k in
                ("Acceleration", "Amplify", "Crisis", "Hazard")) for f in faces},
            "mitigated_count": sum(f.paper.card_id == "61040" for f in faces),
            "hand_sizes": [p.hand_cards.GetSize() for p in world.players],
            "encounter_counts": [p.dealt_encounter_cards.GetSize() for p in world.players],
            "actions": [(world.object_manager.card_dict[o["bind_id"]].face.paper.card_id, o["name"])
                        for o in prompt.options],
            "normal_thwart_targets": [world.object_manager.card_dict[int(t.get("id", t) if isinstance(t, dict) else t)].face.paper.card_id
                for o in prompt.options if o["name"] == "Thwart" and o["bind_id"] == player.GetIdentity().card.object_id
                for t in o.get("all_legal_targets", [])],
        }

    def play(self, commands, **kwargs):
        return self.run_commands("jj", commands, extra_snapshot=self.observe, **kwargs)

    @staticmethod
    def two_players(scene):
        scene.players.append(build_scene("luke_cage").players[0])

    def pay_upkeep(self, *, decline_player=None):
        asked = []

        def choose(prompt):
            if prompt.event_name != "WhenPlayerChooseAbility":
                return NotImplemented
            options = [o for o in prompt.options if o.get("target_payment") and
                       any(p["cost"] == "1" for p in o["target_payment"].values())]
            if not options:
                return NotImplemented
            asked.append(prompt.player_id)
            if prompt.player_id == decline_player:
                return CommandDescriptor()
            option = options[0]
            payment = next(iter(option["target_payment"].values()))["payment"]
            self.assertTrue(payment)
            return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option), [],
                                     [str(next(iter(payment[0])))])

        return asked, choose

    def test_grapnel_while_exhausted_uses_basic_power_and_cleans_up(self):
        snapshots = self.play([
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.SetThreat("01097b",6)',
            'puzzle.PutIntoPlay("61023")', 'puzzle.Exhaust(hero)', ("61023", "Grapnel_Launcher"),
        ], accept_events=("WhenPlayerChooseAbility", "AfterUnitUseBasicPower"))
        last = snapshots[-1]
        self.assertEqual(last["main_threat"], 2)
        self.assertEqual(last["evidence"], 1)
        self.assertTrue(last["exhausted"])
        self.assertEqual(last["thwart"], 3)
        self.assertNotIn("61023", last["controlled"])
        self.assertNotIn(("61001a", "Thwart"), last["actions"])

    def test_grapnel_does_not_exhaust_a_ready_hero(self):
        last = self.play([
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.SetThreat("01097b",6)',
            'puzzle.PutIntoPlay("61023")', ("61023", "Grapnel_Launcher"),
        ], accept_events=("WhenPlayerChooseAbility",))[-1]
        self.assertFalse(last["exhausted"])
        self.assertEqual(last["main_threat"], 2)
        self.assertEqual(last["thwart"], 3)

    def test_grapnel_confused_replaces_basic_thwart(self):
        last = self.play([
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.SetThreat("01097b",6)',
            'puzzle.PutIntoPlay("61023")', 'puzzle.Exhaust(hero)',
            'puzzle.Confuse(hero)', ("61023", "Grapnel_Launcher"),
        ], accept_events=("WhenPlayerChooseAbility", "AfterUnitUseBasicPower"))[-1]
        self.assertFalse(last["confused"])
        self.assertEqual(last["main_threat"], 6)
        self.assertEqual(last["evidence"], 0)
        self.assertEqual(last["thwart"], 3)
        self.assertTrue(last["exhausted"])

    def test_grapnel_ignores_crisis_and_patrol_for_only_its_thwart(self):
        def target_main(prompt):
            if prompt.event_name != "WhenPlayerChooseAbility" or not any(
                    o["name"] == "Thwart" for o in prompt.options):
                return NotImplemented
            choice = HeadlessDeviceManager._DefaultChoice(prompt)
            world = Engine.game.world
            for target in prompt.options[0].get("all_legal_targets", []):
                tid = target.get("id", target) if isinstance(target, dict) else target
                if world.object_manager.card_dict[int(tid)].face.paper.card_id == "01097b":
                    choice.targets = [str(tid)]
                    return choice
            self.fail("Granted thwart did not allow the main scheme")

        last = self.play([
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.SetThreat("01097b",6)',
            'puzzle.PutIntoPlay("01107")',
            'puzzle.FindOrCreateFace("01107").GainCrisis(1,DebugRule(hero))',
            'puzzle.PutIntoPlay("62029")',
            'puzzle.FindOrCreateFace("62029").GainPatrol(1,DebugRule(hero))',
            'puzzle.PutIntoPlay("61023")', ("61023", "Grapnel_Launcher"),
        ], choose_other=target_main)[-1]
        self.assertEqual(last["main_threat"], 2)
        self.assertEqual(last["icons"]["01107"][2], 1)
        # Normal thwart remains subject to the crisis and patrol restrictions.
        self.assertEqual(last["thwart"], 3)
        self.assertNotIn("01097b", last["normal_thwart_targets"])
        self.assertIn("01107", last["normal_thwart_targets"])

    def test_grapnel_retains_additional_basic_thwart_cost(self):
        add_cost = ('hero.effect.Find(func_name="THW")[0].cost_func.Add('
                    '__import__("game.ability.cost_func",fromlist=["CostFunc"])'
                    '.CostFunc.Discard("YourHandCards"))')
        setup = [
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.SetThreat("01097b",6)',
            'puzzle.ClearHand()', 'puzzle.PutIntoPlay("61023")', add_cost,
        ]
        last = self.play(setup)[-1]
        self.assertNotIn(("61023", "Grapnel_Launcher"), last["actions"])
        snapshots = self.play(setup + [
            'puzzle.CreateHandCards("01088")', ("61023", "Grapnel_Launcher"),
        ], accept_events=("WhenPlayerChooseAbility",))
        self.assertEqual(snapshots[-2]["hand_sizes"], [1])
        self.assertEqual(snapshots[-1]["hand_sizes"], [0])
        self.assertEqual(snapshots[-1]["main_threat"], 2)

    def test_grapnel_does_not_waive_an_additional_exhaust_cost(self):
        last = self.play([
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.SetThreat("01097b",6)',
            'puzzle.PutIntoPlay("61023")',
            'hero.effect.Find(func_name="THW")[0].cost_func.Add(__import__("game.ability.cost_func",fromlist=["CostFunc"]).CostFunc.Exhaust("This"))',
            ("61023", "Grapnel_Launcher"),
        ], accept_events=("WhenPlayerChooseAbility",))[-1]
        self.assertTrue(last["exhausted"])
        self.assertEqual(last["main_threat"], 2)

    def test_run_them_to_ground_skips_whole_phase_and_keeps_immunity(self):
        snapshots = self.play([
            'puzzle.PutIntoPlay("61020")', 'puzzle.SetThreat("61020",1)',
            'puzzle.ChangeFormFor(0,"Hero")', ("61001a", "Thwart", "61020"),
            'puzzle.Damage("01094",2)', 'END_TURN',
            'puzzle.Damage("01094",2)',
        ])
        defeated = snapshots[4]
        after = snapshots[-1]
        self.assertEqual(defeated["encounter_counts"], [1])
        self.assertTrue(defeated["skip_pending"])
        self.assertEqual(after["round"], 2)
        self.assertEqual(after["phase"], 2)
        self.assertEqual(after["encounter_counts"], [1])
        self.assertFalse(after["skip_pending"])
        self.assertEqual(after["villain_health"], defeated["villain_health"])
        self.assertEqual(after["main_threat"], defeated["main_threat"])
        self.assertEqual(after["health"], defeated["health"])

    def test_run_them_to_ground_immunity_ends_at_actual_villain_phase_start(self):
        snapshots = self.play([
            'puzzle.PutIntoPlay("61020")', 'puzzle.SetThreat("61020",1)',
            'puzzle.ChangeFormFor(0,"Hero")', ("61001a", "Thwart", "61020"),
            'END_TURN', 'puzzle.ChangeFormFor(0,"Identity")', 'END_TURN',
            'puzzle.Damage("01094",2)',
        ])
        self.assertEqual(snapshots[-1]["round"], 3)
        self.assertEqual(snapshots[-1]["villain_health"], snapshots[4]["villain_health"] - 2)
        self.assertEqual(snapshots[-1]["encounter_counts"], [0])

    def test_run_them_to_ground_deals_each_player_an_immediate_card(self):
        last = self.play([
            'puzzle.PutIntoPlay("61020")', 'puzzle.SetThreat("61020",1)',
            'puzzle.ChangeFormFor(0,"Hero")', ("61001a", "Thwart", "61020"),
        ], configure_scene=self.two_players)[-1]
        self.assertEqual(last["encounter_counts"], [1, 1])
        self.assertTrue(last["skip_pending"])

    def test_cannot_take_damage_also_blocks_unpreventable_damage(self):
        snapshots = self.play([
            'puzzle.PutIntoPlay("61020")', 'puzzle.SetThreat("61020",1)',
            'puzzle.ChangeFormFor(0,"Hero")', ("61001a", "Thwart", "61020"),
            'puzzle.FindOrCreateFace("01094").TakeDamage(hero,__import__("game.element.damage_property",fromlist=["DamageProperty"]).DamageProperty(3,unpreventable=True),DebugRule(hero))',
        ])
        self.assertEqual(snapshots[-1]["villain_health"], snapshots[-2]["villain_health"])

    def test_multiple_skip_requests_apply_to_the_same_next_phase(self):
        from game.world.phase import Phase
        phase = Phase()
        phase.SkipNextVillainPhase()
        phase.SkipNextVillainPhase()
        self.assertTrue(phase.ConsumeVillainPhaseSkip())
        self.assertFalse(phase.ConsumeVillainPhaseSkip())

    def test_temporary_bonus_waits_through_skipped_villain_phases(self):
        snapshots = self.play([
            'puzzle.ChangeFormFor(0,"Hero")',
            'hero.TemporaryGain(DebugRule(hero),None,until_next_villain_phase_begin=True,attack=1)',
            'world.phase.SkipNextVillainPhase()', 'END_TURN',
            'world.phase.SkipNextVillainPhase()', 'END_TURN', 'END_TURN',
        ])
        self.assertEqual(snapshots[-2]["round"], 3)
        self.assertEqual(snapshots[-2]["attack"], 3)
        self.assertEqual(snapshots[-1]["round"], 4)
        self.assertEqual(snapshots[-1]["attack"], 2)

    def test_mitigated_suppresses_new_icons_and_restores_them(self):
        snapshots = self.play([
            'puzzle.PutIntoPlay("01107")',
            'puzzle.FindOrCreateFace("01107").GainKeyword(2,"Amplify",DebugRule(hero))',
            'puzzle.FindOrCreateFace("01107").GainKeyword(1,"Crisis",DebugRule(hero))',
            'puzzle.FindOrCreateFace("01107").GainKeyword(1,"Acceleration",DebugRule(hero))',
            'puzzle.CreateHandCards("61040")', ("61040", "Play", "01107"),
            'puzzle.FindOrCreateFace("01107").GainKeyword(2,"Hazard",DebugRule(hero))',
            'puzzle.Discard("61040")',
        ])
        self.assertEqual(snapshots[-2]["icons"]["01107"], (0, 0, 0, 0))
        before, after = snapshots[5]["icons"]["01107"], snapshots[-1]["icons"]["01107"]
        self.assertEqual(after, (before[0], before[1], before[2], before[3] + 2))

    def test_mitigated_round_upkeep_declined_restores_icons(self):
        snapshots = self.play([
            'puzzle.PutIntoPlay("01107")', 'puzzle.CreateHandCards("61040")',
            ("61040", "Play", "01107"), 'Message.WhenRoundEnd(world).Send()',
        ])
        self.assertEqual(snapshots[-2]["mitigated_count"], 1)
        self.assertEqual(snapshots[-1]["mitigated_count"], 0)
        self.assertEqual(snapshots[-1]["icons"]["01107"], snapshots[1]["icons"]["01107"])

    def test_mitigated_each_player_pays_from_their_own_resources(self):
        asked, choose = self.pay_upkeep()
        snapshots = self.play([
            'puzzle.PutIntoPlay("01107")', 'puzzle.CreateHandCards("61040")',
            ("61040", "Play", "01107"), 'Message.WhenRoundEnd(world).Send()',
        ], configure_scene=self.two_players, choose_other=choose)
        self.assertEqual(asked, [0, 1])
        self.assertEqual(snapshots[-1]["mitigated_count"], 1)
        self.assertEqual(snapshots[-1]["hand_sizes"], [n - 1 for n in snapshots[-2]["hand_sizes"]])
        self.assertEqual(snapshots[-1]["icons"]["01107"], (0, 0, 0, 0))

    def test_mitigated_upkeep_still_resolves_when_villain_phase_is_skipped(self):
        snapshots = self.play([
            'puzzle.PutIntoPlay("01107")', 'puzzle.CreateHandCards("61040")',
            ("61040", "Play", "01107"), 'world.phase.SkipNextVillainPhase()', 'END_TURN',
        ])
        self.assertEqual(snapshots[-1]["round"], 2)
        self.assertEqual(snapshots[-1]["mitigated_count"], 0)
        self.assertEqual(snapshots[-1]["encounter_counts"], [0])
        self.assertEqual(snapshots[-1]["icons"]["01107"], snapshots[1]["icons"]["01107"])

    def test_mitigated_one_player_declining_discards_after_every_player_is_asked(self):
        asked, choose = self.pay_upkeep(decline_player=0)
        snapshots = self.play([
            'puzzle.PutIntoPlay("01107")', 'puzzle.CreateHandCards("61040")',
            ("61040", "Play", "01107"), 'Message.WhenRoundEnd(world).Send()',
        ], configure_scene=self.two_players, choose_other=choose)
        self.assertEqual(asked, [0, 1])
        self.assertEqual(snapshots[-1]["mitigated_count"], 0)
        before, after = snapshots[-2]["hand_sizes"], snapshots[-1]["hand_sizes"]
        self.assertEqual(after, [before[0], before[1] - 1])

    def test_mitigated_stacks_and_cleans_up_when_reattached_or_blanked(self):
        snapshots = self.play([
            'puzzle.PutIntoPlay("01107")',
            'puzzle.CreateHandCards("61040","61040")',
            ("61040", "Play", "01107"), ("61040", "Play", "01107"),
            'puzzle.Discard("61040")',
            'puzzle.FindOrCreateFace("61040").TreatAsIfBlankInternal(1,hero.effect.GetAll()[0])',
            'puzzle.FindOrCreateFace("61040").TreatAsIfBlankInternal(-1,hero.effect.GetAll()[0])',
            'puzzle.FindOrCreateFace("61040").AttachTo2(hero,DebugRule(hero))',
        ])
        self.assertEqual(snapshots[4]["mitigated_count"], 2)
        self.assertEqual(snapshots[5]["icons"]["01107"], (0, 0, 0, 0))
        original = snapshots[1]["icons"]["01107"]
        self.assertEqual(snapshots[6]["icons"]["01107"], original)
        self.assertEqual(snapshots[7]["icons"]["01107"], (0, 0, 0, 0))
        self.assertEqual(snapshots[8]["icons"]["01107"], original)


if __name__ == "__main__":
    unittest.main()
