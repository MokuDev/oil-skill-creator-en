#!/usr/bin/env python3
"""Create a minimal Skill directory, refusing to overwrite existing files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .validate_skill import NAME_RE
except ImportError:  # Use same-package import when script is run directly.
    from validate_skill import NAME_RE


ALLOWED_COMPONENTS = {"scripts", "references", "assets", "tests", "evals"}
# Components that only make sense once they hold real content are not created as
# empty directories; the author adds them with the first file that has a purpose.
CONTENT_ONLY_COMPONENTS = {"references", "assets"}

SCRIPTS_INIT_TEMPLATE = '"""Deterministic helper programs shipped with {name}."""\n'
TESTS_INIT_TEMPLATE = '''"""Tests for the helper programs of {name}.

The test modules import `scripts.*` from the Skill root. Make that root
importable regardless of the working directory the tests are started from.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SKILL_ROOT = str(Path(__file__).resolve().parent.parent)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)
'''
SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {name}

## Goal

TODO: describe which recurring problem this Skill solves for the user, and what observable or measurable improvement they get from using it.

## Workflow

TODO: keep only the judgements, key branches and steps that must run. Steps with fixed results that need to be repeated belong in scripts/.

## Output

TODO: describe the final deliverable, where it is saved, and what should be reported when done.

## Resource navigation

TODO: list only the on-demand resources that actually exist and when they should be read.
"""

README_FALLBACK = """# __SKILL_NAME__

## What it is for

__SUMMARY__

## Installation

Provide the full GitHub repo URL, so users can copy the address and tell the Agent to install this Skill.

Provide the `npx skills add <owner>/<repository>` command with `<owner>/<repository>` already replaced by the real values, and describe the install requirements.

## Configuration

Describe the first-time configuration. When no configuration is needed, state "no extra configuration required" explicitly.

## Usage

Describe how to trigger it in natural language; do not copy the internal flow from SKILL.md.

## Compatibility and dependencies

List the verified platforms, runtime environment, system commands and capabilities the host must provide.

## Data and applicable scope

Describe external services, permissions, privacy, cost and out-of-scope scenarios.

## Testing

Describe how to run program tests and Skill outcome evaluation.
"""


def _parse_components(value: str) -> set[str]:
    if not value.strip():
        return set()
    components = {item.strip() for item in value.split(",") if item.strip()}
    unknown = sorted(components - ALLOWED_COMPONENTS)
    if unknown:
        raise ValueError("unsupported components: " + ", ".join(unknown))
    return components


def _read_readme_template() -> str:
    template = Path(__file__).resolve().parent.parent / "assets" / "README.template.md"
    if template.is_file():
        return template.read_text(encoding="utf-8")
    return README_FALLBACK


def _render_description(description: str) -> str:
    return json.dumps(description, ensure_ascii=False)


def planned_paths(
    output_root: Path, name: str, components: set[str], public: bool
) -> list[Path]:
    target = output_root / name
    paths = [target / "SKILL.md"]
    if public:
        paths.append(target / "README.md")
    for component in sorted(components - CONTENT_ONLY_COMPONENTS):
        paths.append(target / component / _component_entry_name(component))
    return paths


def _component_entry_name(component: str) -> str:
    return "evals.json" if component == "evals" else "__init__.py"


def deferred_components(components: set[str]) -> list[str]:
    """Requested components that are left to the author instead of created empty."""

    return sorted(components & CONTENT_ONLY_COMPONENTS)


def create_skill(
    output_root: str | Path,
    name: str,
    description: str,
    components: set[str] | None = None,
    public: bool = False,
    dry_run: bool = False,
) -> tuple[Path, list[Path]]:
    if not NAME_RE.fullmatch(name) or len(name) > 64:
        raise ValueError("name must be a kebab-case string of at most 64 characters")
    if not description.strip():
        raise ValueError("description cannot be empty")
    if len(description) > 1024 or "<" in description or ">" in description:
        raise ValueError("description must be at most 1024 characters and must not contain angle brackets")

    component_set = set(components or set())
    unknown = sorted(component_set - ALLOWED_COMPONENTS)
    if unknown:
        raise ValueError("unsupported components: " + ", ".join(unknown))

    root = Path(output_root).expanduser().resolve()
    target = root / name
    paths = planned_paths(root, name, component_set, public)
    if target.exists():
        raise FileExistsError(f"target directory already exists, refusing to overwrite: {target}")
    if dry_run:
        return target, paths

    target.mkdir(parents=True)
    skill_text = SKILL_TEMPLATE.format(
        name=name, description=_render_description(description.strip())
    )
    (target / "SKILL.md").write_text(skill_text, encoding="utf-8", newline="\n")

    if public:
        readme = _read_readme_template()
        readme = readme.replace("__SKILL_NAME__", name).replace(
            "__SUMMARY__", description.strip()
        )
        (target / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    for component in sorted(component_set - CONTENT_ONLY_COMPONENTS):
        component_dir = target / component
        component_dir.mkdir()
        if component == "evals":
            evals = {"skill_name": name, "evals": []}
            content = json.dumps(evals, ensure_ascii=False, indent=2) + "\n"
        elif component == "scripts":
            content = SCRIPTS_INIT_TEMPLATE.format(name=name)
        else:
            content = TESTS_INIT_TEMPLATE.format(name=name)
        (component_dir / _component_entry_name(component)).write_text(
            content, encoding="utf-8", newline="\n"
        )

    return target, paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely create a minimal Skill skeleton")
    parser.add_argument("name", help="kebab-case Skill name")
    parser.add_argument("--output-root", required=True, help="parent directory for the Skill")
    parser.add_argument(
        "--description",
        default="TODO: describe what it does, when to trigger it, and which similar tasks should not trigger it.",
        help="trigger description at the top of SKILL.md",
    )
    parser.add_argument(
        "--components",
        default="",
        help=(
            "comma-separated components to create on demand: scripts,references,assets,tests,evals; "
            "references and assets are left to the author instead of being created empty"
        ),
    )
    parser.add_argument("--public", action="store_true", help="also generate README.md")
    parser.add_argument("--dry-run", action="store_true", help="only show the plan, do not write")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        components = _parse_components(args.components)
        target, paths = create_skill(
            args.output_root,
            args.name,
            args.description,
            components=components,
            public=args.public,
            dry_run=args.dry_run,
        )
    except (ValueError, FileExistsError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    deferred = deferred_components(components)
    payload = {
        "status": "dry-run" if args.dry_run else "created",
        "target": str(target),
        "paths": [str(path) for path in paths],
        "deferred_components": deferred,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "preview only" if payload["status"] == "dry-run" else "created"
        print(f"{status}: {target}")
        for path in paths:
            print(f"- {path}")
        if deferred:
            print(
                "not created, add the first file that has a purpose yourself: "
                + ", ".join(deferred)
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
