# Pegasus — PROJECT.md (v2)

> **Authoritative spec.** Replaces v1 (2026-05-19) after Anthropic Managed Agents API verification. All v1 primitive names (Goal / Agent Team / Agent View) were aspirational — v2 uses the actual shipped feature names.

---

## 1. Intent

Build a **cloud-native autonomous project leader** for Claude such that:

> The user starts a multi-week software project from their phone, hands it off to Anthropic's cloud, **turns the laptop off**, and the project completes itself — committed to GitHub, with the user being interrupted only when (a) a decision is genuinely the user's to make or (b) the project is done.

This is a *dev tool that owns a project end-to-end on Anthropic's cloud*. It uses Anthropic's Managed Agents primitives (Outcomes, Multiagent Orchestration, Memory, Subagent, Dreaming) as the substrate.

### Success criteria

1. Smoke project (markdown TOC generator) completes from `/pegasus start` to terminal state with the user's laptop powered off for ≥ 4 hours of the build window.
2. Driver routine self-terminates when all milestones reach satisfied state.
3. User receives a notification within 5 minutes of completion.
4. Mid-project clarification → user replies via `/pegasus tell` from mobile → next tick incorporates it.

### Non-goals (explicit)

- ❌ Custom UI. The Claude Console audit log + session event stream is the monitor.
- ❌ Self-hosted runner. Anthropic Managed Agents only.
- ❌ PR-gated workflow. Auto-merge to `main`.
- ❌ Sub-hour tick cadence. Anthropic routine min is 1h.
- ❌ Multi-project routines. One project = one repo = one routine.
- ❌ Reinventing interview / planning / worker loops — reuse `pegasus-init`, `deep-interview`, `prometheus`, `ralplan`, plus the `worktree-parallel.md` SOP.

---

## 2. User workflow (2026-05-17 original, normative)

The 7 steps Junhyuk specified during the original design session. v2 implements these literally:

1. **사용자가 클로드 세션을 통해 프로젝트를 시작**
2. **리더 에이전트가 딥 인터뷰** — 20–30분
3. **리더 에이전트가 전체 아키텍처/워크플로/task → spec으로 변환**
4. **리더 에이전트가 subagent 병렬 호출, 각자 spec 전달**
5. **각 subagent는 받은 spec을 ralph 루프로 끝까지 완료**
6. **리더가 결과 통합 + 사용자 호출 (최대한 적게)**
7. **완료 시 사용자에게 알림**

Additional invariants:
- 사용자 컴퓨터가 꺼져도 동작
- 루틴은 프로젝트당 1개, `[<project>] driver`
- 완료 시 routine 자동 비활성
- 모바일 알림

---

## 3. Architecture — four layers

