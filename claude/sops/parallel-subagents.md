---
name: parallel-subagents
description: Pegasus leader, driver, and workers default to parallel `Agent`-tool fanout when a task has 2+ independent subtasks. Silent decision — never ask "should I parallelize?".
type: sop
adapted-from: xodn348/pegasus-os/claude/sops/parallel-subagents.md (PROJECT.md §8 ADAPT)
---

> ADAPTED from pegasus-os. Original was a host-side rule wired into the user's global `~/.claude/CLAUDE.md`. Here it's a Pegasus runtime rule: the leader, driver, and workers all default to parallel fanout when work decomposes into 2+ independent pieces.

## Rule

When the current actor (leader, driver, or worker) sees **2 or more independent subtasks**, it MUST fan out in a single message using the `Agent` tool — not sequence them. Independence test:

- File-disjoint: no two subtasks edit the same file.
- No ordering dependency: result of A is not an input to B.
- Independent verification: each can be checked on its own.

If any fail → sequence them.

## Why

Opus 4.7 by default is judicious about fanout. Pegasus needs the opposite: the driver tick budget is one cron firing per hour, and serializing 3 independent worker calls inside that tick wastes wall-clock. The user codified this preference on 2026-04-28: "각 탭에서 알아서 서브에이전트를 불러서 작업을 병렬로 했으면 좋겠어. 속도, 품질 모두 높이고." Pegasus inherits the same default.

## How — Pegasus actors

### Driver (`claude/routines/leader-driver.md`)

Every tick, after picking the current milestone:

1. Identify the workers needed (e.g., CTO for implementation, CFO for cost-check, CMO for messaging copy).
2. Emit them in **one assistant message**, each as a separate `Agent` tool call:
   ```
   Agent(subagent_type=..., prompt=<worker .md body> + spec context)
   Agent(subagent_type=..., prompt=...)
   Agent(subagent_type=..., prompt=...)
   ```
3. Cap **3 workers per fanout** (per PROJECT.md §3). Above 3 → split across ticks or chain via grader feedback.
4. After all workers return, dispatch a separate grader `Agent` call (single, not parallel — it depends on worker outputs).

### Workers (`workers/*.md`)

Workers have the `Agent` tool themselves (PROJECT.md §3). They may fan out to:
- `subagent_type=Explore` for read-only research.
- `subagent_type=general-purpose` for sub-implementations.
- Another worker `.md` body (peer-officer recursion, e.g., CTO asks CFO for budget approval).

Same independence test applies. **Cap 3 per call.** The driver expects one consolidated answer per worker, so workers integrate their nested fanout before returning.

### Leader (`/pegasus start`)

The interview is sequential by design (one question at a time — see `skills/pegasus-init/SKILL.md`). Fanout starts at repo bootstrap:

- `git init` + spec/state writes + initial push can sequence inside one `Bash`.
- Milestone rubric generation: if N milestones, fan out `Agent` calls (one per milestone, capped 3 per message) to write `spec/milestones/M<i>.md`.

## When NOT to fanout

- Single small diff (one file, < ~50 lines).
- Tightly coupled work — B depends on A's commit.
- Integration cost > speedup (rare; usually 3-way fanout pays even with merge friction).
- Cost ceiling reached for the current tick (see decision boundaries in PROJECT.md §6).

## Silent application

Per base principle #1 (Think Before Coding — `claude/PRINCIPLES.md`), surface **intent** ambiguity. The choice to parallelize is **execution strategy** after intent is clear — apply silently, don't ask the user.

This split is the only Karpathy-principle subtlety Pegasus inherits: requirements get surfaced, dispatch strategy gets executed.
