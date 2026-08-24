from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.scaffold_skill import (
    ALLOWED_COMPONENTS,
    CONTENT_ONLY_COMPONENTS,
    COMPONENT_ENTRIES,
    _component_entry,
    create_skill,
    deferred_components,
)


class ScaffoldSkillTests(unittest.TestCase):
    def test_creates_requested_components_without_extra_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target, _ = create_skill(
                temporary,
                "sample-skill",
                "Run stable workflows. Use when the user asks for a fixed artifact; do not trigger on ordinary questions.",
                components={"scripts", "evals"},
                public=True,
            )

            self.assertTrue((target / "SKILL.md").is_file())
            self.assertTrue((target / "README.md").is_file())
            self.assertTrue((target / "scripts").is_dir())
            self.assertTrue((target / "evals" / "evals.json").is_file())
            self.assertFalse((target / "references").exists())
            evals = json.loads((target / "evals" / "evals.json").read_text(encoding="utf-8"))
            self.assertEqual(evals, {"skill_name": "sample-skill", "evals": []})

    def test_seeds_component_directories_instead_of_leaving_them_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target, paths = create_skill(
                temporary,
                "seeded-skill",
                "Run stable workflows. Use when the user asks for a fixed artifact; do not trigger on ordinary questions.",
                components={"scripts", "tests"},
            )

            self.assertTrue((target / "scripts" / "__init__.py").is_file())
            self.assertTrue((target / "tests" / "__init__.py").is_file())
            self.assertIn(target / "scripts" / "__init__.py", paths)
            for directory in (target / "scripts", target / "tests"):
                self.assertTrue(any(item.is_file() for item in directory.iterdir()))

    def test_content_only_components_are_left_to_the_author(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target, paths = create_skill(
                temporary,
                "deferred-skill",
                "Run stable workflows. Use when the user asks for a fixed artifact; do not trigger on ordinary questions.",
                components={"references", "assets", "evals"},
            )

            self.assertFalse((target / "references").exists())
            self.assertFalse((target / "assets").exists())
            self.assertTrue((target / "evals" / "evals.json").is_file())
            self.assertNotIn(target / "references", paths)
            self.assertEqual(
                deferred_components({"references", "assets", "evals"}),
                ["assets", "references"],
            )

    def test_every_component_is_either_content_only_or_renders_an_entry(self) -> None:
        self.assertEqual(
            ALLOWED_COMPONENTS,
            CONTENT_ONLY_COMPONENTS | set(COMPONENT_ENTRIES),
        )
        for component in COMPONENT_ENTRIES:
            file_name, content = _component_entry(component, "sample-skill")
            self.assertTrue(file_name)
            self.assertTrue(content.strip())

    def test_unknown_component_has_no_entry(self) -> None:
        with self.assertRaises(ValueError):
            _component_entry("schemas", "sample-skill")

    def test_generated_tests_package_imports_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target, _ = create_skill(
                temporary,
                "compiled-skill",
                "Run stable workflows. Use when the user asks for a fixed artifact; do not trigger on ordinary questions.",
                components={"scripts", "tests"},
            )
            for module in (target / "scripts" / "__init__.py", target / "tests" / "__init__.py"):
                source = module.read_text(encoding="utf-8")
                compile(source, str(module), "exec")
                self.assertNotIn("from __future__ import annotations", source)

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target, paths = create_skill(
                temporary,
                "dry-run-skill",
                "Produce stable results. Use when the user needs this flow; do not trigger on ordinary tasks.",
                components={"tests"},
                dry_run=True,
            )
            self.assertFalse(target.exists())
            self.assertIn(target / "SKILL.md", paths)

    def test_refuses_to_overwrite_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "existing-skill"
            existing.mkdir()
            with self.assertRaises(FileExistsError):
                create_skill(
                    temporary,
                    "existing-skill",
                    "Use when the user needs it; do not trigger on ordinary tasks.",
                )

    def test_rejects_invalid_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                create_skill(
                    temporary,
                    "Invalid_Name",
                    "Use when the user needs it; do not trigger on ordinary tasks.",
                )


if __name__ == "__main__":
    unittest.main()
