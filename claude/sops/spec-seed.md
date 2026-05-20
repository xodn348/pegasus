---
name: spec-seed
description: For Pegasus multi-worker dispatches (N≥2), lock the per-task spec as `spec/<task>/seed.md` in the project repo before fanout. Single shared truth file prevents worker drift. Adds Stage 2 intent-check to `/go` ship gate.
type: sop
adapted-from: xodn348/pegasus-os/claude/sops/spec-seed.md (PROJECT.md §8 ADAPT)
---

> ADAPTED from pegasus-os. Original placed seed.md under `<project>/.spec/<task>/`. Here it lives under the **GitHub spec source of truth** — `xodn348/<project>/spec/<task>/seed.md` — so every Driver tick re-reads it from the cloned repo. Spec wins over Driver-paraphrased "context" (PROJECT.md §3).

User intent: absorb the load-bearing concepts from Q00/ouroboros (a spec-first agent OS) into Pegasus without installing it.

**Why:** When the driver fans out N workers, each silently encodes a slightly different reading of the spec unless they all read the same seed file. `manifest.json` / `workflow/state.json` are state, not spec. Per-worker `Agent` prompts are assignment, not spec. `seed.md` fills the gap.

## How to apply

### Rule 1 — seed.md exists when N≥2 workers in one tick

For any tick that dispatches **2 or more workers** via `Agent` fanout, the driver creates (or reads, if pre-existing):

```
xodn348/<project>/spec/<YYYY-MM-DD>-<slug>/seed.md
```

For N=1 ticks: opt-in. Write seed.md if the milestone is large or domain-rich (entity 3+, multi-tick). Skip for one-line fixes. Don't impose ceremony on solo small work.

### Rule 2 — Minimum schema

**Required sections:**
- `## Goal` — one sentence, why we're doing this
- `## Acceptance` — checklist of "done" conditions (these are what `/go` Stage 2 evaluates against, AND what the grader subagent reads as rubric)

**Conditional sections** (include only if non-empty):
- `## Constraints` — hard non-negotiables, what we can't do
- `## Ontology` — entities + relations (only when domain has 2+ new or modified entities)
- `## Out of scope` — explicit anti-list (when scope creep is a real risk)

**No status frontmatter, no exit_conditions, no evolve metadata.** Git history IS the lifecycle. If requirements change → edit + commit. Workers re-read on next cycle (next tick = fresh Claude session = fresh clone).

### Rule 3 — Workers cite seed-ref, no spec duplication

When the driver writes per-worker `Agent` prompts:

- Every prompt MUST include `seed-ref: spec/<task>/seed.md` in its first line.
- Prompts contain ONLY the worker's actions and local verification — NOT entity definitions or spec content.
- If a worker discovers something not in the seed (new entity, missing constraint), they MUST report to the driver via their `Agent` return (not silently encode). Driver either updates seed (commit + workers re-read next tick) or rejects.

**Forbidden:** copy-pasting "Tag has fields x, y, z" into 4 different worker prompts. That defeats the entire mechanism — that's the drift it was supposed to prevent.

### Rule 4 — Freeze gate: forced enumeration of alternative interpretations

Before committing seed.md as the working contract, the leader (during `/pegasus start`) OR the driver (when crystallizing a new milestone seed) writes at least 2 alternative readings of the goal in seed.md:

```markdown
## Alternative interpretations considered
1. [reading A]
2. [reading B]
3. [reading C, if applicable]

Convergence: All reduce to [chosen reading] because [reason].
OR
Divergence: 1 and 2 differ on [specific point]. Need clarification before proceeding.
```

If divergent → write `questions/pending.md` + `PushNotification` (per PROJECT.md §6); don't freeze. If convergent → freeze (= commit seed.md and proceed to fanout).

This replaces Ouroboros's LLM-scored ambiguity gate (`bigbang/ambiguity.py`) with a forced-enumeration discipline. No extra LLM call needed; same cognitive work.

### Rule 5 — Grader gets a Stage 2 (intent vs code) check

The driver-side grader (PROJECT.md §5) already does mechanical rubric check. Add Stage 2:

> **Stage 2 — Intent check:** Grader reads `spec/<task>/seed.md > Acceptance` AND the worker diff. For each acceptance item, decides:
>
> 1. Did the diff actually achieve this item, or just satisfy a mechanical check?
> 2. Is there evidence of reward hacking — test mutated to fit code, edge cases skipped, mocks replacing real impl, happy path only?
>
> Output `satisfied / needs_more_work / failed` per item with one-sentence justification.

