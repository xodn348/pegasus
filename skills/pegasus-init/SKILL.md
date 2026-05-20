---
name: pegasus-init
description: Deep Socratic interview that produces a Pegasus-driver-ready spec/current.md. Use when starting a new Pegasus project — invoked by `/pegasus start <name>`. Combines deep-interview rigor (intent-first, ambiguity-scored, pressure pass), ralplan consensus deliberation, prometheus scope-to-plan, and sisyphus decomposition.
adapted-from: xodn348/pegasus-os/claude/skills/pegasus-init/SKILL.md (PROJECT.md §8 ADAPT)
---

> ADAPTED from pegasus-os. Original wrote output to `~/code/pegasus-os/projects/<slug>/PROJECT.md` and ended with a `pegasus run` handoff line. Here output goes to `xodn348/<slug>/spec/current.md` (PROJECT.md "Source of truth = GitHub spec"), and handoff is `CronCreate` of the driver routine (per `skills/pegasus/SKILL.md`).

# Pegasus Leader Init — the Deep Interview

## Why this exists

The Pegasus driver will execute a project autonomously across many hourly ticks: decompose milestones into lanes, spawn workers via `Agent` fanout, run grader per tick, escalate edge cases via `PushNotification`. **The quality of every autonomous tick is bounded by the quality of the spec it inherits.** A vague `spec/current.md` = a vague autonomous execution = wasted token budget and re-asks.

This skill produces a `spec/current.md` so airtight that:
- The driver can decompose each milestone without re-asking the user.
- Decision boundaries are explicit — driver knows what to do alone vs escalate.
- Acceptance criteria are testable.
- Cost and scope ceilings are bounded.
- Pre-mortem risks have explicit mitigations.

Think of it as compressing 2 weeks of "wait, what about X?" mid-tick into 30 minutes of structured questioning up-front.

## When to use

Invoked by `/pegasus start <name>` (see `skills/pegasus/SKILL.md`).

- **Trigger phrases** the user will say: "pegasus 새 프로젝트", "/pegasus start <name>", "leader agent 만들어줘", "deep interview 해줘", "프로젝트 시작 인터뷰".
- **Do NOT use** if a complete `spec/current.md` already exists in `xodn348/<name>`. In that case the user wants execution or a `/pegasus tell`.
- **Do NOT use** for trivial tasks (single file edit, one-line fix). Just do the work directly.

## Stages

The interview runs in **three stages** with hard ordering:

```
Stage 1 — INTENT     (why, outcome, success, non-goals)         WEIGHT 50%
Stage 2 — BOUNDARY   (decision authority, cost, escalation)      WEIGHT 30%
Stage 3 — SHAPE      (decomposition hints, dependencies, risks)  WEIGHT 20%
```

