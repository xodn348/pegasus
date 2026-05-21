---
name: pegasus
description: Clean standalone Pegasus control surface. Use for /pegasus start|tell|status|stop on a project repository with spec/current.md or an interview-ready idea.
---

# Pegasus skill

## Invariants

- The target project repo is the source of truth.
- `spec/current.md` must exist or be created by the interview/spec path before
  autonomous execution starts.
- `workflow/state.json` and `workflow/events.ndjson` hold durable runtime state.
- The skill never force-pushes, deletes repositories, or rewrites history.
- If background routine registration is unavailable, say so explicitly.

## `/pegasus start <repo-or-slug>`

1. Locate or create the target project repository.
2. If `spec/current.md` is missing, run the interview/spec creation path and do
   not start autonomous execution until the spec is approved.
3. Verify the approved spec contains goal, acceptance criteria, non-goals,
   decision boundaries, and verification expectations.
4. Create `workflow/` if needed:
   - `state.json`
   - `events.ndjson`
   - `addenda.md`
   - `questions.md`
5. Initialize state with `phase: planning`, `tick_count: 0`, no current lane,
   and `last_tick_utc: null`.
6. Append `project_started` to `workflow/events.ndjson`.
7. Register the driver routine only when the current Claude Code runtime returns
   a verified routine handle. Store that handle in state. If routine registration
   is unavailable, print the exact manual driver command instead.

## `/pegasus tell <repo-or-slug> "..."`

Append a timestamped addendum to `spec/addenda.md` and append a `user_tell`
event. The next driver run must read addenda before choosing work. If the project
is awaiting a user answer, the driver decides whether the addendum resolves it.

## `/pegasus status <repo-or-slug>`

Read `workflow/state.json`, the last 20 events, and pending questions. Return one
screen:

- phase;
- current lane or milestone;
- tick count;
- last verification evidence;
- blocker or pending question;
- whether a routine handle is armed;
- next safe action.

## `/pegasus stop <repo-or-slug>`

Set `phase: stopped`, append `project_stopped`, and report any routine id that
needs deletion. Delete or disable the routine only through a verified runtime
surface. Do not delete worktrees, branches, remotes, or history.