If any "needs_more_work" or "failed" → tick verdict is non-satisfied. Driver advances to next tick with the seed as-is. Either next tick fixes it or the milestone gets `phase=awaiting_user` after N retries (per PROJECT.md §6: "1회 revert" autonomous, "2회째 revert" escalates).

This is the single most unique borrow from Ouroboros (`evaluation/semantic.py`).

### Rule 6 — Sourcing seed.md from `/pegasus start`

After the deep interview (`skills/pegasus-init/`) produces `spec/current.md`:

```
1. Driver, on first tick, reads spec/current.md > Acceptance.
2. For each Acceptance line that decomposes into N≥2 worker tasks: create spec/<milestone>/seed.md
3. Add the Alternative interpretations block (Rule 4).
4. git add + commit + push.
5. Then dispatch via Agent fanout (workers see seed-ref).
```

## Worked example — Pegasus context

Milestone: "Tag support in Tasks." Workers: CTO (impl) / COO (migration) / grader (verification) — N=3 → seed mandatory.

`xodn348/myproject/spec/2026-05-08-task-tagging/seed.md`:

```markdown
## Goal
CLI에서 task에 tag 붙이고, tag로 필터·검색할 수 있게 한다.

## Acceptance
- [ ] `task add --tag X` 동작
- [ ] `task list --tag X` 필터 동작
- [ ] DB migration up/down 무손실
- [ ] Tag 삭제 시 cascade 통합 테스트 통과
- [ ] 기존 tagless task 검색 호환 유지

## Constraints
- Tag.label은 unique per project
- 한 task당 tag 최대 10개
- migration은 idempotent

## Ontology
- Tag: { id, label, color }
- Task: 기존 + tags: [Tag] (N:M)
- 관계: Task ↔ Tag, Tag 삭제 시 task_tags row cascade

## Out of scope
- Tag 권한/공유
- 색상 자동 추천
- Task 외 entity의 tag → 다음 milestone

## Alternative interpretations considered
1. tag = string array 직접 → 검색·리네임·삭제 비효율, 거부
2. tag = 별도 엔티티 + Task와 N:M (현재 안) → 채택
3. tag = 별도 엔티티 + project에 1:N → cross-project 공유 안 됨, 다음 라운드

Convergence: 2번 채택. project-scoped + 별도 엔티티가 검색·리네임·cascade 모두 자연스럽다.
```

Driver's CTO worker `Agent` prompt (truncated):

```
seed-ref: spec/2026-05-08-task-tagging/seed.md
scope: CLI 인터페이스 (--tag 플래그 add/list/filter)
verify: cli tests pass + Acceptance 첫 두 항목 데모
<+ CTO system prompt body from workers/cto.md>
```

Worker mid-work discovers "Tag.description 필드 있으면 좋겠다" → returns drift report instead of silently coding. Driver next-tick judgment: update seed.md or reject.

Grader Stage 2 LLM check: 5 Acceptance items vs diff → "각 항목이 실제 동작 / 테스트만 통과 / reward hacking?". 모두 satisfied → milestone advances.

## Why this design — Ouroboros benchmark summary

Source-level analysis of Q00/ouroboros (2026-05-08, src lines verified):

**Absorbed (load-bearing):**
- seed-as-immutable-contract — `core/seed.py`
- Stage 2 semantic check — `evaluation/semantic.py` (anti-gaming + reward_hacking_risk)
- Forced ambiguity gate — concept from `bigbang/ambiguity.py`; we use forced enumeration
- Drift-via-pattern principle — `verification/verifier.py`

**Skipped:**
- Stage 1 mechanical — driver grader already does
- Stage 3 multi-model consensus — out of scope (single-grader for v1)
- Evolve state machine — would conflict with driver tick lifecycle
- EventStore + LineageProjector — we have `events.ndjson`
- Project-level regex drift — revisit if drift problems actually appear

**Simplified:**
- LLM-scored ambiguity (4-component weighted clarity) → forced enumeration
- 8-field schema → 2 mandatory + 3 conditional
- status: draft|frozen → just git diff

Net: load-bearing 60% of Ouroboros's value with zero new dependencies.

## Pilot validation

Before declaring this SOP stable for Pegasus, run **one real milestone end-to-end** through it. Pre-commit win/lose criteria to `spec/<task>/pilot-rules.md` BEFORE starting:

- **win:** seed.md drafting < 15min ; worker drift caught at least once via Agent return ; spec re-explanation count = 0 across tick boundary ; grader Stage 2 catches at least one real issue OR confidently passes
- **lose:** seed drafting > 30min ; workers ignore or duplicate seed ; Stage 2 always rubber-stamps without finding anything ; SOP feels like ceremony

Honest retro after one milestone. If lose conditions hit, revise SOP before propagating.
