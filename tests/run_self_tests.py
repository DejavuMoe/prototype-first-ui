#!/usr/bin/env python3
"""End-to-end self-tests for the prototype-first-ui Skill package."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import traceback
from typing import Callable, Dict, List, Optional, Sequence, Tuple
import zipfile

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
PYTHON = sys.executable
BASE_ENV = dict(
    os.environ,
    PYTHONDONTWRITEBYTECODE="1",
    GIT_TERMINAL_PROMPT="0",
    GIT_CONFIG_COUNT="2",
    GIT_CONFIG_KEY_0="commit.gpgsign",
    GIT_CONFIG_VALUE_0="false",
    GIT_CONFIG_KEY_1="tag.gpgsign",
    GIT_CONFIG_VALUE_1="false",
)


class CommandError(AssertionError):
    pass


def run(
    command: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    expect: int = 0,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    merged = dict(BASE_ENV)
    if env:
        merged.update(env)
    if os.environ.get("PUI_TEST_TRACE") == "1":
        print("TRACE RUN: %s" % " ".join(str(value) for value in command), flush=True)
    result = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        env=merged,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=45,
    )
    if result.returncode != expect:
        raise CommandError(
            "Command returned %d, expected %d:\n%s\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (result.returncode, expect, " ".join(command), result.stdout, result.stderr)
        )
    return result


def run_fail(command: Sequence[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    if os.environ.get("PUI_TEST_TRACE") == "1":
        print("TRACE RUN-FAIL: %s" % " ".join(str(value) for value in command), flush=True)
    result = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        env=BASE_ENV,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=45,
    )
    if result.returncode == 0:
        raise CommandError("Command unexpectedly succeeded: %s" % " ".join(command))
    return result


def git(repo: Path, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(repo), *args], expect=expect)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def init_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    run(["git", "init", "-b", "master", str(repo)])
    git(repo, "config", "user.name", "Prototype Test")
    git(repo, "config", "user.email", "prototype@example.invalid")


def valid_inventory(method: str = "rendered-dom") -> Dict[str, object]:
    return {
        "schemaVersion": 1,
        "profile": "operational-strict",
        "capture": {
            "method": method,
            "sources": ["dom-content.json"],
            "capturedAt": "2026-08-29T00:00:00Z",
            "surfaces": [{"source": "dom-content.json", "url": "http://127.0.0.1/"}],
            "limitations": [],
        },
        "briefSources": [],
        "approvedCopySources": [],
        "items": [
            {
                "id": "content-upload",
                "text": "Upload",
                "channels": ["text", "aria-label"],
                "locations": ["button#upload"],
                "visibility": ["visible"],
                "captures": ["dom-content.json"],
                "purpose": "user-action",
                "origin": "production-behavior",
                "decision": "allow",
                "evidence": {"source": "src/actions.ts", "reference": "upload action"},
                "flags": [],
                "notes": None,
            }
        ],
    }


def test_content_audit() -> str:
    with tempfile.TemporaryDirectory(prefix="pui-content-") as raw:
        root = Path(raw)
        capture = {
            "schemaVersion": 1,
            "generator": "prototype-first-ui/collect_dom_content.js",
            "capturedAt": "2026-08-29T00:00:00Z",
            "page": {
                "url": "http://127.0.0.1:8000/",
                "title": "Objects",
                "language": "en",
                "viewport": {"width": 1280, "height": 800, "devicePixelRatio": 1},
            },
            "items": [
                {"text": "Upload", "channel": "text", "location": "button#upload", "visibility": "visible"},
                {"text": "Upload", "channel": "aria-label", "location": "button#upload", "visibility": "visible"},
                {"text": "No objects", "channel": "text", "location": "main", "visibility": "visible"},
                {
                    "text": "Built for independent developers",
                    "channel": "text",
                    "location": "header p",
                    "visibility": "visible",
                },
                {
                    "text": "object-browser",
                    "channel": "data-*",
                    "location": "main[data-screen-id]",
                    "visibility": "visible",
                },
            ],
            "limitations": ["Only the current state is captured."],
        }
        capture_path = root / "capture.json"
        brief_path = root / "brief.txt"
        inventory_path = root / "content-inventory.json"
        write_json(capture_path, capture)
        write(brief_path, "Design a private object browser built for independent developers.")

        run(
            [
                PYTHON,
                str(SCRIPTS / "content_audit.py"),
                "seed",
                "--capture",
                str(capture_path),
                "--profile",
                "operational-strict",
                "--brief-file",
                str(brief_path),
                "--output",
                str(inventory_path),
            ]
        )
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        assert_true(len(inventory["items"]) == 4, "Duplicate visible/ARIA strings should be grouped")
        by_text = {item["text"]: item for item in inventory["items"]}
        assert_true("brief-overlap" in by_text["Built for independent developers"]["flags"], "Brief leak was not flagged")
        assert_true("promotional-language" in by_text["Built for independent developers"]["flags"], "Promotional copy was not flagged")

        classifications = {
            "Upload": ("user-action", "production-behavior", {"source": "src/actions.ts", "reference": "upload"}),
            "No objects": ("empty-state", "production-behavior", {"source": "src/state.ts", "reference": "empty"}),
            "object-browser": ("machine-identifier", "production-domain", None),
            "Built for independent developers": ("approved-product-copy", "task-brief", None),
        }
        for item in inventory["items"]:
            purpose, origin, evidence = classifications[item["text"]]
            item.update({"purpose": purpose, "origin": origin, "decision": "allow", "evidence": evidence})
        write_json(inventory_path, inventory)
        failed = run_fail([PYTHON, str(SCRIPTS / "content_audit.py"), "check", "--inventory", str(inventory_path)])
        assert_true("prohibited origin" in failed.stderr or "not allowed" in failed.stderr, "Bad copy should fail content check")

        inventory["items"] = [item for item in inventory["items"] if item["text"] != "Built for independent developers"]
        write_json(inventory_path, inventory)
        run([PYTHON, str(SCRIPTS / "content_audit.py"), "check", "--inventory", str(inventory_path)])

        upload_item = next(item for item in inventory["items"] if item["text"] == "Upload")
        upload_item["origin"] = "unknown"
        write_json(inventory_path, inventory)
        unknown = run_fail([PYTHON, str(SCRIPTS / "content_audit.py"), "check", "--inventory", str(inventory_path)])
        assert_true("origin is unknown" in unknown.stderr, "Unknown origin should block final content sign-off")
        upload_item["origin"] = "production-behavior"
        write_json(inventory_path, inventory)
        run([PYTHON, str(SCRIPTS / "content_audit.py"), "check", "--inventory", str(inventory_path)])

        source = root / "source"
        write(source / "index.html", '<main data-screen-id="object-browser"><button aria-label="Upload">Upload</button></main>')
        static_capture = root / "static.json"
        static_inventory = root / "static-inventory.json"
        run([PYTHON, str(SCRIPTS / "content_audit.py"), "static-scan", "--root", str(source), "--output", str(static_capture)])
        run(
            [
                PYTHON,
                str(SCRIPTS / "content_audit.py"),
                "seed",
                "--capture",
                str(static_capture),
                "--profile",
                "operational-strict",
                "--output",
                str(static_inventory),
            ]
        )
        static_data = json.loads(static_inventory.read_text(encoding="utf-8"))
        for item in static_data["items"]:
            if item["text"] == "object-browser":
                item.update({"purpose": "machine-identifier", "origin": "production-domain", "decision": "allow"})
            else:
                item.update({"purpose": "user-action", "origin": "production-behavior", "decision": "allow"})
        write_json(static_inventory, static_data)
        run_fail([PYTHON, str(SCRIPTS / "content_audit.py"), "check", "--inventory", str(static_inventory)])
        run(
            [
                PYTHON,
                str(SCRIPTS / "content_audit.py"),
                "check",
                "--inventory",
                str(static_inventory),
                "--allow-static",
            ]
        )
    return "Rendered inventory grouping, leak flags, strict rejection, and provisional static fallback passed."


def test_bootstrap() -> str:
    with tempfile.TemporaryDirectory(prefix="pui-bootstrap-") as raw:
        root = Path(raw)
        fresh = root / "fresh"
        fresh.mkdir()
        run([PYTHON, str(SCRIPTS / "bootstrap.py"), "init", "--repo", str(fresh)])
        assert_true(git(fresh, "symbolic-ref", "--short", "HEAD").stdout.strip() == "master", "New repository must default to master")
        repo = root / "repo"
        snapshot = root / "snapshot"
        init_repo(repo)
        write(repo / ".gitignore", "node_modules/\n")
        write(repo / "README.md", "baseline\n")
        write(repo / "build" / "source.txt", "tracked source despite generated-looking directory\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "old history")
        old_head = git(repo, "rev-parse", "HEAD").stdout.strip()

        write(repo / "README.md", "dirty working tree\n")
        (repo / "staged.bin").write_bytes(bytes(range(256)))
        git(repo, "add", "staged.bin")
        write(repo / "new.txt", "untracked\n")
        write(repo / "build" / "untracked-source.txt", "must survive exclusion\n")
        write(repo / "node_modules" / "ignored.txt", "regenerable\n")
        write(repo / ".env", "LOCAL_SECRET=preserved-only-in-local-recovery\n")
        symlink_created = False
        try:
            os.symlink("README.md", repo / "readme-link")
            symlink_created = True
        except (OSError, NotImplementedError):
            pass
        git(repo, "remote", "add", "origin", "https://user:secret@example.com/repo.git?token=x#fragment")

        run(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "snapshot",
                "--repo",
                str(repo),
                "--output",
                str(snapshot),
            ]
        )
        run(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "verify-snapshot",
                "--repo",
                str(repo),
                "--snapshot-dir",
                str(snapshot),
            ]
        )
        metadata_text = (snapshot / "metadata.json").read_text(encoding="utf-8")
        assert_true("user:secret" not in metadata_text and "token=x" not in metadata_text, "Remote credentials were not redacted")
        metadata = json.loads(metadata_text)
        assert_true(metadata["remotesRedacted"][0]["fetch"] == "https://example.com/repo.git", "Unexpected redacted remote")
        assert_true((snapshot / "history.bundle").is_file(), "History bundle missing")
        assert_true((snapshot / "working-tree.patch").is_file(), "Working tree patch missing")
        assert_true((snapshot / "index.patch").is_file(), "Index patch missing")
        assert_true((snapshot / "VERIFIED.json").is_file(), "Verified marker missing")
        if os.name != "nt":
            assert_true(stat.S_IMODE(snapshot.stat().st_mode) == 0o700, "Snapshot directory should be owner-only")
            for protected_file in ("working-tree.zip", "history.bundle", "metadata.json", "SHA256SUMS", "VERIFIED.json"):
                assert_true(
                    stat.S_IMODE((snapshot / protected_file).stat().st_mode) == 0o600,
                    "%s should be owner-readable/writable only" % protected_file,
                )
        bundle_heads = run(["git", "bundle", "list-heads", str(snapshot / "history.bundle")]).stdout
        assert_true(old_head in bundle_heads, "Old HEAD not recoverable from bundle")

        with zipfile.ZipFile(snapshot / "working-tree.zip") as archive:
            names = set(archive.namelist())
            assert_true("README.md" in names, "Tracked file missing from archive")
            assert_true("build/source.txt" in names, "Tracked file under generated-looking directory was lost")
            assert_true("build/untracked-source.txt" in names, "Non-ignored untracked file under generated-looking directory was lost")
            assert_true("new.txt" in names and ".env" in names, "Working tree files missing")
            assert_true("node_modules/ignored.txt" not in names, "Ignored generated dependency should be omitted")
            assert_true(not any(name == ".git" or name.startswith(".git/") for name in names), ".git leaked into working archive")
            if symlink_created:
                info = archive.getinfo("readme-link")
                mode = info.external_attr >> 16
                assert_true(stat.S_ISLNK(mode), "Symlink was followed instead of archived as a link")

        tampered = root / "tampered"
        shutil.copytree(snapshot, tampered)
        with (tampered / "working-tree.zip").open("ab") as handle:
            handle.write(b"tamper")
        run_fail(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "verify-snapshot",
                "--repo",
                str(repo),
                "--snapshot-dir",
                str(tampered),
            ]
        )

        stale_repo = root / "stale-repo"
        stale_snapshot = root / "stale-snapshot"
        init_repo(stale_repo)
        write(stale_repo / "file.txt", "one\n")
        git(stale_repo, "add", "-A")
        git(stale_repo, "commit", "-m", "one")
        run([PYTHON, str(SCRIPTS / "bootstrap.py"), "snapshot", "--repo", str(stale_repo), "--output", str(stale_snapshot)])
        write(stale_repo / "file.txt", "two\n")
        git(stale_repo, "add", "-A")
        git(stale_repo, "commit", "-m", "two")
        stale = run_fail(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "init",
                "--repo",
                str(stale_repo),
                "--snapshot-dir",
                str(stale_snapshot),
                "--yes-reset-history",
            ]
        )
        assert_true("HEAD changed" in stale.stderr, "A stale history bundle should block reset")
        assert_true((stale_repo / ".git").is_dir(), "Stale-snapshot refusal was destructive")

        result = run_fail(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "init",
                "--repo",
                str(repo),
                "--snapshot-dir",
                str(snapshot),
                "--branch",
                "master",
                "--commit",
            ]
        )
        assert_true("--yes-reset-history" in result.stderr, "Explicit reset flag was not enforced")
        assert_true((repo / ".git").is_dir(), "Failed reset attempt removed .git")

        run(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "scaffold",
                "--repo",
                str(repo),
                "--project-name",
                "Test App",
                "--project-slug",
                "test-app",
                "--surface-type",
                "operational",
                "--content-profile",
                "operational-strict",
            ]
        )
        assert_true("Test App" in (repo / "AGENTS.md").read_text(encoding="utf-8"), "Scaffold replacement failed")

        readonly_metadata = repo / ".git" / "readonly-test"
        write(readonly_metadata, "Read-only Git metadata must not block an authorized reset.\n")
        readonly_metadata.chmod(stat.S_IREAD)

        run(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "init",
                "--repo",
                str(repo),
                "--snapshot-dir",
                str(snapshot),
                "--branch",
                "master",
                "--yes-reset-history",
                "--commit",
            ]
        )
        assert_true(git(repo, "rev-list", "--count", "HEAD").stdout.strip() == "1", "New history must have one root commit")
        assert_true(git(repo, "remote").stdout.strip() == "", "Remote was reattached")
        assert_true(git(repo, "branch", "--show-current").stdout.strip() == "master", "Wrong branch")
        assert_true(git(repo, "config", "--local", "--get", "user.name").stdout.strip() == "Prototype Test", "Local identity not preserved")
        old_object = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", old_head],
            env=BASE_ENV,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=45,
        )
        assert_true(old_object.returncode != 0, "Old commit unexpectedly remains in new object database")

        sub_repo = root / "submodule-repo"
        sub_snapshot = root / "submodule-snapshot"
        init_repo(sub_repo)
        write(sub_repo / "file.txt", "x\n")
        write(
            sub_repo / ".gitmodules",
            '[submodule "vendor/example"]\n\tpath = vendor/example\n\turl = https://example.invalid/vendor.git\n',
        )
        git(sub_repo, "add", "-A")
        git(sub_repo, "commit", "-m", "submodule declaration")
        run([PYTHON, str(SCRIPTS / "bootstrap.py"), "snapshot", "--repo", str(sub_repo), "--output", str(sub_snapshot)])
        refused = run_fail(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "init",
                "--repo",
                str(sub_repo),
                "--snapshot-dir",
                str(sub_snapshot),
                "--yes-reset-history",
            ]
        )
        assert_true("submodules" in refused.stderr.lower(), "Submodule reset was not refused")
        assert_true((sub_repo / ".git").is_dir(), "Submodule refusal was destructive")

        work_repo = root / "worktree-repo"
        linked = root / "linked-worktree"
        work_snapshot = root / "worktree-snapshot"
        init_repo(work_repo)
        write(work_repo / "file.txt", "x\n")
        git(work_repo, "add", "-A")
        git(work_repo, "commit", "-m", "base")
        git(work_repo, "worktree", "add", "-b", "linked", str(linked))
        run([PYTHON, str(SCRIPTS / "bootstrap.py"), "snapshot", "--repo", str(work_repo), "--output", str(work_snapshot)])
        refused = run_fail(
            [
                PYTHON,
                str(SCRIPTS / "bootstrap.py"),
                "init",
                "--repo",
                str(work_repo),
                "--snapshot-dir",
                str(work_snapshot),
                "--yes-reset-history",
            ]
        )
        assert_true("worktrees" in refused.stderr.lower(), "Multiple worktrees were not refused")
    return "Snapshot privacy modes, redaction, archive completeness, tamper/stale detection, explicit authorization, local reset, submodule and worktree refusal passed."


def make_workflow_repo(root: Path) -> tuple[Path, str]:
    repo = root / "workflow-repo"
    init_repo(repo)
    write(repo / "AGENTS.md", "# Agent rules\n")
    write(repo / "docs" / "product" / "constraints.md", "# Constraints\n")
    write(repo / "src" / "app.ts", "export const existing = true;\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "chore: baseline")

    project = repo / "designs" / "app"
    write(project / "index.html", '<link rel="stylesheet" href="styles.css"><button data-component-id="upload">Upload</button>\n')
    write(project / "styles.css", "button { color: black; }\n")
    (project / "image.bin").write_bytes(b"\x00\xff\x01")
    write_json(
        project / "design-review.json",
        {
            "schemaVersion": 1,
            "assets": [{"path": "index.html", "status": "approved", "approvalEvidence": "Test user approved this exact preview."}],
        },
    )
    write_json(project / "content-inventory.json", valid_inventory())
    write_json(
        project / "ui-contract.json",
        {
            "schemaVersion": 2,
            "project": {"name": "App", "slug": "app", "surfaceType": "operational"},
            "content": {
                "defaultProfile": "operational-strict",
                "inventory": "content-inventory.json",
                "approvedCopySources": [],
            },
            "designSources": None,
            "surfaces": [
                {
                    "id": "object-browser",
                    "contentProfile": "operational-strict",
                    "prototype": {
                        "entry": "index.html",
                        "assetPath": "index.html",
                        "files": ["index.html", "styles.css", "image.bin"],
                        "states": ["ready", "empty", "error"],
                        "stableIds": ["object-browser", "upload"],
                    },
                    "production": {
                        "routeOrWindow": "/objects",
                        "files": [],
                        "interfaces": ["listObjects", "uploadObject"],
                        "tests": [],
                    },
                    "status": "approved",
                }
            ],
        },
    )
    write(repo / "docs" / "ui" / "capabilities.md", "# Capabilities\n")
    git(repo, "add", "designs", "docs/ui")
    git(repo, "commit", "-m", "design: approve object browser")
    return repo, git(repo, "rev-parse", "HEAD").stdout.strip()


def test_workflow_gate() -> str:
    with tempfile.TemporaryDirectory(prefix="pui-workflow-") as raw:
        root = Path(raw)
        repo, design_commit = make_workflow_repo(root)
        project = repo / "designs" / "app"
        run(
            [
                PYTHON,
                str(SCRIPTS / "validate_workflow.py"),
                "structure",
                "--repo",
                str(repo),
                "--project-dir",
                "designs/app",
            ]
        )
        run(
            [
                PYTHON,
                str(SCRIPTS / "validate_workflow.py"),
                "contract",
                "--project-dir",
                str(project),
                "--phase",
                "approved",
                "--asset-path",
                "index.html",
            ]
        )
        run(
            [
                PYTHON,
                str(SCRIPTS / "validate_workflow.py"),
                "approval",
                "--project-dir",
                str(project),
                "--asset-path",
                "index.html",
            ]
        )
        gate = [
            PYTHON,
            str(SCRIPTS / "validate_workflow.py"),
            "implementation-gate",
            "--repo",
            str(repo),
            "--project-dir",
            "designs/app",
            "--asset-path",
            "index.html",
            "--design-commit",
            design_commit,
        ]
        run(gate)

        write(project / "index.html", '<button data-component-id="upload">Upload objects</button>\n')
        git(repo, "add", "designs/app/index.html")
        git(repo, "commit", "-m", "design: unapproved prototype drift")
        drifted = run_fail(gate)
        assert_true("changed after the design commit" in drifted.stderr, "Committed prototype drift should invalidate approval")
        git(repo, "reset", "--hard", design_commit)

        meta = json.loads((project / "design-review.json").read_text(encoding="utf-8"))
        meta["assets"][0]["status"] = "changes-requested"
        write_json(project / "design-review.json", meta)
        git(repo, "add", "designs/app/design-review.json")
        git(repo, "commit", "-m", "design: revoke prototype approval")
        revoked = run_fail(gate)
        assert_true("not approved" in revoked.stderr, "Current approval-status reversal should block implementation")
        git(repo, "reset", "--hard", design_commit)

        for filename, content in (("styles.css", b"button { color: red; }\n"), ("image.bin", b"\x00\xfe\x02")):
            (project / filename).write_bytes(content)
            git(repo, "add", "designs/app/" + filename)
            git(repo, "commit", "-m", "design: change reviewed dependency")
            drifted = run_fail(gate)
            assert_true("dependency changed" in drifted.stderr, "Dependency drift must invalidate approval: " + filename)
            git(repo, "reset", "--hard", design_commit)

        contract_path = project / "ui-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["surfaces"][0]["prototype"]["files"].remove("styles.css")
        write_json(contract_path, contract)
        git(repo, "add", "designs/app/ui-contract.json")
        git(repo, "commit", "-m", "design: drop reviewed dependency")
        assert_true("Prototype mapping changed" in run_fail(gate).stderr, "Removing a dependency must not bypass approval")
        git(repo, "reset", "--hard", design_commit)

        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["surfaces"][0]["production"]["files"] = ["src/app.ts"]
        write_json(contract_path, contract)
        git(repo, "add", "designs/app/ui-contract.json")
        git(repo, "commit", "-m", "docs: record implementation mapping")
        run(gate)
        git(repo, "reset", "--hard", design_commit)

        review_path = project / "design-review.json"
        original_review = json.loads(review_path.read_text(encoding="utf-8"))
        approval_command = [PYTHON, str(SCRIPTS / "validate_workflow.py"), "approval", "--project-dir", str(project), "--asset-path", "index.html"]
        for malformed in (
            {"schemaVersion": 1, "assets": [{"path": "index.html", "status": "approved", "approvalEvidence": None}]},
            {"schemaVersion": 1, "assets": original_review["assets"] * 2},
            {"type": "design", "assets": {"Main": {"versions": [{"path": "index.html", "status": "approved"}]}}},
        ):
            write_json(review_path, malformed)
            run_fail(approval_command)
        write_json(review_path, original_review)
        run(approval_command)

        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        check_contract = [PYTHON, str(SCRIPTS / "validate_workflow.py"), "contract", "--project-dir", str(project), "--phase", "approved"]
        for files in ([], ["index.html", "missing.css"], ["index.html", "../outside.css"], ["index.html", "C:/outside.css"]):
            contract["surfaces"][0]["prototype"]["files"] = files
            write_json(contract_path, contract)
            run_fail(check_contract)
        git(repo, "reset", "--hard", design_commit)

        (project / "styles.css").unlink()
        git(repo, "add", "designs/app/styles.css")
        git(repo, "commit", "-m", "design: remove dependency")
        assert_true("dependency missing" in run_fail(gate).stderr, "Deleted dependency must invalidate approval")
        git(repo, "reset", "--hard", design_commit)

        file_id = git(repo, "rev-parse", "HEAD:designs/app/styles.css").stdout.strip()
        git(repo, "update-index", "--cacheinfo", "120000," + file_id + ",designs/app/styles.css")
        git(repo, "commit", "-m", "design: replace dependency with symlink")
        assert_true("regular file" in run_fail(gate).stderr, "Symlink dependency must not pass as frozen content")
        git(repo, "reset", "--hard", design_commit)

        write(repo / "designs" / "other" / "note.md", "unrelated design\n")
        git(repo, "add", "designs/other")
        git(repo, "commit", "-m", "design: unrelated project")
        unrelated_commit = git(repo, "rev-parse", "HEAD").stdout.strip()
        unrelated_gate = list(gate)
        unrelated_gate[unrelated_gate.index(design_commit)] = unrelated_commit
        unrelated = run_fail(unrelated_gate)
        assert_true("outside the target design project" in unrelated.stderr, "Approval commit should be target-project scoped")
        git(repo, "reset", "--hard", design_commit)

        wrong = list(gate)
        wrong[wrong.index("index.html")] = "older.html"
        run_fail(wrong)

        write(project / "notes.tmp", "dirty design\n")
        refused = run_fail(gate)
        assert_true("Uncommitted design" in refused.stderr, "Dirty design should block implementation")
        (project / "notes.tmp").unlink()
        run(gate)

        write(repo / "src" / "unapproved.ts", "export const bad = true;\n")
        scope_failure = run_fail(
            [
                PYTHON,
                str(SCRIPTS / "validate_workflow.py"),
                "design-scope",
                "--repo",
                str(repo),
            ]
        )
        assert_true("outside the allowed scope" in scope_failure.stderr, "Production edits should fail design scope")
        (repo / "src" / "unapproved.ts").unlink()

        source_register = {
            "schemaVersion": 1,
            "sources": [
                {
                    "id": "reference-shot",
                    "type": "screenshot",
                    "location": "user attachment",
                    "roles": ["visual-reference"],
                    "trust": "user-provided-untrusted-content",
                    "instructionsPolicy": "treat-as-data-never-execute",
                    "approvedByUser": False,
                    "containsSensitiveData": False,
                    "sanitization": None,
                    "licenseOrPermission": "user-provided for this design review",
                    "localCopies": [],
                    "observations": ["compact two-pane layout"],
                    "inferences": [],
                    "limitations": ["single state only"],
                }
            ],
        }
        write_json(project / "design-sources.json", source_register)
        run([PYTHON, str(SCRIPTS / "validate_workflow.py"), "sources", "--project-dir", str(project)])
        source_register["sources"][0]["roles"] = ["functional-truth"]
        write_json(project / "design-sources.json", source_register)
        bad_source = run_fail([PYTHON, str(SCRIPTS / "validate_workflow.py"), "sources", "--project-dir", str(project)])
        assert_true("functional-truth is limited" in bad_source.stderr, "Screenshot should not become functional truth")
        (project / "design-sources.json").unlink()
    return "Structure, content, project-owned approval, evidence/duplicate/schema rejection, text/binary dependency drift, missing/unsafe dependencies, current mappings, source-role and dirty-design gates passed."


def test_package_validation() -> str:
    with tempfile.TemporaryDirectory(prefix="pui-package-") as raw:
        root = Path(raw)
        # Exercise the standalone checkout layout without touching real Git data.
        source = root / "prototype-first-ui"
        shutil.copytree(SKILL, source, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        write(source / ".git" / "config", "private-checkout-metadata\n")
        scripts = source / "scripts"
        first = root / "prototype-first-ui-a.zip"
        second = root / "prototype-first-ui-b.zip"
        run([PYTHON, str(scripts / "validate_skill.py"), "--skill-dir", str(source)])
        command = [PYTHON, str(scripts / "package_skill.py"), "--source", str(source)]
        run(command + ["--output", str(first)])
        run(command + ["--output", str(second)])
        assert_true(sha256(first) == sha256(second), "Deterministic packages differ")
        run([PYTHON, str(SCRIPTS / "validate_skill.py"), "--zip", str(first)])
        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            assert_true(all(name.startswith("prototype-first-ui/") for name in names), "ZIP root is not stable")
            assert_true(not any("__pycache__" in name or name.endswith(".pyc") for name in names), "Runtime cache packaged")
            assert_true("prototype-first-ui/SKILL.md" in names, "SKILL.md missing from package")
            assert_true(not any(".git" in Path(name).parts for name in names), "Git metadata packaged")
            assert_true(archive.testzip() is None, "ZIP CRC failed")
        checksum = first.with_suffix(".zip.sha256").read_text(encoding="ascii").split()[0]
        assert_true(checksum == sha256(first), "Published checksum does not match ZIP")
        notes = first.with_suffix(".notes.md").read_text(encoding="utf-8")
        version = notes.split()[1]
        run(command + ["--output", str(second), "--tag", "v" + version])
        rejected = run_fail(command + ["--output", str(second), "--tag", "v999.0.0"])
        assert_true("must match metadata.version" in rejected.stderr, "Wrong release tag was not rejected")
        rejected = run_fail(command + ["--output", str(source / "nested.zip")])
        assert_true("outside the source" in rejected.stderr, "Output inside source was not rejected")
        assert_true(not (source / "nested.zip").exists(), "Rejected output was created")
        write(source / "LICENSE", "Wrong license\n")
        rejected = run_fail(command + ["--output", str(second)])
        assert_true("both declare MIT" in rejected.stderr, "License mismatch was not rejected")
        shutil.copyfile(SKILL / "LICENSE", source / "LICENSE")
        write(source / "CHANGELOG.md", "# Changelog\n\n## 999.0.0 — 2026-09-29\n\n- Wrong version\n")
        rejected = run_fail(command + ["--output", str(second)])
        assert_true("first CHANGELOG.md release" in rejected.stderr, "Changelog mismatch was not rejected")
        with zipfile.ZipFile(first, "a") as archive:
            archive.writestr("prototype-first-ui/.git/config", "forbidden")
        rejected = run_fail([PYTHON, str(scripts / "validate_skill.py"), "--zip", str(first)])
        assert_true("Development metadata" in rejected.stderr, "ZIP Git metadata was not rejected")
    return "Structure, syntax, deterministic ZIP/checksum, source Git exclusion, ZIP Git rejection, release version/license/changelog and output-path gates passed."


def test_javascript_syntax() -> str:
    node = shutil.which("node")
    if not node:
        return "Node.js unavailable; JavaScript syntax validation skipped (reported, not claimed)."
    run([node, "--check", str(SCRIPTS / "collect_dom_content.js")])
    return "DOM collector JavaScript syntax passed under Node.js; live browser DOM behavior remains a separate integration check."


# --------------------------------------------------------------------------
# Design tooling: tokens, lint, starter quality and the pfui front door.
# --------------------------------------------------------------------------

PFUI = SCRIPTS / "pfui.py"
TOKENS = SCRIPTS / "design_tokens.py"
LINT = SCRIPTS / "design_lint.py"
SLOT_PATTERN = r"\{\{([^{}\s]+)\}\}"


def lint_json(*args: str, expect: Optional[int] = None) -> Dict[str, object]:
    command = [PYTHON, str(LINT), "--json", *args]
    result = subprocess.run(command, env=BASE_ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=45)
    if expect is not None and result.returncode != expect:
        raise CommandError("lint returned %d, expected %d\n%s\n%s" % (result.returncode, expect, result.stdout[-3000:], result.stderr[-2000:]))
    assert_true(all(ord(character) < 128 for character in result.stdout), "JSON output must be ASCII-safe")
    return json.loads(result.stdout)


def rule_ids(report: Dict[str, object]) -> set:
    return {item["rule"] for item in report["findings"]}  # type: ignore[union-attr]


def fill_slots(folder: Path) -> None:
    import re

    for path in folder.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        text = re.sub(SLOT_PATTERN, lambda match: match.group(1).replace(".", " ").replace("-", " ").capitalize(), text)
        path.write_text(text, encoding="utf-8")


def sample_tokens() -> Dict[str, object]:
    return {
        "$extensions": {"contrast": [
            {"fg": "color.text.primary", "bg": "color.bg.surface", "min": 4.5},
            {"fg": "color.text.muted", "bg": "color.bg.surface", "min": 4.5},
        ]},
        "color": {
            "$type": "color",
            "gray": {"50": {"$value": "#fafafa"}, "500": {"$value": "#8a8a8a"}, "600": {"$value": "#5f5f5f"}, "900": {"$value": "#111111"}},
            "brand": {"$value": {"colorSpace": "oklch", "components": [0.55, 0.17, 255]}},
            "bg": {"surface": {"$value": "{color.gray.50}", "$extensions": {"mode": {"dark": "{color.gray.900}"}}}},
            "text": {
                "primary": {"$value": "{color.gray.900}", "$extensions": {"mode": {"dark": "{color.gray.50}"}}},
                "muted": {"$value": "{color.gray.500}"},
            },
            "button": {"$value": "{color.text.primary}"},
        },
        "space": {"$type": "dimension", "4": {"$value": "16px"}, "half": {"$value": {"value": 0.5, "unit": "rem"}}},
        "font": {"size": {"$type": "dimension", "body": {"$value": "1rem"}}},
        "duration": {"$type": "duration", "fast": {"$value": "120ms"}},
        "shadow": {"md": {"$type": "shadow", "$value": {"color": "#00000022", "offsetX": "0px", "offsetY": "4px", "blur": "12px", "spread": "0px"}}},
    }


def test_design_tokens() -> str:
    import xml.etree.ElementTree as ElementTree

    with tempfile.TemporaryDirectory(prefix="pui-tokens-") as raw:
        root = Path(raw)
        source = root / "tokens.json"
        data = sample_tokens()
        write_json(source, data)
        failed = run_fail([PYTHON, str(TOKENS), "check", str(source)])
        assert_true("color.text.muted on color.bg.surface" in failed.stdout and "FAIL" in failed.stdout, "Failing contrast pair was not reported")
        data["color"]["text"]["muted"] = {"$value": "{color.gray.600}", "$extensions": {"mode": {"dark": "{color.gray.500}"}}}  # type: ignore[index]
        write_json(source, data)
        report = json.loads(run([PYTHON, str(TOKENS), "check", str(source), "--json"]).stdout)
        assert_true(report["passed"] and len(report["contrast"]) == 4, "Contrast must pass in default and dark modes")
        assert_true(report["modes"] == ["default", "dark"], "Modes were not detected")

        broken = sample_tokens()
        broken["color"]["a"] = {"$value": "{color.b}"}  # type: ignore[index]
        broken["color"]["b"] = {"$value": "{color.a}"}  # type: ignore[index]
        broken["color"]["c"] = {"$value": "{color.missing}"}  # type: ignore[index]
        broken["color"]["d"] = {"$value": "{space.4}"}  # type: ignore[index]
        write_json(root / "broken.json", broken)
        failed = run_fail([PYTHON, str(TOKENS), "check", str(root / "broken.json")])
        for expected in ("alias cycle", "unknown reference {color.missing}", "color token aliases dimension"):
            assert_true(expected in failed.stderr, "Missing token error: %s\n%s" % (expected, failed.stderr))

        out = root / "out"
        run([PYTHON, str(TOKENS), "build", str(source), "--out", str(out), "--format", "css,json,ios,android,flutter"])
        css = (out / "tokens.css").read_text(encoding="utf-8")
        assert_true(":root[data-theme=\"dark\"]" in css and "@media (prefers-color-scheme: dark)" in css, "Dark CSS blocks missing")
        assert_true("--color-text-primary: var(--color-gray-900);" in css, "Aliases should stay var() references")
        assert_true("--space-half: 0.5rem;" in css and "--shadow-md: 0 4px 12px 0 #00000022;" in css, "Dimension or shadow formatting changed")
        colorset = json.loads((out / "ios" / "DesignTokens.xcassets" / "bg-surface.colorset" / "Contents.json").read_text(encoding="utf-8"))
        assert_true(len(colorset["colors"]) == 2 and colorset["colors"][1]["appearances"][0]["value"] == "dark", "iOS dark appearance missing")
        swift = (out / "ios" / "DesignTokens.swift").read_text(encoding="utf-8")
        assert_true("public enum DesignTokens" in swift and 'SwiftUI.Color("text-primary")' in swift and "space4: CGFloat = 16" in swift, "Swift output incomplete")
        night = ElementTree.parse(str(out / "android" / "values-night" / "colors.xml")).getroot()
        night_names = {element.get("name") for element in night}
        assert_true({"bg_surface", "text_primary", "button"} <= night_names and "gray_50" not in night_names, "values-night must hold only changed colors")
        dimens = (out / "android" / "values" / "dimens.xml").read_text(encoding="utf-8")
        assert_true('name="font_size_body">16sp<' in dimens and 'name="space_4">16dp<' in dimens, "Android dimension units wrong")
        dart = (out / "flutter" / "design_tokens.dart").read_text(encoding="utf-8")
        assert_true("class DesignColorsDark" in dart and "Color(0xFF111111)" in dart and "Duration(milliseconds: 120)" in dart, "Flutter output incomplete")
        resolved = json.loads((out / "tokens.resolved.json").read_text(encoding="utf-8"))
        assert_true(resolved["modes"]["dark"]["color.button"] == "#fafafa", "Alias chains must resolve per mode")

        inline = root / "inline"
        run([PYTHON, str(TOKENS), "build", str(source), "--out", str(inline), "--resolve"])
        inline_css = (inline / "tokens.css").read_text(encoding="utf-8")
        dark_block = inline_css.split(':root[data-theme="dark"]', 1)[1].split("}", 1)[0]
        assert_true("--color-button: #fafafa;" in dark_block, "--resolve must override alias chains in mode blocks")

        overlay_base = sample_tokens()
        overlay_base["color"]["bg"]["surface"] = {"$value": "{color.gray.50}"}  # type: ignore[index]
        overlay_base["color"]["text"]["primary"] = {"$value": "{color.gray.900}"}  # type: ignore[index]
        overlay_base["color"]["text"]["muted"]["$value"] = "{color.gray.600}"  # type: ignore[index]
        write_json(root / "base.json", overlay_base)
        write_json(root / "dark.json", {"color": {"bg": {"surface": {"$value": "{color.gray.900}"}}, "text": {"primary": {"$value": "{color.gray.50}"}, "muted": {"$value": "{color.gray.500}"}}}})
        overlay = json.loads(run([PYTHON, str(TOKENS), "check", str(root / "base.json"), "--overlay", "dark=%s" % (root / "dark.json"), "--json"]).stdout)
        assert_true(overlay["modes"] == ["default", "dark"] and overlay["passed"], "Overlay modes were not merged")

        ramp = json.loads(run([PYTHON, str(TOKENS), "ramp", "--name", "brand", "--hue", "160", "--chroma", "0.14"]).stdout)["brand"]
        sys.path.insert(0, str(SCRIPTS))
        from design_tokens import parse_css_color, relative_luminance

        steps = [key for key in ramp if not key.startswith("$")]
        luminance = [relative_luminance(parse_css_color(ramp[key]["$value"])) for key in steps]
        assert_true(len(steps) == 11 and all(a > b for a, b in zip(luminance, luminance[1:])), "Ramp must darken monotonically")
        run([PYTHON, str(TOKENS), "contrast", "#767676", "#ffffff", "--min", "4.5"])
        run_fail([PYTHON, str(TOKENS), "contrast", "#767676", "#ffffff", "--min", "7"])
    return "DTCG parsing, per-mode contrast, cycle/reference/type errors, overlays, CSS/JSON/iOS/Android/Flutter builds, --resolve and OKLCH ramps passed."


BAD_HTML = """<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<link rel="stylesheet" href="https://cdn.example.com/x.css">
<link rel="stylesheet" href="app.css">
<link rel="stylesheet" href="missing.css">
</head>
<body>
<div onclick="go()">Open</div>
<h1>{{hero.title}}</h1>
<h3>Lorem ipsum dolor sit amet</h3>
<button><svg viewBox="0 0 24 24"><path d="M1 1"/></svg></button>
<input placeholder="Email">
<a href="#x">Click here</a>
<img src="logo.png">
<button>\U0001F680 Launch</button>
<p id="dup">John Doe</p><p id="dup">Acme Corp</p>
<label for="nope">Name</label>
<table><tr><td>1</td></tr></table>
<div tabindex="3">x</div>
</body>
</html>
"""
BAD_CSS = """:root { --a: #111; --b: #222; --c: #333; --d: #444; --e: #555; --f: #666; --g: #777; --h: #888; }
button:focus { outline: none; }
.hero { color: #9a9a9a; background: #ffffff; font-size: 11px; transition: all 300ms; }
.btn-x { height: 20px; z-index: 99999; padding: 7px 13px; }
.card { color: red; }
@keyframes spin { to { transform: rotate(1turn); } }
"""
GOOD_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Orders</title><link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="app.css"></head>
<body>
<main>
<h1>Orders</h1>
<label class="check"><input type="checkbox" role="switch">Auto-assign docks</label>
<label for="q">Search orders</label><input id="q" type="search">
<button class="btn" type="button" aria-label="Close"><svg aria-hidden="true"></svg></button>
<table><thead><tr><th scope="col">Order</th></tr></thead><tbody><tr><td>A-104</td></tr></tbody></table>
<a href="#help">Shipping policy</a>
</main>
</body>
</html>
"""
GOOD_TOKENS_CSS = """:root { color-scheme: light; --c-text: #1b1e23; --c-bg: #ffffff; --c-muted: #6b6f75; --c-line: #d8dde4; --c-focus: #4289ef; --c-accent: #2870d4; --c-on-accent: #ffffff; --c-disabled: #b0b3b8; }
:root[data-theme="dark"] { color-scheme: dark; --c-text: #f3f5f9; --c-bg: #111419; --c-muted: #a6aab2; }
"""
GOOD_CSS = """body { color: var(--c-text); background: var(--c-bg); font-size: 1rem; }
.btn { min-height: 2.5rem; color: var(--c-on-accent); background: var(--c-accent); transition: background-color 120ms ease-out; }
.btn::after { content: ""; height: 2px; }
.btn:disabled { color: var(--c-disabled); background: var(--c-bg); }
:focus-visible { outline: 2px solid var(--c-focus); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition-duration: 0.01ms !important; } }
"""


def test_design_lint() -> str:
    with tempfile.TemporaryDirectory(prefix="pui-lint-") as raw:
        root = Path(raw)
        bad = root / "bad"
        write(bad / "index.html", BAD_HTML)
        write(bad / "app.css", BAD_CSS)
        report = lint_json(str(bad), expect=1)
        expected = {
            "html-lang", "viewport-zoom", "remote-asset", "missing-asset", "placeholder-text", "control-name",
            "field-label", "img-alt", "duplicate-id", "aria-reference", "heading-skip", "positive-tabindex",
            "static-click", "table-header", "ambiguous-link", "filler-copy", "emoji-icon", "doc-title",
            "outline-removed", "low-contrast", "font-size-min", "raw-color", "reduced-motion", "touch-target",
            "z-index-scale", "spacing-grid", "transition-all", "missing-main",
        }
        missing = expected - rule_ids(report)
        assert_true(not missing, "Lint missed rules: %s" % ", ".join(sorted(missing)))

        good = root / "good"
        write(good / "index.html", GOOD_HTML)
        write(good / "tokens.css", GOOD_TOKENS_CSS)
        write(good / "app.css", GOOD_CSS)
        clean = lint_json(str(good), expect=0)
        noisy = [item for item in clean["findings"] if item["severity"] != "info"]  # type: ignore[union-attr]
        assert_true(not noisy, "Clean sample produced findings: %s" % noisy)

        write_json(bad / "pfui.json", {"schemaVersion": 1, "platform": "ios", "lint": {"disable": ["emoji-icon"], "severity": {"filler-copy": "error"}}})
        configured = lint_json(str(bad), expect=1)
        assert_true("emoji-icon" not in rule_ids(configured), "pfui.json disable was ignored")
        filler = [item for item in configured["findings"] if item["rule"] == "filler-copy"]  # type: ignore[union-attr]
        assert_true(filler and all(item["severity"] == "error" for item in filler), "Severity override was ignored")
        write(root / "ios" / "x.css", ".btn { min-height: 36px; }\n")
        ios = lint_json(str(root / "ios"), "--platform", "ios")
        assert_true("touch-target" in rule_ids(ios), "iOS target threshold must be 44px")
        assert_true("touch-target" not in rule_ids(lint_json(str(root / "ios"), "--platform", "web")), "36px is valid on the web")

        email = root / "email"
        write(email / "index.html", '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width"><title>News</title></head><body><table role="presentation"><tr><td><img src="https://example.com/a.png" alt="Logo"></td></tr></table><script>1</script></body></html>')
        write(email / "mail.css", "td { display: flex; width: 700px; }\n")
        mail = lint_json(str(email), "--medium", "email", expect=1)
        rules = rule_ids(mail)
        assert_true({"email-script", "email-layout", "email-width"} <= rules and "remote-asset" not in rules, "Email medium rules wrong: %s" % rules)

        script = root / "script"
        write(script / "app.js", "const title = '{{screen.title}}';\n")
        assert_true("placeholder-text" in rule_ids(lint_json(str(script), expect=1)), "Unresolved slots in scripts must be reported")
        human = run_fail([PYTHON, str(LINT), str(bad)])
        assert_true("error(s)" in human.stdout, "Human-readable summary missing")
    return "Rule coverage on a defective page, clean sample, label/disabled/pseudo-element regressions, pfui.json overrides, platform targets, email medium, script slots and ASCII-safe JSON passed."


def test_starter_quality() -> str:
    sys.path.insert(0, str(SCRIPTS))
    import design_tokens

    system = SKILL / "assets" / "starter" / "system"
    report = design_tokens.check_tokens(system / "tokens.json")
    failures = [item for item in report["contrast"] if item["status"] != "pass"]  # type: ignore[union-attr]
    assert_true(report["passed"] and not report["errors"] and not failures, "Starter tokens must pass: %s %s" % (report["errors"], failures))
    assert_true(len(report["contrast"]) >= 100 and report["modes"] == ["default", "dark"], "Starter contrast coverage shrank")  # type: ignore[arg-type]
    token_set = design_tokens.load_token_set(system / "tokens.json", [])
    fresh = design_tokens.build_css(token_set, "tokens.json")
    assert_true(fresh == (system / "tokens.css").read_text(encoding="utf-8"), "assets/starter/system/tokens.css is stale; rebuild it")
    with tempfile.TemporaryDirectory(prefix="pui-starter-") as raw:
        root = Path(raw)
        run([PYTHON, str(PFUI), "init", "system", "--name", "Harbor"], cwd=root)
        clean = json.loads(run([PYTHON, str(PFUI), "check", "designs/system", "--json"], cwd=root).stdout)
        assert_true(clean["passed"] and clean["summary"]["warnings"] == 0, "Initialized system must pass check cleanly: %s" % clean["lint"]["findings"])
        for kind, extra in (("app", ["--platform", "ios", "--product"]), ("site", ["--lang", "zh-CN"]), ("deck", []), ("doc", ["--page", "Letter"])):
            run([PYTHON, str(PFUI), "init", kind, "--name", "Sample %s" % kind, *extra], cwd=root)
            folder = root / "designs" / ("sample-%s" % kind)
            pending = json.loads(run([PYTHON, str(PFUI), "check", str(folder), "--json"], cwd=root, expect=1).stdout)
            other = [item for item in pending["lint"]["findings"] if item["rule"] != "placeholder-text" and item["severity"] != "info"]
            assert_true(not other, "%s scaffold has non-slot findings: %s" % (kind, other))
            fill_slots(folder)
            done = json.loads(run([PYTHON, str(PFUI), "check", str(folder), "--json"], cwd=root).stdout)
            assert_true(done["passed"] and done["summary"]["warnings"] == 0, "%s scaffold must pass once slots are filled: %s" % (kind, done["lint"]["findings"]))
        doc_css = (root / "designs" / "sample-doc" / "document.css").read_text(encoding="utf-8")
        assert_true("size: letter;" in doc_css and "8.5in" in doc_css, "Doc page size was not applied")
        assert_true('data-platform="ios"' in (root / "designs" / "sample-app" / "index.html").read_text(encoding="utf-8"), "Platform attribute missing")
        assert_true('lang="zh-CN"' in (root / "designs" / "sample-site" / "index.html").read_text(encoding="utf-8"), "Language was not applied")
    return "Starter tokens (contrast in both modes, fresh CSS), clean system check, and app/site/deck/doc scaffolds (slot-only findings, clean when filled) passed."


def read_server_port(process: subprocess.Popen) -> int:
    import queue
    import re
    import threading

    lines: "queue.Queue[str]" = queue.Queue()

    def pump() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            lines.put(line)

    threading.Thread(target=pump, daemon=True).start()
    deadline = dt.datetime.now() + dt.timedelta(seconds=20)
    while dt.datetime.now() < deadline:
        try:
            line = lines.get(timeout=1)
        except queue.Empty:
            continue
        match = re.search(r"Preview: http://127\.0\.0\.1:(\d+)/", line)
        if match:
            return int(match.group(1))
    raise AssertionError("serve did not print its preview URL")


def http_status(url: str) -> Tuple[int, bytes]:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def test_pfui_cli() -> str:
    with tempfile.TemporaryDirectory(prefix="pui-cli-") as raw:
        root = Path(raw)
        doctor = json.loads(run([PYTHON, str(PFUI), "doctor", str(root), "--json"]).stdout)
        assert_true(doctor["levels"]["files"] is True and "browsers" in doctor and "project" in doctor, "doctor JSON shape changed")
        run([PYTHON, str(PFUI), "--version"])
        run([PYTHON, str(PFUI), "init", "app", "--name", "Orders", "--product"], cwd=root)
        project = root / "designs" / "orders"
        contract = json.loads((project / "ui-contract.json").read_text(encoding="utf-8"))
        files = contract["surfaces"][0]["prototype"]["files"]
        assert_true({"index.html", "app.js", "styles/tokens.css", "styles/base.css", "styles/params.js"} <= set(files), "Contract must list copied dependencies: %s" % files)
        sys.path.insert(0, str(SCRIPTS))
        from validate_workflow import validate_contract

        assert_true(not validate_contract(contract, project, "draft"), "Generated contract must be valid")
        run([PYTHON, str(PFUI), "gate", "review", "--project-dir", str(project)])
        refused = run_fail([PYTHON, str(PFUI), "init", "app", "--name", "Orders"], cwd=root)
        assert_true("already contains files" in refused.stderr, "init must refuse a non-empty folder")
        write(project / "app.css", "/* edited by the user */\n")
        (project / "fixtures.js").unlink()
        run([PYTHON, str(PFUI), "init", "app", "--name", "Orders", "--force"], cwd=root)
        assert_true((project / "app.css").read_text(encoding="utf-8") == "/* edited by the user */\n", "--force must never overwrite")
        assert_true((project / "fixtures.js").is_file(), "--force should restore missing files")
        status = json.loads(run([PYTHON, str(PFUI), "status", "--json"], cwd=root).stdout)
        entry = next(item for item in status["projects"] if item["path"] == "orders")
        assert_true(entry["assets"][0]["status"] == "draft" and entry["kind"] == "app", "status did not report the draft")

        run([PYTHON, str(PFUI), "init", "system"], cwd=root)
        tokens_path = root / "designs" / "system" / "tokens.json"
        data = json.loads(tokens_path.read_text(encoding="utf-8"))
        data["radius"]["md"]["$value"] = "10px"
        write_json(tokens_path, data)
        stale = json.loads(run([PYTHON, str(PFUI), "check", "designs/system", "--json"], cwd=root).stdout)
        warnings = [message for section in stale["sections"] for message in section["warnings"]]
        assert_true(any("out of date" in message for message in warnings), "Stale tokens.css must be reported")
        run([PYTHON, str(PFUI), "tokens", "build", str(tokens_path), "--out", str(tokens_path.parent)])
        fresh = json.loads(run([PYTHON, str(PFUI), "check", "designs/system", "--json"], cwd=root).stdout)
        assert_true(not [m for s in fresh["sections"] for m in s["warnings"]], "Rebuilt tokens should not be stale")
        run([PYTHON, str(PFUI), "lint", "--list-rules"])

        # tokens check/build default to designs/system/tokens.json and its folder.
        run([PYTHON, str(PFUI), "tokens", "check"], cwd=root)
        (root / "designs" / "system" / "tokens.css").unlink()
        run([PYTHON, str(PFUI), "tokens", "build", "--format", "css"], cwd=root)
        assert_true((root / "designs" / "system" / "tokens.css").is_file(), "tokens build must default --out to the token folder")
        empty = root / "empty"
        empty.mkdir()
        assert_true(run([PYTHON, str(PFUI), "tokens", "check"], cwd=empty, expect=2).returncode == 2, "Missing default token file must be a usage error")

        # Approval lives in design-review.json; the contract surface must agree.
        fill_slots(project)
        review_path = project / "design-review.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["assets"][0].update({"status": "approved", "approvalEvidence": "User approved index.html as shown."})
        write_json(review_path, review)
        drafting = json.loads(run([PYTHON, str(PFUI), "check", str(project), "--json"], cwd=root).stdout)
        contract_warnings = [message for section in drafting["sections"] if section["kind"] == "contract" for message in section["warnings"]]
        assert_true(any("implementation-gate requires it" in message for message in contract_warnings), "Approved review with a prototype surface must warn")
        final = json.loads(run([PYTHON, str(PFUI), "check", str(project), "--json", "--final"], cwd=root, expect=1).stdout)
        assert_true(any("implementation-gate requires it" in message for section in final["sections"] for message in section["errors"]), "--final must make the mismatch an error")
        review["assets"][0].update({"status": "needs-review", "approvalEvidence": None})
        write_json(review_path, review)
        contract = json.loads((project / "ui-contract.json").read_text(encoding="utf-8"))
        contract["surfaces"][0]["status"] = "approved"
        write_json(project / "ui-contract.json", contract)
        premature = json.loads(run([PYTHON, str(PFUI), "check", str(project), "--json"], cwd=root, expect=1).stdout)
        assert_true(any("approval must be recorded first" in message for section in premature["sections"] for message in section["errors"]), "Surface approval without review approval must fail")
        contract["surfaces"][0]["status"] = "prototype"
        write_json(project / "ui-contract.json", contract)

        # A project-local, uncommitted install of the skill is not a design-scope violation.
        repo = root / "scope-repo"
        init_repo(repo)
        write(repo / "README.md", "base\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "base")
        installed = repo / ".agents" / "skills" / "prototype-first-ui"
        shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "tests", "evals"))
        scope = [PYTHON, str(installed / "scripts" / "validate_workflow.py"), "design-scope", "--repo", str(repo)]
        run(scope)
        write(repo / "src" / "app.ts", "export const changed = true;\n")
        assert_true(".agents" not in run_fail(scope).stderr and "src/app.ts" in run_fail(scope).stderr, "Only production paths may violate design scope")

        process = subprocess.Popen(
            [PYTHON, "-u", str(PFUI), "serve", str(root / "designs"), "--port", "0"],
            env=BASE_ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        try:
            port = read_server_port(process)
            base = "http://127.0.0.1:%d" % port
            code, body = http_status(base + "/__pfui/manifest.json")
            manifest = json.loads(body.decode("utf-8"))
            pages = {page["path"]: page for page in manifest["pages"]}
            assert_true(code == 200 and pages["orders/index.html"]["states"] == ["ready", "loading", "empty", "error"], "Manifest states wrong")
            assert_true(http_status(base + "/__pfui/review.html")[0] == 200, "Review harness not served")
            assert_true(http_status(base + "/orders/index.html?state=empty")[0] == 200, "Prototype not served")
            assert_true(http_status(base + "/__pfui/unknown")[0] == 404, "Unknown internal route must 404")
            assert_true(http_status(base + "/%2e%2e/%2e%2e/pfui.json")[0] == 404, "Traversal must not escape the root")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
    return "doctor/status JSON, init contract and non-overwrite rules, gate passthrough, stale token detection, token path defaults, review/contract consistency, project-local install scope, lint passthrough and localhost serve (manifest, harness, traversal) passed."


TESTS: List[tuple[str, Callable[[], str]]] = [
    ("content-audit", test_content_audit),
    ("bootstrap-safety", test_bootstrap),
    ("workflow-gates", test_workflow_gate),
    ("package-validation", test_package_validation),
    ("javascript-syntax", test_javascript_syntax),
    ("design-tokens", test_design_tokens),
    ("design-lint", test_design_lint),
    ("starter-quality", test_starter_quality),
    ("pfui-cli", test_pfui_cli),
]


def run_named_case(name: str) -> tuple[str, str, float]:
    mapping = dict(TESTS)
    started = dt.datetime.now(dt.timezone.utc)
    try:
        detail = mapping[name]()
        status = "passed"
        print("PASS %s: %s" % (name, detail), flush=True)
    except Exception as exc:  # noqa: BLE001 - report the complete test failure
        status = "failed"
        detail = "%s: %s" % (type(exc).__name__, exc)
        print("FAIL %s: %s" % (name, detail), file=sys.stderr, flush=True)
        traceback.print_exc()
    duration = (dt.datetime.now(dt.timezone.utc) - started).total_seconds()
    return status, detail, round(duration, 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[name for name, _ in TESTS], required=True)
    parser.add_argument("--case-result")
    args = parser.parse_args()

    status, detail, duration = run_named_case(args.case)
    if args.case_result:
        write_json(
            Path(args.case_result).resolve(),
            {"name": args.case, "status": status, "detail": detail, "durationSeconds": duration},
        )
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
