from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch

from engine import Engine  # noqa: F401 - establishes the project's import order


class TestHerculesDefeatTheHydra(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.hercules.hercules.59002")
        self.ability = self.module.GetAbilities()[0]
        self.labor = MagicMock()
        self.labor.CastTo.return_value = self.labor
        self.player = MagicMock()
        self.effect = SimpleNamespace(this=self.labor)
        self.message = SimpleNamespace(
            GetToPlayer=MagicMock(return_value=self.player),
        )

    def test_uses_normal_eligible_minion_before_nemesis_fallback(self):
        target = MagicMock()

        with patch.object(
            self.module.Find,
            "FindAndReveal",
            return_value=target,
        ) as find_and_reveal, patch.object(
            self.module.Faces,
            "DiscardAll",
        ) as discard_all:
            self.ability.operation(self.effect, self.message)

        find_and_reveal.assert_called_once()
        self.labor.HealthUnits.assert_called_once_with([target], "All", self.effect)
        self.labor.AttachTo2.assert_called_once_with(target, self.effect)
        discard_all.assert_not_called()

    def test_falls_back_to_hercules_nemesis_minion(self):
        target = MagicMock()
        normal_finder = object()
        nemesis_finder = object()

        with patch.object(
            self.module,
            "CardFinder",
            side_effect=[normal_finder, nemesis_finder],
        ) as card_finder, patch.object(
            self.module.Find,
            "FindAndReveal",
            side_effect=[None, target],
        ) as find_and_reveal, patch.object(
            self.module.Faces,
            "DiscardAll",
        ) as discard_all:
            self.ability.operation(self.effect, self.message)

        fallback_kwargs = card_finder.call_args_list[1].kwargs
        self.assertIs(fallback_kwargs["card_type"], self.module.Minion)
        self.assertEqual(fallback_kwargs["non_trait"], "ELITE")
        self.assertIs(fallback_kwargs["is_nemesis"], self.player)
        self.assertTrue(
            fallback_kwargs["check_face_fn"](
                SimpleNamespace(printed_health=6),
            )
        )
        self.assertEqual(
            card_finder.call_args_list[0].kwargs["is_nemesis"],
            False,
        )
        self.assertEqual(
            find_and_reveal.call_args_list[1],
            call(
                self.effect,
                self.player,
                who_perform=self.player,
                finder=nemesis_finder,
            ),
        )
        self.labor.HealthUnits.assert_called_once_with([target], "All", self.effect)
        self.labor.AttachTo2.assert_called_once_with(target, self.effect)
        discard_all.assert_not_called()

    def test_discards_labor_when_no_target_exists_anywhere(self):
        with patch.object(
            self.module.Find,
            "FindAndReveal",
            side_effect=[None, None],
        ), patch.object(
            self.module.Faces,
            "DiscardAll",
        ) as discard_all:
            self.ability.operation(self.effect, self.message)

        discard_all.assert_called_once_with([self.labor], self.effect)
        self.labor.HealthUnits.assert_not_called()
        self.labor.AttachTo2.assert_not_called()


class TestHerculesLaborDiscardRouting(unittest.TestCase):

    def test_labor_cards_are_bound_to_the_encounter_discard_pile(self):
        module = import_module("cards.pack.hercules")
        labor = MagicMock()
        gift = MagicMock()
        set_aside = [labor, gift]
        labor_deck = MagicMock()
        gift_deck = MagicMock()
        encounter_discard = MagicMock()
        player = SimpleNamespace(
            special_decks={},
            set_aside_deck=SimpleNamespace(Get=MagicMock(return_value=set_aside)),
        )
        effect = SimpleNamespace(
            GetInitiator=MagicMock(return_value=player),
            world=SimpleNamespace(additional_decks=[]),
        )
        labor_finder = SimpleNamespace(Checks=MagicMock(return_value=[labor]))
        gift_finder = SimpleNamespace(Checks=MagicMock(return_value=[gift]))

        with patch.object(
            module,
            "Deck2",
            side_effect=[labor_deck, gift_deck],
        ), patch.object(
            module,
            "CardFinder",
            side_effect=[labor_finder, gift_finder],
        ), patch.object(
            module.Worlds,
            "GetEncounterDiscardPile",
            return_value=encounter_discard,
        ), patch.object(
            module.Faces,
            "BindDiscardPile",
        ) as bind_discard, patch.object(
            module.Faces,
            "MoveAllTo",
        ):
            module.SetupHerculesSpecialDecks(effect, SimpleNamespace())

        bind_discard.assert_called_once_with([labor], encounter_discard)


if __name__ == "__main__":
    unittest.main()
