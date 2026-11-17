# Agent Town Hall release record

## v0.1.0 — published

- Package: [`agent-town-hall` on PyPI](https://pypi.org/project/agent-town-hall/)
- GitHub: [source](https://github.com/neilalec/agent-town-hall), [release](https://github.com/neilalec/agent-town-hall/releases/tag/v0.1.0)
- Version/tag: `0.1.0` / `v0.1.0`
- Release source commit: `6115353c82a6dfc7881c29d4be26257df9471ea1`
- CLI: `agent-chat`; Python import: `agent_chat`; licence: MIT
- Copyright (c) 2026 Neil Massella

The GitHub release and PyPI project contain the same reviewed wheel and source
archive. Publication used GitHub Actions OIDC Trusted Publishing; no PyPI API token
is stored in the repository. The publishing workflow run is
[44098168860](https://github.com/neilalec/agent-town-hall/actions/runs/44098168860).
The release source and publishing-controls commit each passed all nine
Windows/macOS/Linux Python 3.10/3.12/3.14 CI jobs (18 jobs total).

The initial availability snapshot in [NAME_AVAILABILITY.json](NAME_AVAILABILITY.json)
records pre-publication 404 responses; it is historical and does not describe current
availability.

## Frozen v0.1.0 artifacts

Do not rebuild or replace the published v0.1.0 distributions, move its tag, or
regenerate its release checksums. The published SHA-256 values are:

```text
58ea87ac88ec2be89ed952df0fc12206aae1aab6dfda2ff39516203647c55c55  agent_town_hall-0.1.0-py3-none-any.whl
ee3a80e91b824b3355d94190a841330949fd2797e5432f9b5891cd8ff77c4127  agent_town_hall-0.1.0.tar.gz
```

The uploaded PyPI files were checked against the GitHub release hashes. The GitHub
release also includes `SHA256SUMS` for download verification.

## Future releases

The v0.1.0 publishing workflow is deliberately pinned to that release and has no
automatic trigger. A future release needs a reviewed version bump, new release
artifacts and checksums, an updated fail-closed verifier/workflow, passing CI, and an
explicitly approved manual publication. Do not treat a push, tag or GitHub release as
authorization to publish to PyPI. See [the Trusted Publishing record](docs/PYPI_PUBLISHING.md).

Local development checks are described in [RELEASE_VALIDATION.md](RELEASE_VALIDATION.md).
