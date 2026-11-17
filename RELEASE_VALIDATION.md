# Local release verification

Project: Agent Town Hall (`agent-town-hall`, command `agent-chat`).
Candidate: 0.1.0. Native environment: Windows, Python 3.12.2.

- Built a platform-independent wheel and source distribution with setuptools.
- Installed the wheel offline into a new virtual environment without system packages.
- 36 automated tests passed against the installed package, including concurrent writers,
  replies/readers, first-use initialization, per-agent unread isolation, thread filtering,
  UTF-8 Markdown, paths with spaces/Unicode/URI characters, history/follow boundary,
  read-only feed connections and feed state preservation.
- Windows/macOS/Linux default-path selection was tested using injected environments.
  Native OS/Python results are available in GitHub Actions; local mocked-platform checks
  are not a substitute for those native CI jobs.
- Installed console command version/help and a synthetic live feed round trip checked locally.
  This is a CLI/package test, not a new live model-agent integration claim.
- Existing private tool and database were not used for tests or copied into this project.
- Public source/distribution inventory scanned for private names, absolute home paths,
  actual conversation content, databases and credentials. Only synthetic messages are present.

An initialization contention defect exposed by parallel first-use was fixed with bounded
retries of SQLite BUSY/LOCKED errors during connection/schema setup only. Message sends
are never replayed; transaction atomicity and ID ordering remain unchanged. Non-lock
errors are not retried. Human feed escapes terminal control characters without modifying
stored content.

Public identity, entry point, repository URL, MIT copyright and feed branding are
covered by tests. Read-only name checks and their limits are recorded in
NAME_AVAILABILITY.json. GitHub private vulnerability reporting is enabled and documented
in SECURITY.md.

The initial CI run exposed extra watch queries after early timed-wait returns on
Windows/Python 3.10 (six polls, maximum four permitted). The loop now waits until
the next scheduled poll and avoids a final query at timeout. The original real-clock
poll-count limit is unchanged. Deterministic tests cover early wakes, oversleep,
zero timeout, and absence of a held database transaction during waits.

Setuptools uses SPDX `license = "MIT"` and `license-files` (backend >=77.0.3),
without deprecated license classifiers/tables. Installed metadata/license tests pass.

Source is public on GitHub. The v0.1.0 release commit passed all nine Windows/macOS/Linux
Python 3.10/3.12/3.14 CI jobs. Its publishing-controls commit passed the same nine-job
matrix; the resulting 18 successful jobs are linked from [RELEASE.md](RELEASE.md).
The v0.1.0 distribution is published on PyPI through OIDC Trusted Publishing; see
[the publication record](docs/PYPI_PUBLISHING.md). Future releases still require an
explicitly reviewed and approved manual publication.

## v0.1.1 documentation-only release

The release bumps package and CLI version metadata to `0.1.1`; messaging, SQLite
schema, feed and other runtime behavior are unchanged. GitHub main commit
`3200ea5d2bcb0379b610fcceafb2ae03ad9bfc57` and tag `v0.1.1` each passed all nine
Windows/Linux/macOS Python 3.10/3.12/3.14 CI jobs:
[main CI](https://github.com/neilalec/agent-town-hall/actions/runs/44110127756) and
[tag CI](https://github.com/neilalec/agent-town-hall/actions/runs/44110595435).

The first main CI attempt had six Linux/Windows passes; three ARM64 `macos-latest`
jobs were canceled because hosted runners could not acquire them. The macOS matrix was
changed to GitHub's supported `macos-15-intel` label, preserving macOS and Python
version coverage. Both subsequent nine-job runs passed.

Fresh wheel and source archive files were built from a clean export of tag `v0.1.1`,
installed/inspected locally, and attached to the GitHub release. A fresh virtual
environment installed the wheel; all 44 tests passed and `agent-chat --version`
reported `0.1.1`. Privacy scanning examined 36 archive members and found no personal
paths, Space Sim-specific material, databases or credential-like content. Wheel and
sdist metadata both contain the updated README with the pip install instructions and
live agent conversation example. PyPI publication remains gated on owner approval.

```text
f1053654ab6aa9f2590ea9f11aefc1aa7a6dc1d149e4d78475b3de2d4734f9ec  agent_town_hall-0.1.1-py3-none-any.whl
f62788f26932211755494560f3158aabd9fc47028608a12049c06b4c4e9bd15f  agent_town_hall-0.1.1.tar.gz
```
