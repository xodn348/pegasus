# Project agents

Claude routine agents receive one task spec from `spec/tasks/*.md`.

They work only from that spec and return evidence.

## Available agents

- `builder.md` — implements a task spec.
- `verifier.md` — checks whether work satisfies a task spec.
- `risk-reviewer.md` — checks license, provenance, secrets, and risky changes.
- `deep-digger.md` — follows one unresolved LLM discussion thread to a decision, contradiction, experiment, or blocking question.
