import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def _run_cli(repo_root: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    py_path = str(repo_root)
    if env.get("PYTHONPATH"):
        py_path = py_path + os.pathsep + env["PYTHONPATH"]
    env["PYTHONPATH"] = py_path

    return subprocess.run(
        [sys.executable, "-m", "minilegion", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )


class CLITests(unittest.TestCase):
    def test_init_creates_state_in_default_ai_dir_and_uses_folder_name(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res = _run_cli(repo_root, root, "init")
            self.assertEqual(res.returncode, 0, res.stderr)

            state_path = root / "project-ai" / "STATE.json"
            self.assertTrue(state_path.exists())
            data = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(data["project_name"], "demo-project")

    def test_init_fails_if_state_already_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res1 = _run_cli(repo_root, root, "init")
            self.assertEqual(res1.returncode, 0, res1.stderr)

            res2 = _run_cli(repo_root, root, "init")
            self.assertNotEqual(res2.returncode, 0)

    def test_status_fails_if_state_missing(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res = _run_cli(repo_root, root, "status")
            self.assertNotEqual(res.returncode, 0)

    def test_status_prints_summary_when_initialized(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res1 = _run_cli(repo_root, root, "init")
            self.assertEqual(res1.returncode, 0, res1.stderr)

            res2 = _run_cli(repo_root, root, "status")
            self.assertEqual(res2.returncode, 0, res2.stderr)
            self.assertIn("current_stage", res2.stdout)
            self.assertIn("initialized", res2.stdout)

    def test_init_respects_project_override_ai_dir(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)
            (root / "minilegion.yaml").write_text(
                """
project:
  ai_dir: custom-ai
""".lstrip(),
                encoding="utf-8",
            )

            res = _run_cli(repo_root, root, "init")
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue((root / "custom-ai" / "STATE.json").exists())


if __name__ == "__main__":
    unittest.main()
