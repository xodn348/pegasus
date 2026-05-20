---
name: violation-rules
description: Heuristics for detecting when an existing spec was NOT applied even though it should have been. VERBATIM from pegasus-os (PROJECT.md §8).
type: reflector
---

> VERBATIM from [`xodn348/pegasus-os/claude/reflectors/violation-rules.md`](https://github.com/xodn348/pegasus-os/blob/main/claude/reflectors/violation-rules.md). In Pegasus, these rules are consumed by the host-side `daily-self-improve` routine running against `~/code/pegasus-os/claude/bus/events.ndjson`. They do **not** run against per-project buses — project buses have a narrower kind set (PROJECT.md §7) and are not subject to spec-violation tracking.

# How daily-self-improve detects spec violations

For each rule, the routine queries `bus/events.ndjson` for the previous 24h and emits a finding if the rule matches. Findings become candidate patches.

## Worktree spec miss

**Match**: `user_prompt` event whose `spec_keywords` includes `"worktree-parallel"`, AND no event with `kind="spec_triggered"` and `spec="worktree-parallel"` occurs in the same `session` within 5 minutes.

**Plausible failure modes**:
- Claude misclassified the request as too small for worktrees → spec needs a sharper trigger phrase clause.
- Perception loop never armed → spec already says this is mandatory, so the *enforcement* (e.g. block tool invocation) is missing.

**Patch shape**: append a row to spec's "observed misses" log with a 1-line summary; if the same miss repeats 3+ times, propose a sharper trigger heuristic.

## Parallel-subagents spec miss

**Match**: `user_prompt` event with multiple imperatives (heuristic: "and", "그리고", commas separating verbs) where the same session never spawns 2+ `Agent` tool calls in a single assistant turn.

**Patch shape**: add an example to the spec's "smelt-test" section.

## Repeated permission denial

**Match**: same `Bash(cmd ...)` denied 3+ times across distinct sessions in 7 days.

**Patch shape**: this is **auto-merge eligible**. Append the matching glob to `kernel/settings.json` `permissions.allow` and commit `pegasus: auto-allow <cmd>`. No PR needed.

## Repeated verification failure on same repo

**Match**: 3+ `verification` events with `outcome="fail"` in the same `cwd` within 7 days.

**Patch shape**: open a PR proposing a check-in to that repo's `CLAUDE.md` documenting the failing command. Don't auto-merge — needs human eyes.

## Skill never triggered when relevant

**Match**: `user_prompt` text matches a skill's stated triggers (regex provided in skill frontmatter), but the next 10 events do not include `skill_invoked` for that skill.

**Patch shape**: add a comment to the skill's trigger section noting the missed phrase.

## Spec contradicts MEMORY.md feedback

**Match**: scan `~/.claude/projects/-Users-jnnj92/memory/feedback_*.md` for sentences whose negation appears in `sops/*.md`. (Heuristic — false positives expected; routine should flag, not auto-fix.)

**Patch shape**: open a PR with both files highlighted, ask user.

---

# Rule output schema

Each match the routine emits should be one JSON object:
```json
{
  "rule": "worktree-spec-miss",
  "evidence": [{"ts": "...", "session": "...", "prompt_excerpt": "..."}],
  "occurrences": 3,
  "auto_merge_eligible": false,
  "proposed_patch": {
    "file": "claude/sops/worktree-parallel.md",
    "diff": "..."
  }
}
```

These are written to `bus/proposals/YYYY-MM-DD.jsonl` for the routine to act on.
