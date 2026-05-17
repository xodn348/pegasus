# Pegasus

**Cloud-native autonomous project leader for Claude.**

Start a project from anywhere — your phone, your laptop, an airport lounge — interview Claude about what you want, hand it off to the cloud, and walk away. Your computer can be off the entire time. Claude continues working in Anthropic's cloud, commits to GitHub, and reports back when there's news.

---

## Why

Existing Claude workflows assume your computer stays on. Long projects mean keeping a terminal alive, babysitting agents, or accepting that work pauses when your laptop sleeps.

Pegasus inverts that. The user's computer is **incidental** — only needed for conversation moments. The actual work runs on cloud-side **Scheduled Agents (Routines)** that own their own sandbox, clone the repo, dispatch subagents, commit results, and self-iterate on a cron tick.

The user interacts via **mobile Claude Code** sessions. No Project required, no special UI. Just a `/pegasus` skill and a GitHub repo.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  GitHub: xodn348/<project-name>                  │
│      (the shared disk — single source of truth for everything)   │
│                                                                  │
│  spec/current.md     workflow/state.json     events.ndjson       │
│  subagents/<id>/inbox.md      reports/      questions/pending.md │
│  output/<files>      done.md (completion marker)                 │
└──────────────────────────────────────────────────────────────────┘
        ▲                                                  ▲
        │ read & commit via GitHub MCP                     │ clone, commit,
        │                                                  │ push via gh CLI
        │                                                  │
┌───────┴──────────────────┐              ┌────────────────┴────────┐
│ Mobile Claude Code       │              │  Cloud Routine          │
│ (any new session)        │              │  [<project>] driver     │
│                          │              │                         │
│  /pegasus start <name>   │              │  - cron tick (hourly)   │
│  /pegasus status <name>  │              │  - reads state.json     │
│  /pegasus tell <name>... │              │  - spawns subagents     │
│  /pegasus stop <name>    │              │    (Task tool, worktree │
│                          │              │     isolation)          │
│  Computer-OFF capable    │              │  - merges, commits,     │
│  after handoff.          │              │    pushes to main       │
│                          │              │  - exits early if       │
│                          │              │    done.md present      │
└──────────────────────────┘              └─────────────────────────┘
```

### The four actors

| Actor                  | Where                                | Responsibility                                                                                |
| ---------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------- |
| **User**               | Mobile Claude Code                   | Triggers, answers clarifying questions, reads reports                                         |
| **Leader (in chat)**   | Mobile Claude Code session via Skill | Deep interview, spec authoring, repo bootstrap, routine creation                              |
| **Driver (in cloud)**  | Anthropic cloud Routine              | Reads state on every tick, dispatches subagents, integrates results, commits                  |
| **Subagents (in cloud)** | Spawned by Driver via Task tool    | Execute one scoped chunk each in an isolated worktree, report back via file-based mailbox     |

All four communicate through the GitHub repo — no API connections between them.

### Layers

1. **Specs** (`spec/`) — the contract. Authored by Leader during interview. Driver and subagents read it. User can hand-edit any time.
2. **State** (`workflow/state.json`) — the cursor. Where are we, what's done, what's next.
3. **Bus** (`events.ndjson`) — append-only timeline of every transition. Auditable history.
4. **Mailbox** (`subagents/<id>/inbox.md`, `reports/`) — message-passing between Driver and subagents.
5. **Output** (`output/`) — the actual deliverable being built.
6. **Done** (`done.md`) — terminal marker. Driver no-ops thereafter.

---

## Interview — reuses existing tools

Pegasus doesn't reinvent intake. The Leader composes proven interview skills the user already has installed:

- **[`deep-interview`](https://github.com/xodn348/oh-my-codex/tree/main/skills/deep-interview)** — Socratic clarification loop with ambiguity gating. `--quick | --standard | --deep` profiles.
- **[`prometheus`](https://github.com/xodn348/.claude/tree/main/skills/prometheus)** — 5-question scoping interview that produces Goal / Scope / Steps / Files / Risks / Success criteria.
- **[`ralplan`](https://github.com/xodn348/oh-my-codex/tree/main/skills/ralplan)** — Planner → Architect → Critic consensus loop. Auto-calls deep-interview on vague input.
- **Ouroboros pattern** — single-truth `spec/<task>/seed.md` lock for multi-worker tasks (already absorbed into `/go` Stage 2).

The Leader's first job is to choose the right intake depth:

| Project shape       | Tool chain                                   |
| ------------------- | -------------------------------------------- |
| Tiny feature / fix  | `prometheus` only (5 questions)              |
| Standard project    | `deep-interview --standard` → `ralplan`      |
| Ambitious / vague   | `deep-interview --deep` → `ralplan --consensus` → seed.md per worker |

Output of all three lands in `spec/` of the project repo. Driver reads from there.

---

## Quickstart

### 1. Install the `pegasus` skill (one time)

```bash
# Skill source lives in this repo
cd ~/code/pegasus
zip -r pegasus.zip skills/pegasus/
```

In the **Claude mobile app** → `Customize` → `Skills` → `Upload Custom Skill` → select `pegasus.zip`.

The skill is now available account-wide, in every new Claude Code session (mobile, desktop, web).

### 2. Start a project from your phone

Open a new Claude Code session in the mobile app:

```
/pegasus start gardener
```

The Leader will:

1. Run a 20–30 minute deep interview (via `deep-interview --standard`).
2. Author `spec/current.md`, `workflow/state.json` for the project.
3. Create the GitHub repo `xodn348/gardener`.
4. Commit the initial spec.
5. Register a Routine named `[gardener] driver` (cron `0 * * * *`).
6. Tell you "handed off — you can close this session."

You can now turn off your phone. The cloud continues.

### 3. Check status — from anywhere, any time

```
/pegasus status gardener
```

The Leader fetches the latest `state.json` + `events.ndjson` and gives you a one-screen progress report.

### 4. Answer questions or refine scope

If the Driver hits something it can't decide alone, it appends to `questions/pending.md` in the repo. Next time you invoke status, the Leader surfaces those.

```
/pegasus tell gardener "use SQLite, not Postgres — single user"
```

Leader commits your input into `spec/current.md` (with a diff) and pushes. The next Driver tick picks it up automatically.

### 5. Stop or wrap up

```
/pegasus stop gardener
```

Leader writes `done.md`, which makes every future Driver tick a no-op. Routine stays in your dashboard as `enabled: false`.

---

## Project repo layout (auto-generated)

```
xodn348/<project-name>/
├── spec/
│   ├── current.md              # canonical project spec
│   ├── interview-transcript.md # full Socratic record
│   └── seeds/                  # per-subagent locked spec slices
├── workflow/
│   ├── state.json              # cursor + completion %
│   └── plan.md                 # ralplan output (Planner/Architect/Critic)
├── subagents/
│   └── <id>/
│       ├── inbox.md            # Driver → subagent assignment
│       └── reports.jsonl       # subagent → Driver progress
├── events.ndjson               # append-only bus
├── questions/pending.md        # Driver → user
├── output/                     # actual code/docs being built
├── done.md                     # terminal marker (presence = no-op)
└── CLAUDE.md                   # project-local agent instructions
```

---

## Driver routine — minimal bootstrap

The routine config is tiny. The real logic lives in `claude/routines/leader-driver.md` of this repo:

```bash
# Routine prompt (committed once, never edited per-project)
set -e
gh auth login --with-token < $PAT
git config --global user.name 'xodn348'
git config --global user.email 'xodn348@tamu.edu'
git config --global commit.gpgsign false

