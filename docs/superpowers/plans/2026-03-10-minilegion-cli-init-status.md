# Minilegion CLI (init/status) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `python -m minilegion init` and `python -m minilegion status` that safely initialize and report workflow state using the existing strict config/state foundations.

**Architecture:** Implement an `argparse` CLI in `minilegion/__main__.py` with subcommands `init` and `status`. Commands load config from `Path.cwd()`, resolve `ai_dir`, then read/write state via `StateManager`. Test via `unittest` by running the CLI in subprocesses with `PYTHONPATH` pointing to the repo root.

**Tech Stack:** Python 3.12, `unittest`, `argparse`, `subprocess`.

---

## File Structure (locked-in)

- Create: `minilegion/__main__.py`
- Create: `tests/test_cli.py`

## Task 1: CLI Tests (RED)

**Files:**
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
cd "D:\pln kiro\test powers\test4\.worktrees\cli-init-status"
python -m unittest -v tests.test_cli
```

Expected: FAIL due to missing `minilegion.__main__` / CLI.

## Task 2: Implement CLI (GREEN)

**Files:**
- Create: `minilegion/__main__.py`

- [ ] **Step 1: Implement `minilegion/__main__.py` (minimal to pass tests)**

Create `minilegion/__main__.py`:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from minilegion.config import ConfigError, load_config
from minilegion.memory.state import StateManager


def _project_name_from_cwd(cwd: Path) -> str:
    return cwd.name


def cmd_init(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    project_name = args.name or _project_name_from_cwd(project_root)

    try:
        cfg = load_config(project_root)
    except ConfigError as e:
        print(str(e), file=sys.stderr)
        return 1

    ai_dir = project_root / cfg.project.ai_dir
    state_path = ai_dir / "STATE.json"
    if state_path.exists():
        print(f"State already exists at: {state_path}", file=sys.stderr)
        return 1

    manager = StateManager(ai_dir)
    manager.initialize(
        project_name,
        mode=cfg.project.mode,
        max_revise_cycles=cfg.guards.max_revise_cycles,
    )

    print(f"Initialized state: {state_path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project_root = Path.cwd()

    try:
        cfg = load_config(project_root)
    except ConfigError as e:
        print(str(e), file=sys.stderr)
        return 1

    ai_dir = project_root / cfg.project.ai_dir
    state_path = ai_dir / "STATE.json"
    if not state_path.exists():
        print("Project not initialized. Run: python -m minilegion init", file=sys.stderr)
        return 1

    state = StateManager(ai_dir).read()

    # Stable, greppable output
    print(f"project_root: {project_root}")
    print(f"ai_dir: {ai_dir}")
    print(f"state_path: {state_path}")
    print(f"current_stage: {state.get('current_stage', '')}")
    print(f"mode: {state.get('mode', '')}")
    print(f"next_step: {state.get('next_step', '')}")
    print(f"updated_at: {state.get('updated_at', '')}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="minilegion", add_help=True)
    sub = p.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize project state")
    p_init.add_argument("--name", help="Override project name")
    p_init.set_defaults(_handler=cmd_init)

    p_status = sub.add_parser("status", help="Show current project status")
    p_status.set_defaults(_handler=cmd_status)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args._handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Re-run tests (all green)**

Run:

```powershell
cd "D:\pln kiro\test powers\test4\.worktrees\cli-init-status"
python -m unittest -v tests.test_cli
```

Expected: PASS.

- [ ] **Step 3: Run full suite**

Run:

```powershell
cd "D:\pln kiro\test powers\test4\.worktrees\cli-init-status"
python -m unittest -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add minilegion/__main__.py tests/test_cli.py
git commit -m "feat(cli): add init and status commands"
```

---

## Plan complete and saved

Plan saved to `docs/superpowers/plans/2026-03-10-minilegion-cli-init-status.md`. Ready to execute.
