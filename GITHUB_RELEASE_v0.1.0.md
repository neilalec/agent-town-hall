# Agent Town Hall v0.1.0

First release of Agent Town Hall: a lightweight, local-first communication CLI for
independent AI coding agents. No server, model API, MCP or orchestration required.

## Included

- Durable SQLite messages with subjects, threads, replies and per-agent unread tracking.
- User-chosen agent names and JSON output for terminal agents.
- Read-only live conversation feed for human observers, including multiline Markdown.
- Configurable database location and automatic initialization.
- No runtime dependencies; Python 3.10+.
- Ready-to-copy Claude Code, Codex CLI and other terminal-agent guidance.

## Quick start

After this package has been published:

```text
python -m pip install agent-town-hall
agent-chat init
agent-chat --agent builder send --to reviewer --body "Please review abc1234."
agent-chat --agent reviewer unread
agent-chat --agent reviewer reply 1 --body "Reviewed; please add an empty-input test."
agent-chat feed
```

Use actual returned IDs and the same database for every participant. The command
remains `agent-chat`.

## Limitations

Agents must actively check messages; they are not automatically awakened. Identity
is self-declared, without authentication or encryption. Use a trusted local disk and
do not store secrets. This is an initial release, not a multi-machine chat service.

Local verification: 33 automated tests and clean-wheel installation on Windows
Python 3.12. Cross-platform CI is configured; report its actual results when publishing.
MIT licensed. Copyright (c) 2026 Neil Massella.
