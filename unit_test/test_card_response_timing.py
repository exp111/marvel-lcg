import contextlib
import io
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log, Notify
from game.ability import AbilityType
from game.ability.factory import AbilityFactory
from game.effect.effect_invoke import EffectInvoker
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


class TestCardResponseTiming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        linked_cards = patch.object(CardsDB, "linked_papers", {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    @staticmethod
    def face(world, card_id):
        faces = [card.face for card in world.object_manager.card_dict.values()
                 if card.face.paper.card_id == card_id]
        return next((face for face in faces if face.IsInPlay()), faces[0])

    def play_action(self, actor, commands, *, target, legacy, action="Attack",
                    action_card=None, response=None, accept=True, before_action=None):
        scene = SceneLoader.NewScene("rhino", None, [actor], 124)
        scene.rules = ["v16_all", "no_v18_timing" if legacy else "v18_timing"]
        setup = iter(commands)
        selected = []
        offers = []
        observed = []
        observer_offers = []
        invoke = EffectInvoker.InvokeOperation

        def record(effect, message):
            card_id = effect.this.paper.card_id
            if effect.ability.flags.is_response or effect.ability.flags.is_interrupt:
                if card_id == "50154":
                    radio = self.face(effect.world, "50152")
                    observed.append((message.name, radio.health,
                                     getattr(message, "dealt_damage", None)))
                elif card_id == "60015":
                    scheme = getattr(message, "scheme", message.trigger)
                    observed.append((message.name, scheme.IsInPlay()))
                elif card_id in {"60094", "25008"}:
                    glow_in_play = (self.face(effect.world, "25002").IsInPlay()
                                    if card_id == "25008" else None)
                    observed.append((message.name, message.trigger.IsInPlay(), glow_in_play))
                elif card_id == "40024":
                    observed.append((message.name, effect.this.health))
            return invoke(effect, message)

        def choose(prompt):
            world = Engine.game.world
            if len(devices.prompts) > 50:
                return None
            if prompt.event_name == "WhenPlayerInTurn":
                command = next(setup, None)
                if command is not None:
                    Engine.game.controller_manager.console.SetCommand(command, world)
                    return CommandDescriptor()
                if selected:
                    return None
                if before_action:
                    before_action(world)
                option = next(option for option in prompt.options
                              if (action_card is None and option["name"] == action
                                  and option["bind_id"] == 1)
                              or (action_card is not None
                                  and world.object_manager.card_dict[
                                      option["bind_id"]].face.paper.card_id == action_card
                                  and (action is None or option["name"] == action)))
                target_id = next(target_id for target_id in option["all_legal_targets"]
                                 if world.object_manager.card_dict[
                                     target_id].face.paper.card_id == target)
                selected.append(option)
                return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option),
                                         [str(target_id)])
            for option in prompt.options:
                if option["name"] == "Timing_observer":
                    observer_offers.append(prompt.event_name)
                card = world.object_manager.card_dict.get(option.get("bind_id"))
                if response and card and card.face.paper.card_id == response:
                    offers.append(prompt.event_name)
                    if accept:
                        target_id = option["all_legal_targets"][0]
                        return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option),
                                                 [str(target_id)])
            return (CommandDescriptor() if prompt.show_cancel
                    else HeadlessDeviceManager._DefaultChoice(prompt))

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(EffectInvoker, "InvokeOperation", record),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Notify, "Game") as notices,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(len(selected), 1)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game.world, observed, offers, observer_offers

    def test_nuclear_reaction_resolves_after_lethal_damage_without_crashing(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                world, observed, _, _ = self.play_action("hulk", [
                    'ChangeForm(c1, "Hero")',
                    'puzzle.PutIntoPlay("50152")',
                    'puzzle.PutIntoPlay("50154")',
                    'puzzle.SetThreat("50154", 9)',
                    'puzzle.FindOrCreateFace("50152").SetHealth(2, DebugRule(c1))',
                ], target="50152", legacy=legacy)
                self.assertEqual(observed, [("AfterFaceDealDamage", 0, 3)])
                self.assertFalse(self.face(world, "50152").IsInPlay())
                self.assertFalse(self.face(world, "50154").IsInPlay())
                self.assertEqual(world.const_players[0].GetIdentity().health, 8)

    def test_nuclear_reaction_counts_dealt_damage_even_when_tough_prevents_it(self):
        for legacy in (False, True):
            for tough in (False, True):
                with self.subTest(legacy=legacy, tough=tough):
                    initial_health = []
                    commands = [
                        'ChangeForm(c1, "Hero")',
                        'puzzle.PutIntoPlay("50152")',
                        'puzzle.PutIntoPlay("50154")',
                        'puzzle.SetThreat("50154", 1)',
                    ]
                    if tough:
                        commands.append('puzzle.Tough("50152")')
                    world, observed, _, _ = self.play_action(
                        "hulk", commands, target="50152", legacy=legacy,
                        before_action=lambda world:
                            initial_health.append(self.face(world, "50152").health),
                    )
                    remaining = initial_health[0] - (0 if tough else 3)
                    self.assertEqual(observed, [("AfterFaceDealDamage", remaining, 3)])
                    self.assertEqual(self.face(world, "50154").threat, 4)
                    self.assertEqual(self.face(world, "50152").health, remaining)
                    self.assertFalse(self.face(world, "50152").IsTough())

    def test_nuclear_reaction_does_not_trigger_again_from_its_own_explosion(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                world, observed, _, _ = self.play_action("hulk", [
                    'ChangeForm(c1, "Hero")',
                    'puzzle.PutIntoPlay("50152")',
                    'puzzle.PutIntoPlay("50154")',
                    'puzzle.SetThreat("50154", 9)',
                ], target="50152", legacy=legacy)
                self.assertEqual(len(observed), 1)
                self.assertEqual(observed[0][0], "AfterFaceDealDamage")
                self.assertFalse(self.face(world, "50154").IsInPlay())
                self.assertEqual(self.face(world, "50152").health, 5)
                self.assertEqual(world.const_players[0].GetIdentity().health, 8)

    def test_tough_preserves_damage_dealt_without_taken_damage_or_overkill(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                dealt = []
                taken = []
                villain_health = []

                def observe_damage(world):
                    hero = world.const_players[0].GetIdentity()
                    minion = self.face(world, "01110")
                    villain_health.append(self.face(world, "01094").health)
                    hero.effect.RegisterTemp(
                        AbilityFactory.WhenUnitWouldAttack(
                            AbilityType.Temp0, "This",
                            lambda effect, message: message.GainOverKill(effect),
                        ),
                        AbilityFactory.AfterFaceDealDamage(
                            AbilityType.ForcedResponse, None, minion,
                            lambda effect, message: dealt.append(message.dealt_damage),
                        ),
                        AbilityFactory.AfterUnitTookDamage(
                            AbilityType.ForcedResponse, minion,
                            lambda effect, message: taken.append(message.took_damage),
                        ),
                        unregister_after_exec=True, until_turn_end=True,
                    )

                world, _, _, _ = self.play_action("hulk", [
                    'ChangeForm(c1, "Hero")',
                    'puzzle.PutIntoPlay("01110")',
                    'puzzle.Tough("01110")',
                ], target="01110", legacy=legacy, before_action=observe_damage)
                self.assertEqual(dealt, [3])
                self.assertEqual(taken, [])
                minion = self.face(world, "01110")
                self.assertTrue(minion.IsInPlay())
                self.assertEqual(minion.health, 2)
                self.assertFalse(minion.IsTough())
                self.assertEqual(self.face(world, "01094").health, villain_health[0])

    def test_nuclear_reaction_does_not_count_overkill_damage_to_the_villain(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                villain_health = []

                def grant_overkill(world):
                    villain_health.append(self.face(world, "01094").health)
                    world.const_players[0].GetIdentity().effect.RegisterTemp(
                        AbilityFactory.WhenUnitWouldAttack(
                            AbilityType.Temp0, "This",
                            lambda effect, message: message.GainOverKill(effect),
                        ),
                        unregister_after_exec=True, until_turn_end=True,
                    )

                world, observed, _, _ = self.play_action("hulk", [
                    'ChangeForm(c1, "Hero")',
                    'puzzle.PutIntoPlay("50152")',
                    'puzzle.PutIntoPlay("50154")',
                    'puzzle.SetThreat("50154", 1)',
                    'puzzle.FindOrCreateFace("50152").SetHealth(2, DebugRule(c1))',
                ], target="50152", legacy=legacy, before_action=grant_overkill)
                self.assertEqual(len(observed), 1)
                self.assertEqual(observed[0][:2], ("AfterFaceDealDamage", 0))
                self.assertEqual(self.face(world, "50154").threat, 4)
                self.assertEqual(self.face(world, "01094").health, villain_health[0] - 1)

    def test_nelson_and_murdock_responds_after_attorney_discards_the_scheme(self):
        for legacy in (False, True):
            for accept in (False, True):
                with self.subTest(legacy=legacy, accept=accept):
                    world, observed, offers, _ = self.play_action("daredevil", [
                        'puzzle.PutIntoPlay("60013")',
                        'puzzle.PutIntoPlay("60015")',
                        'puzzle.PutIntoPlay("01107")',
                        'puzzle.SetThreat("01107", 1)',
                    ], target="01107", legacy=legacy, action=None, action_card="60013",
                        response="60015", accept=accept)
                    self.assertEqual(offers, ["AfterUnitDefeatedScheme"])
                    self.assertEqual(observed, [("AfterUnitDefeatedScheme", False)]
                                     if accept else [])
                    self.assertFalse(self.face(world, "01107").IsInPlay())
                    self.assertEqual(self.face(world, "01094").IsConfused(), accept)

    def test_nelson_and_murdock_does_not_respond_to_a_non_attorney(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                world, observed, offers, _ = self.play_action("daredevil", [
                    'ChangeForm(c1, "Hero")',
                    'puzzle.PutIntoPlay("60015")',
                    'puzzle.PutIntoPlay("01107")',
                    'puzzle.SetThreat("01107", 1)',
                ], target="01107", legacy=legacy, action="Thwart", response="60015")
                self.assertFalse(self.face(world, "01107").IsInPlay())
                self.assertEqual(offers, [])
                self.assertEqual(observed, [])

    def test_flight_remembers_death_glow_and_responds_after_enemy_leaves_play(self):
        for legacy in (False, True):
            for attached, accept in ((True, True), (True, False), (False, True)):
                with self.subTest(legacy=legacy, attached=attached, accept=accept):
                    commands = [
                        'ChangeForm(c1, "Hero")',
                        'puzzle.PutIntoPlay("25008")',
                        'puzzle.PutIntoPlay("01110")',
                        'puzzle.SetThreat("01097b", 3)',
                    ]
                    if attached:
                        commands.append('puzzle.FindOrCreateFace("25002").AttachTo2('
                                        'puzzle.FindOrCreateFace("01110"), DebugRule(c1))')
                    world, observed, offers, _ = self.play_action(
                        "valkyrie", commands, target="01110", legacy=legacy,
                        response="25008", accept=accept,
                    )
                    resolved = attached and accept
                    self.assertEqual(offers, ["AfterUnitBeDefeated"] if attached else [])
                    self.assertEqual(observed, [("AfterUnitBeDefeated", False, False)]
                                     if resolved else [])
                    self.assertFalse(self.face(world, "01110").IsInPlay())
                    self.assertEqual(self.face(world, "25008").IsInPlay(), not resolved)
                    self.assertEqual(self.face(world, "01097b").threat, 0 if resolved else 3)
                    if attached:
                        self.assertTrue(self.face(world, "25002").card.area.flags.is_set_aside)

    def test_consolidate_power_moves_the_discarded_minion_to_the_boost_deck(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                world, observed, _, _ = self.play_action("hulk", [
                    'ChangeForm(c1, "Hero")',
                    'puzzle.PutIntoPlay("60094")',
                    'puzzle.PutIntoPlay("01110")',
                ], target="01110", legacy=legacy)
                self.assertEqual(observed, [("AfterUnitBeDefeated", False, None)])
                minion = self.face(world, "01110")
                boost_cards = self.face(world, "01094").components.boostable.GetDeck().Get()
                self.assertEqual(boost_cards, [minion])
                self.assertNotIn(minion, world.scenario.encounter_discard_pile.Get())

    def test_deadpool_mandatory_healing_precedes_optional_defeat_interrupts(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                interrupt_calls = []

                def install_interrupt(world):
                    deadpool = self.face(world, "40024")
                    observer = AbilityFactory.WhenUnitWouldBeDefeated(
                        AbilityType.Interrupt, deadpool,
                        lambda effect, message: interrupt_calls.append(message),
                    ).SetName("Timing observer")
                    world.const_players[0].GetIdentity().effect.RegisterTemp(
                        observer, unregister_after_exec=True, until_turn_end=True,
                    )

                world, observed, _, observer_offers = self.play_action("hulk", [
                    'ChangeForm(c1, "Hero")',
                    'puzzle.PutIntoPlay("40024")',
                    'puzzle.FindOrCreateFace("40024").SetHealth(1, DebugRule(c1))',
                ], target="01094", legacy=legacy, action_card="40024",
                    before_action=install_interrupt)
                deadpool = self.face(world, "40024")
                self.assertTrue(deadpool.IsInPlay())
                self.assertEqual(deadpool.health, 3)
                self.assertEqual(self.face(world, "01097b").acceleration_token, 1)
                self.assertEqual(observed, [("WhenUnitWouldBeDefeated", 0)])
                self.assertEqual(observer_offers, [])
                self.assertEqual(interrupt_calls, [])


if __name__ == "__main__":
    unittest.main()
