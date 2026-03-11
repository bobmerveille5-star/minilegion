# Minilegion Canonical Pipeline

Date: 2026-03-10

This document defines the canonical (happy path) pipeline order. The strict state
machine may allow backtracking, but the canonical order is the single source of
truth for "what comes next" (`next_step`) in normal execution.

## Canonical Order (Happy Path)

1. `init` -> `initialized`
2. `brief` -> `briefed`
3. `design` -> `designed`
4. `research` -> `researched`
5. `plan` -> `planned`
6. `execute` -> `executed`
7. `review` -> `reviewed`
8. `archive` -> `archived`

## Command Contracts (Canonical)

Each command:

- Must refuse to run if the current stage is not the expected one (exit non-zero).
- Must refuse to run if required inputs are missing (exit non-zero).
- Must not mutate state on failure.
- Must set `next_step` deterministically to the next canonical command on success.

| Command | Required Stage | On Success: Stage | On Success: `next_step` | Required Inputs | Writes (minimum) |
| --- | --- | --- | --- | --- | --- |
| `init` | (none, but requires missing `STATE.json`) | `initialized` | (empty) | project name (default: cwd name) | `project_name`, `mode`, `max_revise_cycles`, baseline state shape |
| `brief` | `initialized` | `briefed` | `design` | `goal` | `goal`, `next_step` |
| `design` | `briefed` | `designed` | `research` | `design_option` | `design_option`, `next_step` |
| `research` | `designed` | `researched` | `plan` | `files_for_plan[]` | `files_for_plan`, `research_validated`, `next_step` |
| `plan` | `researched` | `planned` | `execute` | (tbd) | (tbd) |
| `execute` | `planned` | `executed` | `review` | (tbd) | (tbd) |
| `review` | `executed` | `reviewed` | `archive` | (tbd) | (tbd) |
| `archive` | `reviewed` | `archived` | `brief` | (tbd) | (tbd) |

## State Location

- State is persisted to `<ai_dir>/STATE.json`.
- `<ai_dir>` comes from layered config (`minilegion/config.yaml` defaults, overridden by `./minilegion.yaml`).

