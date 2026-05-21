# Pegasus

Pegasus turns a project request into spec-driven Claude routine work.

## Install

One-line install:

```sh
curl -fsSL https://raw.githubusercontent.com/xodn348/pegasus/refs/heads/main/scripts/install.sh | sh
```

This installs everything Pegasus needs:

- `pegasus` CLI
- Codex skill: `~/.codex/skills/pegasus/SKILL.md`
- Claude Code slash command: `~/.claude/commands/pegasus.md`

If `pegasus` is not found after install, add this to your shell profile:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Agent-safe install if your runtime blocks `curl | sh`:

```sh
python3 -m pip install --user --upgrade "git+https://github.com/xodn348/pegasus.git" && python3 -m pegasus install-integrations
```

Requirements:

- Python 3.11+
- `curl` and `tar` for the one-line installer
- `git` for the agent-safe installer
- Claude CLI only if you want Claude routine verification

## Quick start

Run Pegasus inside an existing GitHub repo checkout:

```sh
pegasus run . --goal "Ship the next feature"
pegasus status .
```

If Pegasus needs a decision before it can delegate, status shows `Phase: needs_input`
and lists questions from `workflow/questions.md`. Answer them from the repo:

```sh
pegasus answer . "Ship a CLI that writes project specs and delegates one task."
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

After install, both agent apps can use Pegasus from a repo:

Codex:

```text
$pegasus run . --goal "Ship the next feature"
```

You can also use:

```text
/pegasus run . --goal "Ship the next feature"
```

Claude Code:

```text
/pegasus run . --goal "Ship the next feature"
```

## What Pegasus does

1. Writes the project spec in the repo.
2. Writes blocking questions and `Phase: needs_input` when the goal is not actionable.
3. Records answers back into repo files.
4. Splits actionable work into smaller task specs.
5. Writes Claude routine request files for those task specs.
6. Uses a deep-digger agent when LLM discussion needs one thread followed to ground.
7. Attempts to start or verifies one Claude routine for the project.
8. Reports progress from repo files.

## Deep digger agent

`agents/project-agents/deep-digger.md` is for discussions that keep expanding sideways. It picks one unresolved thread and digs until it reaches a decision, contradiction, next experiment, or one blocking question.

## Commands

- `pegasus run <repo> --goal "..."` — start or continue
- `pegasus answer <repo> "..."` — answer blocking questions
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
python -m pegasus run ./my-project --goal "Improve it"
python -m pegasus answer ./my-project "Build a small CLI that writes project specs."
python -m pegasus tell ./my-project "Add this requirement"
python -m pegasus status ./my-project
python -m pegasus stop ./my-project
```
