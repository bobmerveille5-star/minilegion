# Minilegion CLI (research) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `python -m minilegion research --file path [--file path ...]` with strict preconditions, canonical path storage, and deterministic `designed -> researched` transition.

**Architecture:** Extend `minilegion/__main__.py` with a `research` subcommand that resolves `<ai_dir>/STATE.json` via layered config, enforces `current_stage=designed`, validates and canonicalizes `--file` inputs to project-relative POSIX paths, then updates state and transitions to `researched`.

**Tech Stack:** Python `argparse`, `pathlib`, `unittest` via subprocess harness (`tests/test_cli.py`), existing `StateManager` + config loader.

---

## File Map

- Modify: `minilegion/__main__.py`
- Modify (tests): `tests/test_cli.py`
- Reference: `minilegion/memory/state.py` (transitions + state keys)
- Reference: `docs/pipeline.md`
- Reference: `docs/superpowers/specs/2026-03-10-minilegion-cli-research-design.md`

## Chunk 1: Tests First (CLI subprocess)

### Task 1: Add failing tests for `research`

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add failing test: `research` fails if project not initialized**

```python
def test_research_fails_if_state_missing(self):
    repo_root = Path(__file__).resolve().parents[1]
    with temp_project_dir(repo_root) as root:
        res = _run_cli(repo_root, root, "research", "--file", "docs/a.md")
        self.assertNotEqual(res.returncode, 0)
```

- [ ] **Step 2: Add failing test: `research` fails if stage not `designed`**

```python
def test_research_fails_if_stage_not_designed(self):
    repo_root = Path(__file__).resolve().parents[1]
    with temp_project_dir(repo_root) as root:
        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res = _run_cli(repo_root, root, "research", "--file", "docs/a.md")
        self.assertNotEqual(res.returncode, 0)
```

- [ ] **Step 3: Add failing test: `research` fails if no `--file` and must not mutate stage**

```python
def test_research_fails_if_file_missing_and_does_not_mutate_stage(self):
    repo_root = Path(__file__).resolve().parents[1]
    with temp_project_dir(repo_root) as root:
        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res_brief = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
        self.assertEqual(res_brief.returncode, 0, res_brief.stderr)

        res_design = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertEqual(res_design.returncode, 0, res_design.stderr)

        res = _run_cli(repo_root, root, "research")
        self.assertNotEqual(res.returncode, 0)

        state_path = root / "project-ai" / "STATE.json"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["current_stage"], "designed")
```

- [ ] **Step 4: Add failing test: `research` fails if file does not exist and must not mutate stage**

```python
def test_research_fails_if_file_missing_on_disk_and_does_not_mutate_stage(self):
    repo_root = Path(__file__).resolve().parents[1]
    with temp_project_dir(repo_root) as root:
        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res_brief = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
        self.assertEqual(res_brief.returncode, 0, res_brief.stderr)

        res_design = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertEqual(res_design.returncode, 0, res_design.stderr)

        res = _run_cli(repo_root, root, "research", "--file", "docs/does-not-exist.md")
        self.assertNotEqual(res.returncode, 0)

        state_path = root / "project-ai" / "STATE.json"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["current_stage"], "designed")
```

- [ ] **Step 5: Add failing test: `research` succeeds from `designed` and persists canonical paths**

```python
def test_research_succeeds_from_designed_and_sets_next_step(self):
    repo_root = Path(__file__).resolve().parents[1]
    with temp_project_dir(repo_root) as root:
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "a.md").write_text("ok", encoding="utf-8")

        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res_brief = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
        self.assertEqual(res_brief.returncode, 0, res_brief.stderr)

        res_design = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertEqual(res_design.returncode, 0, res_design.stderr)

        res = _run_cli(repo_root, root, "research", "--file", "docs/a.md")
        self.assertEqual(res.returncode, 0, res.stderr)

        state_path = root / "project-ai" / "STATE.json"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["current_stage"], "researched")
        self.assertTrue(data["research_validated"])
        self.assertEqual(data["files_for_plan"], ["docs/a.md"])
        self.assertEqual(data["next_step"], "plan")
```

- [ ] **Step 6: Add failing test: `research` respects project override `ai_dir`**

```python
def test_research_respects_project_override_ai_dir(self):
    repo_root = Path(__file__).resolve().parents[1]
    with temp_project_dir(repo_root) as root:
        (root / "minilegion.yaml").write_text(
            """
project:
  ai_dir: custom-ai
""".lstrip(),
            encoding="utf-8",
        )
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "a.md").write_text("ok", encoding="utf-8")

        res_init = _run_cli(repo_root, root, "init")
        self.assertEqual(res_init.returncode, 0, res_init.stderr)

        res_brief = _run_cli(repo_root, root, "brief", "--goal", "Ship Sprint 1")
        self.assertEqual(res_brief.returncode, 0, res_brief.stderr)

        res_design = _run_cli(repo_root, root, "design", "--option", "Option A")
        self.assertEqual(res_design.returncode, 0, res_design.stderr)

        res = _run_cli(repo_root, root, "research", "--file", "docs/a.md")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue((root / "custom-ai" / "STATE.json").exists())
```

- [ ] **Step 7: Run tests to confirm failures (or at least one failure)**

Run: `python -m unittest -v`

Expected: FAIL because `research` command is not implemented.

- [ ] **Step 8: Commit tests**

```bash
git add tests/test_cli.py
git commit -m "test(cli): add research command expectations"
```

## Chunk 2: Implementation (Minimal to Pass)

### Task 2: Implement `research` subcommand

**Files:**
- Modify: `minilegion/__main__.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add `cmd_research(args)` handler skeleton**

Pattern must match `brief/design/status`:
- Load config (layered).
- Resolve `ai_dir`, ensure `STATE.json` exists.
- `check_stage(["designed"])`.
- Validate `args.file` list is non-empty.

- [ ] **Step 2: Validate and canonicalize each `--file`**

For each input:
- Resolve relative to `project_root`
- Require `exists()` and `is_file()`
- Require under `project_root` (`relative_to` must succeed)
- Store canonical relative path using `.as_posix()`

- [ ] **Step 3: Apply state mutation**

```python
manager.update(files_for_plan=files, research_validated=True, next_step="plan")
manager.transition("researched")
```

- [ ] **Step 4: Add `research` argparse subparser**

`research --file` repeatable (use `action="append"`).

- [ ] **Step 5: Add stable output lines**

Print at least:
- `current_stage: researched`
- `next_step: plan`
- `files_for_plan_count: ...`
- `files_for_plan: [...]` (JSON one-liner)

- [ ] **Step 6: Run tests**

Run: `python -m unittest -v`

Expected: PASS.

- [ ] **Step 7: Commit implementation**

```bash
git add minilegion/__main__.py
git commit -m "feat(cli): add research command"
```

## Chunk 3: Verification and PR

### Task 3: Final verification and branch push

- [ ] **Step 1: Run full test suite**

Run: `python -m unittest -v`

Expected: PASS.

- [ ] **Step 2: Push branch**

Run: `git push -u origin feat/cli-research`

