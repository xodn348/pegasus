---
name: pegasus
description: Cloud-native autonomous project leader on Claude Code. /pegasus start | tell | status | stop. Claude Code session auth only, no Anthropic API keys.
version: 2
---

# Pegasus — Leader skill

PROJECT.md §2 7-step workflow normative. Leader (L1) interviews, bootstraps, hands off via Claude Code Cron.

**No Anthropic API. No beta headers. Claude Code session auth only.**

---

## Verbs

### `/pegasus start <name>`

1. **Deep interview (20–30 min).** Run `pegasus-init` skill (from pegasus-os reuse). Output: `spec/interview-transcript.md`.
2. **Synthesize spec.** Run `ralplan` against the transcript. Output: `spec/current.md`, `workflow/plan.md` (milestones), `workflow/state.json` (phase=planning).
3. **Acceptance rubrics.** For each milestone, write `spec/milestones/M<n>.md` with grader-readable acceptance criteria. Grader subagent reads these per tick.
4. **Repo bootstrap.** Create `xodn348/<name>` (private). Push initial spec + plan + state + empty `workflow/events.ndjson`.
5. **Routine register.** Use `CronCreate` tool — `schedule="0 * * * *"`, `name="[<name>] driver"`, `prompt` = substituted `claude/routines/leader-driver.md` (substitute `{{PROJECT_NAME}}` + `{{REPO_URL}}`). Capture returned cron id → `state.json.routine_id`. Push.
6. **Handoff message** to user: "Driver routine `[<name>] driver` armed at hourly. Phone off OK." Set `state.json.phase = "executing"`.

### `/pegasus tell <name> "..."`

Append to `spec/addenda.md` in `xodn348/<name>` with timestamp + content. Push. Driver picks it up on next tick by diffing addenda since `state.last_tick_utc`.

### `/pegasus status <name>`

Read `xodn348/<name>/workflow/state.json` + last 20 lines of `events.ndjson`. Render: phase, current milestone, tick count, completion %, last tick verdict, pending questions.

### `/pegasus stop <name>`

`CronDelete` the routine using `state.routine_id`. Set `state.json.phase = "stopped"`. Append `pegasus_stopped` to `events.ndjson`. Push.

---

## Decision boundaries (PROJECT.md §6)

Leader makes setup / teardown decisions only. Driver runs autonomously per §6 table. Anything outside Driver autonomy → Driver writes `questions/pending.md` + `phase=awaiting_user` + `PushNotification`. Leader resumes by user invoking `/pegasus tell`.

---

## State of truth

- `xodn348/<name>` GitHub repo = source of truth
- `events.ndjson` = single timeline (Driver mirrors any cron-runtime events here)
- **No external memory store.** Every tick is a fresh Claude Code session that re-clones/pulls and reads `state.json`.

---

## Model + tool tiering (PROJECT.md §3)

When Driver spawns workers via `Agent`:
- Coordinator role collapses into Driver itself — `Agent` tool natively fans out, no separate coordinator agent needed.
- Worker model + tools per `workers.json`: Opus for CEO/GC (judgment), Haiku for CTO/CFO/CMO/COO (execution).
- MCP servers are configured in the user's Claude Code MCP config separately, not declared in workers.json.

---

## Reuse from pegasus-os

- `skills/pegasus-init/SKILL.md` — interview chain (80% reused)
- `sops/spec-seed.md` — spec finalization
- `bus/SCHEMA.md` — event schema

Don't copy. Reference by path. Pegasus repo only contains the **glue + delta**.
