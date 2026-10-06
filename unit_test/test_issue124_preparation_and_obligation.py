import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log, Notify
from game.message import Message
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)
from game.world.world_render import WorldRender


SAVE = Path(__file__).parent / "fixtures" / "issue124_ready_for_a_fight.json"


class TestIssue124PreparationAndObligation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        linked_cards = patch.object(CardsDB, "linked_papers", {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    def run_game(self, scene, devices, *, load_type="New"):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Notify, "Game") as notices,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(scene, devices, load_type=load_type)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game

    @staticmethod
    def select(option):
        return CommandDescriptor(
            HeadlessDeviceManager._DescriptorId(option),
            [str(target) for target in option.get("automatic_targets", [])],
        )

    def play_saved_preparation(self, *, accept_suit):
        initial = []
        suit_offers = []
        completed = []
        attacks = []
        after_effect = Message.AfterEffectResolved.Send
        after_attack = Message.AfterUnitAttackEnd.Send

        def record_attack(message):
            result = after_attack(message)
            if initial and message.attacker.paper.card_id == "60065":
                attacks.append(message.world.const_players[0].GetIdentity().IsExhaust())
            return result

        def record_preparation(message):
            result = after_effect(message)
            if initial and message.trigger.paper.card_id == "52019":
                player = message.world.const_players[0]
                hero = player.GetIdentity()
                suit = next(card for card in player.GetControlUpgrade()
                            if card.paper.card_id == "08009")
                completed.append((hero.IsExhaust(), suit.IsExhaust()))
            return result

        def choose(prompt):
            world = Engine.game.world
            hero = world.const_players[0].GetIdentity()
            if not initial:
                initial.append((hero.paper.card_id, hero.IsExhaust()))
            if completed or len(devices.prompts) > 30:
                return None
            if prompt.event_name == "WhenUnitWouldScheme":
                return HeadlessDeviceManager._DefaultChoice(prompt)
            if prompt.event_name == "WhenUnitBeingAttack":
                defense = next((option for option in prompt.options
                                if option.get("bind_id") == hero.card.object_id), None)
                if defense:
                    return self.select(defense)
            for option in prompt.options:
                card = world.object_manager.card_dict.get(option.get("bind_id"))
                if card and card.face.paper.card_id == "08009":
                    suit_offers.append((prompt.event_name, hero.paper.card_id,
                                        hero.IsExhaust(), len(attacks)))
                    if accept_suit:
                        return self.select(option)
            return (CommandDescriptor() if prompt.show_cancel
                    else HeadlessDeviceManager._DefaultChoice(prompt))

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (
            patch.object(Message.AfterEffectResolved, "Send", record_preparation),
            patch.object(Message.AfterUnitAttackEnd, "Send", record_attack),
        ):
            self.run_game(validate_file(SAVE), devices, load_type="InTesting")
        self.assertEqual(initial, [("08001b", False)])
        self.assertEqual(devices.prompts[0].event_name, "WhenUnitWouldScheme")
        self.assertEqual(attacks, [True])
        self.assertEqual(suit_offers, [("AfterEffectResolved", "08001a", True, 1)])
        return completed

    def test_saved_preparation_offers_suit_after_changing_form_and_defending(self):
        self.assertEqual(self.play_saved_preparation(accept_suit=True), [(False, True)])

    def test_suit_response_remains_optional_after_the_saved_attack(self):
        self.assertEqual(self.play_saved_preparation(accept_suit=False), [(True, False)])

    def test_imprisoned_reveals_without_error_and_preserves_restrictions(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                scene = validate_file(SAVE)
                scene.inputs = []
                if legacy:
                    scene.rules.remove("v18_timing")
                    scene.rules.append("no_v18_timing")
                commands = iter([
                    'ChangeForm(c1, "Hero")',
                    'puzzle.Reveal("60150")',
                    'puzzle.ChangeFormFor(0, "Identity")',
                ])
                turns = []

                def choose(prompt):
                    if len(devices.prompts) > 35:
                        return None
                    if prompt.event_name == "WhenPlayerInTurn":
                        turns.append(prompt)
                        command = next(commands, None)
                        if command is None:
                            return None
                        Engine.game.controller_manager.console.SetCommand(
                            command, Engine.game.world,
                        )
                        return CommandDescriptor()
                    return (CommandDescriptor() if prompt.show_cancel
                            else HeadlessDeviceManager._DefaultChoice(prompt))

                devices = HeadlessDeviceManager(choice_provider=choose)
                game = self.run_game(scene, devices)
                self.assertEqual(len(turns), 4)
                before = [option["name"] for option in turns[1].options]
                after = [option["name"].replace("_", " ") for option in turns[-1].options]
                self.assertIn("Attack", before)
                self.assertIn("Thwart", before)
                self.assertNotIn("Attack", after)
                self.assertNotIn("Thwart", after)
                self.assertIn("Spend 3 resources of any type → discard Imprisoned", after)
                self.assertTrue(any(name.startswith(
                    "Exhaust characters with total THW 3 or more → discard Imprisoned"
                ) for name in after))
                player = game.world.const_players[0]
                self.assertEqual(player.GetIdentity().paper.card_id, "08001a")
                obligation, = player.obligations_area.Get()
                self.assertEqual(obligation.paper.card_id, "60150")
                self.assertIs(obligation.bind_face, player.GetIdentity())
                self.assertEqual(game.world.const_players[1].obligations_area.Get(), [])

    def play_obligation(self, commands, *, discard=None, legacy=False):
        scene = validate_file(SAVE)
        scene.inputs = []
        if legacy:
            scene.rules.remove("v18_timing")
            scene.rules.append("no_v18_timing")
        setup = iter(commands)
        selected = []

        def choose(prompt):
            if len(devices.prompts) > 40:
                return None
            if prompt.event_name == "WhenPlayerInTurn":
                command = next(setup, None)
                if command:
                    Engine.game.controller_manager.console.SetCommand(
                        command, Engine.game.world,
                    )
                    return CommandDescriptor()
                if not discard or selected:
                    return None
                option = next((option for option in prompt.options
                               if option["name"].startswith(discard)), None)
                if option is None:
                    return None
                selected.append(option["name"])
                if discard == "Spend":
                    payment = option["target_payment"]["0"]
                    return CommandDescriptor(
                        HeadlessDeviceManager._DescriptorId(option), [],
                        [str(next(iter(entry))) for entry in payment["payment"]][:3],
                    )
                return self.select(option)
            if selected and prompt.options and prompt.options[0]["name"] == "Pay_cost_Exhaust":
                option = prompt.options[0]
                return CommandDescriptor(
                    HeadlessDeviceManager._DescriptorId(option),
                    [str(target) for target in option["all_legal_targets"]],
                )
            return (CommandDescriptor() if prompt.show_cancel
                    else HeadlessDeviceManager._DefaultChoice(prompt))

        devices = HeadlessDeviceManager(choice_provider=choose)
        game = self.run_game(scene, devices)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        if discard:
            self.assertEqual(len(selected), 1)
        return game

    def test_both_imprisoned_costs_discard_the_obligation(self):
        for discard in ("Spend", "Exhaust"):
            for legacy in (False, True):
                with self.subTest(discard=discard, legacy=legacy):
                    game = self.play_obligation([
                        'ChangeForm(c1, "Hero")',
                        'puzzle.PutIntoPlay("01083")',  # Mockingbird adds 1 THW.
                        'puzzle.ClearHand()',
                        'puzzle.CreateHandCards("52019", "52019", "52019")',
                        'puzzle.Reveal("60150")',
                    ], discard=discard, legacy=legacy)
                    player = game.world.const_players[0]
                    self.assertEqual(player.obligations_area.Get(), [])
                    self.assertIn("60150", [face.paper.card_id for face in
                                           game.world.scenario.encounter_discard_pile.Get()])
                    self.assertEqual(player.GetIdentity().IsExhaust(), discard == "Exhaust")
                    ally, = player.allies.Get()
                    self.assertEqual(ally.IsExhaust(), discard == "Exhaust")
                    self.assertEqual(len(player.hand_cards.Get()), 0 if discard == "Spend" else 3)

    def test_imprisoned_boost_reveals_into_the_attacked_players_area(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                game = self.play_obligation([
                    'ChangeForm(c1, "Hero")',
                    'puzzle.CreateEncounterDeck("60150")',
                    'DoAttack("Bullseye")',
                ], legacy=legacy)
                player = game.world.const_players[0]
                obligation, = player.obligations_area.Get()
                self.assertEqual(obligation.paper.card_id, "60150")
                self.assertIs(obligation.bind_face, player.GetIdentity())
                self.assertTrue(obligation.IsInPlay())
                self.assertEqual(game.world.const_players[1].obligations_area.Get(), [])


if __name__ == "__main__":
    unittest.main()
