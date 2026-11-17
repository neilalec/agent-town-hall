# Agent Town Hall release record

## v0.1.0 - published

- PyPI: https://pypi.org/project/agent-town-hall/0.1.0/
- GitHub: https://github.com/neilalec/agent-town-hall/releases/tag/v0.1.0
- Source commit: `6115353c82a6dfc7881c29d4be26257df9471ea1`
- GitHub Actions OIDC publication run: [44098168860](https://github.com/neilalec/agent-town-hall/actions/runs/44098168860)
- Both distributions on PyPI match the reviewed GitHub release hashes; see the
  v0.1.0 section in [docs/PYPI_PUBLISHING.md](docs/PYPI_PUBLISHING.md).

Do not move the v0.1.0 tag or rebuild/replace its wheel, sdist or checksums.

## v0.1.1 - GitHub release published; PyPI approval pending

This documentation-only release improves the README introduction, installation guide
and live agent-conversation example. No messaging or feed behavior changed.

- GitHub release: https://github.com/neilalec/agent-town-hall/releases/tag/v0.1.1
- Source commit: `3200ea5d2bcb0379b610fcceafb2ae03ad9bfc57`
- Annotated tag object: `eb33a29e79f9aaf68a5dc2484683b6bdee1231a1`
- Release ID: `448797163`
- Main CI: [all nine jobs passed](https://github.com/neilalec/agent-town-hall/actions/runs/44110127756)
- Tag CI: [all nine jobs passed](https://github.com/neilalec/agent-town-hall/actions/runs/44110595435)
- PyPI still lists v0.1.0. The v0.1.1 OIDC upload has not been triggered and awaits
  explicit owner approval.

The GitHub release includes these distributions and their SHA256SUMS manifest:

```text
f1053654ab6aa9f2590ea9f11aefc1aa7a6dc1d149e4d78475b3de2d4734f9ec  agent_town_hall-0.1.1-py3-none-any.whl
f62788f26932211755494560f3158aabd9fc47028608a12049c06b4c4e9bd15f  agent_town_hall-0.1.1.tar.gz
```

See [GITHUB_RELEASE_v0.1.1.md](GITHUB_RELEASE_v0.1.1.md) and the
[Trusted Publishing record](docs/PYPI_PUBLISHING.md).

## Future releases

The current OIDC workflow is manually gated and pinned to v0.1.1. Any future version
requires a reviewed version bump, new artifacts and hashes, updated verifier/workflow,
passing CI, and explicit publication approval. Pushes, tags and GitHub releases never
publish automatically.

Local test and release verification details are in [RELEASE_VALIDATION.md](RELEASE_VALIDATION.md).
