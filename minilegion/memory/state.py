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
