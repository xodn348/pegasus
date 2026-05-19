# Pegasus — PROJECT.md

> **Authoritative spec for the Pegasus project.** The Leader agent inherits this file at every `/pegasus start` session. The Driver routine clones the repo and reads this file before every tick. Do not let this drift from reality.

---

## 1. Intent (the real outcome)

Build a **cloud-native autonomous project leader** for Claude such that:

> The user can start a multi-week software project from their phone, hand it off to Anthropic's cloud, **turn their laptop off**, and the project completes itself — committed to GitHub, with the user being interrupted only when (a) a decision boundary is hit or (b) the project is done.

This is not a chat bot. This is not a code-gen wrapper. This is a **dev tool that owns a project end-to-end on the cloud**, using Anthropic's Managed Agent primitives (Goal, Agent Team, Agent View, Subagent, Memory, Webhooks) as the substrate.

**Success criteria** (testable):

1. Smoke project (markdown TOC generator) completes from `/pegasus start` to `done` with the user's laptop powered off for ≥ 4 hours of the build window.
2. Driver routine self-terminates when Goal is met (no manual cleanup).
3. User receives a mobile push notification within 5 minutes of completion.
4. Mid-project clarification (`questions/pending.md`) → user replies via `/pegasus tell` from mobile → next Driver tick incorporates the addendum and proceeds, with no laptop session re-opened.

**Non-goals (explicit):**

- ❌ A custom UI. Use Anthropic's Agent View. No web dashboard, no Electron app.
- ❌ A self-hosted runner (Fly, Render, Lambda). Anthropic Managed Agents only.
- ❌ A PR-gated workflow. Driver auto-merges to `main` (precedent: `museum-as-code`).
- ❌ Sub-hour tick cadence. Anthropic minimum is 1h; that's the contract.
- ❌ Multi-project routines or shared repos. One project = one repo = one routine.
- ❌ Reinventing interview, planning, or worker-loop skills. Reuse `deep-interview`, `prometheus`, `ralplan`, `ralph` / `worktree-parallel`.

---

## 2. The user workflow (original 2026-05-17 design, normative)

This is the workflow Junhyuk specified during the design session and never deviated from. The current Pegasus build is a literal implementation of these seven steps:

1. **사용자가 클로드 세션을 통해 프로젝트를 시작** — mobile or desktop, doesn't matter.
2. **리더 에이전트가 딥 인터뷰** — 20–30분, 거의 모든 측면. Reuses `deep-interview` / `prometheus` / `ralplan`.
3. **리더 에이전트가 전체 아키텍처/워크플로/task 모두 spec 단위로 변환** — written into the project repo's `spec/` and `workflow/`.
4. **리더 에이전트가 subagent를 병렬 호출, 각자에 맞는 spec 전달** — via **Agent Team** native primitive; Agent View exposes the tree.
5. **각 서브에이전트는 받은 spec을 ralph 루프로 끝까지 완료** — test-pass-or-loop discipline, one worker per task lane.
6. **리더가 서브에이전트와 소통, 종료까지 확인. 디버깅·추가 인터뷰 필요시에만 사용자 호출 (최대한 적게)** — `questions/pending.md` is the escalation channel; webhook pushes it to mobile only when truly stuck.
7. **프로젝트 완료시 사용자에게 알림 보고** — Anthropic webhook on `goal_met` → Claude mobile push.

Additional invariants from the same session:
- **사용자 컴퓨터가 꺼져도 동작** — baseline, not a feature.
- **루틴은 프로젝트당 1개**, named `[<project>] driver`.
- **완료시 routine 자동 삭제** (via Goal completion).
- **모바일 푸시 native** — no email/Telegram fallback in v1.

---

## 3. Architecture — five layers

