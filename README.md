# Pegasus

Pegasus is a clean standalone Claude Code project-leader scaffold.

It is designed for one job: turn a user-approved project spec into a repeatable
leader routine that can continue work, ask only when decision boundaries require
it, and report completion with evidence.

## Status

Clean rewrite scaffold. This repo supersedes the earlier prototype history and
is the canonical home for Pegasus going forward.

## What changed in the clean rewrite

- No subtree merge from `pegasus-os`.
- No wholesale copy of prior adapted bus/SOP/reflector files.
- The old prototype is treated as requirements history only.
- Attribution is centralized in [`NOTICE.md`](./NOTICE.md).
- The repo contains a small, reviewable control surface instead of a personal OS
  dump.

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

The exact runtime integration is intentionally explicit: if Claude Code routine
registration is unavailable in the current session, the skill must say so and
print the manual next step instead of pretending a background routine is armed.

## Safety boundaries

Pegasus never does these without explicit user approval:

- force-push;
- delete a repository;
- rewrite Git history;
- change dependency versions;
- modify CI or deployment settings;
- mark a project done without fresh verification evidence.

## Next implementation slice

1. Install the skill into the target Claude Code skills path.
2. Dry-run `/pegasus status` against `examples/project/`.
3. Wire routine registration only after the current Claude Code runtime surface is
   verified.
4. Add fixture tests for state and event parsing before expanding automation.