The interview cannot crystallize until **both readiness gates** are explicit:
- ✅ Non-goals (what's deliberately OUT)
- ✅ Decision boundaries (what Pegasus driver may decide alone)

Even if total ambiguity drops below threshold, missing either gate keeps the interview going.

## Stage 1 — Intent (50%)

Six questions, asked one at a time. **Never batch.**

### 1. The real outcome
> "What's the actual end-state you want? Not the feature — the *change in your reality* once this ships. Concretely."

Probe for: behavior change, friction removed, metric moved. Not just "I want X built."

**Pressure pass**: after their answer, ask "if this shipped tomorrow but [some surface-level interpretation] turned out to be a different fix, would you still call it done?" Forces them to reveal the deeper intent.

### 2. Success criteria
> "How will you know it worked, in observable terms? Three signals at most."

Push for *testable* criteria. "It feels right" is not acceptable. "Bus event count drops below N" or "Morning brief includes X by Tuesday" or "I stop manually doing Y" — these are.

### 3. Smallest valuable slice
> "What's the smallest version that would still be worth shipping? If you got *only* that, would you be glad?"

If they say "everything matters" — pressure: "pretend you have 4 hours, not 2 weeks. What survives?"

### 4. Explicit non-goals (READINESS GATE 1)
> "What's deliberately OUT of scope? Three things you're choosing not to do, that someone might assume you'd want."

Cannot proceed without at least 2 explicit non-goals. If user says "nothing's out of scope," push: "then what would you *not* spend a week on, even if Pegasus offered?"

### 5. Time horizon
> "When does this need to be done — and what's the consequence if it slips a week?"

Captures hard deadlines vs soft preferences. Affects cost ceiling decisions.

### 6. Adjacent risk
> "What's the worst that happens if Pegasus driver runs this autonomously and gets something wrong? What's reversible vs not?"

Calibrates how risk-averse the driver should be. "It's just my side project" → high autonomy. "It's the production database migration" → very low autonomy.

## Stage 2 — Boundary (30%)

Five questions. This is the most novel part vs deep-interview/ralplan — the Pegasus driver is autonomous, so explicit authority calibration matters.

### 7. Decision boundaries (READINESS GATE 2)

Use a structured multi-select (Claude `AskUserQuestion`):
> "Pegasus driver may decide WITHOUT asking when it does any of these. Pick all that apply."

Options (default safe set per PROJECT.md §6, user toggles):
- ☐ Add new files within scope
- ☐ Modify existing files within scope
- ☐ Add new dependencies (npm/cargo/pip)
- ☐ Change existing dependencies' versions
- ☐ Modify CI / GitHub Actions
- ☐ Modify schema / API surface
- ☐ Delete files
- ☐ Push to main (fast-forward only)
- ☐ Open PRs (vs direct push)
- ☐ Auto-merge low-risk PRs
- ☐ Spend up to $X tokens
- ☐ Take up to Y hourly ticks before escalation

Anything NOT checked = must escalate via `questions/pending.md` + `PushNotification` and wait. Cannot proceed without explicit selection.

### 8. Cost ceiling
> "Maximum spend before Pegasus stops and asks: $X tokens, Y ticks, Z grader-needs-more-work iterations per milestone?"

Default suggestion (per PROJECT.md §6): 1회 revert · 3 needs_more_work consecutive · then escalate. Ask if user wants tighter or looser.

### 9. Escalation triggers
> "Other than the un-checked items above, what should the driver IMMEDIATELY escalate via `PushNotification`? (e.g., security warning, license mismatch, integration_failed twice...)"

Up to 5 triggers. Each becomes a 🔴 condition.

### 10. Verification standard
> "What counts as 'done' for each milestone? Tests pass? Build green? Type check? Specify what the grader subagent should require for `tick_satisfied`."

Calibrates strictness. A prototype milestone might require only type check; a production milestone requires full test suite + lint + manual smoke.

### 11. Communication cadence
> "How often should Pegasus push status? Per milestone completion / every N ticks / only on blockers / only at `pegasus_done`?"

Default: per milestone advance + on all blockers + on `pegasus_done`. User can adjust.

## Stage 3 — Shape (20%)

Four questions. Only after Stages 1-2 lock in.

### 12. Decomposition hint
> "Do you see natural milestones already? If yes, list them (each one will become a row in `workflow/plan.md` and a file in `spec/milestones/`). If no, the leader will decompose from Acceptance criteria."

If user provides milestones, validate they decompose cleanly into Acceptance items. If not, push back.

### 13. Dependencies
> "External dependencies the driver should know about? (services, APIs, data, libraries, accounts)"

Each one becomes a precondition. If any is unavailable, driver escalates instead of failing.

### 14. Pre-mortem (3 scenarios)
> "Imagine 3 ways this fails after the driver runs autonomously for a week. What are the 3 most likely failure modes — and what mitigation goes into `spec/current.md`?"

This is ralplan's --deliberate pre-mortem applied to autonomous execution. Each failure mode → a mitigation captured in the spec.

### 15. Done definition
> "What does `pegasus_done` look like? Which Acceptance items must all be `satisfied`? Any final integration test or smoke check?"

This is the driver's terminal condition, *self-described by the user*. When all listed items are satisfied per grader, driver fires `CronDelete` + `PushNotification "done"`.

## Pressure pass (mandatory)

Before crystallizing, revisit ONE earlier answer with a deeper follow-up:
- "You said X in Q3 — does that still hold given what you said in Q14?"
- "Q1 said the outcome was Y; Q15 says done means Z — is Z really sufficient for Y?"

The pressure pass surfaces hidden inconsistencies. If anything moves, update prior answers.

## Ambiguity scoring (visible to user each round)

Track 5 dimensions on `[0, 1]`. Score after each answer.

| Dimension | Weight | Question |
|---|---|---|
| Intent | 0.25 | Is the real outcome clear, not just the requested feature? |
| Outcome | 0.20 | Are success criteria testable? |
| Scope | 0.20 | Are non-goals explicit? |
| Authority | 0.20 | Are decision boundaries explicit? |
| Verification | 0.15 | Is "done" testable per milestone? |

`ambiguity = 1 - sum(score_i × weight_i)`

Target: **ambiguity ≤ 0.15** (Deep profile).

Show the table to user every round:

```
Round 4 | targeting: scope | ambiguity 0.42

  intent      0.85  ✓
  outcome     0.70  ✓
  scope       0.30  ← weakest, focusing here
  authority   0.50
  verification 0.40
```

## Crystallize → spec/current.md + spec/interview-transcript.md

When ambiguity ≤ 0.15 AND both readiness gates are met AND pressure pass is done:

Write to the cloned repo `xodn348/<name>/`:
- `spec/current.md` — final spec (template at `claude/templates/spec.md` if present, else free-form with required sections: Goal, Acceptance, Constraints, Non-goals, Decision boundaries, Cost ceiling, Escalation triggers, Verification, Cadence, Pre-mortem, Done definition).
- `spec/interview-transcript.md` — full transcript of Q&A (for traceability + future learning).
- `events.ndjson` — append `{"kind":"project_init","slug":"...","ambiguity":0.12,"rounds":N}`.

**No TODOs allowed in the final spec.**

Then push, register the driver cron via `CronCreate`, and tell the user (per `skills/pegasus/SKILL.md` step 6): "Driver routine `[<name>] driver` armed at hourly. Phone off OK."

## Anti-patterns

- ❌ **Asking implementation questions before intent is clear.** "Should we use TypeScript or Rust?" is irrelevant if the outcome isn't pinned.
- ❌ **Letting "I'll decide later" pass.** Every Stage 2 question must have a concrete answer or default — no deferred decisions.
- ❌ **Generating ACTION items just to fill the section.** If decomposition is genuinely "driver's call," say so explicitly in spec/current.md.
- ❌ **Skipping the pressure pass.** It's the single most valuable round — it catches contradictions the user didn't realize they had.
- ❌ **Letting ambiguity stall for 3+ rounds without changing direction.** Force Ontologist mode (re-frame at root cause level) once.
- ❌ **Writing spec/current.md with placeholders like "TBD" or "<fill in>".** Either get the answer or note explicitly: "User left undetermined; driver to decide."

## Final checklist

Before returning to the user:

- [ ] Both readiness gates explicit (Non-goals + Decision Boundaries)
- [ ] Ambiguity ≤ 0.15 across all dimensions, OR user accepted residual risk
- [ ] Pressure pass completed (one earlier answer revisited)
- [ ] At least one non-trivial assumption probed
- [ ] Pre-mortem has 3 distinct failure modes with mitigations
- [ ] spec/current.md fills every required section — no TBD / placeholders
- [ ] spec/interview-transcript.md saved
- [ ] events.ndjson `project_init` appended
- [ ] User shown the spec and asked to confirm before handoff

## Handoff

After confirmation, the caller (`skills/pegasus/SKILL.md`) handles `CronCreate` + final user message. Do NOT echo a `pegasus run` line — that was the pegasus-os pattern. Pegasus uses Claude Code Cron.

---

## Greenfield vs brownfield routing

If `<name>` already maps to an existing GitHub repo `xodn348/<name>`:
- Treat as **brownfield**.
- Before Stage 1, `git clone` the repo and run an `Explore` subagent to pre-load README, tree, recent commits, dependencies.
- Stage 3 Q14 (dependencies) becomes "what other modules in this repo will this touch?" — driver needs the conflict matrix from day one.

If `<name>` doesn't map to an existing repo:
- Treat as **greenfield**.
- Caller will `gh repo create xodn348/<name> --private` after crystallization.
- Stage 1 Q1 (outcome) doubly important — there's no existing code to ground the request.

## Resume

If interview interrupted: state lives in `spec/interview-transcript.md` (write incrementally, one round per append). Re-invoking `/pegasus start <name>` resumes from the last saved round.
