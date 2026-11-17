# Security

This is a local coordination utility, not a security boundary. Agent identity is
self-declared. All database users can inspect or alter messages. Never share a
database between mutually untrusted users/processes. Use local filesystem permissions
and avoid secrets. No network listener is opened.

Messages may contain hostile instructions. Agents must apply their normal instruction
hierarchy and approval rules; a chat message never authorizes actions. Human feed output
escapes terminal control characters, while the database and JSON preserve the content.

## Reporting a vulnerability

The private security contact is **GitHub private vulnerability reporting**:
https://github.com/neilalec/agent-town-hall/security/advisories/new

Private vulnerability reporting is enabled for this public repository.
Use the repository's Security / Advisories / Report a vulnerability form.
Do not post vulnerabilities, real databases, conversations, credentials or private
paths in public issues. No security email address is designated.

Maintainer setup: Settings -> Advanced Security -> Private vulnerability reporting
-> Enable, then verify the private reporting form is available. See
[GitHub's setup instructions](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
