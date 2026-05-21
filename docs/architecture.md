# Architecture

Pegasus has five layers.

```text
L0 User command       /pegasus start|tell|status|stop
L1 Leader skill       interview/spec validation, bootstrap, status, stop
L2 Driver routine     repeatable run prompt, stateless except project files
L3 Workers            optional builder/verifier/risk-review prompts
L4 Project repo       spec/current.md, workflow/state.json, events.ndjson
```

## State model

The project repository is the only durable runtime state. The driver may be a
fresh Claude Code session each run, so it must reload files before making any
choice.

Required files after start:

```text
spec/current.md
spec/addenda.md
workflow/state.json
workflow/events.ndjson
workflow/questions.md
```

Optional milestone rubrics live in `spec/milestones/*.md`.

## Start and handoff model

`/pegasus start` has two valid paths:

1. **Spec exists** — validate `spec/current.md`, initialize workflow state, and
   hand off to the driver.
2. **Spec missing** — run the interview/spec creation path first, then initialize
   workflow state.

Routine registration is not assumed. Pegasus may arm a background routine only
when the current Claude Code runtime confirms the routine id or equivalent
handle. Otherwise it reports the exact manual driver command.

## Driver run model

Each driver run follows the same phase order:

1. Load project state and approved spec.
2. Fold in addenda newer than `last_tick_utc`.
3. If awaiting user, check whether addenda resolves the question.
4. Pick the smallest ready lane or milestone.
5. Fan out at most three independent workers when useful.
6. Integrate results in the driver-owned working tree.
7. Run verification and optional grader review.
8. Persist state and append lifecycle events.
9. Notify, escalate, or stop.

## Worker model

Workers are optional. They are small role prompts for:

- building a lane;
- verifying a lane;
- reviewing risk/provenance/destructive actions.

Workers do not push or mark work done. They return evidence to the driver.

## Verification model

A lane is done only when the verification command or checklist named in the spec
passes and the driver records the evidence in `workflow/events.ndjson`. A
milestone may additionally require a grader check against `spec/milestones/*.md`.

## Notification model

Pegasus can notify on escalation or completion only through a verified available
surface. If no notification tool is available, it records the event and reports
that notification was not sent.

## Hard bans

- no force-push;
- no repository deletion;
- no dependency or CI change without explicit authority;
- no done state without fresh verification evidence;
- no fake claim that a routine or notification was armed.
