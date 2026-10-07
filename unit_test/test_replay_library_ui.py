from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestReplayLibraryUI(unittest.TestCase):
    def test_save_watch_resume_and_end_of_recording_controls(self):
        node = shutil.which("node")
        compiler = shutil.which("tsc.cmd") or shutil.which("tsc")
        if not node or not compiler:
            self.skipTest("Node and TypeScript are required for the client regression")
        with tempfile.TemporaryDirectory(prefix="marvel-replay-library-") as output:
            compiled = subprocess.run(
                [compiler, "-p", str(ROOT / "public/js/tsconfig.json"), "--outDir", output],
                cwd=ROOT, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            checked = subprocess.run(
                [node, str(ROOT / "unit_test/replay_library_ui.cjs"), str(Path(output) / "marvel")],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)


if __name__ == "__main__":
    unittest.main()
