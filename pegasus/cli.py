from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

TASK_RE = re.compile(r"[^a-z0-9]+")


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


def render_claude_routine(name: str, root: Path) -> str:
    return f"""# Claude routine

Name: {name}
Project: {root}
Status: registered

Pegasus uses one Claude routine per project.
The routine name must be the project name.
When the project is done, Pegasus deletes this file and the routine must be removed from Claude.

Start command:

```text
claude --name {name} --add-dir {root} --permission-mode auto
```
"""


def ensure_one_claude_routine(p: ProjectPaths, name: str) -> list[str]:
    if p.routine.exists():
        text = p.routine.read_text(encoding="utf-8")
        expected = f"Name: {name}"
        if expected not in text:
            raise SystemExit(f"Existing Claude routine belongs to a different project. Expected {expected} in {p.routine}")
        return []
    p.routine.write_text(render_claude_routine(name, p.root), encoding="utf-8")
    return [str(p.routine.relative_to(p.root))]


def cleanup_claude_routine(p: ProjectPaths) -> bool:
    if not p.routine.exists():
        return False
    p.routine.unlink()
    return True


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
    status_text = p.status.read_text(encoding="utf-8").strip()
    print(status_text)
    if "Phase: done" in status_text and cleanup_claude_routine(p):
        print("\nDeleted Claude routine after completion.")
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
    if p.questions.exists():
        print("\nQuestions:")
        print(p.questions.read_text(encoding="utf-8").strip())
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    root = Path(args.repo).expanduser().resolve()
    p = paths(root)
    ensure_layout(p)
    removed = cleanup_claude_routine(p)
    message = "Pegasus was stopped by user request."
    if removed:
        message += " Claude routine record was deleted."
    p.status.write_text(render_status("stopped", message), encoding="utf-8")
    print(f"Stopped Pegasus project at {root}")
    if removed:
        print("Deleted Claude routine record.")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