```
┌──────────────────────────────────────────────────────────────────────────┐
│  L0 — User Terminal:  Claude Mobile App                                  │
│  • /pegasus start <name>          • Agent View로 진행 직접 모니터        │
│  • /pegasus tell <name> "..."     • Webhook 푸시로 완료 알림 수신       │
│  • /pegasus status / stop                                                │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │ in-session
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L1 — Leader (Claude Code session, ephemeral)                            │
│  • 딥 인터뷰 (deep-interview --standard / ralplan)                       │
│  • spec/architecture/plan 작성                                            │
│  • xodn348/<project> 부트스트랩                                          │
│  • Goal-bound Routine 등록 → 핸드오프 → 세션 종료 OK                     │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │ creates ONE routine
                     │ name = "[<project>] driver"
                     │ goal = "all plan.md tasks status=done"
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L2 — Driver Routine (cloud Managed Agent)                               │
│  • Goal-bound: tick마다 Anthropic이 success_check 자동 평가              │
│  • 충족 → routine 자동 종료 + webhook 푸시 + 대시보드에서 제거           │
│  • 미충족 → 다음 step 결정 → Agent Team launch                           │
│  • Memory (beta) 에 cross-tick 상태 유지                                 │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │ launches Agent Team per tick
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L3 — Agent Team (parallel subagents, native primitive)                  │
│  • Worker w1: spec/tasks/t1.md → ralph loop → subagent/w1 branch         │
│  • Worker w2: spec/tasks/t2.md → ralph loop → subagent/w2 branch         │
│  • Worker wN: ...                                                        │
│  • Agent View가 모바일에 트리 형태 실시간 노출                           │
│  • 워커 ≤ 3/tick (12분 wall-clock budget)                                │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │ all read/write
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  L4 — Shared State: GitHub xodn348/<project>                             │
│  spec/  workflow/plan.md  events.ndjson  subagents/<id>/  output/        │
│  questions/pending.md  done.md (legacy marker, Goal supersedes)          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Why each layer is where it is

| Layer | Could it move? | No, because… |
|-------|----------------|--------------|
| L0 Mobile | → desktop?   | Mobile is the *baseline* — desktop is incidental. Anything desktop-only kills the value prop. |
| L1 Leader | → cloud?     | Interviews are interactive. Routine has no human in the loop. Leader must be in-session. |
| L2 Driver | → local cron?| Local cron requires laptop on. Anthropic Routine = "computer off" satisfied. |
| L3 Team   | → manual `Task` calls? | Native Agent Team gives Agent View, Goal-aware termination, parallel safety for free. |
| L4 GitHub | → in-memory Anthropic Memory? | Memory is beta + private. GitHub is auditable, hand-editable, survives outages. Memory is *complementary*, not primary. |

---

## 4. Anthropic Managed Agent primitives — what we use and how

Anthropic shipped these between 2026-05-07 and 2026-05-08. Pegasus is designed around them, not against them.

| Primitive            | What it does                                              | Where it lands in Pegasus                                  |
|----------------------|-----------------------------------------------------------|------------------------------------------------------------|
| **Goal**             | Declarative `success_check`; routine auto-exits when met  | Replaces `done.md` polling. `goal = "all tasks done"`.    |
| **Agent Team**       | Native multi-agent orchestration (subagent tree)          | L3 worker dispatch. Driver declares the team per tick.    |
| **Agent View**       | Built-in tree UI for monitoring                           | Mobile monitoring. `/pegasus status` becomes the *backup*. |
| **Subagent**         | Worktree-isolated child agent (Task tool, generalized)    | Each Team member runs `ralph` mode in its own worktree.   |
| **Memory (beta)**    | Cross-session persistent memory per managed agent         | Driver's mental model across ticks (complements GitHub).   |
| **Webhooks**         | Push events (`goal_met`, `escalation`, `tick_complete`)   | Mobile push without polling. Step 7 of user workflow.     |
| **Dreaming**         | Self-improvement between sessions                         | **Skip in v1.** Re-evaluate after smoke test.             |

### Goal declaration — concrete

```yaml
# Registered with routine
routine:
  name: "[<project>] driver"
  schedule: "0 * * * *"          # hourly (Anthropic minimum)
  goal:
    description: "Complete every task in workflow/plan.md for xodn348/<project>"
    success_check: |
      gh api repos/xodn348/<project>/contents/workflow/state.json \
        | jq -r '.content' | base64 -d \
        | jq -e '.tasks | all(.status == "done")' >/dev/null
    timeout: "30d"               # escalate (not fail) after 30 days
  webhook:
    on_goal_met:           POST → user's Claude push subscription
    on_user_input_needed:  POST → same
    on_tick_error:         POST → same (after 3 consecutive failures)
  prompt_source: "xodn348/pegasus/claude/routines/leader-driver.md"
```

**Result:** No `done.md` polling. No manual routine cleanup. Anthropic does it natively.

### Agent Team declaration — concrete

```yaml
# Built by Driver each tick, after picking ready tasks
team:
  name: "<project>-workers-tick-${TICK}"
  members:
    - { id: w1, spec_path: "spec/tasks/t1.md", mode: ralph, branch: "subagent/w1" }
    - { id: w2, spec_path: "spec/tasks/t2.md", mode: ralph, branch: "subagent/w2" }
  view: true                     # surfaces in Agent View
  budget_minutes: 12
  on_complete: <integrate.sh>    # Driver fast-forwards subagent branches, verifies, pushes main
