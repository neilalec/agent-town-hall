# Agent Town Hall v0.1.0 release checklist

Confirmed identity:
- GitHub: `neilalec/agent-town-hall`
- PyPI: `agent-town-hall`; CLI: `agent-chat`; Python import: `agent_chat`
- Version: `0.1.0`; license: MIT
- Copyright (c) 2026 Neil Massella

GitHub source publication and the v0.1.0 GitHub release are owner-approved.
The public repository exists and private vulnerability reporting is enabled.
**PyPI publication is not approved yet.** No automatic publishing workflow exists.

## Availability

See NAME_AVAILABILITY.json for dated read-only checks. Authenticated GitHub lookup
as the owner returned 404 for the target repository. PyPI project JSON and simple
index returned 404. No conflict was found, but availability is not a reservation
and must be rechecked immediately before publication.

## GitHub release gates

1. Run every Windows/macOS/Linux Python 3.10/3.12/3.14 job on the final commit.
   Inspect actual results and fix failures; do not weaken checks to make them green.
2. Rebuild reviewed wheel/sdist from that clean commit. Verify metadata, privacy,
   contents and SHA-256 sums. Test the wheel in a clean environment.
3. Point v0.1.0 at that exact tested commit. The old unpublished local candidate tag
   may be moved; never rewrite a published tag. Publish the approved GitHub release
   using GITHUB_RELEASE_v0.1.0.md and verified artifacts only after all checks pass.
4. Verify public source, license, release assets and private reporting enablement.

## PyPI is a separate step

Recheck name availability, obtain explicit upload approval, and publish only after
GitHub CI/release verification. Never imply that GitHub publication also publishes
a package on PyPI.

Local verification: RELEASE_VALIDATION.md. Existing private installations and
inboxes are outside this project and must not be used as release fixtures.

Trusted Publishing preparation and exact owner setup: [docs/PYPI_PUBLISHING.md](docs/PYPI_PUBLISHING.md). The manual upload workflow is prepared but must not be dispatched before separate PyPI approval.
