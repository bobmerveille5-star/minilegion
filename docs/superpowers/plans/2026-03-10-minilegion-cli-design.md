# Minilegion CLI (design) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `python -m minilegion design --option "..."` with strict preconditions and a deterministic `briefed -> designed` transition.

**Architecture:** Extend the existing `minilegion/__main__.py` argparse CLI with a `design` subcommand that reads layered config to locate `<ai_dir>/STATE.json`, enforces stage via `StateManager.check_stage(["briefed"])`, validates `--option`, then updates state and transitions to `designed`.

**Tech Stack:** Python `argparse`, `unittest` via subprocess harness (`tests/test_cli.py`), existing `StateManager` + config loader.

---

## File Map

- Modify: `minilegion/__main__.py`
- Modify (tests): `tests/test_cli.py`
- Reference: `minilegion/memory/state.py` (transitions + state keys)
- Reference: `minilegion/config.py` (layered `ai_dir` resolution)

## Chunk 1: Tests First (CLI subprocess)

### Task 1: Add failing tests for `design`

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add failing test: `design` fails if project not initialized**

```python
def test_design_fails_if_state_missing(self):
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "demo-project"
        root.mkdir(parents=True)

        res = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertNotEqual(res.returncode, 0)
```

- [ ] **Step 2: Add failing test: `design` fails if stage not `briefed`**

```python
def test_design_fails_if_stage_not_briefed(self):
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "demo-project"
        root.mkdir(parents=True)

        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertNotEqual(res.returncode, 0)
```

- [ ] **Step 3: Add failing test: `design` fails if `--option` missing and must not mutate stage**

```python
def test_design_fails_if_option_missing_and_does_not_mutate_stage(self):
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "demo-project"
        root.mkdir(parents=True)

        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res_brief = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
        self.assertEqual(res_brief.returncode, 0, res_brief.stderr)

        res = _run_cli(repo_root, root, "design")
        self.assertNotEqual(res.returncode, 0)

        state_path = root / "project-ai" / "STATE.json"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["current_stage"], "briefed")
```

- [ ] **Step 4: Add failing test: `design` succeeds from `briefed` and sets `next_step`**

```python
def test_design_succeeds_from_briefed_and_sets_next_step(self):
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "demo-project"
        root.mkdir(parents=True)

        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res_brief = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
        self.assertEqual(res_brief.returncode, 0, res_brief.stderr)

        res = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertEqual(res.returncode, 0, res.stderr)

        state_path = root / "project-ai" / "STATE.json"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["current_stage"], "designed")
        self.assertEqual(data["design_option"], "Option A")
        self.assertEqual(data["next_step"], "research")
```

- [ ] **Step 5: Add failing test: `design` respects project override `ai_dir`**

```python
def test_design_respects_project_override_ai_dir(self):
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

        res_brief = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
        self.assertEqual(res_brief.returncode, 0, res_brief.stderr)

        res = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue((root / "custom-ai" / "STATE.json").exists())
```

- [ ] **Step 6: Run tests to confirm failures (or at least one failure)**

Run: `python -m unittest -v`

Expected: FAIL because `design` command is not implemented.

- [ ] **Step 7: Commit tests**

```bash
git add tests/test_cli.py
git commit -m "test(cli): add design command expectations"
```

## Chunk 2: Implementation (Minimal to Pass)

### Task 2: Implement `design` subcommand

**Files:**
- Modify: `minilegion/__main__.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add `cmd_design(args)` handler skeleton**

Implement the same config/state resolution pattern as `brief/status`:
- Load config (layered).
- Resolve `ai_dir`, ensure `STATE.json` exists.
- `check_stage(["briefed"])`.
- Validate `args.option` (strip; non-empty).

- [ ] **Step 2: Apply state mutation**

```python
manager.update(design_option=option, next_step="research")
manager.transition("designed")
```

- [ ] **Step 3: Add `design` argparse subparser**

`design --option` flag, with help text.

- [ ] **Step 4: Add stable output lines**

Print at least:
- `current_stage: designed`
- `next_step: research`
- `design_option: ...`

- [ ] **Step 5: Run tests**

Run: `python -m unittest -v`

Expected: PASS.

- [ ] **Step 6: Commit implementation**

```bash
git add minilegion/__main__.py
git commit -m "feat(cli): add design command"
```

## Chunk 3: Verification

### Task 3: Final verification and branch push

**Files:**
- None (commands only)

- [ ] **Step 1: Run full test suite**

Run: `python -m unittest -v`

Expected: PASS.

- [ ] **Step 2: Push branch**

Run: `git push -u origin feat/cli-design`

