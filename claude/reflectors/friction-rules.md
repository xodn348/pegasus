---
name: friction-rules
description: What counts as "user friction" — signals that the OS is making the user repeat themselves or work around something. VERBATIM from pegasus-os (PROJECT.md §8).
type: reflector
---

> VERBATIM from [`xodn348/pegasus-os/claude/reflectors/friction-rules.md`](https://github.com/xodn348/pegasus-os/blob/main/claude/reflectors/friction-rules.md). Used by host-side reflectors against the pegasus-os bus, not per-project buses.

# Friction signals

These rules are gentler than violation-rules: they don't say "the spec broke," they say "something annoyed the user N times." Outputs are always proposals, never auto-merge.

## Manual workarounds

**Signal**: user prompt contains "again", "still", "왜", "다시", "anyway just do", "fine, just" within a session that recently saw an error or refusal.

**Action**: log as friction event. If 5+ in a week, summarize the underlying cause in next morning brief.

## Repeated re-prompting

**Signal**: 3+ user prompts in a single session that semantically restate the same goal (cosine sim shortcut: 60%+ token overlap).

**Action**: candidate spec gap. Surface in weekly retro.

## Tool that never gets used

**Signal**: a permission allowlist entry that has zero `pre_tool` hits in 30 days.

**Action**: propose removal in next weekly retro. Auto-merge after second consecutive flag.

## Hook that errors

**Signal**: `error` event with `where` matching a hook name.

**Action**: propose disabling the hook with a comment, file an issue note in `bus/issues.md`.

## Long sessions with no completion

**Signal**: `session_start` followed by no `stop` event with `outcome=completed` (heuristic: stop event present but verification failed or absent).

**Action**: the post-mortem in weekly retro should look at these specifically — they're the highest-value sessions to learn from.

## Self-improver disagreement (explicit only)

**Signal**: a previously auto-merged patch is reverted by the user *with explicit intent*. Two ways to count:

1. **Bus event `action_taken` with `action:"revert"` and `explicit:true`** — produced by `pegasus revert <N>`. This is the canonical, surgical signal.
2. **Git log subject matches the marker** `pegasus: revert ` — also accepted (the CLI inserts this trailer; a hand-written `git revert` only counts if the user manually adds the same trailer).

**Not** counted: arbitrary `git revert`, force-push rewrites, history surgery, branch resets. The user often reverts things for unrelated reasons; the distrust signal must come from a *mentioned* revert, not pattern-matching every git operation.

**Action**: **demote** the specific rule that produced the reverted patch from auto-merge to PR-only for 30 days. Log as `self_improve_distrust` event with the rule name + reverted target.

**Bound**: a single revert demotes only ONE rule (the one cited in the reverted patch's bus `self_improve_proposal` event). It does not punish unrelated rules that happened to ship around the same time.

---

# Why these are softer than violations

Violations say "spec exists, wasn't followed." Friction says "user is working harder than necessary." The first can be auto-patched mechanically; the second requires judgment, so it always surfaces to the user via brief or retro.
