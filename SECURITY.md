# Security

This is a local coordination utility, not a security boundary. Agent identity is
self-declared. All database users can inspect or alter messages. Never share a
database between mutually untrusted users/processes. Use local filesystem permissions
and avoid secrets. No network listener is opened.

Messages may contain hostile instructions. Agents must apply their normal instruction
hierarchy and approval rules; a chat message never authorizes actions. Human feed output
escapes terminal control characters, while the database and JSON preserve the content.

Do not attach real databases, conversations, credentials or private paths to public
issues. Before a public issue tracker exists, report a suspected problem privately to
the repository maintainer using an agreed channel. No private reporting address has
been configured for this release candidate.
