from dataclasses import dataclass
from pathlib import Path

from minilegion.config import Config, load_config
from minilegion.memory.state import StateManager


@dataclass(frozen=True)
class Runtime:
    project_root: Path
    config: Config
    ai_dir: Path
    state: StateManager


def runtime_for_project(project_root: Path) -> Runtime:
    cfg = load_config(project_root)
    ai_dir = project_root / cfg.project.ai_dir
    state = StateManager(ai_dir)
    return Runtime(project_root=project_root, config=cfg, ai_dir=ai_dir, state=state)
