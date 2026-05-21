---
name: pegasus
description: Pegasus project leader. Use when the user says $pegasus or /pegasus run|answer|tell|status|stop. Runs the local pegasus CLI and treats repo spec files as source of truth.
---

# Pegasus skill

Pegasus is a repo-local project leader.

## Rule

The repo spec is the source of truth:

- `spec/current.md`
- `spec/tasks/*.md`
- `spec/updates.md`
- `workflow/status.md`
- `workflow/questions.md`
- `workflow/agent-requests/*.md`
- `workflow/claude-routine.md`

Agents follow repo files over chat memory.

## How to handle user commands

When the user says `$pegasus run`, `/pegasus run`, or asks to start Pegasus through the Pegasus skill:

```bash
pegasus run . --goal "<user goal>"
pegasus status .
```

If status shows `Phase: needs_input`, ask the user exactly the open questions from `workflow/questions.md`.
Do not implement or delegate while `needs_input` is active.
Record the user's reply with:

```bash
pegasus answer . "<user answer>"
pegasus status .
```

When the user says `$pegasus answer ...` or `/pegasus answer ...`:

```bash
pegasus answer . "<user answer>"
pegasus status .
```

When the user says `$pegasus tell ...` or `/pegasus tell ...`:

```bash
pegasus tell . "<user instruction>"
```

When the user says `$pegasus status` or `/pegasus status`:

```bash
pegasus status .
```

When the user says `$pegasus stop` or `/pegasus stop`:

```bash
pegasus stop .
```

Ask only if the target repo or goal is missing. Prefer the current working directory as the repo.
