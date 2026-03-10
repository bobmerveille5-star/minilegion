from __future__ import annotations

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
