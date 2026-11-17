"""Verify and stage only the approved GitHub v0.1.0 assets; never build or upload."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

REPOSITORY = "neilalec/agent-town-hall"
TAG = "v0.1.0"
COMMIT = "6115353c82a6dfc7881c29d4be26257df9471ea1"
TAG_OBJECT = "efad8be28e0a9eb9d1cdbf1f9b7b7c88a76d720c"
RELEASE_ID = 448680974
FILES = {
    "agent_town_hall-0.1.0-py3-none-any.whl": {
        "sha256": "58ea87ac88ec2be89ed952df0fc12206aae1aab6dfda2ff39516203647c55c55",
        "id": 759208454, "size": 12000,
    },
    "agent_town_hall-0.1.0.tar.gz": {
        "sha256": "ee3a80e91b824b3355d94190a841330949fd2797e5432f9b5891cd8ff77c4127",
        "id": 759208453, "size": 26031,
    },
    "SHA256SUMS": {
        "sha256": "c3f2c37654767e1395cab89385b80a6a3b23f2d241818311021c592129b3a717",
        "id": 759208452, "size": 200,
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_metadata(release, tag_ref, tag_object):
    require(release.get("id") == RELEASE_ID and release.get("tag_name") == TAG,
            "Release identity differs from the approved v0.1.0 release")
    require(release.get("html_url") == f"https://github.com/{REPOSITORY}/releases/tag/{TAG}",
            "Unexpected release URL")
    require(release.get("draft") is False and release.get("prerelease") is False,
            "Release must be published and stable")
    require(tag_ref.get("ref") == f"refs/tags/{TAG}" and
            tag_ref.get("object", {}).get("type") == "tag" and
            tag_ref.get("object", {}).get("sha") == TAG_OBJECT,
            "Approved annotated tag was changed")
    require(tag_object.get("sha") == TAG_OBJECT and
            tag_object.get("object", {}).get("type") == "commit" and
            tag_object.get("object", {}).get("sha") == COMMIT,
            "Tag no longer targets the approved tested commit")
    assets = release.get("assets", [])
    require(len(assets) == len(FILES) and {a.get("name") for a in assets} == set(FILES),
            "Unexpected, duplicate or missing release assets")
    for asset in assets:
        approved = FILES[asset["name"]]
        require(asset.get("id") == approved["id"] and asset.get("size") == approved["size"]
                and asset.get("state") == "uploaded"
                and asset.get("digest") == "sha256:" + approved["sha256"],
                "Release asset identity/digest changed: " + asset["name"])


def verify_and_stage(directory, output):
    directory, output = Path(directory), Path(output)
    require(not directory.is_symlink() and directory.is_dir(), "Invalid download directory")
    require({p.name for p in directory.iterdir()} == set(FILES), "Unexpected download contents")
    for name, approved in FILES.items():
        path = directory / name
        require(path.is_file() and not path.is_symlink(), "Non-regular asset: " + name)
        raw = path.read_bytes()
        require(len(raw) == approved["size"] and hashlib.sha256(raw).hexdigest() == approved["sha256"],
                "Asset checksum differs from the reviewed release: " + name)
    manifest = {}
    for line in (directory / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ")
        require(name not in manifest, "Duplicate checksum entry")
        manifest[name] = digest
    expected = {name: info["sha256"] for name, info in FILES.items() if name != "SHA256SUMS"}
    require(manifest == expected, "GitHub SHA256SUMS does not match the approved distributions")
    # Fail if output exists: never mix old/unreviewed files into the upload directory.
    output.mkdir(parents=True, exist_ok=False)
    for name, digest in expected.items():
        target = output / name
        shutil.copyfile(directory / name, target)
        require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, "Staged copy changed")
    print(json.dumps({"verified_commit": COMMIT, "release": TAG, "packages": expected}, sort_keys=True))


def gh_json(endpoint):
    result = subprocess.run(["gh", "api", endpoint], check=True, capture_output=True,
                            text=True, encoding="utf-8", timeout=60)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_metadata(
            gh_json(f"repos/{REPOSITORY}/releases/tags/{TAG}"),
            gh_json(f"repos/{REPOSITORY}/git/ref/tags/{TAG}"),
            gh_json(f"repos/{REPOSITORY}/git/tags/{TAG_OBJECT}"))
        # Download only fixed, approved filenames. No user-supplied tag or package paths.
        require(not args.directory.exists(), "Download directory already exists")
        command = ["gh", "release", "download", TAG, "--repo", REPOSITORY,
                   "--dir", str(args.directory)]
        for name in FILES:
            command += ["--pattern", name]
        subprocess.run(command, check=True, timeout=120)
        verify_and_stage(args.directory, args.output)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Release verification failed: {error}\n")


if __name__ == "__main__":
    main()
