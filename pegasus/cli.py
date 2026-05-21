from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import signal
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

TASK_RE = re.compile(r"[^a-z0-9]+")
CLAUDE_AGENT_TIMEOUT_SECONDS = 5
CLAUDE_CREATE_TIMEOUT_SECONDS = 15



CODEX_SKILL = """---
name: pegasus
description: Pegasus project leader. Use when the user says $pegasus or /pegasus run|tell|status|stop. Runs the local pegasus CLI and treats repo spec files as source of truth.
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
"""

CLAUDE_COMMAND = """---
description: Run Pegasus project leadership in the current repo.
argument-hint: "run|tell|status|stop [args]"
allowed-tools: Bash(pegasus:*), Bash(python3 -m pegasus:*)
---

# /pegasus

Pegasus is a repo-local project leader. It writes project specs and workflow files into the current GitHub repo.

Argument: `$ARGUMENTS`

## Rules

- Use the current working directory as the repo unless the user gives another path.
- The repo spec is the source of truth: `spec/current.md`, `spec/tasks/*.md`, `spec/updates.md`, and `workflow/*.md`.
- Do not claim Claude routine work is running unless Pegasus reports `registered`.

## Execute

If `$ARGUMENTS` starts with `run`, `tell`, `status`, or `stop`, run:

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
"""

@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    spec: Path
    tasks: Path
    updates: Path
    status: Path
    questions: Path
    requests: Path
    routine: Path


@dataclass(frozen=True)
class ClaudeListResult:
    ok: bool
    agents: list[dict[str, object]]
    diagnostic: str = ""


@dataclass(frozen=True)
class ClaudeRoutineInspection:
    status: str
    agents: list[dict[str, object]]
    diagnostic: str = ""


@dataclass(frozen=True)
class ClaudeCreateResult:
    attempted: bool
    ok: bool
    diagnostic: str


@dataclass(frozen=True)
class ClaudeCleanupResult:
    removed_record: bool
    verified_absent: bool
    diagnostic: str


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def paths(root: Path) -> ProjectPaths:
    return ProjectPaths(
        root=root,
        spec=root / "spec" / "current.md",
        tasks=root / "spec" / "tasks",
        updates=root / "spec" / "updates.md",
        status=root / "workflow" / "status.md",
        questions=root / "workflow" / "questions.md",
        requests=root / "workflow" / "agent-requests",
        routine=root / "workflow" / "claude-routine.md",
    )


def ensure_layout(p: ProjectPaths) -> None:
    p.spec.parent.mkdir(parents=True, exist_ok=True)
    p.tasks.mkdir(parents=True, exist_ok=True)
    p.status.parent.mkdir(parents=True, exist_ok=True)
    p.requests.mkdir(parents=True, exist_ok=True)


def slugify(text: str, fallback: str = "task") -> str:
    slug = TASK_RE.sub("-", text.lower()).strip("-")
    return slug[:60] or fallback


