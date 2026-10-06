from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestForcedTimingChoiceUI(unittest.TestCase):
    def test_forced_and_optional_prompts_use_the_real_client_buttons(self):
        node = shutil.which("node")
        compiler = shutil.which("tsc.cmd") or shutil.which("tsc")
        if not node or not compiler:
            self.skipTest("Node and TypeScript are required for the client regression")
        with tempfile.TemporaryDirectory(prefix="marvel-forced-choice-") as output:
            result = subprocess.run(
                [compiler, "-p", str(ROOT / "public/js/tsconfig.json"), "--outDir", output],
                cwd=ROOT, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(
                [node, str(ROOT / "unit_test/forced_timing_choice_ui.cjs"),
                 str(Path(output) / "marvel")],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
