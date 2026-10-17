from pathlib import Path
import shutil
import subprocess
import unittest


class TestDeckEditorUI(unittest.TestCase):
    def test_starters_and_imports_render_without_stale_cards(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is required for the deck editor UI regression")
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [node, str(root / "unit_test/deck_editor_ui.cjs")],
            cwd=root, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
