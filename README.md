# Pegasus

**Cloud-native autonomous project leader for Claude.**

Start a project from your phone, hand it off to Anthropic's cloud via a Managed Agent routine, turn your laptop off. Pegasus continues, commits to GitHub, and pings you when there's news.

---

## What it is

A `/pegasus` skill + a per-project GitHub repo + an hourly cloud routine. You interview, Pegasus executes. Computer-off is the baseline, not a feature.

| Verb                       | What happens                                                            |
| -------------------------- | ----------------------------------------------------------------------- |
| `/pegasus start <name>`    | Deep interview → spec → repo `xodn348/<name>` → routine `[<name>] driver` registered |
| `/pegasus status <name>`   | One-screen progress report                                              |
| `/pegasus tell <name> "…"` | Append addendum to spec; next tick picks it up                          |
| `/pegasus stop <name>`     | Mark project terminated; routine disables itself                        |

Built on Anthropic Managed Agents (beta header `managed-agents-2026-04-01`): **Outcomes** for per-tick rubric grading, **Multiagent Orchestration** for parallel worker delegation, **Memory** for cross-tick state, **Console audit log** for monitoring.

---

## Status

🟡 **Design complete. Implementation pending.** See [`PROJECT.md`](./PROJECT.md) for the full engineering spec (architecture, Outcomes/iteration model, decision boundaries, state contract, milestones, open questions).

---

## Repo

```
pegasus/
├── README.md     # this file — public-facing intro
└── PROJECT.md    # engineering source of truth (v2)
```

Implementation files arrive once the open questions in `PROJECT.md §11` are closed.
