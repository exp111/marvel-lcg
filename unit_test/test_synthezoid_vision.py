from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.ability import TimingPriority
from game.event.manager import EventManager


class TestVisionMassForm(unittest.TestCase):

    def test_forced_response_finds_either_mass_form_and_flips_it(self):
        for module_name in (
            "cards.pack.synthezoid.vision.57040",
            "cards.pack.synthezoid.vision.57041",
        ):
            with self.subTest(module=module_name):
                module = import_module(module_name)
                leader = MagicMock()
                form = MagicMock()
                effect = SimpleNamespace(this=MagicMock())
                effect.this.CastTo.return_value = leader

                with patch.object(module, "CardFinder") as finder:
                    finder.return_value.Checks.return_value = [form]
                    forced_response = next(
                        ability
                        for ability in module.GetAbilities()
                        if ability.operation.__name__ == "_flip_mass_form"
                    )
                    forced_response.operation(effect, MagicMock())

                finder.assert_called_once_with(names=["Dense", "Intangible"])
                finder.return_value.Checks.assert_called_once_with(
                    leader.GetAttachedAttachments.return_value
                )
                form.card.Flip.assert_called_once_with(effect)

    def test_printed_stat_modifiers_are_not_scripted_a_second_time(self):
        modules_without_extra_keywords = (
            "cards.pack.synthezoid.she_hulk.57007",
            "cards.pack.synthezoid.taskmaster.57023",
            "cards.pack.synthezoid.taskmaster.57024",
            "cards.pack.synthezoid.vision.57046a",
            "cards.pack.synthezoid.vision.57046b",
            "cards.pack.synthezoid.moon_knight.57066",
        )
        for module_name in modules_without_extra_keywords:
            with self.subTest(module=module_name):
                module = import_module(module_name)
                with patch.object(
                    module.AbilityFactory, "GiveKeywordToAttached", return_value=[]
                ) as give_keyword:
                    module.GetAbilities()
                give_keyword.assert_not_called()

        expected_non_stat_keywords = {
            "cards.pack.synthezoid.she_hulk.57008": ("Leader", {"stalwart": 1}),
            "cards.pack.synthezoid.vision.57047": ("Leader", {"stalwart": 1}),
            "cards.pack.synthezoid.vision.57048": ("Leader", {"retaliate": 1}),
        }
        for module_name, (target_name, keywords) in expected_non_stat_keywords.items():
            with self.subTest(module=module_name):
                module = import_module(module_name)
                target = getattr(module, target_name)
                with patch.object(
                    module.AbilityFactory, "GiveKeywordToAttached", return_value=[]
                ) as give_keyword:
                    module.GetAbilities()
                give_keyword.assert_called_once_with(target, **keywords)


class TestSheHulkVillain(unittest.TestCase):

    def test_forced_response_damages_the_hero_that_changed_form_once(self):
        for module_name in (
            "cards.pack.synthezoid.she_hulk.57001",
            "cards.pack.synthezoid.she_hulk.57002",
        ):
            with self.subTest(module=module_name):
                module = import_module(module_name)
                villain = MagicMock()
                hero = MagicMock()
                effect = SimpleNamespace(this=villain)
                message = SimpleNamespace(trigger=hero)
                forced_response = next(
                    ability
                    for ability in module.GetAbilities()
                    if ability.operation.__name__ == "_damage_changed_hero"
                )

                forced_response.operation(effect, message)

                villain.DealDamage.assert_called_once_with([hero], 1, effect)

    def test_expert_stages_inherit_the_correct_she_hulk_scripts(self):
        cards_path = Path(__file__).parents[1] / "data" / "cards.json"
        cards = json.loads(cards_path.read_text(encoding="utf-8"))["synthezoid"]
        by_id = {card["card_id"]: card for card in cards}

        self.assertEqual(by_id["57003"]["ability_link"], "57001")
        self.assertEqual(by_id["57004"]["ability_link"], "57002")


class TestForcedEffectDispatch(unittest.TestCase):

    def test_registered_forced_effect_runs_without_a_local_forced_effect(self):
        class DummyMessage:
            name = "DummyMessage"

            def __init__(self, world):
                self.world = world
                self.related_faces = set()

        world = MagicMock()
        world.is_game_over = False
        manager = EventManager(world)
        message = DummyMessage(world)
        effect = MagicMock()
        effect.ability.priority = TimingPriority.ForcedResponse

        manager.registered_message_type[DummyMessage] = 1
        manager.effects["Forced"][DummyMessage] = {
            TimingPriority.ForcedResponse: [effect]
        }

        with patch.object(manager, "ProcessForcedEffect", return_value=False) as process:
            manager.BroadcastMessage(message)

        process.assert_called_once_with(
            message,
            [effect],
            TimingPriority.ForcedResponse,
            None,
        )


if __name__ == "__main__":
    unittest.main()
