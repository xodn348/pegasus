# Pegasus — autonomous project leader workflow

## Purpose

Pegasus is a Claude Code project leader. The target workflow is:

> user starts a project from phone or laptop → Pegasus interviews once → writes a
> project spec and workflow state → arms a repeatable driver routine → the laptop
> may go offline → the driver continues from GitHub-backed state → Pegasus asks
> only for real decision boundaries or final completion.

This repository is a clean rewrite of that workflow. It keeps the intended
product behavior while avoiding wholesale imports from the older prototype or
from `pegasus-os`.

## Success criteria

- `/pegasus start <name>` creates or validates a project repo, writes spec/state,
  and either arms a verified background routine or prints the exact manual step
  when the current runtime cannot arm one.
- The driver can resume from repository files alone after a fresh session.
- Each run chooses bounded work, may fan out to workers, verifies results, and
  persists events/state.
- `/pegasus tell <name> "..."` appends user updates that the next driver run
  must read.
- `/pegasus status <name>` reports phase, progress, last evidence, and pending
  questions.
- `/pegasus stop <name>` stops the workflow without destructive cleanup.
- Completion requires fresh verification evidence and a final user notification
  when a notification surface is available.

## Non-goals

- No Anthropic API key integration.
- No Managed Agents API dependency.
- No custom UI.
- No force-push or destructive repository cleanup.
- No import of the old prototype's adapted `pegasus-os` files.
- No fake background execution: if routine registration is unavailable, say so.

## Source of truth

A Pegasus-run project stores durable truth in the project repository:

- `spec/current.md` — approved user intent, scope, authority, and acceptance
  criteria.
- `spec/milestones/*.md` — optional milestone rubrics for grader checks.
- `spec/addenda.md` — user updates after start.
- `workflow/state.json` — phase, current lane/milestone, tick count, routine id,
  failure counts, last tick timestamp.
- `workflow/events.ndjson` — project lifecycle events.
- `workflow/questions.md` — unresolved user questions.

If a prompt summary conflicts with these files, the files win.

## Canonical lifecycle

1. **Start** — `/pegasus start <name>` receives a name or target repo.
2. **Interview/spec** — If no approved spec exists, Pegasus runs the interview
   path and writes `spec/current.md`. If a spec already exists, it validates it.
3. **Bootstrap** — Pegasus initializes `workflow/state.json`,
   `workflow/events.ndjson`, `spec/addenda.md`, and `workflow/questions.md`.
4. **Routine handoff** — Pegasus registers the driver routine only through a
   verified Claude Code routine surface. If unavailable, it reports the manual
   command; it must not claim laptop-off operation is armed.
5. **Driver tick** — Each driver run starts fresh, reloads project files, folds in
   addenda, picks ready work, and appends `tick_started`.
6. **Fanout** — The driver may dispatch up to three independent workers when work
   is file-disjoint, unordered, and independently verifiable.
7. **Integration** — The driver integrates worker output and owns the project
   working tree. Workers do not push or mark work done.
8. **Verification/grading** — Verification named in the spec runs first. For
   milestone work, a grader pass may compare evidence against the milestone
   rubric before state advances.
9. **Persist** — The driver updates state, appends events, and commits/pushes only
   when the project spec grants that authority.
10. **Escalate or complete** — Boundary crossings write `workflow/questions.md`,
    set `phase: awaiting_user`, and notify if possible. Completion writes
    `project_done` and notifies if possible.

## Decision boundaries

Autonomous by default when the spec allows the target files and scope:

- read project files;
- create or edit in-scope files;
- run documented tests and checks;
- ask bounded workers for implementation, verification, or risk review;
- commit or push only if the project spec grants that authority.

Escalate before:

- force-push or history rewrite;
- repository deletion or archive changes;
- dependency or CI changes;
- schema/API surface changes;
- changing `spec/current.md` after approval except through explicit user-approved
  revision;
- marking done when verification is missing or ambiguous;
- any action outside the project spec.

## Driver phases

1. `load_state`
2. `fold_addenda`
3. `pick_work`
4. `fanout_workers`
5. `integrate`
6. `verify`
7. `grade`
8. `persist`
9. `notify_or_escalate`

## Acceptance criteria for this repo

- [x] Clean standalone scaffold exists.
- [x] Provenance policy is explicit.
- [x] Skill, driver prompt, worker prompts, schema, and example state are present.
- [x] The intended autonomous workflow is documented without wholesale file import
  from the previous prototype.
- [ ] Live Claude Code routine registration is verified.
- [ ] The `/pegasus` verbs have executable tests or dry-run harnesses.