```
┌──────────────────────────────────────────────────────────────────────────┐
│  L0 — User Terminal:  Claude Mobile App                                  │
│  • /pegasus start <name>       • Claude Console에서 audit log 확인       │
│  • /pegasus tell <name> "..."  • 세션 이벤트 stream으로 진행 모니터      │
│  • /pegasus status / stop                                                │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L1 — Leader (Claude Code session, ephemeral)                            │
│  • 딥 인터뷰 (deep-interview / pegasus-init / ralplan)                   │
│  • spec/architecture/plan 작성                                            │
│  • xodn348/<project> 부트스트랩                                          │
│  • Cron Routine 등록 → 핸드오프 → 세션 종료 OK                           │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │ creates ONE routine
                     │ name = "[<project>] driver"
                     │ schedule = "0 * * * *"
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L2 — Driver (Managed Agent session, fires per tick)                     │
│  • 매 tick마다 새 Managed Agent session 생성                              │
│  • 현재 milestone에 대해 user.define_outcome 발사 (rubric 첨부)          │
│  • Memory store에서 cross-tick 상태 로드                                  │
│  • plan.md의 ready task 선택 → Multiagent Orchestration으로 위임         │
│  • Outcome grader가 milestone "satisfied" 판정 → state.json에 done 표시  │
│  • 모든 milestone done → 루틴 self-disable                                │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │ delegates to specialists at runtime
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L3 — Workers (Multiagent Orchestration specialists)                     │
│  • Lead agent (Driver)가 런타임에 specialist 호출, 선언적 roster 아님    │
│  • 각 worker: 자체 모델/프롬프트/도구, 공유 파일시스템에서 병렬 작동      │
│  • 각자 ralph 루프 (테스트 통과까지 자체 반복)                            │
│  • 결과를 lead agent에 반환 → Driver가 main에 통합                       │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │ all read/write
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L4 — Shared State: GitHub xodn348/<project>                             │
│  spec/  workflow/plan.md  events.ndjson  subagents/<id>/  output/        │
│  questions/pending.md  state.json                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

### Why each layer is where it is

| Layer | Role | Non-negotiable because |
|---|---|---|
| L0 Mobile | Entry + monitor | Computer-off baseline. Desktop is incidental. |
| L1 Leader | Interview + bootstrap | Interviews are interactive. Cron has no human. |
| L2 Driver | Cron-fired Managed Agent | Anthropic Routine cron = "computer off" satisfied. |
| L3 Workers | Multiagent Orchestration | Native parallelism, shared FS, persistent event log. |
| L4 GitHub | Source of truth | Auditable, hand-editable, survives outages. |

---

## 4. Anthropic Managed Agents primitives — actual shipped features

Verified against [claude.com/blog/new-in-claude-managed-agents](https://claude.com/blog/new-in-claude-managed-agents), [Outcomes cookbook](https://platform.claude.com/cookbook/managed-agents-cma-verify-with-outcome-grader), and 9to5mac coverage. Beta header required: `managed-agents-2026-04-01`.

| Primitive | What it does | Where we use it |
|---|---|---|
| **Outcomes** | Declarative milestone with `description` + `rubric` (text or file) + `max_iterations`. A separate grader LLM evaluates the agent's work against the rubric. Terminal states: `satisfied` / `failed` / `max_iterations_reached` / `interrupted`. Posted via `user.define_outcome` event. | Each Driver tick declares an Outcome for the **current milestone**. Grader's `satisfied` verdict → milestone done in state.json. |
| **Multiagent Orchestration** | Lead agent delegates to specialists at runtime (own model/prompt/tools), parallel on shared filesystem, persistent event log. **Not a declarative team manifest** — the lead agent decides who/when at runtime. | Driver = lead agent. Workers = specialists. Driver picks worker per ready task. |
| **Memory** | Per-agent persistent store, accessed across that agent's sessions. Public beta. | Driver Managed Agent's memory holds cross-tick context (spec hash, in-progress task ids, recent failures). |
| **Subagent** | Additional Claude model called by main agent for sub-tasks. Worktree isolation is a separate Claude Code harness feature. | Used inside L3 specialists when they need deeper recursion. |
| **Dreaming** | Background self-improvement reviewing past sessions + memory. Research preview, no public config. | **Skip v1.** Re-evaluate after smoke test. |
| **Session event stream + Console audit log** | Every session emits structured events. Visible in Claude Console. | Mobile monitoring (`/pegasus status` is the fallback when offline). |

### Renames since v1

| v1 name (wrong) | v2 actual name | What changed |
|---|---|---|
| Goal | **Outcomes** | No `success_check` callable, no `timeout` field. Rubric + max_iterations only. |
| Agent Team | **Multiagent Orchestration** | No team YAML manifest. Lead agent delegates at runtime. |
| Agent View | (dropped) | No such product. Console audit log + event stream replace it. |
| Webhook `goal_met` | Session event `session.outcome_evaluation_ended` | Real event name. Terminal `result` field carries satisfied/failed/etc. |

---

## 5. Outcomes + max_iterations — the iteration model

This is the v2's most important constraint. Read carefully.

### What Outcomes actually is

When a Managed Agent session has an Outcome attached, **a separate grader LLM** evaluates whether the agent's work satisfies the rubric. The agent gets up to `max_iterations` (default 3, max 20) rounds: work → grader checks → not satisfied → work more → grader checks again → ... until grader says satisfied OR cap hit.

- `max_iterations` is bounded by Anthropic at **20 hard**.
- One Outcome lives in **one session**. It does not persist across sessions.

### Why this matters for multi-week projects

A multi-week Pegasus project cannot be one giant Outcome — 20 grader evaluations is not enough to converge an entire project, and Outcomes don't span sessions anyway. So the model is:

**One Outcome per Driver tick, scoped to one milestone-shaped chunk of work.**

| Layer | Lifespan | Cap |
|---|---|---|
| Project | weeks–months | unlimited (we track in state.json) |
| Milestone | hours–days | unlimited tick count, but one Outcome per tick |
| Tick | < 15 min | one Outcome, `max_iterations=20` (Driver picks ~5) |

### How a tick uses Outcomes

1. Driver wakes (cron fires, fresh Managed Agent session).
2. Driver reads `workflow/state.json`, picks ready tasks for the current milestone.
3. Driver declares Outcome: `description: "Advance milestone <M> by completing tasks <t1, t2, t3>"`, `rubric: <link to spec/milestones/<M>.md acceptance criteria>`, `max_iterations: 5`.
4. Driver delegates to workers via Multiagent Orchestration.
5. Workers commit to their branches; Driver integrates.
6. Driver requests grader evaluation.
7. If `satisfied`: state.json updates (milestone advances), bus event `tick_satisfied`. Routine waits for next cron tick.
8. If `max_iterations_reached`: bus event `tick_max_iterations`, milestone stays in progress, next tick retries.
9. If `failed`: bus event `tick_failed`, milestone marked blocked, possible user escalation.

### Project termination

Project is `done` when all milestones in `workflow/plan.md` are status `done` in `state.json`. The cron routine self-disables at that point. **Project termination is OUR state machine, not Outcomes.** Outcomes only judge per-tick convergence.

---

## 6. Lifecycle — one project end to end

| Step | Where | What happens | Output committed |
|---|---|---|---|
| 1 | L0 mobile | `/pegasus start gardener` | — |
| 2 | L1 Leader | 25-min deep interview (pegasus-init + ralplan) | `spec/current.md`, `spec/interview-transcript.md` |
| 3 | L1 Leader | Milestone synthesis | `workflow/plan.md` (milestones list), `workflow/state.json`, `spec/milestones/M1.md` … |
| 4 | L1 Leader | Repo create + initial commit | `xodn348/gardener` initialized |
| 5 | L1 Leader | Cron routine register | `[gardener] driver` enabled, hourly |
| 6 | L1 → L0 | "Handed off. Phone off OK." | — |
| 7 | L2 Driver (hourly) | Outcome per current milestone, delegate, integrate, grader | `events.ndjson` += tick events |
| 8 | L3 Workers | ralph loops on tasks within tick | subagent branches |
| 9 | L2 Driver | Grader `satisfied` → milestone done | state.json updates |
| 10 | L0 mobile | Optional: `/pegasus status` (or Console audit log) | — |
| 11 | L2 Driver | All milestones done → disable routine | `state.json.phase = "done"` |
| 12 | L0 mobile | Notification on completion | — |
| 13 | repo | Permanent audit | — |

Hard guarantee: between step 6 and step 12, the laptop is unnecessary.

---

## 7. Decision boundaries

Driver may decide alone. Anything outside → `questions/pending.md` + `phase = "awaiting_user"`.

| Decision | Driver autonomous? |
|---|---|
| Pick next ready task | ✅ |
| Set tick `max_iterations` (≤ 20) | ✅ |
| Declare Outcome rubric from spec | ✅ (rubric file is spec; Driver only references it) |
| Spawn ≤ 3 workers via Multiagent Orchestration | ✅ |
| Integrate worker branch (fast-forward) | ✅ |
| Integrate via 3-way merge with conflicts | ❌ |
| Revert merge after grader/verify fail | ✅ once; escalate on 2nd |
| Add a new milestone | ❌ |
| Modify `spec/current.md` (vs addendum) | ❌ |
| Push to `main` | ✅ |
| Force-push / rewrite history | ❌ |
| Mark milestone done without grader `satisfied` | ❌ |
| Disable routine when all milestones done | ✅ |

---

## 8. State + bus contracts

### `workflow/state.json`

```json
{
  "name": "<project>",
  "created_utc": "<iso8601>",
  "phase": "planning | executing | awaiting_user | done",
  "current_milestone_id": "M1",
  "milestones": [
    {
      "id": "M1",
      "title": "...",
      "status": "pending | in_progress | done | blocked",
      "rubric_path": "spec/milestones/M1.md",
      "tasks": [
        { "id": "t1", "title": "...", "status": "pending|in_progress|done|blocked", "depends_on": [] }
      ]
    }
  ],
  "tick_count": 0,
  "last_tick_utc": null,
  "completion_pct": 0,
  "routine_id": "<anthropic-routine-id>",
  "managed_agent_id": "<anthropic-agent-id>"
}
```

### `events.ndjson` event kinds

```
project_init             — Leader bootstrap
user_tell                — addendum from mobile
question_raised          — Driver wrote questions/pending.md
question_resolved        — addendum matched an open question
tick_started             — Driver session opened, Outcome declared
tick_satisfied           — Outcome grader returned satisfied
tick_failed              — Outcome grader returned failed
tick_max_iterations      — hit the cap mid-convergence; retry next tick
tick_interrupted         — session terminated early
specialist_invoked       — Multiagent Orchestration delegation
specialist_returned      — specialist finished, branch ready
integration_failed       — merge or verify failed; reverted
milestone_advanced       — milestone status flipped to done
escalation               — phase flipped to awaiting_user
pegasus_done             — all milestones done; routine disabled
pegasus_stopped          — user-initiated /pegasus stop
```

Anthropic session events (`session.outcome_evaluation_ended` etc.) are mirrored into this bus by the Driver so the bus is the single timeline.

---

## 9. Reuse from `xodn348/pegasus-os`

Aggressive reuse. No reinvention.

- **VERBATIM**: `claude/bus/SCHEMA.md` (event schema generalizes), `claude/CLAUDE.md` base principles (Think / Simplicity / Surgical / Goal-Driven), `claude/reflectors/violation-rules.md` + `friction-rules.md`.
- **ADAPT**: `claude/sops/parallel-subagents.md`, `claude/sops/spec-seed.md`, `claude/sops/worktree-parallel.md` (inline into worker prompt), `claude/skills/pegasus-init/SKILL.md` (already 80% of Leader interview logic).
- **INSPIRE**: pegasus-os cloud-routine pattern (cron + ephemeral runner + commit-only writes).
- **SKIP**: `daily-self-improve.md`, `oss-contributor-prompt.md`, `weekly-retro.md`, `kernel/hooks/*.sh` — pegasus-os specific.

Two buses run in parallel by design — the Mac-side `pegasus-os/claude/bus/events.ndjson` (user's cross-session observability) and the per-project `xodn348/<project>/events.ndjson` (project-lifecycle observability). They share schema, they don't share data.

---

## 10. v1 milestones (post-PROJECT.md surgery, post-verification)

Tracked in `workflow/plan.md` once we bootstrap pegasus through itself.

| # | Task | Lane |
|---|---|---|
| 1 | Rewrite `skills/pegasus/SKILL.md` to register cron routine + send `user.define_outcome` events per tick | skill |
| 2 | Rewrite `claude/routines/leader-driver.md` to: load state → declare Outcome → delegate via Multiagent Orchestration → wait for grader → update state | routine |
| 3 | `claude/lib/outcome-helpers.md` — how to format `user.define_outcome` events with rubric file references | new file |
| 4 | `claude/lib/event-handlers.md` — map `session.outcome_evaluation_ended` and friends to our bus event kinds | new file |
| 5 | Extract from pegasus-os: `bus/SCHEMA.md`, `reflectors/{violation,friction}-rules.md`, base principles | extraction |
| 6 | Adapt SOPs: `parallel-subagents.md`, `spec-seed.md`, `worktree-parallel.md` | extraction |
| 7 | Reflectors v0.1 — three Pegasus-specific violation rules (decision boundary breach, scope drift, mid-run reinterview) | reflectors |
| 8 | Smoke test — `markdown-toc` project end-to-end | end-to-end |

Yesterday's `c5ac133` (skills/pegasus/SKILL.md + claude/routines/leader-driver.md) is **superseded** by milestones 1–2. Will revert or rewrite when those land.

---

## 11. Open questions (still unknown)

1. **Routine prompt body size limit** — no public limit documented. Test before relying on the ~6KB leader-driver.md inline.
2. **Per-tick session lifecycle** — does a cron routine "tick" create a brand-new Managed Agent session each time, or attach to a persistent one? If the latter, memory and Outcomes carry over; if the former, memory store is the only continuity.
3. **Mobile notification delivery** — what's the configurable target for `session.outcome_evaluation_ended` notifications? Claude mobile push? Email? Need cookbook follow-up.
4. **Multiagent Orchestration declarative hooks** — confirmed no public team YAML, but is there a "specialist registry" we can pre-declare, or is delegation purely a runtime prompt-level call?
5. **Memory beta scope** — confirmed per-agent. If we want project-wide memory across the Leader and the Driver Managed Agents (two different agents), we build that layer ourselves (likely via state.json).

Resolve these via cookbook follow-up, schedule-skill dry-run, or in-context experiment before milestones 1–3 ship.

---

## 12. Anti-patterns

- ❌ Polling for completion — session event stream is the push channel.
- ❌ Custom UI — Console audit log exists.
- ❌ Reinventing interview/planning/worker skills.
- ❌ Treating one Outcome as the project — it's per-tick.
- ❌ Modifying `spec/current.md` from Driver (addendum-only).
- ❌ Force-push or rewrite history.
- ❌ Trusting `max_iterations_reached` as "this is done" — it isn't.

---

## 13. Footer

Project owner: Junhyuk Lee (xodn348@tamu.edu).
Spec version: **v2.0** — 2026-05-19, post-verification of Anthropic Managed Agents API shape. Supersedes v1 (which used aspirational primitive names).
README remains the public-facing intro; this file is the engineering source of truth.
