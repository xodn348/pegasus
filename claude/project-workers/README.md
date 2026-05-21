# Project workers

Pegasus workers are optional prompts used by the driver for bounded lanes.
They are deliberately small so the project spec remains the source of truth.

- `builder.md` — implement the assigned lane only.
- `verifier.md` — verify evidence against the spec.
- `risk-reviewer.md` — check boundaries, provenance, and destructive actions.
