---
name: worktree-parallel
description: Pegasus driver fanout SOP — decompose milestones into file-disjoint lanes before `Agent` calls. Enforces no-edit planning phase, conflict matrix, independence checks, and publication gate. tmux/iTerm pane mechanics are out of scope here (Pegasus workers are `Agent` subagent calls, not desktop panes).
type: sop
adapted-from: xodn348/pegasus-os/claude/sops/worktree-parallel.md (PROJECT.md §8 ADAPT)
---

> ADAPTED from pegasus-os. Original (587 lines) was a desktop-pane orchestration manual: iTerm AppleScript splits, tmux send-keys, bypass-permissions dialog automation, leader-UUID targeting. **None of that applies to Pegasus** — workers are `Agent` tool subagents inside a cron-fired Claude Code session, not desktop processes. What we DO inherit: decomposition discipline, file-disjoint guarantees, independence checks, and the publication gate. That's the load-bearing 15% of the original.

## Scope

This SOP applies to Pegasus driver ticks that fan out **2 or more workers** in a single tick (per `parallel-subagents.md`). Single-worker ticks skip this SOP.

## Core rule

```text
multi-worker tick
  → seed.md exists (per spec-seed.md)
  → no-edit decomposition pass: lanes + file ownership + conflict matrix
  → independence checks pass (file-disjoint, no ordering)
  → disjoint worker `Agent` calls in one message (cap 3)
  → driver collects worker returns + grader verdict in same tick
  → driver gates push to main (PROJECT.md §6)
```

## Mandatory no-edit decomposition phase

Before any worker `Agent` call, the driver must produce a plan **without editing files**:

```text
Phase 1 — no edits (driver's own reasoning):
- map likely touchpoints in the cloned repo (use Read/Bash, not Edit/Write)
- propose independent lanes (one Agent call per lane)
- list expected files per lane
- build a conflict matrix: rows=lanes, columns=files, cells=C/M/D/R
  (C=create, M=modify, D=delete, R=rename)
- reject or merge lanes if any file overlaps
- assign one verification/evidence lane when useful

Phase 2 — execution:
- fan out workers via Agent tool in one message
- workers edit only their assigned disjoint files
- workers must report drift to driver instead of silently widening scope
- workers run their own verification and report evidence in their Agent return
```

The conflict matrix and lane assignments belong in `spec/<task>/seed.md` (per spec-seed.md Rule 4 ontology section) OR in `workflow/tick-<N>.md` if the milestone-level seed.md is already frozen.

## Independence checks

All must pass for two subtasks to ship as parallel `Agent` calls in the same tick:

- **File-level disjoint:** no two lanes edit the same file.
- **Module boundary:** prefer existing package/module/service boundaries.
- **No ordering dependency:** if lane B depends on lane A's commit, sequence them across ticks.
- **Independent verification:** each lane can run meaningful checks without another lane's unmerged changes.
- **Structural changes conflict broadly:** deletion, rename, split, or move of a file conflicts with any lane that modifies that file. Sequence structural changes after dependent modifications land.

If truly independent lanes cannot be found, **abort parallel dispatch and execute sequentially** (one Agent call this tick, the rest in subsequent ticks).

## Worker `Agent` call discipline

Each worker `Agent` prompt MUST include:

1. **seed-ref:** path to the per-task seed.md (spec-seed.md Rule 3).
2. **Lane goal + file ownership:** exact list of files the worker may create/modify.
3. **Scope guard:** "do not edit outside assigned files; report drift in your Agent return."
4. **Verification commands:** test/lint/build to run locally before reporting done.
5. **Commit requirement:** worker commits its slice locally (but does NOT push — see Publication gate).
6. **Report format:** structured return — files changed, tests run, commit SHA, blockers/risks.

The worker `.md` body from `workers/*.md` provides the persona/system-prompt; the per-call additions above provide the task. Don't paste long spec content — point to seed.md.

## Driver perception during the tick

