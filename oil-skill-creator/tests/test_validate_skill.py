from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_skill import audit_skill, parse_frontmatter


VALID_SKILL = """---
name: sample-skill
description: Produce stable artifacts. Use when the user asks for a fixed workflow; do not trigger on ordinary questions.
compatibility: Python 3, supporting macOS, Windows and Linux.
---

# sample-skill

Read the [rules](references/rules.md), run `scripts/run.py`, deliver the result.
"""

VALID_README = """# sample-skill

## What it is for

Describe the value.

## Installation

Hand the repo URL to the Agent to install:

https://github.com/example/sample-skill

You can also use `npx skills add example/sample-skill`.

## Configuration

No extra configuration required.

## Usage

Describe the usage.

## Compatibility and dependencies

Supports macOS, Windows and Linux.

## Data and applicable scope

Only handles local data.
"""


def make_valid_skill(root: Path) -> Path:
    skill = root / "sample-skill"
    (skill / "references").mkdir(parents=True)
    (skill / "scripts").mkdir()
    (skill / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
    (skill / "README.md").write_text(VALID_README, encoding="utf-8")
    (skill / "references" / "rules.md").write_text("# Rules\n", encoding="utf-8")
    (skill / "scripts" / "run.py").write_text("print('ok')\n", encoding="utf-8")
    return skill


class ValidateSkillTests(unittest.TestCase):
    def test_valid_public_skill_passes_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            report = audit_skill(skill, public=True, weak_model=True)
            self.assertTrue(report.passed(strict=True), report.to_dict(strict=True))

    def test_folded_description_is_parsed(self) -> None:
        raw = """---
name: folded-skill
description: >
  First line.
  Use when the user needs it; do not trigger on ordinary tasks.
---
body
"""
        frontmatter, body = parse_frontmatter(raw)
        self.assertEqual(frontmatter["name"], "folded-skill")
        self.assertIn("Use when the user needs it", frontmatter["description"])
        self.assertEqual(body, "body\n")

    def test_broken_resource_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "SKILL.md").write_text(
                VALID_SKILL.replace("references/rules.md", "references/missing.md"),
                encoding="utf-8",
            )
            report = audit_skill(skill)
            self.assertIn("resource.missing", {item.code for item in report.errors})

    def test_history_heading_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\n## Change log\n\n- Adjusted the flow.\n")
            report = audit_skill(skill)
            self.assertIn("content.history", {item.code for item in report.errors})

    def test_rule_forbidding_previous_task_reuse_is_not_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\nDo not reuse the specific content from the previous task.\n")
            report = audit_skill(skill)
            self.assertNotIn("content.history", {item.code for item in report.errors})

    def test_history_in_reference_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "references" / "rules.md").write_text(
                "# Change log\n\n- Adjusted the flow.\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("content.history", {item.code for item in report.errors})

    def test_personal_path_in_readme_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            personal_path = "/Users/" + "example/private/config.json"
            with (skill / "README.md").open("a", encoding="utf-8") as handle:
                handle.write(f"\nThe config lives at {personal_path}.\n")
            report = audit_skill(skill)
            self.assertIn("content.personal-path", {item.code for item in report.errors})

    def test_personal_path_in_script_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            personal_path = "/home/" + "alice/.config/sample-skill"
            (skill / "scripts" / "run.py").write_text(
                f'CONFIG = "{personal_path}"\n', encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("content.personal-path", {item.code for item in report.errors})

    def test_configurable_user_path_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "scripts" / "run.py").write_text(
                """from pathlib import Path
import os

CONFIG = Path(os.environ.get("SAMPLE_SKILL_CONFIG", Path.home() / ".sample-skill"))
""",
                encoding="utf-8",
            )
            report = audit_skill(skill)
            self.assertNotIn("content.personal-path", {item.code for item in report.errors})

    def test_public_readme_sections_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "README.md").write_text("# sample-skill\n", encoding="utf-8")
            report = audit_skill(skill, public=True)
            self.assertIn("readme.section-missing", {item.code for item in report.errors})

    def test_github_readme_requires_agent_install_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            readme = (skill / "README.md").read_text(encoding="utf-8")
            (skill / "README.md").write_text(
                readme.replace("Hand the repo URL to the Agent to install:\n\n", ""),
                encoding="utf-8",
            )
            report = audit_skill(skill, public=True)
            self.assertIn(
                "readme.install-agent-missing",
                {item.code for item in report.warnings},
            )

    def test_github_readme_requires_npx_install_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            readme = (skill / "README.md").read_text(encoding="utf-8")
            (skill / "README.md").write_text(
                readme.replace(
                    "\nYou can also use `npx skills add example/sample-skill`.\n", "\n"
                ),
                encoding="utf-8",
            )
            report = audit_skill(skill, public=True)
            self.assertIn(
                "readme.install-command-missing",
                {item.code for item in report.warnings},
            )

    def test_embedded_secret_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            fake_secret = "sk-" + "abcdefghijklmnopqrstuvwxyz123456"
            (skill / "references" / "secret.md").write_text(
                f"token: {fake_secret}", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.embedded-secret", {item.code for item in report.errors})

    def test_plaintext_secret_assignment_in_json_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            secret_value = "m8Lq7xP2vN4cR9tY6wK3zB5d"
            (skill / "config.json").write_text(
                f'{{"api_key": "{secret_value}"}}\n', encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.plaintext-secret", {item.code for item in report.errors})

    def test_credential_reference_in_json_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "config.json").write_text(
                '{"credential_ref": "sample-skill/default"}\n', encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertNotIn("security.plaintext-secret", {item.code for item in report.errors})

    def test_private_key_block_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
            (skill / "references" / "secret.txt").write_text(
                private_key_header + "\nabc123\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.embedded-secret", {item.code for item in report.errors})

    def test_private_key_block_in_pem_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
            (skill / "key.pem").write_text(
                private_key_header + "\nabc123\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.embedded-secret", {item.code for item in report.errors})

    def test_private_key_block_in_key_file_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            private_key_header = "-----BEGIN " + "ENCRYPTED PRIVATE KEY-----"
            (skill / "server.key").write_text(
                private_key_header + "\nabc123\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.embedded-secret", {item.code for item in report.errors})

    def test_pgp_private_key_block_in_asc_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            private_key_header = "-----BEGIN " + "PGP PRIVATE KEY BLOCK-----"
            (skill / "key.asc").write_text(
                private_key_header + "\nabc123\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.embedded-secret", {item.code for item in report.errors})

    def test_prefixed_secret_assignment_in_env_template_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            secret_value = "m8Lq7xP2vN4cR9tY6wK3zB5d"
            (skill / ".env.example").write_text(
                "OPENAI_" + f"API_KEY={secret_value}\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.plaintext-secret", {item.code for item in report.errors})

    def test_prefixed_secret_assignments_in_structured_config_are_errors(self) -> None:
        cases = {
            "config.json": ('{\n  "SUPABASE_' + 'SERVICE_ROLE_KEY": "m8Lq7xP2vN4cR9tY6wK3zB5d"\n}\n'),
            "config.yaml": ("service:\n  GITHUB_" + "TOKEN: m8Lq7xP2vN4cR9tY6wK3zB5d\n"),
        }
        for filename, content in cases.items():
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temporary:
                skill = make_valid_skill(Path(temporary))
                (skill / filename).write_text(content, encoding="utf-8")
                report = audit_skill(skill)
                self.assertIn(
                    "security.plaintext-secret", {item.code for item in report.errors}
                )

    def test_prefixed_secret_placeholder_in_env_template_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / ".env.example").write_text(
                "OPENAI_API_KEY=your_api_key_here\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertNotIn("security.plaintext-secret", {item.code for item in report.errors})

    def test_folded_yaml_secret_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            secret_value = "m8Lq7xP2vN4cR9tY6wK3zB5d"
            (skill / "config.yaml").write_text(
                "api_" + f"key: >-\n  {secret_value}\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("security.plaintext-secret", {item.code for item in report.errors})

    def test_folded_yaml_secret_placeholder_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "config.yaml").write_text(
                "api_" + "key: >-\n  your_api_key_here\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertNotIn("security.plaintext-secret", {item.code for item in report.errors})

    def test_windows_shared_profile_paths_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "references" / "rules.md").write_text(
                "C:\\Users\\Public\\sample and C:/Users/Default/sample\n",
                encoding="utf-8",
            )
            report = audit_skill(skill)
            self.assertNotIn("content.personal-path", {item.code for item in report.errors})

    def test_windows_personal_path_with_forward_slashes_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "references" / "rules.md").write_text(
                "C:/Users/" + "alice/private/config.json\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("content.personal-path", {item.code for item in report.errors})

    def test_root_home_path_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "references" / "rules.md").write_text(
                "/" + "root/.config/sample-skill/config.json\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn("content.personal-path", {item.code for item in report.errors})

    def test_sensitive_credential_file_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / ".env").write_text("SAFE_PLACEHOLDER=1\n", encoding="utf-8")
            report = audit_skill(skill)
            self.assertIn("security.sensitive-file", {item.code for item in report.errors})

    def test_env_template_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / ".env.example").write_text(
                "API_KEY=your_api_key_here\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertNotIn("security.sensitive-file", {item.code for item in report.errors})
            self.assertNotIn("security.plaintext-secret", {item.code for item in report.errors})

    def test_unreachable_reference_is_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "references" / "orphan.md").write_text(
                "# Orphan rule\n\nThis rule has no entry point.\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn(
                "layer.reference-unreachable", {item.code for item in report.warnings}
            )

    def test_duplicate_markdown_block_is_a_warning(self) -> None:
        duplicate = (
            "Every deterministic, repeatable step that can be checked by a program "
            "should be written into a script; the executing Agent should only choose "
            "strategy and handle non-exhaustive exceptions."
        )
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write(f"\n{duplicate}\n")
            (skill / "references" / "rules.md").write_text(
                f"# Rules\n\n{duplicate}\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn(
                "content.duplicate-exact", {item.code for item in report.warnings}
            )

    def test_near_duplicate_markdown_block_is_a_warning(self) -> None:
        original = (
            "When targeting weaker models, every instruction must spell out its actor, "
            "input, output and stopping condition; branches must sit next to the step "
            "they belong to, and terminology must stay consistent throughout."
        ) * 5
        similar = original.replace("must spell out", "needs to spell out", 1)
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write(f"\n{original}\n")
            (skill / "references" / "rules.md").write_text(
                f"# Rules\n\n{similar}\n", encoding="utf-8"
            )
            report = audit_skill(skill)
            self.assertIn(
                "content.duplicate-near", {item.code for item in report.warnings}
            )

    def test_weak_model_profile_rejects_long_paragraph(self) -> None:
        long_paragraph = "This step must keep a single action and state its input and output clearly." * 30
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write(f"\n{long_paragraph}\n")
            report = audit_skill(skill, weak_model=True)
            self.assertIn(
                "readability.long-paragraph", {item.code for item in report.warnings}
            )

    def test_invalid_eval_schema_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "evals").mkdir()
            (skill / "evals" / "evals.json").write_text(
                """{
  "skill_name": "sample-skill",
  "evals": [{"id": 1, "prompt": "test", "assertions": []}]
}
""",
                encoding="utf-8",
            )
            report = audit_skill(skill)
            self.assertIn("evals.schema", {item.code for item in report.errors})

    def test_universal_mode_rejects_host_brand(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\nRun this flow only in Codex.\n")
            report = audit_skill(skill, universal=True)
            self.assertIn(
                "compatibility.host-coupling", {item.code for item in report.errors}
            )
            self.assertNotIn(
                "compatibility.host-coupling",
                {item.code for item in audit_skill(skill).errors},
            )

    def test_universal_mode_rejects_host_specific_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = make_valid_skill(Path(temporary))
            (skill / "references" / "claude-adapter.md").write_text(
                "# Adapter\n", encoding="utf-8"
            )
            report = audit_skill(skill, universal=True)
            self.assertIn(
                "compatibility.host-specific-path",
                {item.code for item in report.errors},
            )


class EmptyDirectoryTests(unittest.TestCase):
    def _write_skill(self, root: Path) -> Path:
        skill = root / "sample-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
        return skill

    def test_empty_directory_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self._write_skill(Path(temporary))
            (skill / "assets").mkdir()
            report = audit_skill(skill)
            codes = {finding.code for finding in report.warnings}
            self.assertIn("layer.empty-directory", codes)

    def test_directory_with_a_nested_file_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self._write_skill(Path(temporary))
            nested = skill / "assets" / "pages"
            nested.mkdir(parents=True)
            (nested / "review.html").write_text("<p>page</p>\n", encoding="utf-8")
            report = audit_skill(skill)
            codes = {finding.code for finding in report.warnings}
            self.assertNotIn("layer.empty-directory", codes)


if __name__ == "__main__":
    unittest.main()
