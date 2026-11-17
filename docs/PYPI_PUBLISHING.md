# First PyPI publication: Agent Town Hall 0.1.0

**Prepared, not authorized to run yet. No PyPI upload has been triggered.**
The GitHub release and v0.1.0 tag remain unchanged. Publishing controls live on main,
separately from the frozen released application commit.

## What the owner must configure on PyPI

Log in to the intended PyPI maintainer account (it need not have the same name as
GitHub), with verified email and 2FA. Open https://pypi.org/manage/account/publishing/
and add a **pending GitHub Actions publisher** with exactly these fields:

| Field | Value |
| --- | --- |
| PyPI project name | `agent-town-hall` |
| GitHub repository owner | `neilalec` |
| GitHub repository name | `agent-town-hall` |
| Workflow filename | `publish-pypi.yml` |
| Environment name | `pypi` |

The workflow file is `.github/workflows/publish-pypi.yml`, but PyPI's filename field
gets **only** `publish-pypi.yml`. The environment must match exactly; do not omit it.
Use production PyPI, not TestPyPI. No API token, password secret or pre-upload is needed.
A pending publisher does not reserve the package name; recheck availability before the
approved upload. First successful use creates the project and converts the publisher
to a normal Trusted Publisher. This setup has not been performed on the owner's behalf.

Official guidance: [creating a project](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[publishing with OIDC](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

## GitHub controls already prepared

- Dedicated environment: `pypi`, required reviewer `neilalec`.
- Administrator bypass disabled; deployment branch limited to `main`.
- Self-review is allowed so the sole maintainer can dispatch then separately approve
  their own run. This is a manual checkpoint, not independent two-person approval.
- Only `workflow_dispatch`, on main, by `neilalec`; no push, tag, release, schedule,
  reusable-workflow or automatic follow-on event can publish.
- The confirmation must be exactly `PUBLISH agent-town-hall 0.1.0`.
- Top-level permissions are empty. Only the publishing job gets `contents: read`
  (GitHub release retrieval) and `id-token: write` (OIDC). No stored PyPI credentials.
- Checkout and the official PyPA publishing action are pinned to reviewed full SHAs.
- No build commands and no installation/execution of the downloaded package.
- Concurrent runs are serialized; existing PyPI files are not silently skipped.

The GitHub token used for read-only release downloads is the job's automatically
issued token, not a PyPI API token. The PyPA action exchanges OIDC for short-lived
publishing credentials and generates standard provenance attestations; package bytes
are not modified. This does not claim the workflow built the released artifacts.

## Frozen artifact boundary

`scripts/verify_pypi_release.py` checks the original release ID, annotated tag object,
tested application commit `6115353c82a6dfc7881c29d4be26257df9471ea1`, original asset
IDs/sizes, GitHub API digests, the downloaded GitHub SHA256SUMS and hardcoded reviewed
hashes. It rejects changed tags, replaced assets, missing/extra files, tampering or
an existing output directory. Only these two unchanged distributions are copied into
the clean upload directory; SHA256SUMS is **not** sent as a Python distribution:

```text
58ea87ac88ec2be89ed952df0fc12206aae1aab6dfda2ff39516203647c55c55  agent_town_hall-0.1.0-py3-none-any.whl
ee3a80e91b824b3355d94190a841330949fd2797e5432f9b5891cd8ff77c4127  agent_town_hall-0.1.0.tar.gz
```

The release is currently mutable on GitHub; pinned asset/tag identities and hashes
make replacement fail closed rather than trusting the current filename alone.
Ordinary CI package-build checks are separate and are never used as publish inputs.
Do not rebuild, replace release assets, move v0.1.0 or regenerate its checksums.

## Only after explicit publication approval

1. Confirm the pending publisher fields above and the environment reviewer rules.
2. Review the publishing-controls commit and its CI; verify v0.1.0 still targets the
   tested application commit and its assets still have the reviewed hashes.
3. Open Actions -> **Publish approved v0.1.0 to PyPI** -> Run workflow; choose main
   and enter the exact confirmation phrase. **Do not do this during preparation.**
4. In the waiting job, review the commit/artifact intent and approve deployment to
   `pypi` as `neilalec`. An agent must not approve this on the owner's behalf without
   explicit authorization. No upload or OIDC exchange occurs before this gate.
5. The job retrieves and verifies the release, then invokes the official PyPA action.
   Inspect verification/hash logs and PyPI results. A failure stops the upload path;
   investigate partial publication before retrying, never bypass checks or overwrite files.
6. Verify the PyPI version, both file hashes and a clean installation. Record the
   actual workflow/PyPI URLs. Until then do not claim Trusted Publishing is tested end to end.

Future releases cannot be published by changing a dispatch version input: there is
no such input. They require an explicitly reviewed change to version, tag, asset
identities and hashes plus a new owner approval/manual environment gate. This
workflow is intentionally scoped to the first 0.1.0 publication.

A safe local verifier-only check (no upload, OIDC or build) is:

```text
python scripts/verify_pypi_release.py --directory build/pypi-check-download --output build/pypi-check-upload
```

Use new directories each time. The helper uses authenticated `gh` for GitHub reads
and stages copies locally; it has no PyPI client or upload implementation.

## Preparation validation

44 local tests passed, including eight publication-policy/verifier tests, without
running the publishing action. A verifier-only live GitHub download/staging check
passed for the exact released assets. YAML parsing and environment rule readback
passed. These are preparation checks, not an end-to-end OIDC/upload test; that must
wait for owner approval and the PyPI pending-publisher configuration.
