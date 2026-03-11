from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from minilegion.config import ConfigError, load_config
from minilegion.memory.state import InvalidTransition, StateManager


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


def cmd_brief(args: argparse.Namespace) -> int:
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

    manager = StateManager(ai_dir)
    try:
        manager.check_stage(["initialized"])
    except InvalidTransition as e:
        print(str(e), file=sys.stderr)
        return 1

    goal = args.goal
    if goal is None:
        existing = manager.get("goal", "")
        if isinstance(existing, str) and existing.strip():
            goal = existing

    if goal is None or not str(goal).strip():
        print("Missing goal. Provide --goal or set a goal before briefing.", file=sys.stderr)
        return 1

    goal = str(goal).strip()

    manager.update(goal=goal, next_step="design")
    manager.transition("briefed")

    print("current_stage: briefed")
    print("next_step: design")
    return 0


def cmd_design(args: argparse.Namespace) -> int:
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

    manager = StateManager(ai_dir)
    try:
        manager.check_stage(["briefed"])
    except InvalidTransition as e:
        print(str(e), file=sys.stderr)
        return 1

    option = args.option
    if option is None or not str(option).strip():
        print("Missing design option. Provide --option.", file=sys.stderr)
        return 1

    option = str(option).strip()

    manager.update(design_option=option, next_step="research")
    manager.transition("designed")

    print("current_stage: designed")
    print("next_step: research")
    print(f"design_option: {option}")
    return 0


def cmd_research(args: argparse.Namespace) -> int:
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

    manager = StateManager(ai_dir)
    try:
        manager.check_stage(["designed"])
    except InvalidTransition as e:
        print(str(e), file=sys.stderr)
        return 1

    raw_files = getattr(args, "files", None) or []
    raw_files = [str(f) for f in raw_files]
    if not raw_files:
        print("Missing files. Provide at least one --file.", file=sys.stderr)
        return 1

    project_root_resolved = project_root.resolve()
    canonical: list[str] = []

    for raw in raw_files:
        raw = str(raw).strip()
        if not raw:
            print("Missing files. Provide at least one --file.", file=sys.stderr)
            return 1

        p = Path(raw)
        if not p.is_absolute():
            p = project_root / p

        resolved = p.resolve()
        if not resolved.exists() or not resolved.is_file():
            print(f"File not found: {raw}", file=sys.stderr)
            return 1

        try:
            rel = resolved.relative_to(project_root_resolved)
        except ValueError:
            print(f"File must be under project root: {raw}", file=sys.stderr)
            return 1

        canonical.append(rel.as_posix())

    manager.update(
        files_for_plan=canonical,
        research_validated=True,
        next_step="plan",
    )
    manager.transition("researched")

    print("current_stage: researched")
    print("next_step: plan")
    print(f"files_for_plan_count: {len(canonical)}")
    print(f"files_for_plan: {json.dumps(canonical, ensure_ascii=False)}")
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

    p_brief = sub.add_parser("brief", help="Brief the project (requires a goal)")
    p_brief.add_argument("--goal", help="Set/override the project goal")
    p_brief.set_defaults(_handler=cmd_brief)

    p_design = sub.add_parser("design", help="Choose a design option (requires briefed)")
    p_design.add_argument("--option", help="Set the design option")
    p_design.set_defaults(_handler=cmd_design)

    p_research = sub.add_parser(
        "research", help="Provide files to inform planning (requires designed)"
    )
    p_research.add_argument(
        "--file",
        dest="files",
        action="append",
        help="Add a file to the planning input list (repeatable)",
    )
    p_research.set_defaults(_handler=cmd_research)

    p_status = sub.add_parser("status", help="Show current project status")
    p_status.set_defaults(_handler=cmd_status)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args._handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
