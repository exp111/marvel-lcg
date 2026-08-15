from pathlib import Path
import unittest


class TestCenterPreviewInput(unittest.TestCase):

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[1]

    def test_enlarged_card_consumes_click_at_overlay_container(self):
        source = (
            self.project_root / "public" / "js" / "marvel" / "hover.ts"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "CenterPreview.preview_container.onclick = (event) =>",
            source,
        )
        self.assertIn("event.stopImmediatePropagation()", source)
        self.assertIn("event.preventDefault()", source)
        self.assertNotIn("CenterPreview.preview_center.onclick", source)

    def test_enlarged_card_blocks_input_until_fade_finishes(self):
        css = (
            self.project_root / "public" / "css" / "marvel" / "image-preview.css"
        ).read_text(encoding="utf-8")

        self.assertIn("#image-preview-div-center {", css)
        self.assertIn("pointer-events: all", css)
        self.assertIn("#image-preview-div-center.hide {", css)
        self.assertIn("0s calc(var(--anime-time-card)) visibility", css)


if __name__ == "__main__":
    unittest.main()
