#!/usr/bin/env python3
"""Create an immutable Skill baseline before remediation; refuses to overwrite."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

try:
    from .validate_skill import parse_frontmatter
except ImportError:
    from validate_skill import parse_frontmatter


EXCLUDED_DIRS = {".git", ".venv", "node_modules", "__pycache__", "dist"}
EXCLUDED_FILES = {".DS_Store"}


def _skill_name(skill_path: Path) -> str:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        raise ValueError("target directory is missing SKILL.md")
    frontmatter, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    name = frontmatter.get("name", "").strip()
    if not name:
        raise ValueError("SKILL.md is missing name")
    return name


def _included_files(skill_path: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(skill_path.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(skill_path)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"snapshot does not accept symbolic links: {path}")
        if path.is_file() and path.name not in EXCLUDED_FILES:
            files.append(path)
    return files


def default_workspace(skill_path: Path, name: str) -> Path:
    """Return a default workspace that does not fall inside a common Skill scan directory."""
    parent = skill_path.parent
    if parent.name.lower() == "skills":
        return parent.parent / "skill-workspaces" / f"{name}-workspace"
    return parent / f"{name}-workspace"


def _digest(skill_path: Path, files: list[Path]) -> str:
    checksum = hashlib.sha256()
    for path in files:
        relative = path.relative_to(skill_path).as_posix().encode("utf-8")
        checksum.update(len(relative).to_bytes(4, "big"))
        checksum.update(relative)
        content = path.read_bytes()
        checksum.update(len(content).to_bytes(8, "big"))
        checksum.update(content)
    return checksum.hexdigest()


def verify_snapshot(workspace: str | Path) -> dict[str, object]:
    workspace_path = Path(workspace).expanduser().resolve()
    destination = workspace_path / "skill-snapshot"
    metadata_path = workspace_path / "snapshot.json"
    if not destination.is_dir() or not metadata_path.is_file():
        raise ValueError(f"snapshot or metadata does not exist: {destination}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"snapshot metadata is invalid: {metadata_path}") from exc
    if not isinstance(metadata, dict):
        raise ValueError(f"snapshot metadata must be an object: {metadata_path}")
    recorded_path = Path(str(metadata.get("snapshot", ""))).expanduser().resolve()
    if recorded_path != destination:
        raise ValueError("snapshot.json points to a snapshot path that does not match the current workspace")
    files = _included_files(destination)
    digest = _digest(destination, files)
    if metadata.get("files") != len(files) or metadata.get("sha256") != digest:
        raise ValueError("skill-snapshot content has changed, refusing to use it as a remediation baseline")
    return {
        "snapshot": str(destination),
        "files": len(files),
        "sha256": digest,
    }


def snapshot_skill(
    skill_path: str | Path,
    workspace: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    source = Path(skill_path).expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"Skill directory does not exist: {source}")
    name = _skill_name(source)
    workspace_path = (
        Path(workspace).expanduser().resolve()
        if workspace is not None
        else default_workspace(source, name)
    )
    destination = workspace_path / "skill-snapshot"
    metadata = workspace_path / "snapshot.json"
    if destination.exists() or metadata.exists():
        raise FileExistsError(f"snapshot already exists, refusing to overwrite: {destination}")

    files = _included_files(source)
    payload: dict[str, object] = {
        "status": "dry-run" if dry_run else "created",
        "source": str(source),
        "snapshot": str(destination),
        "files": len(files),
        "sha256": _digest(source, files),
    }
    if dry_run:
        return payload

    workspace_path.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    for path in files:
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    metadata.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an immutable old-version Skill snapshot before remediation")
    parser.add_argument("skill_path", help="existing Skill directory")
    parser.add_argument(
        "--workspace",
        help="working directory; when the Skill sits in a scan directory called 'skills', the default is its sibling skill-workspaces",
    )
    parser.add_argument("--dry-run", action="store_true", help="only show the plan, do not write")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = snapshot_skill(args.skill_path, args.workspace, args.dry_run)
    except (ValueError, FileExistsError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "preview only" if payload["status"] == "dry-run" else "created"
        print(f"{status}: {payload['snapshot']}")
        print(f"file count: {payload['files']}")
        print(f"SHA-256: {payload['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
