from importlib import import_module
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.card.face.base import Unit2


def find_condition(ability, name):
    return next(condition for condition in ability.conditions if condition.__name__ == name)


class TestIonicPhysiology(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.wonder_man.wonder_man.58002")
        self.ability = self.module.GetAbilities()[0]
        self.identity = MagicMock()
        self.player = SimpleNamespace(GetIdentity=MagicMock(return_value=self.identity))
        self.event = SimpleNamespace(CastTo=MagicMock())
        self.upgrade = MagicMock()
        self.effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=self.upgrade)),
            GetInitiator=MagicMock(return_value=self.player),
        )
        self.message = SimpleNamespace(
            played_face=self.event,
            play_effect=SimpleNamespace(ability=SimpleNamespace(is_play=True)),
        )

    def test_heals_after_event_is_tucked(self):
        self.upgrade.TuckCardUnderHere.return_value = True

        self.ability.operation(self.effect, self.message)

        self.identity.HealthUnits.assert_called_once_with([self.identity], 1, self.effect)

    def test_does_not_heal_when_event_cannot_be_tucked(self):
        self.upgrade.TuckCardUnderHere.return_value = False

        self.ability.operation(self.effect, self.message)

        self.identity.HealthUnits.assert_not_called()


class TestSentry(unittest.TestCase):

    def setUp(self):
        self.module = import_module("cards.pack.wonder_man.58015")
        self.ability = self.module.GetAbilities()[0]
        self.sentry = MagicMock()
        self.player = MagicMock()
        self.effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=self.sentry)),
            GetInitiator=MagicMock(return_value=self.player),
        )

    def test_places_six_threat_when_search_finds_no_side_scheme(self):
        with patch.object(self.module.Search, "EncounterCard", return_value=None):
            self.ability.operation(self.effect, SimpleNamespace())

        self.sentry.PlaceThreatOnSchemes.assert_called_once_with(
            "MainScheme", 6, self.effect
        )

    def test_places_six_threat_when_reveal_is_prevented(self):
        scheme = MagicMock()
        scheme.Reveal.return_value = None

        with patch.object(self.module.Search, "EncounterCard", return_value=scheme):
            self.ability.operation(self.effect, SimpleNamespace())

        self.sentry.PlaceThreatOnSchemes.assert_called_once_with(
            "MainScheme", 6, self.effect
        )

    def test_passes_fallback_for_side_scheme_that_does_not_enter_play(self):
        scheme = MagicMock()
        scheme.Reveal.return_value = MagicMock()

        with patch.object(self.module.Search, "EncounterCard", return_value=scheme):
            self.ability.operation(self.effect, SimpleNamespace())

        fallback = scheme.Reveal.call_args.kwargs["if_no_entered_play"]
        fallback()
        self.sentry.PlaceThreatOnSchemes.assert_called_once_with(
            "MainScheme", 6, self.effect
        )


class TestStrongerTogether(unittest.TestCase):

    def test_can_protect_any_character_except_your_hero(self):
        module = import_module("cards.pack.wonder_man.58019")
        ability = module.GetAbilities()[0]
        hero = MagicMock()
        enemy = MagicMock()
        player = SimpleNamespace(GetHero=MagicMock(return_value=hero))
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))
        message = SimpleNamespace(trigger=enemy)
        check_who = find_condition(ability, "check_who_take_damage")

        with patch.object(module.Condition, "CheckWhichCard", return_value=True) as check:
            self.assertTrue(check_who(effect, message))

        finder = check.call_args.args[0]
        self.assertIs(finder.card_type, Unit2)
        self.assertTrue(finder.check_effect_fns[0](effect, enemy))
        self.assertFalse(finder.check_effect_fns[0](effect, hero))


class TestSignatureSunglasses(unittest.TestCase):

    def test_response_is_not_available_without_a_valid_choice(self):
        module = import_module("cards.pack.wonder_man.wonder_man.58010")
        ability = module.GetAbilities()[0]
        condition = find_condition(ability, "can_use_signature_sunglasses")
        player = SimpleNamespace(
            discard_pile=SimpleNamespace(Get=MagicMock(return_value=[])),
        )
        effect = SimpleNamespace(GetInitiator=MagicMock(return_value=player))

        with patch.object(module, "FindIonicPhysiology", return_value=None):
            self.assertFalse(condition(effect, SimpleNamespace()))

    def test_response_is_available_with_a_tucked_card(self):
        module = import_module("cards.pack.wonder_man.wonder_man.58010")
        ability = module.GetAbilities()[0]
        condition = find_condition(ability, "can_use_signature_sunglasses")
        ionic = SimpleNamespace(
            GetPlacedCardArea=MagicMock(
                return_value=SimpleNamespace(GetSize=MagicMock(return_value=1))
            )
        )
        effect = SimpleNamespace(GetInitiator=MagicMock())

        with patch.object(module, "FindIonicPhysiology", return_value=ionic):
            self.assertTrue(condition(effect, SimpleNamespace()))


class TestAvengersCompound(unittest.TestCase):

    def test_action_is_not_available_with_no_tucked_ally_or_ally_in_hand(self):
        module = import_module("cards.pack.wonder_man.58034")
        ability = module.GetAbilities()[1]
        condition = find_condition(ability, "can_use_avengers_compound")
        support = SimpleNamespace(
            GetPlacedCardArea=MagicMock(
                return_value=SimpleNamespace(GetSize=MagicMock(return_value=0))
            )
        )
        player = SimpleNamespace(
            hand_cards=SimpleNamespace(Get=MagicMock(return_value=[])),
        )
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=support)),
            GetInitiator=MagicMock(return_value=player),
        )

        self.assertFalse(condition(effect, SimpleNamespace()))

    def test_action_is_available_with_a_tucked_ally(self):
        module = import_module("cards.pack.wonder_man.58034")
        ability = module.GetAbilities()[1]
        condition = find_condition(ability, "can_use_avengers_compound")
        support = SimpleNamespace(
            GetPlacedCardArea=MagicMock(
                return_value=SimpleNamespace(GetSize=MagicMock(return_value=1))
            )
        )
        effect = SimpleNamespace(
            this=SimpleNamespace(CastTo=MagicMock(return_value=support)),
            GetInitiator=MagicMock(),
        )

        self.assertTrue(condition(effect, SimpleNamespace()))


if __name__ == "__main__":
    unittest.main()
