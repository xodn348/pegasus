---
name: pegasus
description: Pegasus project leader. Use for /pegasus run|tell|status|stop with a GitHub repo spec as the source of truth.
---

# Pegasus skill

## Rule

The GitHub repo spec is the source of truth.

## `/pegasus run <repo-or-idea>`

Start or continue a project.

1. Find or create the GitHub repo.
2. Ask only the questions needed to write `spec/current.md`.
3. Write or update the repo spec.
4. Split work into `spec/tasks/*.md`.
5. Delegate task specs to cloud agents.
6. Review results and update `workflow/status.md`.
7. Ask the user only for big decisions or risky changes.

## `/pegasus tell <repo> "..."`

Append the user's new instruction to `spec/updates.md`.

## `/pegasus status <repo>`

Read the repo spec and `workflow/status.md`, then report progress simply.

## `/pegasus stop <repo>`

Mark the project stopped in `workflow/status.md`. Do not delete repo data.
