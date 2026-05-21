# Architecture

Pegasus has four layers.

```text
L0 User command       /pegasus start|tell|status|stop
L1 Leader skill       validates spec, initializes state, renders status
L2 Driver routine     repeatable run prompt, stateless except project files
L3 Project repo       spec/current.md, workflow/state.json, events.ndjson
```

## State model

The project repository is the only durable runtime state. The driver may be a
fresh Claude Code session each run, so it must reload files before making any
choice.

## Worker model

Workers are optional. They are small role prompts for:

- building a lane;
- verifying a lane;
- reviewing risk/provenance/destructive actions.

Workers do not push or mark work done. They return evidence to the driver.

## Verification model

A lane is done only when the verification command or checklist named in the spec
passes and the driver records the evidence in `workflow/events.ndjson`.

## Routine registration

Pegasus may register a background routine only when the current Claude Code
runtime exposes a verified routine-registration surface. Otherwise it reports the
manual next command. Silent fake arming is forbidden.
