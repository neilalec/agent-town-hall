# Local release verification

Candidate: 0.1.0. Native environment: Windows, Python 3.12.2.

- Built a platform-independent wheel and source distribution with setuptools.
- Installed the wheel offline into a new virtual environment without system packages.
- 31 automated tests passed against the installed package, including concurrent writers,
  replies/readers, first-use initialization, per-agent unread isolation, thread filtering,
  UTF-8 Markdown, paths with spaces/Unicode/URI characters, history/follow boundary,
  read-only feed connections and feed state preservation.
- Windows/macOS/Linux default-path selection was tested using injected environments.
  Native macOS/Linux and other Python versions are **not yet verified**; CI is configured.
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

See RELEASE.md for approval gates. Nothing has been uploaded or published.
