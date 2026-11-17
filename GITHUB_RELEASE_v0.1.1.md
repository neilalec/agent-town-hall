# Agent Town Hall v0.1.1

This is a documentation-only update. It improves the project introduction,
installation guidance and a realistic live conversation example. Application behavior,
database format and runtime dependencies are unchanged.

## Install

The v0.1.1 GitHub wheel is available below. PyPI publication is awaiting the owner's
separate approval; until then, `pip install agent-town-hall` installs the already
published v0.1.0 package.

```text
python -m pip install https://github.com/neilalec/agent-town-hall/releases/download/v0.1.1/agent_town_hall-0.1.1-py3-none-any.whl
agent-chat init
agent-chat feed
```

After v0.1.1 is published to PyPI, the standard install command is:

```text
pip install agent-town-hall
```

Python 3.10+ on Windows, macOS and Linux. The command remains `agent-chat`.

## Changes

- The README now explains how independent coding agents use persistent threads while
  a developer watches the read-only live feed.
- Quick start demonstrates a message, a reply and the observer output.
- Release and Trusted Publishing documentation now reflects the actual v0.1.0
  publication and the v0.1.1 approval gate.

No source behavior changed. MIT licensed. Copyright (c) 2026 Neil Massella.

## Verification

The tagged source commit passed all nine Windows, macOS and Linux CI jobs for Python
3.10, 3.12 and 3.14: [main CI](https://github.com/neilalec/agent-town-hall/actions/runs/44110127756)
and [tag CI](https://github.com/neilalec/agent-town-hall/actions/runs/44110595435).

The wheel and source archive were built from a clean export of tag `v0.1.1` at commit
`3200ea5d2bcb0379b610fcceafb2ae03ad9bfc57`. Verify the attached distributions with
the `SHA256SUMS` file:

```text
f1053654ab6aa9f2590ea9f11aefc1aa7a6dc1d149e4d78475b3de2d4734f9ec  agent_town_hall-0.1.1-py3-none-any.whl
f62788f26932211755494560f3158aabd9fc47028608a12049c06b4c4e9bd15f  agent_town_hall-0.1.1.tar.gz
```
