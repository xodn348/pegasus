# Workers — C-suite library

Pre-built **Anthropic Managed Agent** specialists the Pegasus coordinator delegates to. Each worker is a focused executive persona with a minimal system prompt. The coordinator (Driver) picks who to invoke per task at runtime, via the native `multiagent` config (`agent_toolset_20260401`).

## Library

| File | Worker | One-line role |
|---|---|---|
| [`ceo.md`](./ceo.md) | CEO | Vision, final decisions when officers disagree |
| [`cto.md`](./cto.md) | CTO | Tech roadmap, build vs buy, architecture |
| [`cfo.md`](./cfo.md) | CFO | Cash model, runway, unit economics |
| [`cmo.md`](./cmo.md) | CMO | Positioning, messaging, growth channels |
| [`coo.md`](./coo.md) | COO | Operations, hiring, vendor management |
| [`general-counsel.md`](./general-counsel.md) | General Counsel | Legal / regulatory / IP risk |

6 of the 20-agent roster cap. Room to grow.

## File format

Each worker is a markdown file with YAML frontmatter that the Leader skill reads when it calls `client.beta.agents.create(...)`:

```yaml
---
name: <Worker name>
model: claude-opus-4-7      # or sonnet / haiku, per cost tradeoff
tools: [read, write, ...]   # agent_toolset_20260401 configs
version: 1
---

# System prompt
<the actual prompt body, 4–8 lines>
```

The body of the markdown IS the system prompt. No fluff sections.

## Provenance

All worker prompts in this directory are **clean-room** written for Pegasus by the project owner. No verbatim text copied from `gstack`, `oh-my-openagent`, `superpowers`, or other external skill packs. Licensed MIT — see [`../LICENSE`](../LICENSE).

If you fork Pegasus and want to import worker prompts from other packs, check the source pack's license first. Pegasus tolerates additions only when they are MIT-compatible or written from scratch.
