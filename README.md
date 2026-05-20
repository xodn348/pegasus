# Pegasus

**Cloud-native autonomous project leader for Claude Code.**

Start a project from your phone, hand it off via a Claude Code routine, turn your laptop off. Pegasus continues, commits to GitHub, and pings you when there's news.

---

## What it is

A `/pegasus` skill + a per-project GitHub repo + an hourly Claude Code Cron routine. You interview, Pegasus executes. Computer-off is the baseline, not a feature.

| Verb                       | What happens                                                            |
| -------------------------- | ----------------------------------------------------------------------- |
| `/pegasus start <name>`    | Deep interview → spec → repo `xodn348/<name>` → routine `[<name>] driver` registered via `CronCreate` |
| `/pegasus status <name>`   | One-screen progress report from `state.json` + `events.ndjson`          |
| `/pegasus tell <name> "…"` | Append addendum to spec; next tick picks it up                          |
| `/pegasus stop <name>`     | `CronDelete` the routine; mark project terminated                       |

Built on **Claude Code session primitives** — `CronCreate`/`CronDelete` (Driver lifecycle), `Agent` tool (C-suite worker fanout + self-grading), `PushNotification` (mobile escalation), GitHub (single source of truth). **No Anthropic API key, no Managed Agents beta, no external infrastructure.**

---

## Status

🟢 **Spec v4 + scaffold landed.** Pending: deep-interview wiring (reuses `pegasus-init` verbatim), worker ralph-loop semantics, first smoke test. See [`PROJECT.md`](./PROJECT.md) — the engineering source of truth.

---

## Repo

```
pegasus/
├── README.md                       # this file
├── PROJECT.md                      # engineering source of truth (v4)
├── LICENSE                         # MIT
├── workers.json                    # C-suite worker roster (model + tools + skills)
├── workers/                        # CEO / CTO / CFO / CMO / COO / GC system prompts
├── skills/pegasus/SKILL.md         # Leader skill — /pegasus start | tell | status | stop
└── claude/routines/leader-driver.md  # Driver tick prompt (hourly Claude Code Cron)
```

---

## Credits

Pegasus stands on the shoulders of several MIT-licensed projects whose patterns we absorbed (concepts only — no code copied).

| Source | License | What we borrowed |
| --- | --- | --- |
| [Q00/ouroboros](https://github.com/Q00/ouroboros) | MIT | Spec-seed pattern, Stage 2 semantic intent check, ambiguity-gated interview philosophy |
| [code-yeongyu/oh-my-codex](https://github.com/code-yeongyu/oh-my-codex) | MIT (per `package.json`) | `deep-interview` skill structure (3-stage, ambiguity ≤ 0.15 gate, pressure pass) + `ralplan` consensus planning pattern — both reused via the user's `pegasus-init` skill |
| [xodn348/pegasus-os](https://github.com/xodn348/pegasus-os) | (user's own) | `pegasus-init` interview skill, `bus/SCHEMA.md` event schema, reflector rule format, base coding principles |
| "Ralph loop" terminology | (folklore via [Geoffrey Huntley](https://ghuntley.com/ralph/)) | Worker-iteration pattern in workflow step 5 |

Code originally written by the Pegasus author (Junhyuk Lee) is MIT — see [`LICENSE`](./LICENSE).
