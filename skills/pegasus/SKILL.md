---
name: pegasus
description: Clean standalone Pegasus control surface. Use for /pegasus start|tell|status|stop on a project repository with spec/current.md.
---

# Pegasus skill

## Invariants

- The target project repo is the source of truth.
- `spec/current.md` must exist before start.
- `workflow/state.json` and `workflow/events.ndjson` hold durable runtime state.
- The skill never force-pushes, deletes repositories, or rewrites history.
- If background routine registration is unavailable, say so explicitly.

## `/pegasus start <repo-or-slug>`

1. Locate the target repository or project directory.
2. Verify `spec/current.md` exists.
3. Create `workflow/` if needed:
   - `state.json`
   - `events.ndjson`
   - `addenda.md`
   - `questions.md`
4. Initialize state with `phase: planning`, `tick_count: 0`, and no current lane.
5. Append `project_started` to `workflow/events.ndjson`.
6. Hand off to `claude/routines/pegasus-driver.md` only if the runtime routine
   surface is verified in the current session.

## `/pegasus tell <repo-or-slug> "..."`

Append a timestamped addendum to `workflow/addenda.md` and append a `user_tell`
event. The next driver run must read addenda before choosing work.

## `/pegasus status <repo-or-slug>`

Read `workflow/state.json`, the last 20 events, and pending questions. Return one
screen: phase, current lane, tick count, last evidence, blocker, next safe action.

## `/pegasus stop <repo-or-slug>`

Set `phase: stopped`, append `project_stopped`, and report any routine id that
needs manual deletion. Do not delete worktrees, branches, remotes, or history.
