# v0.1.0 release checklist

This is a local candidate, not a published package. Do not create a repository,
push, tag remotely or upload a distribution until the owner approves publication.

Before publication:

- Confirm the final project/distribution name and check registry/repository availability.
- Confirm copyright ownership and the chosen MIT license.
- Choose the GitHub owner and a private security reporting channel; add project URLs.
- Review the source and built wheel/sdist for private data. Only synthetic tests belong here.
- Run the configured three-OS CI matrix after creating the approved remote repository.
- Rebuild the release artifacts from the reviewed commit and verify their contents.
- Publish v0.1.0 only with explicit approval. No auto-publishing workflow is provided.

Local verification is recorded in RELEASE_VALIDATION.md. Public CI execution and
native macOS/Linux execution remain unverified until that matrix runs. Mocked OS-path
tests are not equivalent to native operating-system tests.
