# Pegasus

Pegasus is a clean standalone Claude Code project-leader scaffold.

It is designed for one workflow: start a project, clarify intent once, persist a
spec and state in a project repo, hand off to a repeatable driver routine, and
let the driver continue from repository state while asking the user only for real
decision boundaries or completion.

## Status

Clean rewrite scaffold. This repo is the canonical home for Pegasus going
forward. The intended workflow is documented, but live Claude Code routine
registration and executable `/pegasus` tests are still the next implementation
slice.

## What changed in the clean rewrite

- No subtree merge from `pegasus-os`.
- No wholesale copy of prior adapted bus/SOP/reflector files.
- The old prototype is treated as requirements history only.
- Attribution is centralized in [`NOTICE.md`](./NOTICE.md).
- The repo contains a small, reviewable control surface instead of a personal OS
  dump.

## Target workflow

```text
/pegasus start <name>
  → interview or validate spec/current.md
  → initialize spec/addenda.md + workflow/state.json + workflow/events.ndjson
  → arm a verified driver routine, or print the manual command if unavailable
  → driver reloads repo state every run
  → driver picks bounded work, optionally fans out workers, verifies, grades
  → driver persists state/events and escalates only at decision boundaries
  → /pegasus tell/status/stop interact through the repo state
```

Laptop-off/background operation is a goal only after the current Claude Code
routine surface is verified. Silent fake arming is forbidden.

## Layout

```text
pegasus/
├── PROJECT.md                         # engineering source of truth
├── NOTICE.md                          # provenance and attribution policy
├── docs/architecture.md               # runtime architecture
├── schemas/project-event.schema.json  # project lifecycle event envelope
├── skills/pegasus/SKILL.md            # /pegasus start|tell|status|stop
├── claude/routines/pegasus-driver.md  # repeatable driver prompt
├── claude/project-workers/            # small optional worker role prompts
└── examples/project/                  # minimal project-state example
```

## Commands

Pegasus exposes one skill with four verbs:

```text
/pegasus start <repo-or-slug>
/pegasus tell <repo-or-slug> "..."
/pegasus status <repo-or-slug>
/pegasus stop <repo-or-slug>
```

## Safety boundaries

Pegasus never does these without explicit user approval:

- force-push;
- delete a repository;
- rewrite Git history;
- change dependency versions;
- modify CI or deployment settings;
- mark a project done without fresh verification evidence;
- pretend a background routine is armed when the runtime did not confirm it.

## Next implementation slice

1. Install the skill into the target Claude Code skills path.
2. Add a dry-run harness for `/pegasus start|tell|status|stop` against
   `examples/project/`.
3. Wire routine registration only after the current Claude Code runtime surface is
   verified.
4. Add fixture tests for state/event parsing and driver phase transitions.
