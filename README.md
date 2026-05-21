# Pegasus

Pegasus turns a project request into spec-driven Claude routine work.

## Install

One-line installer:

```sh
curl -fsSL https://raw.githubusercontent.com/xodn348/pegasus/main/scripts/install.sh | sh
```

If `pegasus` is not found after install, add this to your shell profile:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Requirements:

- Python 3.11+
- `curl` and `tar` for the one-line installer
- Claude CLI only if you want Claude routine verification

## Quick start

Run Pegasus inside an existing GitHub repo checkout:

```sh
pegasus run . --goal "Ship the next feature"
pegasus status .
```

Add later instructions:

```sh
pegasus tell . "Use the GitHub spec as the source of truth."
pegasus status .
```

Stop the project:

```sh
pegasus stop .
```

## What Pegasus does

1. Writes the project spec in the repo.
2. Splits work into smaller task specs.
3. Writes Claude routine request files for those task specs.
4. Attempts to start or verifies one Claude routine for the project.
5. Reports progress from repo files.

## Commands

- `pegasus run <repo> --goal "..."` — start or continue
- `pegasus tell <repo> "..."` — add instructions
- `pegasus status <repo>` — check progress
- `pegasus stop <repo>` — stop

## Source of truth

The repo spec is the source of truth:

- `spec/current.md` — goal, scope, non-goals, acceptance criteria
- `spec/tasks/*.md` — task specs assigned to agents
- `spec/updates.md` — later user instructions
- `workflow/status.md` — current progress
- `workflow/questions.md` — questions for the user
- `workflow/claude-routine.md` — one Claude routine named after the project
- `workflow/agent-requests/*.md` — Claude routine handoff packets

Agents follow the repo spec, not chat memory.

## Claude routine rule

Each project gets one Claude routine named after the project.
Pegasus only marks it `registered` after `claude agents --json` verifies the exact project name and repo path.
If Claude cannot safely create or verify it, Pegasus keeps `pending_start` instead of pretending it is running.

## Developer dry-run

```sh
python -m pegasus run ./my-project --goal "Build the thing"
python -m pegasus tell ./my-project "Add this requirement"
python -m pegasus status ./my-project
python -m pegasus stop ./my-project
```
