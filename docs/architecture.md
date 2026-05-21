# Architecture

Pegasus has one rule: the GitHub spec is the source of truth.

## Flow

1. `/pegasus run` starts or continues a project.
2. Pegasus writes the main spec in the GitHub repo.
3. If the goal is not actionable, Pegasus writes blocking questions to `workflow/questions.md` and sets `workflow/status.md` to `needs_input`.
4. `/pegasus answer` records the user's answer in repo files and resumes project preparation.
5. Pegasus splits actionable work into small task specs.
6. Claude routine agents work from those task specs.
7. Pegasus reviews the results and updates status.
8. Pegasus asks the user only when the spec does not authorize a decision.

## Repo files

```text
spec/current.md       # main project spec
spec/tasks/*.md       # one small spec per delegated task
spec/updates.md       # later user instructions
workflow/status.md    # current progress
workflow/questions.md # questions for the user
workflow/claude-routine.md # one Claude routine named after the project
workflow/agent-requests/*.md # Claude routine handoff packets
```

Agents follow these files over chat memory.
