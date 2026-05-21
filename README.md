# Pegasus

Pegasus turns a project request into spec-driven Claude routine work.

## Install

Recommended one-line install for agents and guarded runtimes:

```sh
python3 -m pip install --user --upgrade "git+https://github.com/xodn348/pegasus.git" && python3 -m pegasus install-integrations
```

This installs:

- `pegasus` CLI
- Codex skill: `~/.codex/skills/pegasus/SKILL.md`
- Claude Code slash command: `~/.claude/commands/pegasus.md`

It avoids the `curl | sh` / download-then-run pattern that many automatic safety classifiers block because it executes an external GitHub script directly.

If `pegasus` is not found after install, add this to your shell profile:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Isolated venv install:

```sh
git clone https://github.com/xodn348/pegasus.git ~/.local/share/pegasus/src
python3 -m venv ~/.local/share/pegasus/venv
~/.local/share/pegasus/venv/bin/python -m pip install --upgrade ~/.local/share/pegasus/src
mkdir -p ~/.local/bin
ln -sf ~/.local/share/pegasus/venv/bin/pegasus ~/.local/bin/pegasus
~/.local/bin/pegasus install-integrations
```

Optional script installer for interactive human terminals. This also installs the Codex skill and Claude Code command:

```sh
curl -fsSL https://raw.githubusercontent.com/xodn348/pegasus/refs/heads/main/scripts/install.sh | sh
```

Requirements:

- Python 3.11+
- `git` for the recommended install
- Codex and/or Claude Code if you want the `/pegasus` agent command surfaces
- `curl` and `tar` only for the optional script installer
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

## Agent commands

After `pegasus install-integrations`, both agent apps can use Pegasus from a repo:

Codex:

```text
pegasus run . --goal "Ship the next feature"
```

Claude Code:

```text
/pegasus run . --goal "Ship the next feature"
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
