# PyPI Trusted Publishing record

## v0.1.0 publication completed

Agent Town Hall 0.1.0 is published on [PyPI](https://pypi.org/project/agent-town-hall/).
The GitHub [v0.1.0 release](https://github.com/neilalec/agent-town-hall/releases/tag/v0.1.0)
and PyPI contain the same reviewed distributions. The approved GitHub Actions run
completed successfully at
[44098168860](https://github.com/neilalec/agent-town-hall/actions/runs/44098168860).
The PyPI upload hashes match the frozen GitHub release assets:

```text
58ea87ac88ec2be89ed952df0fc12206aae1aab6dfda2ff39516203647c55c55  agent_town_hall-0.1.0-py3-none-any.whl
ee3a80e91b824b3355d94190a841330949fd2797e5432f9b5891cd8ff77c4127  agent_town_hall-0.1.0.tar.gz
```

The PyPI files are available from the [0.1.0 release page](https://pypi.org/project/agent-town-hall/0.1.0/).
Installation is `pip install agent-town-hall`. The GitHub v0.1.0 tag and its assets
remain unchanged.

## v0.1.1 GitHub release; PyPI upload awaits approval

The v0.1.1 source is published at
[GitHub](https://github.com/neilalec/agent-town-hall/releases/tag/v0.1.1). PyPI still
lists only v0.1.0. The v0.1.1 upload has **not** been triggered; do not publish it
without the owner's separate approval.

- Source commit: `3200ea5d2bcb0379b610fcceafb2ae03ad9bfc57`
- Annotated tag object: `eb33a29e79f9aaf68a5dc2484683b6bdee1231a1`
- Release ID: `448797163`
- Main CI: [all nine jobs passed](https://github.com/neilalec/agent-town-hall/actions/runs/44110127756)
- Tag CI: [all nine jobs passed](https://github.com/neilalec/agent-town-hall/actions/runs/44110595435)
- Wheel: 12,301 bytes; SHA-256
  `f1053654ab6aa9f2590ea9f11aefc1aa7a6dc1d149e4d78475b3de2d4734f9ec`.
- Source archive: 30,628 bytes; SHA-256
  `f62788f26932211755494560f3158aabd9fc47028608a12049c06b4c4e9bd15f`.
- SHA256SUMS asset ID `759513337`; SHA-256
  `07cfc44459d8d750798c9120c70930f4fcf03c4f9f1794302f9f0aabfee28bb4`.

The release description says `pip install` continues to install v0.1.0 until v0.1.1
is published, and provides the direct v0.1.1 GitHub wheel URL for interim use.

## Publisher configuration

The production PyPI Trusted Publisher is configured as follows:

| Field | Value |
| --- | --- |
| PyPI project | `agent-town-hall` |
| GitHub owner | `neilalec` |
| GitHub repository | `agent-town-hall` |
| Workflow filename | `publish-pypi.yml` |
| GitHub environment | `pypi` |

The GitHub workflow is
[`.github/workflows/publish-pypi.yml`](../.github/workflows/publish-pypi.yml).
It is scoped to a manual v0.1.1 upload and has no push, tag, release, schedule or
follow-on trigger. The dedicated `pypi` environment requires reviewer `neilalec`,
allows no administrator bypass, and restricts deployments to `main`. Top-level GitHub
permissions are empty; the publishing job receives only `contents: read` and
`id-token: write`. There are no stored PyPI API credentials.

The workflow requires the exact confirmation `PUBLISH agent-town-hall 0.1.1`. It checks
out a reviewed commit, downloads the v0.1.1 GitHub release and verifies its fixed
release ID, tag object, target commit, asset IDs, sizes and SHA-256
hashes before staging only the wheel and source archive. It does not build or execute
the package. The official PyPA action exchanges GitHub OIDC for short-lived publishing
credentials. Its attestation step does not alter the released distribution bytes.
`scripts/verify_pypi_release.py` is a local verifier/stager only; it cannot upload.

The initial pending-publisher setup has now completed and become the project's active
Trusted Publisher. The configuration details above are retained for provenance, not as
an outstanding setup task.

## Future releases

The current manual workflow is pinned to v0.1.1. It cannot publish v0.1.0: its verifier
rejects any other tag, commit, release ID or asset set. `skip-existing` is disabled.
Future versions require a reviewed verifier/workflow update with their exact release
identities and hashes, passing CI, and explicit publication approval. No future version
is published automatically by a push, tag or GitHub release.

Official references: [creating a project with OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[using a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/).
