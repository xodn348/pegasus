---
name: pegasus
description: Cloud-native autonomous project leader. /pegasus start | tell | status | stop. Hands a project off to Anthropic cloud so the user's laptop can be off.
version: 1
---

# Pegasus — Leader skill

PROJECT.md §2 7-step workflow normative. This skill is the Leader (L1) brain — interviews, bootstraps, hands off.

Beta headers required on every API call:
- `managed-agents-2026-04-01`
- `experimental-cc-routine-2026-04-01`

---

## Verbs

### `/pegasus start <name>`

1. **Deep interview (20–30 min).** Run `pegasus-init` skill (from pegasus-os reuse). Output: `spec/interview-transcript.md`.
2. **Synthesize spec.** Run `ralplan` against the transcript. Output: `spec/current.md`, `workflow/plan.md` (milestones), `workflow/state.json` (phase=planning).
3. **Acceptance rubrics.** For each milestone, write `spec/milestones/M<n>.md` with grader-readable acceptance criteria. These ARE the Outcomes rubric files.
4. **Repo bootstrap.** Create `xodn348/<name>` (private). Push initial spec + plan + state. Set `workflow/events.ndjson` empty.
5. **Memory store create.** `POST /v1/memory_stores` with workspace scope. Save `memory_store_id` into `state.json`. Memory holds cross-tick continuity since each cron tick is a fresh session.
6. **Coordinator + workers register.** Declare `multiagent={"type":"coordinator","agents":[...6 C-suite...]}` per `workers.json`. Capture the coordinator's `agent_id` into `state.json.managed_agent_id`.
7. **Routine register.** `POST /v1/routines` with `schedule="0 * * * *"`, `name="[<name>] driver"`, prompt body = `claude/routines/leader-driver.md` (substituted with `<name>` and `memory_store_id`). Capture `routine_id` into `state.json`.
8. **Handoff message** to user: "Driver routine `[<name>] driver` armed at hourly. Phone off OK." Set `state.json.phase = "executing"`.

### `/pegasus tell <name> "..."`

Append to `spec/addenda.md` in `xodn348/<name>` with timestamp + content. Also push the addendum text into the memory_store under key `pending_addenda`. Driver picks it up on next tick.

### `/pegasus status <name>`

Read `xodn348/<name>/workflow/state.json` + last 20 lines of `events.ndjson`. Render: phase, current milestone, tick count, completion %, last tick result, any pending questions.

### `/pegasus stop <name>`

`DELETE /v1/routines/{routine_id}`. Set `state.json.phase = "stopped"`. Append `pegasus_stopped` to events.ndjson. Push.

---

## Decision boundaries (PROJECT.md §6)

Leader makes setup/teardown decisions only. Driver runs autonomously per §6 table. Anything outside Driver autonomy → Driver writes `questions/pending.md` + phase=awaiting_user, Leader can resume by user invoking `/pegasus tell`.

---

## State of truth

- `xodn348/<name>` GitHub repo = source of truth
- `memory_store` at `/mnt/memory/` = cross-tick fast cache (state.json mirror + pending_addenda)
- `events.ndjson` = single timeline (Anthropic session events mirrored in via Driver)

Never store project state in this skill's process memory — every verb starts cold and re-reads from GitHub.

---

## v1 必수 (PROJECT.md §3 cross-cutting)

When constructing API calls for routine registration + coordinator:

- `cache_control: {"type": "ephemeral", "ttl": "1h"}` on the system prompt block → 90% cache hit on hourly ticks
- Coordinator model: `claude-sonnet-4-6`. Worker models: `claude-haiku-4-5-20251001` for routine work, `claude-opus-4-7` only when worker prompt body explicitly requires it (CEO, GC for legal reasoning)
- Mount `memory_store_id` on every Driver tick session via the routine config
- Per-worker MCP: see `workers.json` (v1 wires CTO+GitHub only; others deferred to v1.5)
- Anthropic prebuilt skills (xlsx / pdf / pptx / docx) attached to relevant workers via `skills` array

---

## Reuse from pegasus-os

- `skills/pegasus-init/SKILL.md` — interview chain (80% reused)
- `sops/spec-seed.md` — for spec finalization
- `bus/SCHEMA.md` — event schema

Don't copy. Reference by path. Pegasus repo only contains the **glue + delta**.
