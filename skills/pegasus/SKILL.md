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

1. **Deep interview (20–30 min).** Invoke `skills/pegasus-init/SKILL.md` (vendored from pegasus-os per PROJECT.md §8 ADAPT — 15Q, 3-stage, ambiguity ≤ 0.15 gate, pressure pass, readiness gates). Output goes directly to the cloned `xodn348/<name>/` working dir:
   - `spec/current.md` (the spec)
   - `spec/interview-transcript.md` (Q&A trace)
2. **Synthesize milestones.** Apply `claude/sops/spec-seed.md` Rules 2–4 — every `Acceptance` checklist line from `spec/current.md` becomes one milestone in `workflow/plan.md`; Rule 4's "Alternative interpretations considered" block lives inside `spec/current.md` before freeze. Initialize `workflow/state.json` (phase=planning).
3. **Acceptance rubrics.** Per milestone: write `spec/milestones/M<n>.md` = its Acceptance line + one observable verification (test cmd / file existence / metric threshold). Grader reads this per tick.
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

## Reuse from pegasus-os — vendored per PROJECT.md §8

Pegasus is self-contained. The reusable assets were **copied** (VERBATIM or ADAPTED) into this repo so the driver tick doesn't depend on `~/code/pegasus-os/` being present:

| File in this repo | Origin | Mode |
|---|---|---|
| `claude/PRINCIPLES.md` | `pegasus-os/claude/CLAUDE.md` §1 (base principles) | VERBATIM |
| `claude/bus/SCHEMA.md` | `pegasus-os/claude/bus/SCHEMA.md` | VERBATIM + project-bus kinds |
| `claude/reflectors/violation-rules.md` | `pegasus-os/claude/reflectors/...` | VERBATIM |
| `claude/reflectors/friction-rules.md` | `pegasus-os/claude/reflectors/...` | VERBATIM |
| `claude/sops/parallel-subagents.md` | `pegasus-os/claude/sops/...` | ADAPT (pegasus runtime) |
| `claude/sops/spec-seed.md` | `pegasus-os/claude/sops/...` | ADAPT (GitHub-spec layout) |
| `claude/sops/worktree-parallel.md` | `pegasus-os/claude/sops/...` | ADAPT (Agent fanout, no tmux) |
| `skills/pegasus-init/SKILL.md` | `pegasus-os/claude/skills/pegasus-init/` | ADAPT (CronCreate handoff) |

**Not reused** (PROJECT.md §8 SKIP): `daily-self-improve`, `oss-contributor`, `weekly-retro`, `kernel` hooks — those are pegasus-os host-only.
