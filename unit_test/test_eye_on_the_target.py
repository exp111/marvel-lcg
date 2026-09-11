import contextlib
import io
import unittest
from unittest.mock import patch

from engine import Engine
from game.message import Message
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


class TestEyeOnTheTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def reveal_eye(self, timing, form, bullseye, *, remove_support=False, discard_persona=False):
        scene = SceneLoader.NewScene(
            "art_museum_heist" if bullseye == "villain" else "rhino",
            None, ["daredevil"], 98,
        )
        if bullseye == "villain":
            underling = SceneLoader.NewScene("bullseye", None, ["daredevil"], 98)
            scene.campaign.villain = underling.campaign.villain
            scene.campaign.set_aside += underling.campaign.set_aside
            scene.campaign.encounters += underling.campaign.encounters
            scene.campaign.encounter_sets += underling.campaign.encounter_sets
        scene.rules = ["v16_all", timing]
        scene.SetMetadataBool("is_puzzle", True)
        commands = [
            'Puzzle.ClearHand()',
            'Puzzle.PutIntoPlay("60013")',  # Foggy Nelson supplies a Persona choice.
        ]
        if form == "Hero":
            commands.append('Puzzle.ChangeFormFor(0, "Hero")')
        if bullseye == "minion":
            commands.append('Puzzle.PutIntoPlay("60033")')
        commands += [
            'Puzzle.CreateEncounterDeck("01186")',  # A boost card with no icons or ability.
            'Puzzle.Reveal("60036")',
        ]
        command_index = 0
        attacks = []
        minion_reveals = []
        original_attack = Message.AfterUnitAttackUnit.Send
        original_reveal = Message.WhenCardRevealed.Send

        def after_attack(message, *args, **kwargs):
            attacks.append((
                message.attacker.paper.card_id,
                message.attacked.paper.card_id,
                message.taken_damage,
            ))
            return original_attack(message, *args, **kwargs)

        def on_reveal(message, *args, **kwargs):
            if message.trigger.paper.card_id == "60033":
                minion_reveals.append(message.trigger)
            return original_reveal(message, *args, **kwargs)

        def choose(prompt):
            nonlocal command_index
            if prompt.event_name == "WhenPlayerInTurn":
                if command_index == len(commands):
                    return None
                command = commands[command_index]
                command_index += 1
                Engine.game.controller_manager.console.SetCommand(command, Engine.game.world)
                return CommandDescriptor()
            if prompt.event_name == "WhenPlayerChooseAbility":
                for option in prompt.options:
                    face = Engine.game.world.object_manager.card_dict[option["bind_id"]].face
                    if face.paper.card_id == "60036":
                        name = "Remove_an_ally" if remove_support else "Bullseye_attacks_you"
                    elif face.paper.card_id == "60033":
                        name = "Discard_a_Persona" if discard_persona else "Bullseye_attacks_you"
                    else:
                        continue
                    if option["name"].startswith(name):
                        minimum = option["target_num_range"][0]
                        return CommandDescriptor(
                            HeadlessDeviceManager._DescriptorId(option),
                            [str(target) for target in option["all_legal_targets"][:minimum]],
                            [],
                        )
            if prompt.show_cancel:
                return CommandDescriptor()  # Resolve attacks without defenses or interrupts.
            return HeadlessDeviceManager._DefaultChoice(prompt)

        devices = HeadlessDeviceManager(choice_provider=choose)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch.object(Message.AfterUnitAttackUnit, "Send", new=after_attack),
            patch.object(Message.WhenCardRevealed, "Send", new=on_reveal),
            patch.object(WorldRender, "ErrorOccurred") as errors,
        ):
            game = run_scene_with_devices(scene, devices)

        errors.assert_not_called()
        self.assertEqual(command_index, len(commands))
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game.world, attacks, minion_reveals

    def test_existing_villain_or_minion_attacks_in_either_form_without_revealing_a_minion(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for form in ("Hero", "AlterEgo"):
                for bullseye in ("villain", "minion"):
                    with self.subTest(timing=timing, form=form, bullseye=bullseye):
                        world, attacks, reveals = self.reveal_eye(timing, form, bullseye)
                        self.assertEqual(attacks, [(
                            "60065" if bullseye == "villain" else "60033",
                            "60001a" if form == "Hero" else "60001b",
                            2 if bullseye == "villain" else 3,
                        )])
                        self.assertEqual(reveals, [])
                        self.assertEqual(len(world.FindCardsOnField(name="Foggy Nelson")), 1)

    def test_absent_bullseye_is_revealed_without_an_extra_attack_after_his_choice(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for form in ("Hero", "AlterEgo"):
                for discard_persona in (False, True):
                    with self.subTest(timing=timing, form=form, discard=discard_persona):
                        world, attacks, reveals = self.reveal_eye(
                            timing, form, "absent", discard_persona=discard_persona,
                        )
                        self.assertEqual(len(reveals), 1)
                        self.assertTrue(reveals[0].IsInPlay())
                        self.assertEqual(attacks, [] if discard_persona else [(
                            "60033", "60001a" if form == "Hero" else "60001b", 3,
                        )])
                        self.assertEqual(
                            len(world.FindCardsOnField(name="Foggy Nelson")),
                            0 if discard_persona else 1,
                        )

    def test_removing_a_support_does_not_attack_or_reveal_bullseye(self):
        for timing in ("v18_timing", "no_v18_timing"):
            with self.subTest(timing=timing):
                world, attacks, reveals = self.reveal_eye(
                    timing, "Hero", "villain", remove_support=True,
                )
                self.assertEqual(attacks, [])
                self.assertEqual(reveals, [])
                self.assertEqual(world.FindCardsOnField(name="Foggy Nelson"), [])
                self.assertIsNone(world.GetFirstPlayer().discard_pile.FindCard(name="60013"))


if __name__ == "__main__":
    unittest.main()