def read_text_lossy(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def render_spec(goal: str) -> str:
    return f"""# Project spec

## Goal

{goal}

## Scope

Define the work clearly enough for agents to act from this repo.

## Non-goals

- Do not work outside this spec without approval.
- Do not use chat memory as the source of truth.

## Done when

- Task specs exist under `spec/tasks/`.
- Agent results are checked against this spec.
- `workflow/status.md` reports verified progress.
"""


def render_task(index: int, title: str, goal: str) -> tuple[str, str]:
    slug = f"{index:03d}-{slugify(title)}.md"
    text = f"""# Task: {title}

## Goal

{goal}

## Source of truth

Read these repo files before doing work:

- `spec/current.md`
- `spec/updates.md`
- `workflow/status.md`
- `workflow/questions.md`

## Constraints

- Work only on this task unless the main spec says otherwise.
- Stop and report if the task conflicts with later updates.
- Do not use chat memory over repo files.

## Done when

- The task goal is satisfied.
- Evidence is returned for review.

## Return

- Files changed
- Evidence
- Open questions
"""
    return slug, text


def render_status(phase: str, message: str) -> str:
    return f"""# Status

Phase: {phase}

Updated: {now()}

{message}
"""


def routine_name(root: Path, requested: str = "") -> str:
    return requested.strip() or root.name


def list_claude_agents(cwd: Path | None = None) -> ClaudeListResult:
    cmd = ["claude", "agents", "--json"]
    if cwd is not None:
        cmd.extend(["--cwd", str(cwd)])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLAUDE_AGENT_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return ClaudeListResult(False, [], "Claude CLI was not found on PATH.")
    except subprocess.TimeoutExpired:
        return ClaudeListResult(False, [], "Timed out while listing Claude routines.")
    except OSError as exc:
        return ClaudeListResult(False, [], f"Could not list Claude routines: {exc}")
    if proc.returncode != 0:
        stderr = proc.stderr.strip()[:300]
        return ClaudeListResult(False, [], f"`claude agents --json` exited {proc.returncode}: {stderr}")
    try:
        agents = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return ClaudeListResult(False, [], f"Could not parse `claude agents --json`: {exc}")
    if not isinstance(agents, list):
        return ClaudeListResult(False, [], "`claude agents --json` did not return a list.")
    return ClaudeListResult(True, [a for a in agents if isinstance(a, dict)])


def matching_claude_routines(name: str, root: Path) -> ClaudeListResult:
    result = list_claude_agents(root)
    if not result.ok:
        return result
    resolved_root = root.resolve()
    matches: list[dict[str, object]] = []
    for agent in result.agents:
        if agent.get("name") != name:
            continue
        cwd = agent.get("cwd")
        if not isinstance(cwd, str):
            continue
        try:
            if Path(cwd).expanduser().resolve() == resolved_root:
                matches.append(agent)
        except OSError:
            continue
    return ClaudeListResult(True, matches)


def inspect_claude_routine(name: str, root: Path) -> ClaudeRoutineInspection:
    matches = matching_claude_routines(name, root)
    if not matches.ok:
        return ClaudeRoutineInspection("pending_start", [], matches.diagnostic)
    if len(matches.agents) == 0:
        return ClaudeRoutineInspection("absent", [])
    if len(matches.agents) == 1:
        return ClaudeRoutineInspection("registered", matches.agents)
    return ClaudeRoutineInspection("conflict", matches.agents, f"Found {len(matches.agents)} exact Claude routines for this project.")


def routine_prompt(name: str, root: Path) -> str:
    return f"""You are the Claude routine for Pegasus project `{name}`.

Project root: {root}

Read the GitHub repo files as the source of truth before doing work:
- spec/current.md
- spec/updates.md
- workflow/status.md
- workflow/questions.md
- spec/tasks/*.md
- workflow/agent-requests/*.md

Do not rely on chat memory over repo files. Report files changed, evidence, and open questions.
"""


def discover_claude_create_surface() -> ClaudeCreateResult:
    try:
        proc = subprocess.run(
            ["claude", "agents", "--help"],
            capture_output=True,
            text=True,
            timeout=CLAUDE_AGENT_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return ClaudeCreateResult(True, False, "Claude CLI was not found on PATH.")
    except subprocess.TimeoutExpired:
        return ClaudeCreateResult(True, False, "Timed out while checking Claude agents help.")
    except OSError as exc:
        return ClaudeCreateResult(True, False, f"Could not inspect Claude agents help: {exc}")
    if proc.returncode != 0:
        return ClaudeCreateResult(True, False, f"`claude agents --help` exited {proc.returncode}.")
    help_lines = [line.strip().lower() for line in proc.stdout.splitlines()]
    has_noninteractive_create = any(re.match(r"^(create|dispatch|start)\b", line) for line in help_lines)
    if not has_noninteractive_create:
        return ClaudeCreateResult(
            True,
            False,
            "No verified noninteractive Claude routine create command is exposed by `claude agents --help`; kept pending_start.",
        )
    return ClaudeCreateResult(
        True,
        False,
        "Claude agents help mentions creation-like wording, but Pegasus has no verified safe command contract yet; kept pending_start.",
    )


def create_claude_routine(name: str, root: Path) -> ClaudeCreateResult:
    # The current installed Claude CLI exposes reliable listing (`claude agents --json`) but
    # no verified noninteractive create/delete subcommand. Keep this as a narrow adapter
    # boundary so a future discovered command can be added without weakening verification.
    env_template = os.environ.get("PEGASUS_CLAUDE_ROUTINE_CREATE", "").strip()
    if not env_template:
        return discover_claude_create_surface()

    command = env_template.format(name=name, root=str(root), prompt=routine_prompt(name, root))
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return ClaudeCreateResult(True, False, f"Configured Claude routine create command could not be parsed: {exc}")
    if not argv:
        return ClaudeCreateResult(True, False, "Configured Claude routine create command was empty.")
    try:
        proc = subprocess.run(
            argv,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=CLAUDE_CREATE_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ClaudeCreateResult(True, False, "Configured Claude routine create command timed out.")
    except OSError as exc:
        return ClaudeCreateResult(True, False, f"Configured Claude routine create command failed: {exc}")
    if proc.returncode != 0:
        stderr = proc.stderr.strip()[:300]
        return ClaudeCreateResult(True, False, f"Configured Claude routine create command exited {proc.returncode}: {stderr}")
    return ClaudeCreateResult(True, True, "Configured Claude routine create command completed; awaiting post-create verification.")


def render_claude_routine(
    name: str,
    root: Path,
    inspection: ClaudeRoutineInspection | None = None,
    create_result: ClaudeCreateResult | None = None,
    cleanup_diagnostic: str = "",
) -> str:
    inspection = inspection or inspect_claude_routine(name, root)
    status = inspection.status if inspection.status != "absent" else "pending_start"
    diagnostics: list[str] = []
    if inspection.status == "registered":
        agent = inspection.agents[0]
        diagnostics.append(f"Verified by `claude agents --json` at {now()}.")
        diagnostics.append(f"Session: {agent.get('sessionId', 'unknown')}")
        diagnostics.append(f"PID: {agent.get('pid', 'unknown')}")
    elif inspection.status == "conflict":
        diagnostics.append(inspection.diagnostic or "Multiple exact Claude routines match this project.")
        diagnostics.append("Pegasus will not choose or delete a routine until the conflict is resolved.")
    else:
        diagnostics.append("Not verified yet. Pegasus attempted safe discovery/creation and will only report `registered` after exact verification.")
        if inspection.diagnostic:
            diagnostics.append(inspection.diagnostic)
    if create_result is not None:
        diagnostics.append(f"Create attempt: {create_result.diagnostic}")
    if cleanup_diagnostic:
        diagnostics.append(f"Cleanup: {cleanup_diagnostic}")

    diagnostic_text = "\n".join(diagnostics)
    return f"""# Claude routine

Name: {name}
Project: {root}
Status: {status}

Pegasus uses one Claude routine per project.
The routine name must be the project name.
When the project is done or stopped, Pegasus deletes this routine record only after exact absence is verified.
Pegasus only reports `registered` after the local Claude CLI verifies the live routine.

{diagnostic_text}

Routine prompt:

```text
{routine_prompt(name, root).strip()}
```
"""


def write_routine_record(
    p: ProjectPaths,
    name: str,
    inspection: ClaudeRoutineInspection | None = None,
    create_result: ClaudeCreateResult | None = None,
    cleanup_diagnostic: str = "",
) -> bool:
    rendered = render_claude_routine(name, p.root, inspection, create_result, cleanup_diagnostic)
    if p.routine.exists() and read_text_lossy(p.routine) == rendered:
        return False
    p.routine.write_text(rendered, encoding="utf-8")
    return True


def ensure_one_claude_routine(p: ProjectPaths, name: str) -> list[str]:
    if p.routine.exists():
        text = read_text_lossy(p.routine)
        expected = f"Name: {name}"
        if expected not in text:
            raise SystemExit(f"Existing Claude routine belongs to a different project. Expected {expected} in {p.routine}")

    inspection = inspect_claude_routine(name, p.root)
    create_result: ClaudeCreateResult | None = None
    if inspection.status == "absent":
        create_result = create_claude_routine(name, p.root)
        inspection = inspect_claude_routine(name, p.root)

    changed = write_routine_record(p, name, inspection, create_result)
    return [str(p.routine.relative_to(p.root))] if changed else []


def routine_name_from_record(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Name:"):
            return line.removeprefix("Name:").strip()
    return ""


def terminate_verified_claude_routine(inspection: ClaudeRoutineInspection) -> bool:
    if inspection.status != "registered":
        return False
    pid = inspection.agents[0].get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False
    return True


def cleanup_claude_routine(p: ProjectPaths) -> ClaudeCleanupResult:
    if not p.routine.exists():
        return ClaudeCleanupResult(False, True, "No Claude routine record exists.")

    name = routine_name_from_record(read_text_lossy(p.routine))
    if not name:
        return ClaudeCleanupResult(False, False, "Claude routine record has no Name field; kept record.")

    before = inspect_claude_routine(name, p.root)
    if before.status == "conflict":
        write_routine_record(p, name, before, cleanup_diagnostic="Cleanup blocked by duplicate exact Claude routines.")
        return ClaudeCleanupResult(False, False, "Cleanup blocked by duplicate exact Claude routines.")
    if before.status == "pending_start":
        write_routine_record(p, name, before, cleanup_diagnostic="Could not verify absence because Claude routine listing failed.")
        return ClaudeCleanupResult(False, False, "Could not verify absence because Claude routine listing failed.")
    if before.status == "registered":
        terminate_verified_claude_routine(before)

    after = inspect_claude_routine(name, p.root)
    if after.status == "absent":
        p.routine.unlink()
        return ClaudeCleanupResult(True, True, "Verified exact absence after cleanup.")

    write_routine_record(p, name, after, cleanup_diagnostic="Routine still present or unverified after cleanup; kept record.")
    return ClaudeCleanupResult(False, False, "Routine still present or unverified after cleanup; kept record.")


def render_agent_request(task_path: Path, root: Path) -> str:
    task_ref = task_path.relative_to(root)
    return f"""# Agent request

Claude routine input: `{task_ref}`

## Source of truth

Before working, read:

- `spec/current.md`
- `spec/updates.md`
- `workflow/status.md`
- `workflow/questions.md`

## Return

- Result summary
- Files changed
- Evidence
- Open questions
"""


def ensure_agent_requests(p: ProjectPaths) -> list[str]:
    changed: list[str] = []
    for task_path in sorted(p.tasks.glob("*.md")):
        request_path = p.requests / task_path.name
        if write_if_missing(request_path, render_agent_request(task_path, p.root)):
            changed.append(str(request_path.relative_to(p.root)))
    return changed


def init_project(root: Path, goal: str, task_titles: list[str], project_name: str = "") -> list[str]:
    p = paths(root)
    ensure_layout(p)
    changed: list[str] = []

    if write_if_missing(p.spec, render_spec(goal)):
        changed.append(str(p.spec.relative_to(root)))

    if write_if_missing(p.updates, "# Updates\n\nUser instructions after `/pegasus run` go here.\n"):
        changed.append(str(p.updates.relative_to(root)))

    if write_if_missing(p.questions, "# Questions\n\nNone.\n"):
        changed.append(str(p.questions.relative_to(root)))

    changed.extend(ensure_one_claude_routine(p, routine_name(root, project_name)))

    existing_tasks = sorted(p.tasks.glob("*.md"))
    if not existing_tasks:
        titles = task_titles or ["Clarify implementation plan"]
        for idx, title in enumerate(titles, start=1):
            name, content = render_task(idx, title, title)
            task_path = p.tasks / name
            task_path.write_text(content, encoding="utf-8")
            changed.append(str(task_path.relative_to(root)))

    changed.extend(ensure_agent_requests(p))

    status_message = "Pegasus prepared task specs and Claude routine request files."
    if p.status.exists():
        with p.status.open("a", encoding="utf-8") as fh:
            fh.write(f"\n## {now()}\n\nPegasus run continued. Existing status was preserved.\n")
    else:
        p.status.write_text(render_status("running", status_message), encoding="utf-8")
    changed.append(str(p.status.relative_to(root)))
    return changed



def install_integrations(codex_home: Path, claude_home: Path, install_codex: bool = True, install_claude: bool = True) -> list[Path]:
    written: list[Path] = []
    if install_codex:
        skill_dir = codex_home.expanduser() / "skills" / "pegasus"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(CODEX_SKILL, encoding="utf-8")
        written.append(skill_path)
    if install_claude:
        command_dir = claude_home.expanduser() / "commands"
        command_dir.mkdir(parents=True, exist_ok=True)
        command_path = command_dir / "pegasus.md"
        command_path.write_text(CLAUDE_COMMAND, encoding="utf-8")
        written.append(command_path)
    return written


def cmd_install_integrations(args: argparse.Namespace) -> int:
    codex_home = Path(args.codex_home or os.environ.get("CODEX_HOME", "~/.codex"))
    claude_home = Path(args.claude_home or os.environ.get("CLAUDE_HOME", "~/.claude"))
    written = install_integrations(codex_home, claude_home, not args.skip_codex, not args.skip_claude)
    if not written:
        print("No Pegasus integrations were installed.")
        return 0
    print("Pegasus integrations installed:")
    for path in written:
        print(f"- {path.expanduser()}")
    print("\nCodex: use the Pegasus skill by saying `$pegasus run ...` or `/pegasus run ...`.")
    print("Claude Code: use `/pegasus run . --goal \"...\"` inside a repo.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    root = Path(args.repo).expanduser().resolve()
    goal = args.goal or "Define this project from the user's request."
    changed = init_project(root, goal, args.task, args.name)
    print("Pegasus run prepared the repo spec.")
    print(f"Repo: {root}")
    print("Changed:")
    for item in changed:
        print(f"- {item}")
    return 0


def cmd_tell(args: argparse.Namespace) -> int:
    root = Path(args.repo).expanduser().resolve()
    p = paths(root)
    ensure_layout(p)
    if not p.updates.exists():
        p.updates.write_text("# Updates\n\n", encoding="utf-8")
    with p.updates.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {now()}\n\n{args.message}\n")
    print(f"Added update to {p.updates}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.repo).expanduser().resolve()
    p = paths(root)
    if not p.status.exists():
        print("No Pegasus status found. Run `/pegasus run` first.")
        return 1
    print(f"Status file: {p.status.relative_to(root)}")
    status_text = read_text_lossy(p.status).strip()
    print(status_text)
    if "Phase: done" in status_text:
        cleanup = cleanup_claude_routine(p)
        if cleanup.removed_record:
            print("\nDeleted Claude routine after verified completion cleanup.")
        elif cleanup.verified_absent:
            print("\nClaude routine already absent.")
        else:
            print(f"\nClaude routine cleanup incomplete: {cleanup.diagnostic}")
    elif p.routine.exists():
        name = routine_name_from_record(read_text_lossy(p.routine))
        if name:
            write_routine_record(p, name, inspect_claude_routine(name, p.root))

    tasks = sorted(p.tasks.glob("*.md")) if p.tasks.exists() else []
    print("\nTask specs:")
    if tasks:
        for task in tasks:
            print(f"- {task.relative_to(root)}")
    else:
        print("- none")

    requests = sorted(p.requests.glob("*.md")) if p.requests.exists() else []
    print("\nClaude routine requests:")
    if requests:
        for request in requests:
            print(f"- {request.relative_to(root)}")
    else:
        print("- none")

    if p.routine.exists():
        print("\nClaude routine:")
        text = read_text_lossy(p.routine)
        for line in text.splitlines():
            if line.startswith(("Name:", "Project:", "Status:")):
                print(line)

    if p.questions.exists():
        print("\nQuestions:")
        print(read_text_lossy(p.questions).strip())
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    root = Path(args.repo).expanduser().resolve()
    p = paths(root)
    ensure_layout(p)
    cleanup = cleanup_claude_routine(p)
    message = "Pegasus was stopped by user request."
    if cleanup.removed_record:
        message += " Claude routine record was deleted after exact absence was verified."
    elif cleanup.verified_absent:
        message += " No Claude routine record was present."
    else:
        message += f" Claude routine cleanup incomplete: {cleanup.diagnostic}"
    p.status.write_text(render_status("stopped", message), encoding="utf-8")
    print(f"Stopped Pegasus project at {root}")
    if cleanup.removed_record:
        print("Deleted Claude routine record after verified absence.")
    elif cleanup.verified_absent:
        print("No Claude routine record was present.")
    else:
        print(f"Claude routine cleanup incomplete: {cleanup.diagnostic}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pegasus", description="Spec-driven project leader")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="start or continue a project")
    run.add_argument("repo", help="project repo path")
    run.add_argument("--goal", default="", help="main project goal")
    run.add_argument("--task", action="append", default=[], help="task spec title; repeatable")
    run.add_argument("--name", default="", help="Claude routine name; defaults to project directory name")
    run.set_defaults(func=cmd_run)

    tell = sub.add_parser("tell", help="append instructions")
    tell.add_argument("repo", help="project repo path")
    tell.add_argument("message", help="instruction to append")
    tell.set_defaults(func=cmd_tell)

    status = sub.add_parser("status", help="show progress")
    status.add_argument("repo", help="project repo path")
    status.set_defaults(func=cmd_status)

    stop = sub.add_parser("stop", help="stop a project")
    stop.add_argument("repo", help="project repo path")
    stop.set_defaults(func=cmd_stop)

    integrations = sub.add_parser("install-integrations", help="install Codex skill and Claude Code slash command")
    integrations.add_argument("--codex-home", default="", help="Codex home; defaults to CODEX_HOME or ~/.codex")
    integrations.add_argument("--claude-home", default="", help="Claude home; defaults to CLAUDE_HOME or ~/.claude")
    integrations.add_argument("--skip-codex", action="store_true", help="do not install the Codex skill")
    integrations.add_argument("--skip-claude", action="store_true", help="do not install the Claude Code command")
    integrations.set_defaults(func=cmd_install_integrations)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
