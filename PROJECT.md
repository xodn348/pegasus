# Pegasus — clean project-leader scaffold

## Purpose

Pegasus is a Claude Code project leader. It turns a project repository or slug
into a bounded autonomous workflow: read the spec, choose the next safe lane,
execute or delegate, verify, persist state, and ask the user only when a decision
boundary is reached.

## Non-goals

- No Anthropic API key integration.
- No Managed Agents API dependency.
- No custom UI.
- No force-push or destructive repository cleanup.
- No import of the old prototype's adapted `pegasus-os` files.

## Source of truth

A Pegasus-run project stores its truth in the project repository:

- `spec/current.md` — approved user intent and acceptance criteria.
- `spec/addenda.md` — user updates after start.
- `workflow/state.json` — phase, current lane, tick count, routine id.
- `workflow/events.ndjson` — project lifecycle events.
- `workflow/questions.md` — unresolved user questions.

If a prompt summary conflicts with these files, the files win.

## Lifecycle

1. User prepares or approves `spec/current.md`.
2. `/pegasus start <repo-or-slug>` validates the spec and initializes workflow
   state.
3. The driver reads state every run and picks at most three independent lanes.
4. Workers may assist, but the driver owns integration and verification.
5. `/pegasus tell <repo-or-slug> "..."` appends addenda for the next run.
6. `/pegasus stop <repo-or-slug>` stops without destructive cleanup.
7. Completion requires fresh verification evidence and a final event.

## Decision boundaries

Autonomous by default:

- read project files;
- create or edit in-scope files;
- run documented tests;
- commit local changes on a project branch when the project spec allows it;
- ask a bounded worker for implementation, verification, or risk review.

Escalate before:

- force-push or history rewrite;
- repository deletion or archive changes;
- dependency or CI changes;
- schema/API surface changes;
- marking done when verification is missing or ambiguous;
- any action outside the project spec.

## Acceptance criteria for this repo

- [ ] Clean standalone scaffold exists.
- [ ] Provenance policy is explicit.
- [ ] Skill, driver prompt, worker prompts, schema, and example state are present.
- [ ] Validation proves no wholesale file import from the previous prototype.
