# Agent Town Hall v0.1.0 release checklist

Confirmed identity:
- GitHub: `neilalec/agent-town-hall`
- PyPI: `agent-town-hall`; CLI: `agent-chat`; Python import: `agent_chat`
- Version: `0.1.0`; license: MIT
- Copyright (c) 2026 Neil Massella

This is a local, publication-ready candidate, not a published package. No remote
repository, remote tag or upload is authorized yet.

## Availability

See NAME_AVAILABILITY.json for dated read-only checks. Authenticated GitHub lookup
as the owner returned 404 for the target repository. PyPI project JSON and simple
index returned 404. No conflict was found, but availability is not a reservation
and must be rechecked immediately before publication.

## Remaining publication gates

1. Obtain the owner's explicit approval to create the remote and push the reviewed source.
2. Recheck names, create the approved GitHub repository, and run the configured
   Windows/macOS/Linux Python 3.10/3.12/3.14 CI matrix. Native macOS/Linux execution
   remains unverified locally; do not present the configured matrix as a passing run.
3. Enable GitHub private vulnerability reporting in repository Settings -> Advanced
   Security, and verify the private form before announcing it. SECURITY.md documents
   the intended channel; it does not claim enablement. No email address is invented.
4. Rebuild reviewed wheel/sdist, inspect source/artifacts for private data, and verify
   package name, entry point, author, license and repository metadata.
5. With explicit publishing approval, create release/tag v0.1.0 using
   GITHUB_RELEASE_v0.1.0.md and upload the reviewed artifacts to PyPI. No automatic
   publication workflow is installed. Local checks do not reserve a package name.

Local verification: RELEASE_VALIDATION.md. Existing private installations and
inboxes are outside this project and must not be used as release fixtures.
