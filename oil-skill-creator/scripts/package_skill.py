#!/usr/bin/env python3
"""Validate and produce a reproducible .skill archive."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
import zipfile
from pathlib import Path

try:
    from .validate_skill import audit_skill, parse_frontmatter
except ImportError:  # Use same-package import when the script is run directly.
    from validate_skill import audit_skill, parse_frontmatter


EXCLUDED_DIRS = {".git", ".venv", "node_modules", "__pycache__", "dist"}
EXCLUDED_FILES = {".DS_Store"}
EXCLUDED_GLOBS = {"*.pyc", "*.pyo", "*.tmp", "*.log"}
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _is_excluded(relative: Path, include_evals: bool) -> bool:
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    if not include_evals and relative.parts and relative.parts[0] == "evals":
        return True
    if relative.name in EXCLUDED_FILES:
        return True
    return any(fnmatch.fnmatch(relative.name, pattern) for pattern in EXCLUDED_GLOBS)


def _skill_name(skill_path: Path) -> str:
    raw = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(raw)
    return frontmatter["name"]


def package_skill(
    skill_path: str | Path,
    output_dir: str | Path | None = None,
    public: bool = False,
    strict: bool = False,
    weak_model: bool = False,
    universal: bool = False,
    include_evals: bool = False,
    replace: bool = False,
) -> tuple[Path, str, list[str]]:
    path = Path(skill_path).expanduser().resolve()
    report = audit_skill(
        path,
        public=public,
        weak_model=weak_model,
        universal=universal,
    )
    if not report.passed(strict):
        raise ValueError(
            f"validation failed: {len(report.errors)} error(s), {len(report.warnings)} warning(s)"
        )

    name = _skill_name(path)
    destination = (
        Path(output_dir).expanduser().resolve()
        if output_dir is not None
        else path.parent / "dist"
    )
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"{name}.skill"
    if archive.exists() and not replace:
        raise FileExistsError(f"target archive already exists, refusing to overwrite: {archive}")
    if archive.exists():
        archive.unlink()

    files: list[Path] = []
    for item in sorted(path.rglob("*"), key=lambda value: value.as_posix()):
        if item.is_symlink():
            raise ValueError(f"publish package does not accept symbolic links: {item}")
        if not item.is_file():
            continue
        relative = item.relative_to(path)
        if not _is_excluded(relative, include_evals):
            files.append(item)

    added: list[str] = []
    with zipfile.ZipFile(
        archive, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as bundle:
        for item in files:
            relative = item.relative_to(path)
            archive_name = (Path(name) / relative).as_posix()
            info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = item.suffix.lower() in {".py", ".sh", ".ps1"}
            permissions = 0o755 if executable else 0o644
            info.external_attr = permissions << 16
            bundle.writestr(info, item.read_bytes())
            added.append(archive_name)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return archive, digest, added


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="validate and package; identical files produce identical .skill packages")
    parser.add_argument("skill_path", help="Skill directory")
    parser.add_argument("--output-dir", help="output directory, default is sibling dist/")
    parser.add_argument("--public", action="store_true", help="run the public-release README checks")
    parser.add_argument("--strict", action="store_true", help="warnings also block packaging")
    parser.add_argument(
        "--weak-model",
        action="store_true",
        help="use the strict structural thresholds aimed at weaker models",
    )
    parser.add_argument(
        "--universal",
        action="store_true",
        help="refuse to hardcode a specific host's brand in generic flows before packaging",
    )
    parser.add_argument("--include-evals", action="store_true", help="include evals/ in the package")
    parser.add_argument("--replace", action="store_true", help="explicitly overwrite an existing archive of the same name")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        archive, digest, added = package_skill(
            args.skill_path,
            output_dir=args.output_dir,
            public=args.public,
            strict=args.strict,
            weak_model=args.weak_model,
            universal=args.universal,
            include_evals=args.include_evals,
            replace=args.replace,
        )
    except (ValueError, FileExistsError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "archive": str(archive),
        "sha256": digest,
        "files": added,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"created: {archive}")
        print(f"SHA-256: {digest}")
        print(f"file count: {len(added)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