```

The `mode: ralph` flag instructs the worker to loop until its tests pass — the discipline lives in our `worktree-parallel.md` SOP, inlined into the worker prompt. No IP from external `ralph`.

---

## 5. Lifecycle — one project end to end

| Step | Where | What happens | Output committed |
|------|-------|--------------|------------------|
| 1 | L0 mobile | `/pegasus start gardener` | — |
| 2 | L1 Leader | 25-min deep interview | `spec/current.md`, `spec/interview-transcript.md` |
| 3 | L1 Leader | Architecture + plan synthesis | `workflow/plan.md`, `workflow/state.json`, `CLAUDE.md` |
| 4 | L1 Leader | Repo create + initial commit | repo `xodn348/gardener` initialized |
| 5 | L1 Leader | Routine register with Goal + Webhook + Team template | routine `[gardener] driver` enabled |
| 6 | L1 → L0 | "Handed off. Phone off OK." | (verbal) |
| 7 | L2 Driver (hourly) | Goal check → miss → pick ready tasks → launch Agent Team | `events.ndjson` += `tick_summary` |
| 8 | L3 Team | Each worker loops ralph mode in its worktree | branches `subagent/w*` |
| 9 | L2 Driver | Integrate worker branches → verify → push main | tasks status flips to `done` |
| 10 | L0 mobile | Anytime, optionally: Agent View, `/pegasus status`, `/pegasus tell` | — |
| 11 | L2 Driver | Goal met (all tasks done) | (Anthropic terminates routine) |
| 12 | L0 mobile | **Push notification** — "gardener complete" | — |
| 13 | repo | Lives forever as audit trail | — |

Hard guarantee: between step 6 and step 12, the user's laptop is unnecessary. Mobile-only viewing/responding is the only contact.

---

## 6. Decision boundaries (what the Driver may decide alone)

These are read at every Driver tick. If a decision falls outside, Driver writes `questions/pending.md` and sets `phase = awaiting_user`.

| Decision class                                  | Driver autonomous? |
|-------------------------------------------------|--------------------|
| Pick next ready task from `plan.md`             | ✅ yes             |
| Spawn ≤ 3 workers per tick                      | ✅ yes             |
| Integrate worker branch via fast-forward        | ✅ yes             |
| Integrate via 3-way merge with conflicts        | ❌ escalate        |
| Revert a worker merge after verify failure      | ✅ once; escalate on 2nd |
| Add a new task not present in original plan     | ❌ escalate        |
| Modify `spec/current.md` content (vs addendum)  | ❌ never           |
| Touch any file outside `/tmp/proj` (cloud cwd)  | ❌ never           |
| Push to `main`                                  | ✅ yes (auto-merge contract) |
| Force-push or rewrite history                   | ❌ never           |
| Delete subagent branches after merge            | ✅ yes (best-effort)|
| Modify routine config or Goal definition        | ❌ never           |
| Mark project `done` when Goal succeeds          | ✅ Anthropic-native |

These boundaries are inherited by every worker through the inbox template.

---

## 7. State contract (`workflow/state.json`)

```json
{
  "name": "<project>",
  "created_utc": "<iso8601>",
  "phase": "planning | executing | awaiting_user | done",
  "tasks": [
    {
      "id": "t1",
      "title": "...",
      "status": "pending | in_progress | done | blocked",
      "subagent_id": null,
      "depends_on": [],
      "spec_path": "spec/tasks/t1.md"
    }
  ],
  "tick_count": 0,
  "last_tick_utc": null,
  "completion_pct": 0,
  "routine_id": "<anthropic-routine-id>",
  "goal_id": "<anthropic-goal-id>"
}
```

The Goal `success_check` reads this file. Memory beta caches it across ticks for read perf; GitHub is authoritative for writes.

---

## 8. Bus contract (`events.ndjson`)

Append-only NDJSON, mirrored from `pegasus-os/claude/bus/SCHEMA.md`. Every state change emits at least one event.

Event kinds Pegasus emits:

```
project_init         — Leader bootstrap
user_tell            — addendum from mobile
question_raised      — Driver added to questions/pending.md
question_resolved    — addendum matched an open question
tick_summary         — one per Driver tick
subagent_dispatched  — Agent Team member launched
subagent_completed   — worker reported done + integrated
subagent_failed      — worker failed or stalled
integration_failed   — verify script failed; merge reverted
escalation           — phase flipped to awaiting_user
goal_met             — Anthropic webhook event recorded
pegasus_done         — terminal marker (legacy mirror of Goal)
pegasus_stopped      — user-initiated /pegasus stop
```

Anthropic Webhook deliveries are also persisted into this bus, so we have a single timeline even if the Anthropic console is unavailable.

---

## 9. Extraction from `pegasus-os` — what we reuse, what we skip

The earlier `xodn348/pegasus-os` project shipped a working bus + reflectors + SOPs + skills. We reuse aggressively; we do not reinvent.

### REUSE_VERBATIM (copy or symlink as-is)

- **`claude/bus/SCHEMA.md`** — event schema generalizes perfectly. Extend `kind` enum with Pegasus-specific kinds in §8 above.
- **`claude/CLAUDE.md` base principles** — Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution. Inherited by every Leader session and worker inbox.
- **`claude/reflectors/violation-rules.md` + `friction-rules.md`** — same shape; extend with new rules: "Decision Boundary violated without escalation," "Project scope drifted ≥ 3 lanes mid-run," "User re-interviewed during execution."

### REUSE_ADAPT (keep structure, retarget for project-leader context)

- **`claude/sops/parallel-subagents.md`** — copy; add a project-leader section noting parallel decomposition applies *within a single tick's worker fanout*, not across ticks.
- **`claude/sops/spec-seed.md`** — adopt the frozen-contract pattern. Rename `.spec/` → `spec/tasks/` to live inside each project repo. Keep Rules 1–4 (seed existence, schema, citations, freeze gate). Drop Rule 5's `/go` Stage 2 hook for v1.
- **`claude/sops/worktree-parallel.md`** — same; this is the discipline a worker reads when it spawns under Agent Team `mode: ralph`. Inline into worker inbox template.
- **`claude/skills/pegasus-init/SKILL.md`** — already the prototype for Pegasus Leader interview. Adopt the 3-stage structure (Intent / Boundary / Shape) and readiness gates. Re-target Stage 2 explicitly toward "Driver decision boundaries" (this PROJECT.md §6).

### REUSE_INSPIRE (pattern only, no file copy)

- **Cloud-primary Routine pattern** from `claude/ARCHITECTURE.md` — append-only bus + ephemeral runner + commit-only writes. Documented here in §3 and §8.
- **Reflector → proposal → auto-merge-or-PR pipeline** from `daily-self-improve.md` — applied to Pegasus's own self-improvement *later*, not v1.
- **iOS Shortcut entry pattern** from `claude/docs/ios-shortcut-setup.md` — used as inspiration for the v1.1 push-notification-back-to-mobile contract. v1 itself uses Claude mobile app's native `/pegasus` invocation.
- **Readiness gates as Boolean fields in spec** — pegasus-init's pattern of forcing decision boundaries into explicit checkboxes is mirrored in §6.

### SKIP (pegasus-os only, not applicable)

- `claude/routines/daily-self-improve.md` — pegasus-os-specific spec patching. Pegasus does this differently (Goal completion + reflectors on project events).
- `claude/routines/oss-contributor-prompt.md` — unrelated domain.
- `claude/routines/weekly-retro.md` — needs Pegasus event volume to mature first. Phase 2.
- `claude/kernel/hooks/*.sh` — Mac/launchd only. Cloud routine has no Stop hook.
- iTerm / tmux lifecycle SOPs — local terminal concerns, not cloud.

---

## 10. v1 milestone list (post-PROJECT.md)

Track these in `workflow/plan.md` once the project is bootstrapped *through itself*.

| #  | Task                                                                                     | Lane         |
|----|------------------------------------------------------------------------------------------|--------------|
| 1  | Rewrite `skills/pegasus/SKILL.md` to register Goal + Agent Team + Webhook (drop tick loop) | skill        |
| 2  | Shrink `claude/routines/leader-driver.md` to "Goal not met → launch Team → exit" (~30 lines) | routine    |
| 3  | Add `claude/teams/worker.yaml` — Agent Team member template with `mode: ralph`           | new file     |
| 4  | Add `claude/webhooks/handler.md` — how Anthropic webhook events map to mobile push + bus events | new file |
| 5  | Symlink/copy from pegasus-os: `bus/SCHEMA.md`, `reflectors/{violation,friction}-rules.md`, base principles | extraction |
| 6  | Adapt SOPs: `sops/parallel-subagents.md`, `sops/spec-seed.md`, `sops/worktree-parallel.md` | extraction  |
| 7  | Reflectors v0.1 — three Pegasus-specific violation rules from §9                         | reflectors   |
| 8  | Smoke test — `markdown-toc` project: bootstrap → 4h laptop-off → completion push        | end-to-end   |
| 9  | (Deferred) Webhook delivery format finalized once Anthropic docs settle                  | spec         |
| 10 | (Deferred) Dreaming integration once smoke test holds for 3 consecutive projects         | future       |

---

## 11. Diff vs. the 2026-05-19 stopgap impl

Junhyuk's read on yesterday's two-file commit (`c5ac133`) was correct: the 8-phase tick loop in `leader-driver.md` and the `done.md` marker logic in `SKILL.md` are *largely redundant* once Goal, Agent Team, and Webhooks are properly wired. Specifically:

| Topic                  | 2026-05-19 stopgap                  | This spec                                     | Action                                |
|------------------------|-------------------------------------|-----------------------------------------------|---------------------------------------|
| Termination            | `done.md` file + phase polling      | Anthropic Goal `success_check`                | Drop `done.md` writes from Driver. Leave file for hand-stop only. |
| Worker dispatch        | `Task` tool + `inbox.md` markdown   | Agent Team declaration                        | Driver becomes a thin Team-launcher.  |
| Monitoring             | `/pegasus status` ASCII             | Agent View (primary), status (backup)         | Keep status verb; demote to fallback. |
| Completion notification | "deferred" in README               | Anthropic Webhook → Claude mobile push        | Wire webhook in routine registration. |
| Routine cleanup         | Manual `enabled=false` on stop     | Goal-met auto-termination by Anthropic        | Drop the `schedule` disable call.     |
| Tick logic              | 8 phases × ~30 LOC each (~240 LOC) | "Goal not met → launch Team → exit" (~30 LOC) | Rewrite leader-driver.md, much shorter. |

**Decision**: Leave commit `c5ac133` in place as a checkpoint, but milestones 1–3 in §10 replace those files. The replacement should ship in a single commit so the diff is reviewable.

---

## 12. Anti-patterns (do not violate)

- ❌ **Polling for completion.** Goal + Webhook make polling pointless.
- ❌ **Custom UI work.** Agent View exists. Don't.
- ❌ **Reinventing interview/planning skills.** `deep-interview` / `prometheus` / `ralplan` are battle-tested.
- ❌ **Per-tick state file edits outside of `state.json` + `events.ndjson`.** Anything else is invisible to the Goal `success_check`.
- ❌ **Touching the user's laptop during cloud phases.** No syncing local clones, no launchd hooks. Cloud is canonical.
- ❌ **PRs for Driver self-changes.** Auto-merge to main per museum-as-code precedent. PRs are for human contributors only.
- ❌ **Modifying `spec/current.md` from the Driver.** Driver may only write to `workflow/state.json`, `events.ndjson`, `subagents/*`, `questions/*`, `output/*`. Spec is human-authored or addendum-extended only.

---

## 13. Open questions (must be resolved before v1 ships)

These are deliberately listed here rather than silently assumed. Resolve via `/pegasus tell` or in this file directly.

1. **Webhook delivery format** — Anthropic's webhook payload schema for `goal_met` and `user_input_needed`. Need to confirm Claude mobile push subscription is the right target, or whether we route through Gmail as a stopgap.
2. **Routine prompt size limits** — `leader-driver.md` is loaded inline via `cat`. Confirm Anthropic Routine prompt body length is sufficient (current draft ~6KB).
3. **Memory beta scope** — One Memory store per routine, or per project? Affects whether reusable patterns (e.g., "this user prefers SQLite over Postgres") leak across projects.
4. **Agent View permissions on private repos** — Confirm Agent View renders fully when underlying repo is private. If not, repo must be public *or* Agent View needs a token.
5. **30-day Goal timeout escalation** — On timeout, does Anthropic auto-fail or auto-archive? Affects whether we need our own timeout handler.

---

## 14. Footer

Project owner: Junhyuk (xodn348@tamu.edu).
Spec version: v1.0 — drafted 2026-05-19 from the original 2026-05-17 conversation, hardened with the post-2026-05-07 Anthropic Managed Agents primitives.
This file supersedes earlier README architecture sketches; the README remains the public-facing intro.
