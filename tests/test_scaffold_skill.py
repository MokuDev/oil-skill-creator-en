from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.scaffold_skill import create_skill


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
