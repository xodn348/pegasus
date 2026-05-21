# Architecture

Pegasus has one rule: the GitHub spec is the source of truth.

## Flow

1. `/pegasus run` starts or continues a project.
2. Pegasus writes the main spec in the GitHub repo.
3. Pegasus splits the work into small task specs.
4. Claude routine agents work from those task specs.
5. Pegasus reviews the results and updates status.
6. Pegasus asks the user only when the spec does not authorize a decision.

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
