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

import tempfile

from minilegion.runtime import runtime_for_project


class RuntimeIntegrationTests(unittest.TestCase):
    def test_runtime_uses_ai_dir_from_project_override(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "minilegion.yaml").write_text(
                """
project:
  ai_dir: custom-ai
""".lstrip(),
                encoding="utf-8",
            )

            rt = runtime_for_project(root)
            self.assertTrue(str(rt.ai_dir).endswith("custom-ai"))
