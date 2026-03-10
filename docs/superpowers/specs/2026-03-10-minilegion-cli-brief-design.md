# Minilegion CLI (brief) Design

Date: 2026-03-10

## Goal

Add `python -m minilegion brief` as the next safe command after `init/status`.

- Enforces state preconditions via the strict state machine.
- Requires a non-empty goal before transitioning to `briefed`.
- Sets `next_step` deterministically to `design`.

## Non-Goals

- Implementing `designed` stage behavior or any design artifact generation.
- Adding `--force`.
- Adding generic transition commands.

## Command

`python -m minilegion brief [--goal "..."]`

## Preconditions

- Project must be initialized (`<ai_dir>/STATE.json` must exist).
- Current stage must be `initialized`.
- Goal must be defined:
  - If `--goal` is provided: use it.
  - Else: require existing `state["goal"]` to be non-empty.
  - If neither: error (exit non-zero).

## Effects

On success:

1. Persist `goal` (from `--goal` or existing).
2. Set `next_step` to `design`.
3. Transition `current_stage` to `briefed`.

Command must fail explicitly and not mutate state if any precondition fails.

## Output

Print stable, greppable lines including:

- `current_stage: briefed`
- `next_step: design`

## Exit Codes

- Success: 0
- Preconditions failed / missing state / validation issues: 1

## Verification Strategy

Unit tests (subprocess):

- `brief` fails if project not initialized.
- `brief` fails if initialized but goal missing and `--goal` omitted.
- `brief --goal ...` succeeds from `initialized`, transitions to `briefed`, sets `next_step=design`, and persists goal.
- `brief` fails if stage is not `initialized`.

Tests set `PYTHONPATH` to repo root (same pattern as `tests/test_cli.py`).
