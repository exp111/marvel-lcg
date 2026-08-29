from pathlib import Path
import unittest

from engine import Engine  # noqa: F401 - establishes the project's import order
from game.selector.factory import Select


class TestOrderedDeckSelectionUI(unittest.TestCase):

    def test_selectable_deck_cards_show_draw_order_from_right_to_left(self):
        project_root = Path(__file__).resolve().parents[1]
        source = (project_root / "public" / "js" / "marvel" / "cards.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("const targetOrder = new Map<number, number>()", source)
        self.assertIn(
            "if (Effect.select_effect_obj.display_in_target_order)",
            source,
        )
        self.assertIn(
            "if (aOrder !== undefined && bOrder !== undefined) return bOrder - aOrder",
            source,
        )

    def test_swap_prompts_continue_to_follow_live_area_order(self):
        project_root = Path(__file__).resolve().parents[1]
        source = (project_root / "public" / "js" / "marvel" / "cards.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("if (aLegal && bLegal) return 0", source)

    def test_selector_can_request_target_order_display(self):
        selector = Select.From(faces=[], display_in_target_order=True)

        self.assertTrue(selector.selector_end.display_in_target_order)

    def test_selection_marks_the_rightmost_card_as_the_deck_top(self):
        project_root = Path(__file__).resolve().parents[1]
        source = (project_root / "public" / "js" / "marvel" / "cards.ts").read_text(
            encoding="utf-8"
        )
        css = (project_root / "public" / "css" / "marvel" / "deck.css").read_text(
            encoding="utf-8"
        )

        self.assertIn("'selection-order-top-first'", source)
        self.assertIn(
            "isSelecting && cardArea === 'deck' && Effect.select_effect_obj.display_in_target_order",
            source,
        )
        self.assertIn(".deck.clicked.selection-order-top-first::after", css)
        self.assertIn('content: "(" attr(data-total_cards) ") \\f060 Top"', css)
        self.assertIn("justify-content: flex-end", css)

    def test_madame_web_reorders_after_declining_the_optional_discard(self):
        project_root = Path(__file__).resolve().parents[1]
        source = (project_root / "cards" / "pack" / "silk" / "52021.py").read_text(
            encoding="utf-8"
        )

        choose_end = source.index("initiator.MayChooseOneAbility(")
        reorder = source.index("initiator.PlaceOnTopInAnyOrder(rest, effect)")
        self.assertGreater(reorder, choose_end)

    def test_order_sensitive_card_choices_opt_in_to_target_order(self):
        project_root = Path(__file__).resolve().parents[1]
        ordered_selection_scripts = [
            "cards/pack/aoa/magik/45036.py",
            "cards/pack/aos/50023.py",
            "cards/pack/bp/51016.py",
            "cards/pack/core/iron_man/01029b.py",
            "cards/pack/cyclops/33014.py",
            "cards/pack/falcon/53036.py",
            "cards/pack/gmw/the_market/16161.py",
            "cards/pack/ironheart/ironheart/29011.py",
            "cards/pack/ncrawler/48021.py",
            "cards/pack/nebu/nebula/22008.py",
            "cards/pack/next_evol/40056.py",
            "cards/pack/next_evol/cable/40004.py",
            "cards/pack/scw/scarlet_witch/15007.py",
            "cards/pack/silk/52021.py",
            "cards/pack/silk/silk/52005.py",
            "cards/pack/sm/27043.py",
            "cards/pack/thor/06020.py",
        ]

        for relative_path in ordered_selection_scripts:
            with self.subTest(relative_path=relative_path):
                source = (project_root / relative_path).read_text(encoding="utf-8")
                self.assertIn("display_in_target_order=True", source)


if __name__ == "__main__":
    unittest.main()
