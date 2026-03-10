# Minilegion Config + State Foundations Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a strict, validated layered configuration loader and an enforceable persisted workflow state machine that later CLI/LLM layers can safely rely on.

**Architecture:** Use Pydantic models as the configuration contract and state shape contract. Load package defaults from `minilegion/config.yaml`, apply an optional project override `./minilegion.yaml` via deterministic deep-merge rules, then validate strictly. Persist workflow state to `<ai_dir>/STATE.json` and enforce the approved stage transition matrix.

**Tech Stack:** Python 3.12, Pydantic, PyYAML, `unittest`.

---

## File Structure (locked-in)

- Create: `minilegion/__init__.py`
- Create: `minilegion/config.yaml`
- Create: `minilegion/config.py` (Pydantic schema + YAML loading + deep merge)
- Create: `minilegion/runtime.py` (tiny glue: load config, resolve ai_dir, create StateManager)
- Create: `minilegion/memory/__init__.py`
- Create: `minilegion/memory/state.py` (StateManager + VALID_TRANSITIONS + strict persistence)
- Create: `tests/test_config.py`
- Create: `tests/test_state.py`

Notes:
- All paths are relative to `D:\pln kiro\test powers\test4`.
- If this folder is not a git repo yet, initialize git before the first commit.

## Task 1: Configuration Contract (Schema + Layered Load)

**Files:**
- Create: `minilegion/config.yaml`
- Create: `minilegion/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Initialize repo layout and package skeleton**

Create folders:
- `minilegion/`
- `minilegion/memory/`
- `tests/`

Create minimal package init files:

```python
# minilegion/__init__.py
"""Minilegion package."""
```

```python
# minilegion/memory/__init__.py
"""State management primitives for Minilegion."""
```

- [ ] **Step 2: Add default config file (package defaults)**

Create `minilegion/config.yaml`:

```yaml
llm:
  default_adapter: openai
  adapters:
    openai:
      provider: openai
      model: gpt-4o
      max_tokens: 4000
      temperature: 0.2
  role_routing:
    planner: openai
    builder: openai
    reviewer: openai
  fallback_chain:
    - openai

project:
  ai_dir: project-ai
  mode: safe

guards:
  scope_lock: true
  plan_required: true
  review_separate: true
  human_approval: true
  max_revise_cycles: 3
```

- [ ] **Step 3: Write failing tests for layered overrides + strict validation**

Create `tests/test_config.py`:

```python
import unittest
from pathlib import Path
import tempfile

