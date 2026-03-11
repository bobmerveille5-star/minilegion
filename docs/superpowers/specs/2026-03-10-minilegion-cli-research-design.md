# Minilegion CLI (research) Design

Date: 2026-03-10

## Goal

Add `python -m minilegion research` as the strict next command after `design`.

- Enforces state preconditions via the strict state machine.
- Requires at least one `--file` input to populate `files_for_plan`.
- Canonicalizes stored paths to be relative to the project root using `/`.
- Sets `next_step` deterministically to `plan`.

## Non-Goals

- Supporting globs (`--glob`) or directory arguments (`--dir`) in this slice.
- Supporting stdin-driven file lists.
- Performing deep content validation of the files.
- Implementing `planned/executed/reviewed/archived` behavior.

## Command

`python -m minilegion research --file path [--file path ...]`

## Preconditions

- Project must be initialized (`<ai_dir>/STATE.json` must exist).
- Current stage must be `designed`.
- At least one `--file` must be provided.

Command must fail explicitly and not mutate state if any precondition fails.

## Validation

For each `--file` argument:

- Resolve to an absolute path relative to `project_root` (if relative input).
- Path must exist and be a file.
- Path must be under `project_root`.

## Canonicalization

Persist each file as a canonical string:

- Convert the resolved file path to a path relative to `project_root`.
- Store using POSIX separators (`/`) for stability across platforms.

## Effects

On success:

1. Persist `files_for_plan` to the canonical list.
2. Set `research_validated` to `true`.
3. Set `next_step` to `plan`.
4. Transition `current_stage` to `researched`.

## Output

Print stable, greppable lines including:

- `current_stage: researched`
- `next_step: plan`
- `files_for_plan_count: <N>`
- `files_for_plan: <json-array-on-one-line>`

## Exit Codes

- Success: 0
- Preconditions failed / missing state / validation issues: 1

## Verification Strategy

Unit tests (subprocess, same harness as `tests/test_cli.py`):

- `research` fails if project not initialized.
- `research` fails if stage is not `designed`.
- `research` fails if no `--file` is provided and must not mutate stage.
- `research` fails if a provided file does not exist and must not mutate stage.
- `research` succeeds from `designed`, transitions to `researched`, sets `next_step=plan`, and persists canonical `files_for_plan` and `research_validated=true`.
- `research` respects project override `ai_dir` from `minilegion.yaml`.

