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
4. gives those specs to Claude routine agents,
5. checks the results,
6. asks you only for big decisions,
7. reports completion with evidence.

## Commands

- `/pegasus run` — start or continue
- `/pegasus tell` — add instructions
- `/pegasus status` — check progress
- `/pegasus stop` — stop

## Core rule

The GitHub spec is the source of truth.

Each project gets one Claude routine named after the project. Pegasus deletes that routine when the project is done.

Agents follow the repo spec, not chat memory.

## Local dry-run

For local development, the same flow can be tested with:

```text
python -m pegasus run ./my-project --goal "Build the thing"
python -m pegasus tell ./my-project "Add this requirement"
python -m pegasus status ./my-project
python -m pegasus stop ./my-project
```