from minilegion.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_works_with_defaults_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = load_config(root)
            self.assertEqual(cfg.project.ai_dir, "project-ai")
            self.assertEqual(cfg.project.mode, "safe")
            self.assertEqual(cfg.guards.max_revise_cycles, 3)
            self.assertEqual(cfg.llm.default_adapter, "openai")
            self.assertIn("openai", cfg.llm.adapters)

    def test_project_override_deep_merges_and_replaces_lists(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "minilegion.yaml").write_text(
                """
project:
  ai_dir: custom-ai
llm:
  fallback_chain:
    - openai
    - openai
""".lstrip(),
                encoding="utf-8",
            )

            cfg = load_config(root)
            self.assertEqual(cfg.project.ai_dir, "custom-ai")
            # fallback_chain should be replaced by override
            self.assertEqual(cfg.llm.fallback_chain, ["openai", "openai"])

    def test_unknown_keys_fail_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "minilegion.yaml").write_text(
                """
llm:
  nope: true
""".lstrip(),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_config(root)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run tests to verify failure**

Run:

```powershell
cd "D:\pln kiro\test powers\test4"
python -m unittest -v tests.test_config
```

Expected: FAIL with `ModuleNotFoundError` or import errors for `minilegion.config`.

- [ ] **Step 5: Implement `minilegion/config.py` (minimal to satisfy tests)**

Create `minilegion/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping

import yaml
from pydantic import BaseModel
from pydantic import ConfigDict


class ConfigError(Exception):
    pass


class LLMAdapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    max_tokens: int
    temperature: float


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_adapter: str
    adapters: Dict[str, LLMAdapter]
    role_routing: Dict[str, str]
    fallback_chain: List[str]


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ai_dir: str
    mode: str


class GuardsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope_lock: bool
    plan_required: bool
    review_separate: bool
    human_approval: bool
    max_revise_cycles: int


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm: LLMConfig
    project: ProjectConfig
    guards: GuardsConfig


def _deep_merge(base: Any, override: Any) -> Any:
    # dicts merge recursively, lists replace, scalars replace.
    if isinstance(base, Mapping) and isinstance(override, Mapping):
        out: Dict[str, Any] = dict(base)
        for k, v in override.items():
            if k in out:
                out[k] = _deep_merge(out[k], v)
            else:
                out[k] = v
        return out
    if isinstance(override, list):
        return override
    return override


def _read_yaml(path: Path) -> Dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ConfigError(f"Failed to read YAML at {path}: {e}") from e

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config at {path} must be a mapping/object")
    return data


def load_config(project_root: Path) -> Config:
    # Layer 1: package defaults
    defaults_path = Path(__file__).with_name("config.yaml")
    defaults = _read_yaml(defaults_path)

    # Layer 2: project override
    override_path = project_root / "minilegion.yaml"
    merged = defaults
    if override_path.exists():
        override = _read_yaml(override_path)
        merged = _deep_merge(defaults, override)

    try:
        return Config.model_validate(merged)
    except Exception as e:
        raise ConfigError(f"Config validation failed: {e}") from e
```

- [ ] **Step 6: Run config tests again**

Run:

```powershell
cd "D:\pln kiro\test powers\test4"
python -m unittest -v tests.test_config
```

Expected: PASS.

- [ ] **Step 7: Commit**

If needed:

```bash
git init
```

Then:

```bash
git add minilegion/config.yaml minilegion/config.py minilegion/__init__.py minilegion/memory/__init__.py tests/test_config.py
git commit -m "feat(config): add strict layered config contract"
```

## Task 2: Strict Workflow State Machine (Persisted + Transition Guards)

**Files:**
- Create: `minilegion/memory/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Write failing state tests (reference state shape + transitions)**

Create `tests/test_state.py`:

```python
import json
import shutil
import unittest
import uuid
from pathlib import Path

from minilegion.memory.state import InvalidTransition, StateManager


class StateManagerTests(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("tests_tmp") / uuid.uuid4().hex
        self.ai_dir = self.test_root / "project-ai"
        self.ai_dir.mkdir(parents=True)

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_initialize_creates_reference_state_shape(self):
        manager = StateManager(self.ai_dir)

        manager.initialize("demo-project")

        state_path = self.ai_dir / "STATE.json"
        self.assertTrue(state_path.exists())

        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["project_name"], "demo-project")
        self.assertEqual(data["goal"], "")
        self.assertEqual(data["current_stage"], "initialized")
        self.assertEqual(data["mode"], "safe")
        self.assertIsNone(data["design_option"])
        self.assertIsNone(data["design_complexity"])
        self.assertFalse(data["research_validated"])
        self.assertEqual(data["files_for_plan"], [])
        self.assertEqual(data["completed_tasks"], [])
        self.assertEqual(data["pending_tasks"], [])
        self.assertEqual(data["touched_files"], [])
        self.assertEqual(data["open_risks"], [])
        self.assertIsNone(data["review_verdict"])
        self.assertEqual(data["revise_cycles"], 0)
        self.assertEqual(data["max_revise_cycles"], 3)
        self.assertEqual(data["revise_items"], [])
        self.assertEqual(data["next_step"], "")
        self.assertEqual(data["iteration"], 1)
        self.assertEqual(data["history"], [])
        self.assertTrue(data["created_at"])
        self.assertTrue(data["updated_at"])

    def test_transition_persists_allowed_stage_change(self):
        manager = StateManager(self.ai_dir)
        manager.initialize("demo-project")

        manager.transition("briefed")

        reloaded = StateManager(self.ai_dir)
        self.assertEqual(reloaded.get("current_stage"), "briefed")

    def test_transition_rejects_forbidden_stage_change_without_mutation(self):
        manager = StateManager(self.ai_dir)
        manager.initialize("demo-project")

        with self.assertRaises(InvalidTransition):
            manager.transition("planned")

        reloaded = StateManager(self.ai_dir)
        self.assertEqual(reloaded.get("current_stage"), "initialized")

    def test_check_stage_rejects_incompatible_current_stage(self):
        manager = StateManager(self.ai_dir)
        manager.initialize("demo-project")

        with self.assertRaises(InvalidTransition):
            manager.check_stage(["planned", "executed"])

    def test_update_persists_state_for_fresh_instance(self):
        manager = StateManager(self.ai_dir)
        manager.initialize("demo-project")

        manager.update(goal="Ship Sprint 1", next_step="brief")

        reloaded = StateManager(self.ai_dir)
        self.assertEqual(reloaded.get("goal"), "Ship Sprint 1")
        self.assertEqual(reloaded.get("next_step"), "brief")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
cd "D:\pln kiro\test powers\test4"
python -m unittest -v tests.test_state
```

Expected: FAIL (missing `minilegion.memory.state`).

- [ ] **Step 3: Implement `StateManager` with strict transitions + deterministic persistence**

Create `minilegion/memory/state.py`:

```python
import json
from datetime import datetime
from pathlib import Path


VALID_TRANSITIONS = {
    "initialized": ["briefed"],
    "briefed": ["designed", "initialized"],
    "designed": ["researched", "briefed"],
    "researched": ["planned", "designed"],
    "planned": ["executed", "researched"],
    "executed": ["reviewed"],
    "reviewed": ["archived", "executed"],
    "archived": ["briefed"],
}


class InvalidTransition(Exception):
    pass


class StateManager:
    def __init__(self, ai_dir):
        self.ai_dir = Path(ai_dir)
        self.path = self.ai_dir / "STATE.json"
        self._state = self._load()

    def _load(self):
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {}

    def _timestamp(self):
        return datetime.now().isoformat()

    def _save(self):
        self.ai_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def initialize(self, name, *, mode="safe", max_revise_cycles=3):
        timestamp = self._timestamp()
        self._state = {
            "project_name": name,
            "goal": "",
            "current_stage": "initialized",
            "mode": mode,
            "design_option": None,
            "design_complexity": None,
            "research_validated": False,
            "files_for_plan": [],
            "completed_tasks": [],
            "pending_tasks": [],
            "touched_files": [],
            "open_risks": [],
            "review_verdict": None,
            "revise_cycles": 0,
            "max_revise_cycles": max_revise_cycles,
            "revise_items": [],
            "next_step": "",
            "iteration": 1,
            "history": [],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._save()

    def transition(self, new_stage):
        current = self._state.get("current_stage", "unknown")
        allowed = VALID_TRANSITIONS.get(current, [])
        if new_stage not in allowed:
            raise InvalidTransition(
                f"'{current}' -> '{new_stage}' forbidden. Allowed: {allowed}"
            )
        self.update(current_stage=new_stage)

    def check_stage(self, allowed):
        current = self._state.get("current_stage", "unknown")
        if current not in allowed:
            raise InvalidTransition(
                f"'{current}' incompatible. Expected one of: {allowed}"
            )

    def update(self, **kwargs):
        self._state.update(kwargs)
        self._state["updated_at"] = self._timestamp()
        self._save()

    def get(self, key, default=None):
        return self._state.get(key, default)

    def read(self):
        return self._state.copy()
```

- [ ] **Step 4: Run state tests again**

Run:

```powershell
cd "D:\pln kiro\test powers\test4"
python -m unittest -v tests.test_state
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add minilegion/memory/state.py tests/test_state.py
git commit -m "feat(state): add strict persisted workflow state machine"
```

## Task 3: Glue Runtime (Config -> ai_dir -> StateManager)

**Files:**
- Create: `minilegion/runtime.py`
- Modify: `tests/test_state.py`

- [ ] **Step 1: Write a failing integration test asserting config drives ai_dir**

Append to `tests/test_state.py`:

```python
from minilegion.runtime import runtime_for_project


class RuntimeIntegrationTests(unittest.TestCase):
    def test_runtime_uses_ai_dir_from_project_override(self):
        root = self.test_root
        (root / "minilegion.yaml").write_text(
            """
project:
  ai_dir: custom-ai
""".lstrip(),
            encoding="utf-8",
        )

        rt = runtime_for_project(root)
        self.assertTrue(str(rt.ai_dir).endswith("custom-ai"))
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
cd "D:\pln kiro\test powers\test4"
python -m unittest -v tests.test_state
```

Expected: FAIL (missing `minilegion.runtime`).

- [ ] **Step 3: Implement runtime glue**

Create `minilegion/runtime.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from minilegion.config import load_config
from minilegion.memory.state import StateManager


@dataclass(frozen=True)
class Runtime:
    project_root: Path
    config: object
    ai_dir: Path
    state: StateManager


def runtime_for_project(project_root: Path) -> Runtime:
    cfg = load_config(project_root)
    ai_dir = project_root / cfg.project.ai_dir
    state = StateManager(ai_dir)
    return Runtime(project_root=project_root, config=cfg, ai_dir=ai_dir, state=state)
```

- [ ] **Step 4: Run the full test suite**

Run:

```powershell
cd "D:\pln kiro\test powers\test4"
python -m unittest -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add minilegion/runtime.py tests/test_state.py
git commit -m "feat(runtime): wire config to ai_dir and state"
```

---

## Plan complete and saved

Plan saved to `docs/superpowers/plans/2026-03-10-minilegion-config-state-foundations.md`. Ready to execute?
