import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log, Notify
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


ROOT = Path(__file__).resolve().parents[1]


class TestPsylockePsiEnergy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        linked_cards = patch.object(CardsDB, "linked_papers", {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    def run_game(self, legacy, choose):
        scene = SceneLoader.NewScene("rhino", None, ["psylocke"], 130)
        scene.rules = ["v16_all", "no_v18_timing" if legacy else "v18_timing"]
        devices = HeadlessDeviceManager(choice_provider=lambda prompt:
                                        choose(prompt) if len(devices.prompts) < 40 else None)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Notify, "Game") as notices,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(scene, devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
        return game.world

    @staticmethod
    def command(option):
        return CommandDescriptor(
            HeadlessDeviceManager._DescriptorId(option),
            [str(target) for target in option.get("automatic_targets", [])],
        )

    def pay_with_weapon(self, card_id, flip, legacy=False, weapon_index=0):
        commands = [
            'ChangeForm(c1, "Hero")',
            'puzzle.ClearHandFor(0)',
            'puzzle.CreateHandCardsFor(0, "16024")',
        ]
        if card_id == "41002b":
            # Flip both setup copies, then independently spend either copy.
            commands += ['puzzle.FindOrCreateFace("41002a").card.Flip(DebugRule(c1))'] * 2
        setup = iter(commands)
        source = []
        decisions = []
        before_decision = []

        def choose(prompt):
            world = Engine.game.world
            player = world.const_players[0]
            if prompt.event_name == "WhenPlayerInTurn":
                command = next(setup, None)
                if command:
                    Engine.game.controller_manager.console.SetCommand(command, world)
                    return CommandDescriptor()
                if source:
                    return None
                weapons = sorted(player.GetControlUpgrade(), key=lambda face: face.card.object_id)
                source.append(weapons[weapon_index].card)
                option = next(option for option in prompt.options if option["name"] == "Play")
                entries = next(iter(option["target_payment"].values()))["payment"]
                payment_id = next(
                    payment_id for entry in entries for payment_id in entry
                    if world.object_manager.paying_effect_dict[int(payment_id)].this.card == source[0]
                )
                command = self.command(option)
                command.resources = [str(payment_id)]
                return command
            if prompt.event_name == "WhenPlayerChooseAbility" and source:
                decisions.append(prompt)
                before_decision.append((source[0].face.paper.card_id,
                                        source[0].face.IsExhaust(), player.res_pool.Get().text))
                if flip is None:
                    return CommandDescriptor()
                # Also accepts the old prompt so behavior can be checked before
                # the clearer choice labels are introduced.
                option = next(option for option in prompt.options
                              if (option["name"].startswith("Keep_") or option["name"] == "Cancel")
                              == (not flip))
                return self.command(option)
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

        world = self.run_game(legacy, choose)
        self.assertEqual(len(source), 1)
        self.assertEqual(len(decisions), 1)
        resource = "B" if card_id == "41002a" else "R"
        self.assertEqual(before_decision, [(card_id, True, resource)])
        other_id = "41002b" if card_id == "41002a" else "41002a"
        self.assertEqual(source[0].face.paper.card_id, other_id if flip else card_id)
        self.assertTrue(source[0].face.IsExhaust())
        other = next(face for face in world.const_players[0].GetControlUpgrade()
                     if face.card != source[0] and face.HasTrait("PSI-ENERGY"))
        self.assertEqual(other.paper.card_id, card_id)
        self.assertFalse(other.IsExhaust())
        self.assertTrue(any(card.face.paper.card_id == "16024" and card.face.IsInPlay()
                            for card in world.object_manager.card_dict.values()))
        hero = world.const_players[0].GetIdentity()
        katana_count = (0 if card_id == "41002a" else 2) + (1 if flip and card_id == "41002a"
                                                              else -1 if flip else 0)
        self.assertEqual((hero.attack, hero.thwart), (1 + katana_count, 3 - katana_count))
        names = [option["name"].replace("_", " ") for option in decisions[0].options]
        self.assertEqual(names, ["Flip to Psi-Katana", "Keep Psi-Knife"]
                         if card_id == "41002a" else ["Flip to Psi-Knife", "Keep Psi-Katana"])
        for option in decisions[0].options:
            self.assertEqual(option["automatic_targets"], [source[0].object_id])
            self.assertFalse(option["automatic_submit"])
        return decisions[0]

    def test_resources_can_be_generated_without_flipping_either_copy(self):
        for legacy in (False, True):
            for card_id in ("41002a", "41002b"):
                for weapon_index in (0, 1):
                    with self.subTest(legacy=legacy, card_id=card_id, weapon_index=weapon_index):
                        self.pay_with_weapon(card_id, False, legacy, weapon_index)

    def test_ending_the_optional_flip_decision_keeps_the_resource_and_current_side(self):
        for legacy in (False, True):
            for card_id in ("41002a", "41002b"):
                with self.subTest(legacy=legacy, card_id=card_id):
                    self.pay_with_weapon(card_id, None, legacy)

    def test_accepting_the_flip_changes_only_the_weapon_used_for_payment(self):
        for legacy in (False, True):
            for card_id in ("41002a", "41002b"):
                for weapon_index in (0, 1):
                    with self.subTest(legacy=legacy, card_id=card_id, weapon_index=weapon_index):
                        self.pay_with_weapon(card_id, True, legacy, weapon_index)

    def test_only_psylockes_printed_basic_power_interrupt_can_flip_a_ready_weapon(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                setup = iter(['ChangeForm(c1, "Hero")', 'puzzle.ClearHandFor(0)'])
                attacks = []
                attack_targets = []
                flips = []

                def choose(prompt):
                    world = Engine.game.world
                    hero = world.const_players[0].GetIdentity()
                    if prompt.event_name == "WhenPlayerInTurn":
                        command = next(setup, None)
                        if command:
                            Engine.game.controller_manager.console.SetCommand(command, world)
                            return CommandDescriptor()
                        if attacks:
                            return None
                        weapon_ids = {face.card.object_id for face in world.const_players[0].GetControlUpgrade()}
                        self.assertFalse(any(option["bind_id"] in weapon_ids for option in prompt.options),
                                         "Psi weapons have no printed standalone Hero Action")
                        option = next(option for option in prompt.options
                                      if option["name"] == "Attack" and option["bind_id"] == hero.card.object_id)
                        target_id = option["all_legal_targets"][0]
                        attack_targets.append(target_id)
                        attacks.append(world.object_manager.card_dict[target_id].face.health)
                        return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option), [str(target_id)])
                    option = next((option for option in prompt.options
                                   if "Psi-Energy_Control" in option["name"]), None)
                    if option and not flips:
                        target_id = option["all_legal_targets"][0]
                        flips.append(target_id)
                        return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option), [str(target_id)])
                    return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)

                world = self.run_game(legacy, choose)
                self.assertEqual(len(flips), 1)
                self.assertEqual(world.object_manager.card_dict[flips[0]].face.paper.card_id, "41002b")
                self.assertFalse(world.object_manager.card_dict[flips[0]].face.IsExhaust())
                self.assertEqual(world.object_manager.card_dict[attack_targets[0]].face.health, attacks[0] - 2)

    def test_client_waits_for_an_explicit_keep_or_flip_choice_with_auto_targeting(self):
        node = shutil.which("node")
        compiler = shutil.which("tsc.cmd") or shutil.which("tsc")
        if not node or not compiler:
            self.skipTest("Node and TypeScript are required for the client regression")
        prompts = [self.pay_with_weapon(card_id, False) for card_id in ("41002a", "41002b")]
        with tempfile.TemporaryDirectory(prefix="marvel-psi-energy-") as output:
            result = subprocess.run(
                [compiler, "-p", str(ROOT / "public/js/tsconfig.json"), "--outDir", output],
                cwd=ROOT, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            fixture = Path(output) / "prompts.json"
            fixture.write_text(json.dumps([{
                "options_json": json.dumps(prompt.options), "ability_type": prompt.ability_type,
                "event_name": prompt.event_name, "show_cancel": prompt.show_cancel,
            } for prompt in prompts]), encoding="utf-8")
            result = subprocess.run(
                [node, str(ROOT / "unit_test/psi_energy_choice_ui.cjs"),
                 str(Path(output) / "marvel"), str(fixture)],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
