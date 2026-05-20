# Bus event schema

> VERBATIM from [`xodn348/pegasus-os/claude/bus/SCHEMA.md`](https://github.com/xodn348/pegasus-os/blob/main/claude/bus/SCHEMA.md) (PROJECT.md §8). Pegasus operates **two parallel buses sharing this schema** (PROJECT.md §7): Mac-local `~/code/pegasus-os/claude/bus/events.ndjson` (user cross-session observability) and per-project `xodn348/<project>/events.ndjson` (project lifecycle). Schema shared; data partitioned.

`events.ndjson` is the source-of-truth event log. Append-only, one JSON object per line. Routines and the `pegasus-os` CLI read it. Nothing reads any other state — if it didn't get logged here, it never happened.

## Common fields (every event)

| field | type | description |
|---|---|---|
| `ts` | RFC3339 UTC | When the event was logged |
| `kind` | string | Event type (see below) |
| `session` | string | Claude session id (`session_id` from hook stdin) |
| `cwd` | string | Working dir at time of event |
| `host` | string | Hostname (multi-machine awareness) |

## Kinds — pegasus-os bus (host observability)

| kind | when | extra fields |
|---|---|---|
| `session_start` | SessionStart hook | — |
| `user_prompt` | UserPromptSubmit | `prompt` (truncated 4KB), `spec_keywords` (string[]) — heuristic SOP-trigger detection |
| `pre_tool` | PreToolUse | `tool` |
| `post_tool` | PostToolUse | `tool` (use sparingly — high volume) |
| `subagent_stop` | SubagentStop | — |
| `stop` | Stop | `stop_hook_active` |
| `spec_triggered` | written by routines/scripts after detecting a spec was actually applied | `spec`, `evidence` |
| `verification` | written by `/go` or other ship paths | `tool`, `outcome` |
| `worker_spawn` | written by worktree leader | `workflow`, `lane`, `pid` |
| `self_improve_proposal` | daily-self-improve | `target_file`, `summary`, `auto_merged` |
| `morning_brief` | morning-brief | `pushed_to` (string[]) |
| `error` | any | `message`, `where` |

## Kinds — pegasus project bus (PROJECT.md §7)

Same envelope, project-lifecycle kinds:

| kind | when | extra fields |
|---|---|---|
| `project_init` | leader writes spec/plan/state | `slug`, `ambiguity`, `rounds` |
| `user_tell` | `/pegasus tell` appends to addenda | `excerpt` |
| `question_raised` | driver hits decision boundary | `question`, `phase` |
| `question_resolved` | user answers via `/pegasus tell` | `question_id` |
| `tick_started` | driver tick begins | `milestone_id` |
| `tick_satisfied` | grader verdict satisfied | `milestone_id`, `evidence` |
| `tick_needs_more_work` | grader verdict not yet done | `milestone_id`, `reason` |
| `tick_failed` | grader verdict failed | `milestone_id`, `reason` |
| `tick_skipped` | nothing to do this tick | `reason` |
| `specialist_invoked` | driver fans out Agent call | `worker`, `task` |
| `specialist_returned` | Agent call returned | `worker`, `result_summary` |
| `integration_failed` | merge/conflict in driver integration | `details` |
| `milestone_advanced` | next milestone picked | `from`, `to` |
| `escalation` | PushNotification fired to user | `reason`, `severity` |
| `pegasus_done` | all milestones satisfied | — |
| `pegasus_stopped` | user `/pegasus stop` | — |

## Why ndjson, not sqlite as primary

- jq + grep is enough for the rolling 30-day window we care about.
- Append-only file is bullet-proof against concurrent writers (Claude sessions overlap; sqlite locks would bite).
- A nightly routine *can* roll up into `sessions.sqlite` for fast queries, but the ndjson is the truth.

## Retention

- `events.ndjson` keeps last 90 days. Older lines rotated to `events.ndjson.YYYY-MM.gz` weekly.
- Briefs archived in `briefs/YYYY-MM-DD.md` indefinitely (small).

## Privacy posture

### What's logged in `prompt`
- First **4096 bytes** of the user message, plain text.
- Plus heuristic `spec_keywords` (0-1 SOP detected via grep).
- Nothing else from that turn — no Claude response, no tool output, no file contents Claude reads.

### Where it lives
- **pegasus-os bus**: `~/code/pegasus-os/claude/bus/events.ndjson` — local file only, gitignored.
- **Pegasus project bus**: `xodn348/<project>/events.ndjson` — **committed**, no `prompt` field captured. Only structured project-lifecycle kinds (above) are logged.
- Permission `644` by default. On a single-user laptop this is fine; on a multi-user machine, consider `chmod 600 events.ndjson` (the logger reuses existing permissions).
- Never uploaded anywhere — no cloud sync, no telemetry, no backup beyond Time Machine if you have it.

### Toggling host-side prompt logging off

Three layers (apply to pegasus-os bus only — project bus never logs prompt):

| Scope | How |
|---|---|
| Single session | `PEGASUS_OS_LOG_PROMPTS=0 claude` — drops body, keeps spec_keywords |
| Global default | export `PEGASUS_OS_LOG_PROMPTS=0` in `~/.zshrc` |
| Forever | comment out the `UserPromptSubmit` hook in `kernel/settings.json` |

When off, the event still logs but contains `{"prompt_redacted": true}` instead of `prompt`. Spec_keywords still computed (so friction analytics keep working without the body).
