import contextlib
import io
import unittest
from unittest.mock import patch

from engine import Engine
from game.card.factory import CardFactory
from game.operate.worlds import Worlds
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender


class TestCarjackingPreview(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_database()

    def test_choice_identifies_vehicle_before_and_after_encounter_deck_reset(self):
        for timing in ("v18_timing", "no_v18_timing"):
            for last_card in (False, True):
                with self.subTest(timing=timing, last_card=last_card):
                    scene = SceneLoader.NewScene("rhino", None, ["iron_man"], 94)
                    scene.rules = ["v16_all", timing]
                    started = False
                    checkpoint = {}
                    presentations = []
                    original_present = WorldRender.Present

                    def present(render, text, sound, event_name, *faces, **kwargs):
                        if text is not None:
                            presentations.append(text.text_symbol)
                        return original_present(
                            render, text, sound, event_name, *faces, **kwargs,
                        )

                    def choose(prompt):
                        nonlocal started
                        world = Engine.game.world
                        deck = Worlds.GetAllVillains(world)[0].encounter_deck
                        if prompt.event_name == "WhenPlayerInTurn":
                            if started:
                                return None
                            started = True
                            # Build a deterministic encounter deck in a running
                            # game. The top non-vehicle is discarded first.
                            deck.bind_discard_pile.Clear()
                            deck.Clear()
                            if not last_card:
                                CardFactory.GenerateCard("01191", deck, world)
                            CardFactory.GenerateCard("60187", deck, world)
                            CardFactory.GenerateCard("01186", deck, world)
                            if last_card:
                                CardFactory.GenerateCard(
                                    "01191", deck.bind_discard_pile, world,
                                )
                            Engine.game.controller_manager.console.SetCommand(
                                'Reveal("Carjacking")', world,
                            )
                            return CommandDescriptor()
                        if started and prompt.event_name == "WhenPlayerChooseAbility":
                            checkpoint["prompt"] = prompt
                            checkpoint["presentations"] = presentations[:]
                            checkpoint["resets"] = deck.shuffle_with_discard_count
                            checkpoint["deck_ids"] = {
                                face.paper.card_id for face in deck.Get()
                            }
                            vehicle = (deck if last_card else deck.bind_discard_pile).FindCard(
                                name="60187",
                            )
                            checkpoint["visible"] = vehicle.card.IsVisible("Any")
                            return None
                        return HeadlessDeviceManager._DefaultChoice(prompt)

                    devices = HeadlessDeviceManager(choice_provider=choose)
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        patch.object(WorldRender, "Present", new=present),
                        patch.object(WorldRender, "ErrorOccurred") as error,
                    ):
                        run_scene_with_devices(scene, devices)

                    error.assert_not_called()
                    self.assertIn("prompt", checkpoint)
                    self.assertEqual(
                        [
                            option["name"].replace("_", " ")
                            for option in checkpoint["prompt"].options
                        ],
                        [
                            "Spend 3 resources of the same type → attach Motorcycle to your identity",
                            "Reveal Motorcycle",
                        ],
                    )
                    # A public printed-card reference supplies the existing log
                    # hover preview without linking to the shuffled card object.
                    self.assertIn(
                        "Discarded card found: [(0,60187) Motorcycle]",
                        checkpoint["presentations"],
                    )
                    self.assertEqual(checkpoint["resets"], int(last_card))
                    self.assertEqual(checkpoint["visible"], not last_card)
                    self.assertEqual(
                        checkpoint["deck_ids"],
                        {"60187", "01186", "01191"} if last_card else {"01191"},
                    )


if __name__ == "__main__":
    unittest.main()
