import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from cards.database import CardsDB
from engine.log import Log
from game.card.face.card_type.minion import Minion
from game.message import Message
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import (
    initialize_database,
    run_scene_with_devices,
    validate_file,
)
from game.world.world_render import WorldRender


SAVE = Path(__file__).parent / "fixtures" / "issue118_nightcrawler.json"


class TestNightcrawlerForcedChoices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The supplied replay includes Specialized Training's four linked
        # cards. Keep their IDs stable even after other tests initialize DB.
        linked_cards = patch.object(CardsDB, "linked_papers", {})
        linked_cards.start()
        cls.addClassCleanup(linked_cards.stop)
        initialize_database()

    def run_scene(self, scene, devices, *, replay=False):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("game.test.v18_timing_harness.initialize_database"),
            patch.object(WorldRender, "ErrorOccurred") as errors,
            patch.object(Log, "Warn") as warnings,
            patch.object(Engine, "SaveCrash"),
        ):
            game = run_scene_with_devices(
                scene, devices, load_type="InTesting" if replay else "New",
            )
        errors.assert_not_called()
        warnings.assert_not_called()
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(game.world.event_manager.timing_occurrences, [])
        return game

    def test_saved_azazel_engagement_is_in_alter_ego(self):
        engagements = []
        on_engage = Minion.OnEngagePlayer

        def record_engagement(minion, effect):
            if minion.paper.card_id == "48027":
                engagements.append((
                    minion.card.world.round_id,
                    minion.GetEngagedPlayer().IsHero(),
                    minion.IsQuickstrike(),
                ))
            return on_engage(minion, effect)

        devices = HeadlessDeviceManager(choice_provider=lambda prompt: None)
        with patch.object(Minion, "OnEngagePlayer", record_engagement):
            game = self.run_scene(validate_file(SAVE), devices, replay=True)
        self.assertEqual(engagements, [(3, False, True)])
        self.assertEqual(game.world.round_id, 4)
        prompt = devices.stopped_prompt
        self.assertEqual(prompt.event_name, "WhenRoundEnd")
        self.assertEqual(prompt.ability_type, "ForcedInterrupt")
        self.assertFalse(prompt.show_cancel)
        self.assertEqual(len(prompt.options), 2)
        self.assertEqual({option["bind_id"] for option in prompt.options}, {44, 45})

    def test_empty_temporary_order_refreshes_and_both_discard_orders_continue(self):
        for first_index in (0, 1):
            with self.subTest(first_index=first_index):
                prompts = []
                render_ids = []
                discarded = []
                leave_play = Message.AfterCardLeavePlay.Send

                def record_discard(message):
                    if message.trigger.paper.card_id == "60052":
                        discarded.append(message.trigger.card.object_id)
                    return leave_play(message)

                def choose(prompt):
                    if len(devices.prompts) > 30:
                        return None
                    if prompt.event_name == "WhenRoundEnd":
                        prompts.append(prompt)
                        render_ids.append(Engine.game.world.render.last_render_id)
                        if len(prompts) <= 2:
                            # Simulate End, including a stale client retry.
                            return CommandDescriptor()
                        option = prompt.options[first_index]
                        return CommandDescriptor(HeadlessDeviceManager._DescriptorId(option))
                    if prompt.event_name == "WhenPlayerInTurn":
                        return None
                    return (CommandDescriptor() if prompt.show_cancel
                            else HeadlessDeviceManager._DefaultChoice(prompt))

                devices = HeadlessDeviceManager(choice_provider=choose)
                with patch.object(Message.AfterCardLeavePlay, "Send", record_discard):
                    game = self.run_scene(validate_file(SAVE), devices, replay=True)
                self.assertEqual(len(prompts), 3)
                self.assertEqual(prompts[0], prompts[1])
                self.assertEqual(prompts[1], prompts[2])
                self.assertGreater(render_ids[1], render_ids[0])
                self.assertGreater(render_ids[2], render_ids[1])
                first = prompts[0].options[first_index]["bind_id"]
                second = prompts[0].options[1 - first_index]["bind_id"]
                self.assertEqual(discarded, [first, second])
                player = game.world.const_players[0]
                self.assertEqual(
                    {face.card.object_id for face in player.discard_pile.Get()
                     if face.paper.card_id == "60052"}, {44, 45},
                )
                self.assertEqual(game.world.round_id, 5)
                self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")

    def test_azazel_quickstrike_attacks_heroes_but_not_alter_egos(self):
        for legacy in (False, True):
            for hero_form in (False, True):
                for placement in ("Reveal", "PutIntoPlay"):
                    with self.subTest(legacy=legacy, hero=hero_form, placement=placement):
                        scene = validate_file(SAVE)
                        scene.inputs = []
                        if legacy:
                            scene.rules.remove("v18_timing")
                            scene.rules.append("no_v18_timing")
                        commands = iter([
                            *(['ChangeForm(c1, "Hero")'] if hero_form else []),
                            f'puzzle.{placement}("48027")',
                        ])
                        initial_health = []
                        attack_prompts = []

                        def choose(prompt):
                            if len(devices.prompts) > 30:
                                return None
                            if prompt.event_name == "WhenPlayerInTurn":
                                world = Engine.game.world
                                if not initial_health:
                                    initial_health.append(world.const_players[0].GetIdentity().health)
                                command = next(commands, None)
                                if command is None:
                                    return None
                                Engine.game.controller_manager.console.SetCommand(command, world)
                                return CommandDescriptor()
                            if prompt.event_name == "WhenUnitBeingAttack":
                                attack_prompts.append(prompt)
                            return (CommandDescriptor() if prompt.show_cancel
                                    else HeadlessDeviceManager._DefaultChoice(prompt))

                        devices = HeadlessDeviceManager(choice_provider=choose)
                        game = self.run_scene(scene, devices)
                        self.assertEqual(devices.stopped_prompt.event_name, "WhenPlayerInTurn")
                        self.assertEqual(len(attack_prompts), int(hero_form))
                        player = game.world.const_players[0]
                        self.assertEqual(player.GetIdentity().health,
                                         initial_health[0] - (3 if hero_form else 0))
                        self.assertEqual(sum(face.paper.card_id == "48027"
                                             for face in player.engaged_minions.Get()), 1)


if __name__ == "__main__":
    unittest.main()
