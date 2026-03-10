import unittest
from pathlib import Path

from minilegion.config import ConfigError, load_config
from tests.tmpdirs import temp_dir


class ConfigTests(unittest.TestCase):
    def test_load_config_works_with_defaults_only(self):
        repo_root = Path(__file__).resolve().parents[1]
        with temp_dir(repo_root / "tests_tmp") as root:
            cfg = load_config(root)
            self.assertEqual(cfg.project.ai_dir, "project-ai")
            self.assertEqual(cfg.project.mode, "safe")
            self.assertEqual(cfg.guards.max_revise_cycles, 3)
            self.assertEqual(cfg.llm.default_adapter, "openai")
            self.assertIn("openai", cfg.llm.adapters)

    def test_project_override_deep_merges_and_replaces_lists(self):
        repo_root = Path(__file__).resolve().parents[1]
        with temp_dir(repo_root / "tests_tmp") as root:
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
        repo_root = Path(__file__).resolve().parents[1]
        with temp_dir(repo_root / "tests_tmp") as root:
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
