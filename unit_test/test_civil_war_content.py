import json
from importlib import import_module
from pathlib import Path
import unittest
from unittest.mock import MagicMock, Mock, patch

from engine import Engine  # noqa: F401 - establishes project import order


class TestCivilWarExpertScenarios(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]
    scenarios_path = project_root / "data" / "scenarios"

    scenarios = {
        "iron_man": (["56059", "56060"], ["56061", "56062"]),
        "captain_marvel": (["56092", "56093"], ["56094", "56095"]),
        "captain_america": (["56137", "56138"], ["56139", "56140"]),
        "spider_woman": (["56168", "56169"], ["56170", "56171"]),
    }

    def load_scenario(self, name: str, *, expert: bool) -> dict:
        suffix = "_expert" if expert else ""
        path = self.scenarios_path / f"{name}{suffix}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_expert_scenarios_use_stages_three_and_four(self):
        for name, (standard_stages, expert_stages) in self.scenarios.items():
            with self.subTest(scenario=name):
                standard = self.load_scenario(name, expert=False)
                expert = self.load_scenario(name, expert=True)

                self.assertEqual(standard["villain"], standard_stages)
                self.assertEqual(expert["villain"], expert_stages)
                self.assertFalse(standard["expert"])
                self.assertTrue(expert["expert"])
                self.assertEqual(expert["encounter_sets"], ["standard", "expert"])

    def test_expert_scenarios_preserve_the_standard_scenario_content(self):
        fields = ("version", "name", "schemes", "set_aside", "encounters", "modular_sets")

        for name in self.scenarios:
            with self.subTest(scenario=name):
                standard = self.load_scenario(name, expert=False)
                expert = self.load_scenario(name, expert=True)

                for field in fields:
                    self.assertEqual(expert[field], standard[field])

    def test_expert_stages_inherit_the_matching_leader_scripts(self):
        cards_path = self.project_root / "data" / "cards.json"
        cards = json.loads(cards_path.read_text(encoding="utf-8"))["cw"]
        by_id = {card["card_id"]: card for card in cards}

        expected_links = {
            "56061": "56059",
            "56062": "56060",
            "56094": "56092",
            "56095": "56093",
            "56139": "56137",
            "56140": "56138",
            "56170": "56168",
            "56171": "56169",
        }

        for expert_stage, scripted_stage in expected_links.items():
            with self.subTest(card=expert_stage):
                self.assertEqual(by_id[expert_stage]["ability_link"], scripted_stage)

    def test_every_civil_war_rules_card_has_a_script_or_valid_ability_link(self):
        cards_path = self.project_root / "data" / "cards.json"
        cards = json.loads(cards_path.read_text(encoding="utf-8"))["cw"]
        script_ids = {
            path.stem
            for path in (self.project_root / "cards" / "pack" / "cw").rglob("*.py")
            if path.stem != "__init__"
        }

        for card in cards:
            card_id = card["card_id"]
            if not card.get("name") or not card.get("text") or card_id in script_ids:
                continue

            with self.subTest(card=card_id):
                self.assertIn("ability_link", card)
                self.assertIn(card["ability_link"], script_ids)


class TestTwoGunKid(unittest.TestCase):

    def test_additional_attack_target_must_be_a_different_enemy(self):
        module = import_module("cards.pack.cw.56010")
        ability = MagicMock()
        ability.SetTarget.return_value = ability

        with patch.object(
            module.AbilityFactory,
            "WhenUnitMakeAttack",
            return_value=ability,
        ) as make_attack:
            module.GetAbilities()

        check_fn = ability.SetTarget.call_args.kwargs["check_fn"]
        original_target = Mock()
        other_target = Mock()
        attack_message = Mock()
        attack_message.HasTarget.side_effect = (
            lambda target: target is original_target
        )
        effect = Mock()
        effect.GetBindMessage.return_value = attack_message

        self.assertFalse(check_fn(effect, original_target))
        self.assertTrue(check_fn(effect, other_target))

        operation = make_attack.call_args.args[2]
        effect.this.CastTo.return_value = effect.this
        effect.targets = [original_target]
        operation(effect, attack_message)
        attack_message.AddTarget.assert_not_called()

        effect.targets = [original_target, other_target]
        operation(effect, attack_message)

        attack_message.AddTarget.assert_called_once_with(other_target)


if __name__ == "__main__":
    unittest.main()
