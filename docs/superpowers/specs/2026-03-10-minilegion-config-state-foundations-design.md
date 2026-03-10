# Minilegion: Config Contract + Strict State Machine (Foundations)

Date: 2026-03-10

## Goal

Establish a stable, enforceable foundation for Minilegion before any CLI commands or LLM-driven workflow:

- A single source of truth for runtime defaults via a layered configuration contract.
- A strict persisted state machine that makes stage transitions enforceable, not advisory.

## Non-Goals

- Implementing CLI commands (`init`, `status`, etc.).
- Implementing LLM adapters, prompts, or orchestrator logic.
- Adding environment-variable or CLI flag overrides (can be added later, on top of the contract).

## Decisions

### Layered overrides (now)

Configuration is loaded by layering sources in this order:

1. **Package defaults (layer 1):** `minilegion/config.yaml` (shipped with the package)
2. **Project override (layer 2):** `<project_root>/minilegion.yaml`

The layer-2 file is optional.

### Canonical override location

Project override path is fixed to:

`D:\pln kiro\test powers\test4\minilegion.yaml`

This is the canonical root-level override file for the project.

### Merge semantics

Merging is deterministic:

- mappings/dicts: deep merge recursively
- lists: replace entirely by the override value
- scalars: replace entirely by the override value

### Strict schema validation

Config is validated strictly:

- unknown keys are rejected (no silent typos)
- types are validated
- error locations are reported with a dotted path (example: `guards.max_revise_cycles`)

Implementation detail (preferred): Pydantic models as the config schema.

## Config Schema (v1)

Top-level keys:

- `llm`
  - `default_adapter` (string)
  - `adapters` (map of adapter-name -> adapter config)
  - `role_routing` (map of role -> adapter-name)
  - `fallback_chain` (list of adapter-names)
- `project`
  - `ai_dir` (string path, relative to project root by default)
  - `mode` (string, e.g. `safe`)
- `guards`
  - `scope_lock` (bool)
  - `plan_required` (bool)
  - `review_separate` (bool)
  - `human_approval` (bool)
  - `max_revise_cycles` (int)

Notes:

- Defaults for this schema come from `minilegion/config.yaml`.
- The project override file can override any subset of the schema.

## State Machine Contract

### Persistence

State is persisted immediately to disk on every mutation:

- Location: `<ai_dir>/STATE.json`
- Default `ai_dir` comes from config (`project.ai_dir`, currently `project-ai`)

### State shape

State is initialized with the Minilegion reference shape (fields + defaults), including:

- `project_name`, `goal`, `current_stage`, `mode`
- design tracking (`design_option`, `design_complexity`)
- research validation (`research_validated`)
- plan/task tracking (`files_for_plan`, `completed_tasks`, `pending_tasks`, `touched_files`)
- risk tracking (`open_risks`)
- review tracking (`review_verdict`, `revise_cycles`, `max_revise_cycles`, `revise_items`)
- iteration metadata (`next_step`, `iteration`, `history`)
- timestamps (`created_at`, `updated_at`)

### Stage transition matrix (strict)

Transitions MUST match the approved matrix (reference plan), enforced by the state manager:

- `initialized -> briefed`
- `briefed -> designed | initialized`
- `designed -> researched | briefed`
- `researched -> planned | designed`
- `planned -> executed | researched`
- `executed -> reviewed`
- `reviewed -> archived | executed`
- `archived -> briefed`

### Enforcement invariants

- Illegal transition raises an explicit error and MUST NOT mutate the persisted state.
- `check_stage(allowed_stages)` is available to fail fast before executing commands.

## Public API (minimal, stable)

- Config:
  - `load_config(project_root) -> Config`
- State:
  - `StateManager(ai_dir)`
  - `initialize(project_name)`
  - `transition(new_stage)`
  - `check_stage(allowed_stages)`
  - `update(**fields)`
  - `read() -> dict`

## Verification Strategy

- Unit tests verify:
  - initialization writes the expected state shape and defaults
  - update persists deterministically and reload is identical
  - valid transition persists
  - invalid transition does not mutate persisted state
- Config tests verify:
  - defaults-only load passes
  - override file deep-merges and replaces lists as defined
  - unknown keys fail validation
