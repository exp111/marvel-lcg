from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.operate.search import Search
from game.operate.search_internal import SearchInternal
from game.selector.factory import Select
from game.selector.selector_end import SelectorEnd
from game.world.world_rule import WorldRule


class FakeDeck:
    def __init__(self, *, is_deck=True, is_discards=False):
        self.flags = SimpleNamespace(
            is_deck=is_deck,
            is_discards=is_discards,
        )
        self.faces = []
        self.Shuffle = MagicMock()

    def Get(self, from_top=False):
        return list(reversed(self.faces)) if from_top else list(self.faces)

    def GetSize(self):
        return len(self.faces)


def make_deck(card_count=3, **kwargs):
    deck = FakeDeck(**kwargs)
    deck.faces = [
        SimpleNamespace(
            name=f"Card {index + 1}",
            card=SimpleNamespace(area=deck, object_id=index + 1),
        )
        for index in range(card_count)
    ]
    return deck


class TestFullDeckSearchDisplay(unittest.TestCase):

    def test_setup_option_is_off_by_default_and_persisted(self):
        rule = WorldRule()
        self.assertFalse(bool(rule.show_deck_during_full_search))

        rule.SetRule(["show_deck_during_full_search"], False, 1)
        self.assertTrue(bool(rule.show_deck_during_full_search))

        scene = (Path(__file__).resolve().parents[1] / "public" / "scene.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="show_deck_during_full_search"', scene)
        self.assertIn("new_game.rules.push('show_deck_during_full_search')", scene)
        self.assertIn("'show_deck_during_full_search', 'scene_3d'", scene)

    def call_search(self, deck, *, enabled=True, **kwargs):
        effect = SimpleNamespace(
            world=SimpleNamespace(
                rule=SimpleNamespace(show_deck_during_full_search=enabled)
            )
        )
        player = SimpleNamespace()
        with patch.object(
            SearchInternal,
            "SearchForCardsInternal",
            return_value=[],
        ) as search_internal:
            Search.SearchForCards(
                effect,
                player,
                faces=deck.Get(True),
                **kwargs,
            )
        return search_internal.call_args.kwargs["full_search_decks"]

    def test_complete_specialized_deck_enables_full_search_display(self):
        deck = make_deck()

        self.assertEqual(self.call_search(deck), [deck])

    def test_limited_or_non_shuffling_searches_keep_curated_display(self):
        deck = make_deck()

        cases = [
            {"enabled": False},
            {"most_top": 2},
            {"not_move": True},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.call_search(deck, **kwargs), [])

    def test_select_all_gameplay_search_still_displays_the_full_deck(self):
        deck = make_deck()

        self.assertEqual(self.call_search(deck, range="All"), [deck])

    def test_face_the_past_searches_all_listed_areas_through_toggle_aware_search(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "cards"
            / "pack"
            / "magneto"
            / "49022.py"
        ).read_text(encoding="utf-8")

        self.assertIn("include_encounter_deck=True", source)
        self.assertIn("include_encounter_discard_pile=True", source)
        self.assertIn("include_set_aside=True", source)
        self.assertIn('range="All"', source)

    def test_multi_area_search_displays_discard_but_only_shuffles_actual_deck(self):
        encounter_deck = make_deck()
        encounter_discard = make_deck(is_discards=True)
        set_aside = make_deck(is_deck=False)
        effect = SimpleNamespace(
            world=SimpleNamespace(
                rule=SimpleNamespace(show_deck_during_full_search=True)
            )
        )

        with patch.object(
            SearchInternal,
            "SearchForCardsInternal",
            return_value=[],
        ) as search_internal:
            Search.SearchForCards(
                effect,
                SimpleNamespace(),
                faces=(
                    encounter_deck.Get(True)
                    + encounter_discard.Get(True)
                    + set_aside.Get(True)
                ),
                range="All",
            )

        self.assertEqual(
            search_internal.call_args.kwargs["full_search_decks"],
            [encounter_deck],
        )
        self.assertEqual(
            search_internal.call_args.kwargs["full_search_display_faces"],
            encounter_deck.Get(True) + encounter_discard.Get(True),
        )

    def test_partial_explicit_deck_is_not_treated_as_full_search(self):
        deck = make_deck()
        effect = SimpleNamespace(
            world=SimpleNamespace(
                rule=SimpleNamespace(show_deck_during_full_search=True)
            )
        )
        with patch.object(
            SearchInternal,
            "SearchForCardsInternal",
            return_value=[],
        ) as search_internal:
            Search.SearchForCards(
                effect,
                SimpleNamespace(),
                faces=deck.Get(True)[:2],
            )

        self.assertEqual(
            search_internal.call_args.kwargs["full_search_decks"],
            [],
        )

    def test_full_search_forces_prompt_and_exposes_only_display_metadata(self):
        deck = make_deck()
        player = SimpleNamespace(AskChooseSelect=MagicMock(return_value=[]))
        finder = SimpleNamespace(Checks=MagicMock(return_value=[]))
        captured_selector = SimpleNamespace()

        def capture_selector(**kwargs):
            captured_selector.kwargs = kwargs
            return SimpleNamespace()

        with patch("game.operate.search_internal.Select.From", side_effect=capture_selector):
            SearchInternal.SearchForCardsInternal(
                SimpleNamespace(),
                player,
                deck.Get(True),
                process_choose=None,
                process_other=None,
                finder=finder,
                may=False,
                full_search_decks=[deck],
            )

        self.assertTrue(captured_selector.kwargs["force_choose"])
        self.assertEqual(captured_selector.kwargs["faces"], deck.Get(True))
        self.assertEqual(
            captured_selector.kwargs["full_search_display_faces"],
            deck.Get(True),
        )
        player.AskChooseSelect.assert_called_once()

    def test_discard_only_search_opens_no_match_viewer_without_shuffling_discard(self):
        discard = make_deck(is_discards=True)
        player = SimpleNamespace(AskChooseSelect=MagicMock(return_value=[]))
        finder = SimpleNamespace(Checks=MagicMock(return_value=[]))
        captured_selector = SimpleNamespace()

        def capture_selector(**kwargs):
            captured_selector.kwargs = kwargs
            return SimpleNamespace()

        with patch("game.operate.search_internal.Select.From", side_effect=capture_selector):
            SearchInternal.SearchForCardsInternal(
                SimpleNamespace(),
                player,
                discard.Get(True),
                process_choose=None,
                process_other=None,
                finder=finder,
                may=False,
                full_search_display_faces=discard.Get(True),
                full_search_decks=[],
            )

        self.assertTrue(captured_selector.kwargs["force_choose"])
        self.assertEqual(
            captured_selector.kwargs["full_search_display_faces"],
            discard.Get(True),
        )
        self.assertEqual(captured_selector.kwargs["full_search_decks"], [])
        player.AskChooseSelect.assert_called_once()

    def test_full_discard_display_preserves_a_valid_target_selection(self):
        discard = make_deck(is_discards=True)
        valid_target = discard.Get(True)[0]
        player = SimpleNamespace(
            AskChooseSelect=MagicMock(return_value=[valid_target])
        )
        finder = SimpleNamespace(
            Checks=MagicMock(return_value=[valid_target])
        )
        process_choose = MagicMock()
        captured_selector = SimpleNamespace()

        def capture_selector(**kwargs):
            captured_selector.kwargs = kwargs
            return SimpleNamespace()

        with patch("game.operate.search_internal.Select.From", side_effect=capture_selector):
            selected = SearchInternal.SearchForCardsInternal(
                SimpleNamespace(),
                player,
                discard.Get(True),
                process_choose=process_choose,
                process_other=None,
                finder=finder,
                may=False,
                full_search_display_faces=discard.Get(True),
                full_search_decks=[],
            )

        self.assertEqual(selected, [valid_target])
        self.assertIs(captured_selector.kwargs["finder"], finder)
        self.assertEqual(captured_selector.kwargs["range"], (1, 1))
        process_choose.assert_called_once_with(valid_target)

    def test_force_choose_allows_a_no_match_viewer(self):
        selector = Select.From(faces=[], range=(1, 1), force_choose=True)

        self.assertEqual(selector.GetTargetRange(SimpleNamespace(), []), (0, 0))

    def test_direct_full_deck_search_enables_display_from_raw_selector_faces(self):
        deck = make_deck()
        selector = Select.From(
            faces=deck.Get(True),
            from_where=[],
            by_search=True,
        )
        effect = SimpleNamespace(
            world=SimpleNamespace(
                rule=SimpleNamespace(
                    show_deck_during_full_search=True,
                    v16_referential_ability=False,
                )
            ),
            initiator=SimpleNamespace(),
        )

        selector.GetAllLegalTargets(effect)

        self.assertTrue(selector.force_choose)
        self.assertEqual(selector.selector_end.full_search_decks, [deck])
        self.assertEqual(
            selector.selector_end.full_search_display_faces,
            deck.Get(True),
        )

    def test_direct_multi_area_search_displays_discard_without_shuffling_it(self):
        deck = make_deck()
        discard = make_deck(is_discards=True)
        selector = Select.From(
            faces=deck.Get(True) + discard.Get(True),
            from_where=[],
            by_search=True,
        )
        effect = SimpleNamespace(
            world=SimpleNamespace(
                rule=SimpleNamespace(
                    show_deck_during_full_search=True,
                    v16_referential_ability=False,
                )
            ),
            initiator=SimpleNamespace(),
        )

        selector.GetAllLegalTargets(effect)

        self.assertEqual(selector.selector_end.full_search_decks, [deck])
        self.assertEqual(
            selector.selector_end.full_search_display_faces,
            deck.Get(True) + discard.Get(True),
        )

    def test_direct_limited_or_non_shuffling_selectors_do_not_show_full_deck(self):
        deck = make_deck()
        effect = SimpleNamespace(
            world=SimpleNamespace(
                rule=SimpleNamespace(show_deck_during_full_search=True)
            )
        )

        selectors = [
            Select.From(faces=deck.Get(True)[:2], by_search=True),
            Select.From(faces=deck.Get(True), by_search=True, not_move=True),
            Select.From(faces=deck.Get(True), by_search=True, not_shuffle=True),
            Select.From(
                faces=deck.Get(True),
                by_search=True,
                display_in_target_order=True,
            ),
        ]
        for selector in selectors:
            with self.subTest(selector_end=selector.selector_end):
                selector.EnableFullSearchDisplay(
                    effect,
                    selector.selector_target.faces or [],
                )
                self.assertFalse(selector.force_choose)

    def test_suit_up_supplies_the_complete_search_zones_to_its_selector(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "cards"
            / "pack"
            / "aoa"
            / "45017.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "search_faces = initiator.player_deck.Get() + initiator.discard_pile.Get()",
            source,
        )
        self.assertIn("Faces.LookAt(selectable_faces, initiator, effect)", source)
        self.assertIn(").SetTarget(search_faces,", source)

    def test_no_match_viewer_still_shuffles_every_full_search_deck(self):
        first = make_deck()
        second = make_deck()
        selector_end = SelectorEnd(
            peek=True,
            full_search_decks=[first, second],
            force_choose=True,
        )

        with patch.object(SelectorEnd, "DoMove", return_value=[]):
            selector_end.Process(SimpleNamespace(), [])

        first.Shuffle.assert_called_once()
        second.Shuffle.assert_called_once()

    def test_client_displays_full_deck_without_making_invalid_cards_legal(self):
        project_root = Path(__file__).resolve().parents[1]
        effect_source = (project_root / "public" / "js" / "marvel" / "effect.ts").read_text(
            encoding="utf-8"
        )
        cards_source = (project_root / "public" / "js" / "marvel" / "cards.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("...Effect.select_effect_obj.full_search_display_targets", effect_source)
        self.assertIn("search_display_targets.has(object_id)", effect_source)
        self.assertIn(
            "Effect.select_effect_obj.all_legal_targets.includes(object_id)",
            effect_source,
        )
        self.assertIn(
            "if (Effect.select_effect_obj.full_search_display_targets.length > 0)",
            cards_source,
        )


if __name__ == "__main__":
    unittest.main()
