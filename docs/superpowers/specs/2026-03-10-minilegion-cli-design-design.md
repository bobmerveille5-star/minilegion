# Minilegion CLI (design) Design

Date: 2026-03-10

## Goal

Add `python -m minilegion design` as the strict next command after `brief`.

- Enforces state preconditions via the strict state machine.
- Requires a non-empty `design_option` before transitioning to `designed`.
- Sets `next_step` deterministically to `research`.

## Non-Goals

- Supporting `design_complexity` (keep `null` in this slice).
- Adding interactive prompts.
- Adding generic transition commands.
- Allowing "resume" behavior via existing `design_option` without `--option`.

## Command

`python -m minilegion design --option "..."`

## Preconditions

- Project must be initialized (`<ai_dir>/STATE.json` must exist).
- Current stage must be `briefed`.
- `--option` must be provided and non-empty after trimming.

Command must fail explicitly and not mutate state if any precondition fails.

## Effects

On success:

1. Persist `design_option` from `--option` (trimmed).
2. Set `next_step` to `research`.
3. Transition `current_stage` to `designed`.

`design_complexity` remains `null`.

## Output

Print stable, greppable lines including:

- `current_stage: designed`
- `next_step: research`
- `design_option: <value>`

## Exit Codes

- Success: 0
- Preconditions failed / missing state / validation issues: 1

## Verification Strategy

Unit tests (subprocess, same harness as `tests/test_cli.py`):

- `design` fails if project not initialized.
- `design` fails if stage is not `briefed`.
- `design` fails if `--option` is missing or blank and must not mutate stage.
- `design --option ...` succeeds from `briefed`, transitions to `designed`, sets `next_step=research`, and persists `design_option`.
- `design` respects project override `ai_dir` from `minilegion.yaml`.