Inside a single tick (one Claude Code session), driver's `Agent` calls are synchronous — the tool returns when the worker finishes. The driver doesn't need a Monitor stream to "watch" workers like the desktop SOP described; the language runtime IS the watcher.

What the driver MUST do:

- Issue all parallel `Agent` calls **in one assistant message** (true parallel, not sequential).
- After all returns: write each worker's report to `events.ndjson` (`specialist_returned` kind, PROJECT.md §7).
- Run grader `Agent` (single call, depends on worker outputs).
- Write grader verdict to `events.ndjson` (`tick_satisfied` / `tick_needs_more_work` / `tick_failed`).
- Update `state.json` with new completion %, current milestone, last_tick_utc.
- Commit + push EVERYTHING (events, state, worker file changes) in one push at tick end (per Publication gate).

## Publication gate

Workers do NOT push directly. The driver collects worker commits (which happened locally in the cloned worktree) and pushes once per tick after integration. This matches PROJECT.md §6: "fast-forward 머지 · 1회 revert · push to main" are within driver autonomy; everything else (3-way conflicts, force-push, second revert) requires `phase=awaiting_user` + `PushNotification`.

Concretely:

- ✅ Driver may `git push origin main` after a clean tick.
- ✅ Driver may `git revert <sha>` ONCE for a failed integration.
- ❌ Driver may NOT force-push, rewrite history, or use `git push --force-with-lease` for any reason — escalate via PushNotification.
- ❌ Driver may NOT skip the grader and mark a milestone done — `tick_satisfied` requires a recorded grader verdict.

## Independence smoke test — example

Milestone: "Add tag support." Driver's no-edit pass produces:

| Lane | Files (C/M/D/R) | Worker |
|---|---|---|
| 1. CLI add/list/filter | `cli/tag_commands.py` (C), `cli/__init__.py` (M: register), `tests/test_cli_tag.py` (C) | CTO |
| 2. DB migration | `migrations/2026_05_08_add_tags.sql` (C), `db/schema.py` (M: add Tag model) | COO |
| 3. Documentation | `README.md` (M: add Tag section), `docs/cli.md` (M: --tag flag) | CMO |

Conflict matrix check:
- No two lanes touch the same file → ✅ disjoint.
- Lane 1 imports the Tag model from lane 2's `db/schema.py`. **Ordering dependency detected.** Sequence: lane 2 ships in tick N, lane 1 ships in tick N+1.
- Lane 3 (docs) is independent — can run parallel with lane 1 OR lane 2.

Driver decision: tick N fans out lane 2 + lane 3 (independent). Tick N+1 fans out lane 1 alone. Total: 2 ticks instead of all-in-one tick that would have failed integration.

## What NOT to copy from the original pegasus-os SOP

The pegasus-os version contains 400+ lines on:
- iTerm AppleScript split-pane recipes (window/tab/session traversal, UUID matching).
- tmux `split-window` with `$TMUX_PANE` discipline.
- `--dangerously-skip-permissions` warning dialog auto-dismissal (down arrow + Enter).
- Per-worker launcher scripts in `/tmp/<workflow>-launchers/`.
- iTerm session auto-close on worker completion.
- `~/.claude/worktree-reports/<workflow-id>/team-state/` mailbox + heartbeat layout.

**None of this applies to Pegasus.** Pegasus workers are `Agent` tool subagents inside one Claude Code session — they don't have desktop panes, they don't need a mailbox (the `Agent` return value IS the mailbox), and they have no permission dialog because they inherit the parent session's perms.

If a future Pegasus iteration ever runs workers as separate Claude Code sessions on the user's laptop (instead of cron-tick subagents), this section should be re-imported from pegasus-os verbatim. Until then, keep this SOP focused on the cross-runtime invariants: planning discipline, file disjointness, independence, and publication gate.

## Legacy fallback

The driver does NOT have a "use iTerm tabs" fallback. If workers can't be fanned out via `Agent`, the driver sequences them across ticks. No desktop processes involved.
