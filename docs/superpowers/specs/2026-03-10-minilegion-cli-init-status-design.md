# Minilegion CLI (init/status) Design

Date: 2026-03-10

## Goal

Provide the first trustworthy, minimal CLI surface for Minilegion foundations:

- `python -m minilegion init` initializes a project state file at `<ai_dir>/STATE.json`.
- `python -m minilegion status` prints a stable summary of config + current workflow state.

This must reuse the existing strict config contract and state machine.

## Non-Goals

- Shipping an installed `minilegion` console script (no packaging/entrypoints yet).
- Adding `--force` for init (init must fail if `STATE.json` already exists).
- Adding any LLM workflow, prompts, or command execution beyond init/status.

## Decisions

### Execution form

Use module execution:

- `python -m minilegion <command>`

Implementation uses `argparse` with subcommands in `minilegion/__main__.py`.

### Project name default

`init` derives the project name from the current working directory name.

- Override via `--name <project_name>`.

### Config and state wiring

Both commands:

- Use `project_root = Path.cwd()`.
- Load configuration via `load_config(project_root)` (package defaults + optional `./minilegion.yaml`).
- Resolve `ai_dir = project_root / cfg.project.ai_dir`.

### init behavior

- If `<ai_dir>/STATE.json` exists: print an error to stderr and exit non-zero.
- Else create state via:
  - `StateManager(ai_dir).initialize(project_name, mode=cfg.project.mode, max_revise_cycles=cfg.guards.max_revise_cycles)`
- Print the created state path and exit 0.

### status behavior

- If `<ai_dir>/STATE.json` does not exist: print "not initialized, run init" to stderr and exit non-zero.
- Else print a stable, human-readable summary including:
  - `project_root`
  - `ai_dir`
  - `current_stage`
  - `mode`
  - `next_step`
  - `updated_at`

### Exit codes

- Success: 0
- User-facing error conditions: non-zero (1)

## Verification Strategy

Unit tests validate:

- `init` creates `<ai_dir>/STATE.json` using `ai_dir` from config and project name default from folder.
- `init` fails (non-zero) if state already exists.
- `status` fails (non-zero) when state does not exist.
- `status` prints expected summary fields when state exists.

Tests run via `unittest` and execute the CLI with `subprocess.run([sys.executable, '-m', 'minilegion', ...])`.
Because the CLI runs from a temp project directory, tests set `PYTHONPATH` to the repo root.
