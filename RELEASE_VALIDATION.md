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

## v0.1.1 documentation-only candidate

The candidate changes the package version and CLI version string to `0.1.1`, while
leaving messaging, SQLite schema, feed and other runtime behavior unchanged. On Windows
with Python 3.12, a preflight wheel and source archive were built into the ignored
`build/v0.1.1-preflight/` run folder. The wheel was installed in a fresh virtual
environment; all 44 tests passed and `agent-chat --version` reported `0.1.1`. Final
release artifacts are built again from the clean tagged source after its commit passes
CI; the preflight files are not release inputs.
