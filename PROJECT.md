# Pegasus

Pegasus is a project leader for agent work.

The user starts a project with `/pegasus run`. Pegasus writes a clear spec in the GitHub repo, splits the work into smaller specs, sends those specs to Claude routine agents, checks the results, and reports back when the work is verified.

## Workflow

1. User runs `/pegasus run`.
2. Pegasus writes the project spec into the GitHub repo.
3. If the goal is not actionable, Pegasus writes blocking questions to `workflow/questions.md` and sets status to `needs_input`.
4. User answers with `/pegasus answer`.
5. Pegasus records the answer in repo files and continues only after blockers are resolved.
6. Pegasus splits the project into smaller task specs.
7. Pegasus attempts to start or verifies one Claude routine named after the project.
8. Claude routine agents work from those specs.
9. The GitHub spec is the source of truth for every agent.
10. Pegasus collects the results and verifies them.
11. Pegasus asks the user only for big decisions or risky changes.
12. Pegasus reports completion with evidence.

## Commands

- `/pegasus run` — start or continue a project
- `/pegasus answer` — answer blocking questions
- `/pegasus tell` — add instructions
- `/pegasus status` — check progress
- `/pegasus stop` — stop the project

## Source of truth

The GitHub repo contains the truth for the project.

Minimum files:

- `spec/current.md` — goal, scope, non-goals, acceptance criteria
- `spec/tasks/*.md` — small specs assigned to agents
- `spec/updates.md` — later user instructions
- `workflow/status.md` — current progress
- `workflow/questions.md` — questions for the user
- `workflow/claude-routine.md` — one Claude routine named after the project
- `workflow/agent-requests/*.md` — Claude routine handoff packets

Agents must follow the repo spec over chat history or memory.

## Rules

- Keep only one active Pegasus repo: `pegasus`.
- Do not merge this with `pegasus-os`.
- Avoid vendor lock-in.
- Support Claude routine work.
- One project has one Claude routine.
- The Claude routine name is the project name.
- Delete the Claude routine record only after exact absence is verified.
- Delegate by spec, not by vague chat instructions.
- Use the deep-digger agent when an LLM discussion expands sideways and one thread must be followed to a decision, contradiction, experiment, or blocking question.
- MIT/permissive sources are allowed when provenance is clear.
- GPL, SUL, custom, or restrictive sources require review first.
- Do not copy old prototype code or unclear generated output.
- Do not claim Claude routine work is running unless `claude agents --json` verifies the exact project name and repo path.

## Current goal

Reset the repo to a simple, clean public OSS base.
Then rebuild Pegasus around `/pegasus run`, GitHub specs, Claude routine agents, and spec-based delegation.
