---
description: Run Pegasus project leadership in the current repo.
argument-hint: "run|answer|tell|status|stop [args]"
allowed-tools: Bash(pegasus:*), Bash(python3 -m pegasus:*)
---

# /pegasus

Pegasus is a repo-local project leader. It writes project specs and workflow files into the current GitHub repo.

Argument: `$ARGUMENTS`

## Rules

- Use the current working directory as the repo unless the user gives another path.
- The repo spec is the source of truth: `spec/current.md`, `spec/tasks/*.md`, `spec/updates.md`, and `workflow/*.md`.
- If `pegasus status` shows `Phase: needs_input`, ask exactly the questions from `workflow/questions.md` and record the reply with `pegasus answer`.
- Do not implement or delegate while `needs_input` is active.
- Do not claim Claude routine work is running unless Pegasus reports `registered`.

## Execute

If `$ARGUMENTS` starts with `run`, `answer`, `tell`, `status`, or `stop`, run:

```bash
pegasus $ARGUMENTS
```

If `$ARGUMENTS` is empty, run:

```bash
pegasus status .
```

If `$ARGUMENTS` is a plain project goal, run:

```bash
pegasus run . --goal "$ARGUMENTS"
```

Then summarize the result briefly and point to the changed `spec/` and `workflow/` files.