rm -rf /tmp/proj
gh repo clone xodn348/<PROJECT_NAME> /tmp/proj
cd /tmp/proj

# Terminal-state guard
[ -f done.md ] && { echo '=== RUN_RESULT: NO_OP (done) ==='; exit 0; }

# Load and follow the driver playbook
gh repo clone xodn348/pegasus /tmp/pegasus -- --depth=1
cat /tmp/pegasus/claude/routines/leader-driver.md
# (Driver follows that playbook verbatim — see file for full logic)
```

A single per-project routine. Clean dashboard. Spec changes propagate without routine reconfiguration.

---

## Verified capabilities (no fallback)

| Capability                                       | Status                                                                |
| ------------------------------------------------ | --------------------------------------------------------------------- |
| GitHub MCP usable from mobile Claude Code chat   | ✅ Anthropic connector catalog, OAuth, mobile-confirmed                |
| Custom skill upload via mobile app               | ✅ `Customize > Skills > Upload Custom Skill` (account-wide, persists) |
| Auto-commit / auto-merge to main from routine    | ✅ Proven by existing `[oss] contributor`, `[pegasus-os] daily-self-improve` |
| Routine survives user computer being off         | ✅ Routines are cloud-resident; no local dependency                    |
| Subagents share state via shared disk            | ✅ All four actors read/write the same GitHub repo                     |

| Capability                                       | Status                                                                |
| ------------------------------------------------ | --------------------------------------------------------------------- |
| Mobile push when Driver finishes / asks question | ⏳ Not natively supported. Will route through Gmail or Telegram later. |
| Sub-hour tick cadence                            | ⏳ Anthropic cron minimum is 1h. Acceptable for project granularity.  |

---

## Design principles

1. **Computer-off is not a feature — it's the baseline.** Anything that requires a laptop staying on is rejected.
2. **One repo per project, one routine per project.** The dashboard stays readable as projects accumulate.
3. **GitHub is the bus.** No private message channels between Leader / Driver / subagents. Every transition is a commit.
4. **Reuse existing skills.** `deep-interview`, `prometheus`, `ralplan`, `ralph` are already installed and proven. Pegasus orchestrates, doesn't reimplement.
5. **Auto-commit, auto-merge, no PR.** Routines push direct to `main`. Conflicts are resolved by the next tick (rebase + retry). This matches `museum-as-code` auto-merge precedent.
6. **The Leader interviews; the Driver executes.** Two roles, never blurred. Leader runs in chat (interactive). Driver runs in cloud (cron). They communicate only through the repo.

---

## Status

🟡 **Design complete, implementation pending.**

Next milestones:

- [ ] `skills/pegasus/SKILL.md` — Leader prompt + subcommand routing
- [ ] `claude/routines/leader-driver.md` — Driver playbook (tick logic, subagent dispatch, integration, push)
- [ ] First end-to-end smoke test with a trivial project (e.g., "build a markdown table-of-contents generator")
- [ ] Mobile push integration (Gmail or Telegram) — deferred
