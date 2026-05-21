# Claude routine

Name: project
Project: examples/project
Status: pending_start

Pegasus uses one Claude routine per project. It reports `registered` only after `claude agents --json` verifies the exact project name and repo path.

Routine prompt:

```text
Read the repo spec files first: spec/current.md, spec/updates.md, workflow/status.md, workflow/questions.md, spec/tasks/*.md, workflow/agent-requests/*.md.
Report files changed, evidence, and open questions.
```
