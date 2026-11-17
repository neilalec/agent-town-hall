"""Publication controls are tested without OIDC, credentials, or upload calls."""
import contextlib
import copy
import hashlib
import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import verify_pypi_release as verifier


class ReleaseVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="publish-verification-")
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "download"
        self.directory.mkdir()
        self.output = Path(self.tmp.name) / "upload"
        names = [n for n in verifier.FILES if n != "SHA256SUMS"]
        payloads = {names[0]: b"synthetic wheel", names[1]: b"synthetic source archive"}
        manifest = "".join(hashlib.sha256(payloads[n]).hexdigest()+"  "+n+"\n" for n in names)
        payloads["SHA256SUMS"] = manifest.encode("ascii")
        approved = copy.deepcopy(verifier.FILES)
        for name, data in payloads.items():
            (self.directory / name).write_bytes(data)
            approved[name]["sha256"] = hashlib.sha256(data).hexdigest()
            approved[name]["size"] = len(data)
        self.addCleanup(patch.stopall)
        patch.object(verifier, "FILES", approved).start()
        self.release = {
            "id": verifier.RELEASE_ID, "tag_name": verifier.TAG,
            "html_url": f"https://github.com/{verifier.REPOSITORY}/releases/tag/{verifier.TAG}",
            "draft": False, "prerelease": False,
            "assets": [{"name": n, "id": a["id"], "size": a["size"], "state": "uploaded",
                        "digest": "sha256:"+a["sha256"]} for n,a in approved.items()],
        }
        self.tag_ref = {"ref": "refs/tags/"+verifier.TAG,
                        "object": {"type": "tag", "sha": verifier.TAG_OBJECT}}
        self.tag = {"sha": verifier.TAG_OBJECT, "object": {"type": "commit", "sha": verifier.COMMIT}}

    def validate(self):
        verifier.validate_metadata(self.release, self.tag_ref, self.tag)

    def test_approved_metadata_and_exact_two_staged_packages(self):
        self.validate()
        with contextlib.redirect_stdout(io.StringIO()):
            verifier.verify_and_stage(self.directory, self.output)
        self.assertEqual({p.name for p in self.output.iterdir()}, set(verifier.FILES)-{"SHA256SUMS"})
        for f in self.output.iterdir():
            self.assertEqual(f.read_bytes(), (self.directory/f.name).read_bytes())

    def test_tampered_distribution_or_manifest_stops_before_staging(self):
        for name in verifier.FILES:
            with self.subTest(name=name):
                path = self.directory/name; original = path.read_bytes()
                path.write_bytes(original+b"tampered")
                with self.assertRaises(ValueError):verifier.verify_and_stage(self.directory,self.output)
                self.assertFalse(self.output.exists())
                path.write_bytes(original)

    def test_missing_or_extra_download_rejected(self):
        path = self.directory/"unexpected.whl"; path.write_bytes(b"not approved")
        with self.assertRaises(ValueError):verifier.verify_and_stage(self.directory,self.output)
        path.unlink()
        (self.directory/"SHA256SUMS").unlink()
        with self.assertRaises(ValueError):verifier.verify_and_stage(self.directory,self.output)
        self.assertFalse(self.output.exists())

    def test_changed_release_or_tag_rejected(self):
        cases = [("release id", self.release, "id", 0),
                 ("future version", self.release, "tag_name", "v0.2.0"),
                 ("draft", self.release, "draft", True),
                 ("prerelease", self.release, "prerelease", True),
                 ("tag commit", self.tag["object"], "sha", "0"*40),
                 ("tag object", self.tag_ref["object"], "sha", "0"*40)]
        for label, obj, key, bad in cases:
            with self.subTest(label=label):
                old = obj[key]; obj[key] = bad
                with self.assertRaises(ValueError):self.validate()
                obj[key] = old

    def test_replaced_asset_or_digest_rejected(self):
        for key in ["id", "size", "digest", "state"]:
            with self.subTest(key=key):
                asset = self.release["assets"][0]; old = asset[key];asset[key] = "changed"
                with self.assertRaises(ValueError):self.validate()
                asset[key] = old

    def test_duplicate_or_missing_asset_rejected(self):
        assets = self.release["assets"]
        self.release["assets"] = assets+[assets[0]]
        with self.assertRaises(ValueError):self.validate()
        self.release["assets"] = assets[:-1]
        with self.assertRaises(ValueError):self.validate()

    def test_existing_upload_directory_not_reused(self):
        self.output.mkdir();(self.output/"private.txt").write_bytes(b"retain")
        with self.assertRaises(FileExistsError):verifier.verify_and_stage(self.directory,self.output)
        self.assertEqual((self.output/"private.txt").read_bytes(),b"retain")


class PublishingWorkflowPolicyTests(unittest.TestCase):
    def test_manual_only_pinned_oidc_workflow(self):
        root = Path(__file__).resolve().parents[1]
        text = (root/".github/workflows/publish-pypi.yml").read_text()
        triggers = re.search(r"(?ms)^on:\n(.*?)(?=^permissions:)", text).group(1)
        self.assertEqual(re.findall(r"^  ([a-z_]+):",triggers,re.M),["workflow_dispatch"])
        self.assertIn("permissions: {}",text)
        self.assertEqual(text.count("id-token: write"),1)
        self.assertIn("name: pypi",text)
        self.assertIn("github.ref == 'refs/heads/main'",text)
        self.assertIn("github.actor == 'neilalec'",text)
        self.assertIn("inputs.confirmation == 'PUBLISH agent-town-hall 0.1.0'",text)
        uses = re.findall(r"uses: (\S+)",text)
        self.assertEqual(len(uses),2)
        self.assertTrue(all(re.fullmatch(r"[^@]+@[0-9a-f]{40}",u) for u in uses))
        self.assertTrue(any(u.startswith("pypa/gh-action-pypi-publish@") for u in uses))
        self.assertNotIn("secrets.",text)
        self.assertNotRegex(text,r"pip wheel|python[3]? -m build|skip-existing: true|password:")
        self.assertIn("packages-dir: publish-dist/",text)
        self.assertIn("verify_pypi_release.py",text)


if __name__ == "__main__":unittest.main()
