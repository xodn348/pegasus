# Pegasus

Pegasus turns a project request into spec-driven Claude routine work.

You run:

```text
/pegasus run
```

Pegasus then:

1. asks only the needed questions,
2. writes the project spec in GitHub,
3. splits work into smaller specs,
4. attempts to start or verifies one Claude routine for the project,
5. gives task specs to that routine,
6. checks the results,
7. asks you only for big decisions,
8. reports completion with evidence.

## Commands

- `/pegasus run` — start or continue
- `/pegasus tell` — add instructions
- `/pegasus status` — check progress
- `/pegasus stop` — stop

## Core rule

The GitHub spec is the source of truth.

Each project gets one Claude routine named after the project. Pegasus only marks it `registered` after `claude agents --json` verifies the exact project name and repo path. If Claude cannot safely create or verify it, Pegasus keeps `pending_start` instead of pretending it is running.

Agents follow the repo spec, not chat memory.

## Local dry-run

For local development, the same flow can be tested with:

```text
python -m pegasus run ./my-project --goal "Build the thing"
python -m pegasus tell ./my-project "Add this requirement"
python -m pegasus status ./my-project
python -m pegasus stop ./my-project
```
