import contextlib
import io
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from engine import Engine
from build import Build
from engine.log import Log, Notify
from cards.database import CardsDB
from game.card.factory import CardFactory
from game.element.damage_property import DamageProperty
from game.message import Message
from game.operate.worlds import Worlds
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.jj_luke_harness import load_pack_reference, build_scene
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


class TestFirstPassPacks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()
        cls.original_papers = dict(CardsDB.papers)
        cls.original_links = dict(CardsDB.ability_link_cards)
        cls.original_cache = dict(CardsDB.ability_cache)
        cls.original_sets = {key: list(value) for key, value in CardsDB.sets_cards.items()}
        cls.data = load_pack_reference()

    @classmethod
    def tearDownClass(cls):
        for target, original in ((CardsDB.papers, cls.original_papers),
                                 (CardsDB.ability_link_cards, cls.original_links),
                                 (CardsDB.ability_cache, cls.original_cache),
                                 (CardsDB.sets_cards, cls.original_sets)):
            target.clear()
            target.update(original)

    def run_commands(self, pack, commands, *, accept_events=(), configure_scene=None,
                     extra_snapshot=None, choose_other=None):
        scene = build_scene(pack)
        if configure_scene:
            configure_scene(scene)
        commands = iter(commands)
        snapshots = []

        def choose(prompt):
            if len(devices.prompts) > 400:
                raise AssertionError("Unexpected repeated prompt")
            if prompt.event_name == "WhenPlayerInTurn":
                world = Engine.game.world
                player = world.GetFirstPlayer()
                face = player.GetIdentity()
                snapshots.append({
                    "face": face.paper.card_id, "health": face.health,
                    "tough": face.tough, "attack": getattr(face, "attack", None),
                    "allies": {a.paper.card_id: (a.attack, a.thwart, a.health, a.tough) for a in player.GetControlAllies()},
                    "evidence": sum(s.GetCounters("evidence") for s in player.GetControlCards() if s.name == "Alias Investigations"),
                    "side_schemes": [s.paper.card_id for s in world.area_schemes_side.Get()],
                    "exhausted": face.IsExhaust(),
                    "minions": [m.paper.card_id for m in player.GetEngagedMinions()],
                    "encounters": [c.paper.card_id for c in player.dealt_encounter_cards.Get()],
                    "controlled": [c.paper.card_id for c in player.GetControlCards()],
                    "villain_health": sum(v.health for v in Worlds.GetAllVillains(world)),
                    "main_threat": sum(s.threat for s in world.area_schemes_main.Get()),
                })
                if extra_snapshot:
                    snapshots[-1].update(extra_snapshot(world, player, prompt))
                command = next(commands, None)
                if command is None:
                    return None
                if callable(command):
                    return command(prompt)
                if command == "END_TURN":
                    return CommandDescriptor()
                if isinstance(command, tuple):
                    cid, name = command[:2]
                    options = [option for option in prompt.options
                        if world.object_manager.card_dict[option["bind_id"]].face.paper.card_id == cid
                        and (name is None or option["name"] == name)]
                    self.assertTrue(options, (command, prompt.options))
                    selected = SimpleNamespace(options=[options[0]])
                    choice = HeadlessDeviceManager._DefaultChoice(selected)
                    if len(command) == 3:
                        ids = [target.get("id", target) if isinstance(target, dict) else target
                               for target in options[0].get("all_legal_targets", [])]
                        targets = [str(t) for t in ids
                                   if world.object_manager.card_dict[int(t)].face.paper.card_id == command[2]]
                        self.assertTrue(targets, (command, options))
                        choice.targets = targets[:1]
                    return choice
                Engine.game.controller_manager.console.SetCommand(command, world)
                return CommandDescriptor()
            if choose_other:
                choice = choose_other(prompt)
                if choice is not NotImplemented:
                    return choice
            if prompt.event_name in accept_events:
                return HeadlessDeviceManager._DefaultChoice(prompt)
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        output = io.StringIO()
        with (contextlib.redirect_stdout(output),
              patch("game.test.v18_timing_harness.initialize_database"),
              patch.object(WorldRender, "ErrorOccurred") as errors,
              patch.object(Log, "Warn") as warnings,
              patch.object(Notify, "Game") as notices,
              patch.object(Engine, "SaveCrash")):
            game = run_scene_with_devices(scene, devices)
        self.last_game_output = output.getvalue()
        self.last_game = game
        self.last_prompts = devices.prompts
        self.assertFalse(errors.called, (errors.call_args_list, output.getvalue()[-5000:]))
        self.assertFalse(warnings.called, (warnings.call_args_list, output.getvalue()[-5000:]))
        self.assertFalse(notices.called, (notices.call_args_list, output.getvalue()[-5000:]))
        self.assertIsNotNone(devices.stopped_prompt, output.getvalue()[-5000:])
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return snapshots

    def test_every_card_face_constructs_with_real_metadata(self):
        world = SimpleNamespace(GetPlayerNumIcon=lambda: 2)
        count = 0
        for cards in self.data.values():
            for card in cards:
                with self.subTest(card=card["card_id"]):
                    with patch.object(Build, "release", False):
                        face = CardFactory.CreateFace(CardsDB.papers[card["card_id"]], world)
                    self.assertTrue(face.ability.abilities)
                    count += 1
        self.assertEqual(count, 81)

    def test_persistent_cards_enter_play_without_errors(self):
        for pack, cards in self.data.items():
            for card in cards:
                cid = card["card_id"]
                if card["type"] not in ("Ally", "Upgrade", "Support", "PlayerSideScheme", "Minion", "SideScheme", "Attachment") or cid == "61002":
                    continue
                with self.subTest(card=cid):
                    commands = []
                    if cid in ("62009", "62031"):
                        commands.append('puzzle.PutIntoPlay("62029")')
                    commands.append('puzzle.PutIntoPlay("'+cid+'")')
                    self.run_commands(pack, commands)

    def test_all_player_cards_can_be_inspected_in_hand(self):
        for pack, cards in self.data.items():
            ids = [c["card_id"] for c in cards if "RES" in c["desc"]]
            with self.subTest(pack=pack):
                self.run_commands(pack, [
                    'puzzle.ClearHand()',
                    'puzzle.CreateHandCards('+','.join(repr(cid) for cid in ids)+')',
                    'puzzle.ChangeFormFor(0,"Hero")',
                ])

    def test_jessica_setup_has_alias(self):
        snapshots = self.run_commands("jj", [])
        self.assertEqual(snapshots[0]["face"], "61001b")
        self.assertEqual(snapshots[0]["evidence"], 0)

    def test_incognito_blocks_changing_back_for_the_phase(self):
        snapshots = self.run_commands("jj", [
            ("61001b", "Incognito_Mode"), 'puzzle.ChangeFormFor(0,"Identity")',
        ])
        self.assertEqual([s["face"] for s in snapshots], ["61001b", "61001a", "61001a"])

    def test_jessica_basic_thwart_and_alias_response_generate_evidence(self):
        snapshots = self.run_commands("jj", [
            'puzzle.PutIntoPlay("01107")', 'puzzle.SetThreat("01107",2)',
            ("61001b", "Incognito_Mode"), ("61001a", "Thwart"),
        ], accept_events=("AfterUnitUseBasicPower", "AfterSchemeBeDefeated"))
        self.assertEqual(snapshots[-1]["evidence"], 3)

    def test_burstein_process_adds_two_then_one_tough(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.PutIntoPlay("62008")', ("62008", None),
            'puzzle.Ready("62008")', ("62008", None),
        ])
        self.assertEqual([s["tough"] for s in snapshots], [0,0,2,2,3])

    def test_metal_bracer_can_stop_one_damage_before_tough(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.PutIntoPlay("62010")', 'puzzle.Tough(hero)',
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Damage(hero,1)',
        ], accept_events=("WhenFaceWouldDealDamage",))
        self.assertEqual((snapshots[-1]["tough"],snapshots[-1]["health"]), (1,10))

    def test_stakeout_thwart_bonus_and_defeat_reward(self):
        snapshots = self.run_commands("jj", [
            'puzzle.PutIntoPlay("01107")', 'puzzle.SetThreat("01107",4)',
            'puzzle.PutIntoPlay("61014")', ("61014", None),
            ("61001b", "Incognito_Mode"), ("61001a", "Thwart"),
        ], accept_events=("WhenSchemeBeingThwart", "AfterSchemeBeDefeated", "AfterUnitUseBasicPower"))
        self.assertNotIn("01107", snapshots[-1]["side_schemes"])
        self.assertEqual(snapshots[-1]["evidence"],5)

    def test_cottonmouth_attacks_three_times_only_once_per_phase(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62029")',
            'puzzle.DoAttack("62029")', 'puzzle.DoAttack("62029")',
        ])
        self.assertEqual([s["health"] for s in snapshots], [10,10,10,7,6])

    def test_entrapment_pays_form_change_before_damage(self):
        snapshots = self.run_commands("jj", [
            'puzzle.PutIntoPlay("61024")', 'DoScheme("01094")',
        ], accept_events=("AfterUnitSchemeEnd",))
        before, after = snapshots[-2:]
        self.assertEqual(after["face"], "61001a")
        self.assertNotIn("61024", after["controlled"])
        self.assertGreater(after["main_threat"], before["main_threat"])
        self.assertEqual(before["villain_health"] - after["villain_health"],
                         after["main_threat"] - before["main_threat"])

    def test_entrapment_stops_when_form_change_cost_fails(self):
        snapshots = self.run_commands("jj", [
            'puzzle.PutIntoPlay("61024")', 'puzzle.PutIntoPlay("61030")',
            'puzzle.ClearHand()', 'DoScheme("01094")',
        ], accept_events=("AfterUnitSchemeEnd",))
        before, after = snapshots[-2:]
        self.assertEqual(after["face"], "61001b")
        self.assertIn("61024", after["controlled"])
        self.assertEqual(before["villain_health"], after["villain_health"])

    def test_augmented_jaws_discards_all_tough_before_cottonmouth_attacks(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62029")',
            'puzzle.PutIntoPlay("62031")',
            'hero.GainStatus("Tough",DebugRule(hero))',
            'hero.GainStatus("Tough",DebugRule(hero))',
            'hero.GainStatus("Tough",DebugRule(hero))',
            'puzzle.DoAttack("62029")',
        ])
        self.assertEqual((snapshots[-1]["tough"],snapshots[-1]["health"]), (0,1))

    def test_sidewinder_moves_to_encounters_when_discarded_card_has_boost_ability(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.PutIntoPlay("62033")',
            'puzzle.CreateEncounterDeck("62030")',
            'hero.BasicAttack([puzzle.FindOrCreateFace("62033")],DebugRule(hero))',
        ])
        self.assertNotIn("62033",snapshots[-1]["minions"])
        self.assertIn("62033",snapshots[-1]["encounters"])

    def test_unpreventable_damage_keeps_existing_tough_cards(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.ChangeFormFor(0,"Hero")',
            'hero.GainStatus("Tough",DebugRule(hero))',
            'hero.GainStatus("Tough",DebugRule(hero))',
            'hero.DefaultDealDamageTo(hero,[hero],__import__("game.element.damage_property",fromlist=["DamageProperty"]).DamageProperty(3,unpreventable=True),DebugRule(hero))',
        ])
        self.assertEqual((snapshots[-1]["tough"],snapshots[-1]["health"]),(2,7))

    def test_player_phase_bonus_survives_villain_phase_end(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.PutIntoPlay("62002")',
            'puzzle.FindOrCreateFace("62002").TemporaryGain(DebugRule(hero),None,end_event=Message.WhenPhaseEnd,until_player_phase_end=True,attack=1,thwart=1)',
            'Message.WhenPhaseEnd(world.phase_id,"Villain",world).Send()',
            'Message.WhenPhaseEnd(world.phase_id,"Player",world).Send()',
        ])
        self.assertEqual([s["allies"]["62002"][0] for s in snapshots[1:]], [2,3,3,2])

    def test_boost_stars_are_abilities_not_per_player_icons(self):
        for cid in ("62029","62030","62032"):
            face=CardFactory.CreateFace(CardsDB.papers[cid],SimpleNamespace(GetPlayerNumIcon=lambda:4))
            self.assertEqual(face.printed_boost,0 if cid=="62029" else 2)

    def test_luke_keeps_multiple_tough_across_forms_and_pays_per_discard(self):
        snapshots = self.run_commands("luke_cage", [
            'hero.GainStatus("Tough",DebugRule(hero))',
            'hero.GainStatus("Tough",DebugRule(hero))',
            'hero.GainStatus("Tough",DebugRule(hero))',
            'puzzle.ChangeFormFor(0,"Hero")',
            'hero.DiscardTough(DebugRule(hero),rule=1)',
            'hero.DiscardAllTough(DebugRule(hero))',
            'puzzle.ChangeFormFor(0,"Identity")', 'puzzle.Tough(hero)',
            'hero.DiscardAllTough(DebugRule(hero))',
        ])
        self.assertEqual([s["tough"] for s in snapshots], [0,1,2,3,3,2,0,0,1,0])
        self.assertEqual([s["health"] for s in snapshots], [10,10,10,10,10,9,7,7,7,7])

    def test_tough_damage_and_ally_scaling(self):
        snapshots = self.run_commands("luke_cage", [
            'puzzle.PutIntoPlay("62002")',
            'hero.GainStatus("Tough",DebugRule(hero))', 'hero.GainStatus("Tough",DebugRule(hero))',
            'puzzle.PutIntoPlay("62013")', 'puzzle.Damage("62013",1)',
            'puzzle.ChangeFormFor(0,"Hero")', 'puzzle.Damage(hero,5)',
        ])
        self.assertEqual(snapshots[1]["allies"]["62002"][1], 1)
        self.assertEqual(snapshots[3]["allies"]["62002"][1], 3)
        self.assertEqual(snapshots[4]["allies"]["62013"][:2], (3,3))
        self.assertEqual(snapshots[5]["allies"]["62013"][:2], (1,1))
        self.assertEqual((snapshots[-1]["tough"], snapshots[-1]["health"]), (1,9))

    def test_piecing_it_all_together_does_not_use_side_scheme_slot(self):
        snapshots = self.run_commands("jj", [
            'puzzle.PutIntoPlay("61007")', 'puzzle.PutIntoPlay("61021")',
        ])
        self.assertIn("61007", snapshots[-1]["side_schemes"])
        self.assertIn("61021", snapshots[-1]["side_schemes"])

    def test_unpreventable_damage_cannot_be_reduced_prevented_or_capped(self):
        damage = DamageProperty(3, unpreventable=True)
        self.assertTrue(damage.Copy().unpreventable)
        # Use the actual message methods; no presentation or game state is needed
        # because each forbidden modification must return before emitting anything.
        message = object.__new__(Message.WhenUnitWouldTakeDamage)
        message.property = damage
        message.total_prevent_damage = 0
        message.be_prevent = False
        message.cannot_have_more_than_sustained = None
        message.ReduceDamage(1, None)
        message.ReduceDamageTo(0, None)
        self.assertEqual(message.PreventDamage("All", None), 0)
        self.assertEqual(message.PreventAllDamageInternal(), 0)
        message.SetAtLeastHealth(1, None)
        message.SetCannotHaveMoreThanSustained(1, None)
        self.assertEqual(message.will_take_damage, 3)
        self.assertIsNone(message.cannot_have_more_than_sustained)


if __name__ == "__main__":
    unittest.main()
