# Minilegion CLI (brief) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `python -m minilegion brief [--goal "..."]` that requires a non-empty goal, enforces stage preconditions, sets `next_step=design`, and transitions to `briefed`.

**Architecture:** Extend the existing `argparse` CLI in `minilegion/__main__.py`. Implement `cmd_brief()` using `load_config(Path.cwd())`, resolve `ai_dir`, then use `StateManager` to `check_stage(["initialized"])`, validate goal, `update(goal=..., next_step="design")`, and `transition("briefed")`. Tests extend `tests/test_cli.py` and run the CLI via `subprocess` with `PYTHONPATH` pointing to repo root.

**Tech Stack:** Python 3.12, `unittest`, `argparse`, `subprocess`.

---

## File Structure (locked-in)

- Modify: `minilegion/__main__.py`
- Modify: `tests/test_cli.py`

## Task 1: Tests for `brief` (RED)

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_cli.py` (inside `CLITests`):

```python
    def test_brief_fails_if_state_missing(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
            self.assertNotEqual(res.returncode, 0)

    def test_brief_fails_if_goal_missing_and_no_existing_goal(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res_init = _run_cli(repo_root, root, "init")
            self.assertEqual(res_init.returncode, 0, res_init.stderr)

            res = _run_cli(repo_root, root, "brief")
            self.assertNotEqual(res.returncode, 0)

            # must not mutate stage
            state_path = root / "project-ai" / "STATE.json"
            data = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(data["current_stage"], "initialized")

    def test_brief_succeeds_from_initialized_with_goal_and_sets_next_step(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res_init = _run_cli(repo_root, root, "init")
            self.assertEqual(res_init.returncode, 0, res_init.stderr)

            res = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
            self.assertEqual(res.returncode, 0, res.stderr)

            state_path = root / "project-ai" / "STATE.json"
            data = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(data["current_stage"], "briefed")
            self.assertEqual(data["goal"], "Ship Sprint 1")
            self.assertEqual(data["next_step"], "design")

    def test_brief_fails_if_stage_not_initialized(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "demo-project"
            root.mkdir(parents=True)

            res_init = _run_cli(repo_root, root, "init")
            self.assertEqual(res_init.returncode, 0, res_init.stderr)

            res1 = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
            self.assertEqual(res1.returncode, 0, res1.stderr)

            res2 = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
            self.assertNotEqual(res2.returncode, 0)

    def test_brief_respects_project_override_ai_dir(self):
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

            res_init = _run_cli(repo_root, root, "init")
            self.assertEqual(res_init.returncode, 0, res_init.stderr)

            res = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue((root / "custom-ai" / "STATE.json").exists())
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
cd "D:\pln kiro\test powers\test4\.worktrees\cli-brief"
python -m unittest -v tests.test_cli
```

Expected: FAIL (unknown command `brief`).

## Task 2: Implement `brief` (GREEN)

**Files:**
- Modify: `minilegion/__main__.py`

- [ ] **Step 1: Implement handler + subcommand**

In `minilegion/__main__.py`:

- Add `cmd_brief(args)` implementing:
  - load config
  - compute `ai_dir`
  - require state exists
  - `manager.check_stage(["initialized"])`
  - goal = `args.goal` or existing `state["goal"]` if non-empty else error
  - `manager.update(goal=goal, next_step="design")`
  - `manager.transition("briefed")`
- Wire subcommand:
  - `brief` with optional `--goal`

- [ ] **Step 2: Re-run CLI tests**

```powershell
python -m unittest -v tests.test_cli
```

Expected: PASS.

- [ ] **Step 3: Run full suite**

```powershell
python -m unittest -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add minilegion/__main__.py tests/test_cli.py
git commit -m "feat(cli): add brief command"
```
