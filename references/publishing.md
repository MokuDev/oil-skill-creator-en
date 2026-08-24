# GitHub and publishing

## What the README is for

A published Skill's README answers at least:

1. What problem it solves, and why it is worth installing;
2. What the user will get at the end;
3. How to install it;
4. Whether initialization, configuration or secrets are required;
5. How to trigger it in natural language;
6. Dependencies, supported platforms and host capabilities;
7. Where the data goes;
8. Applicable scope and adjacent Skills;
9. How to run tests and troubleshoot.

When no configuration is needed, still write "no extra configuration required" explicitly; do not silently skip the section. The README is for humans, `SKILL.md` is for the Agent. They can link to each other, but do not copy blocks of execution rules.

## Installation instructions

The README of a public GitHub repo defaults to providing two install paths, with the easiest one first:

1. **Let the Agent install**: provide the full repo URL and a one-line natural-language prompt users can paste, e.g. "Please install this Skill: `https://github.com/<owner>/<repository>`".
2. **Install via command**: provide `npx skills add <owner>/<repository>` with `<owner>/<repository>` already replaced by real values.

The command must match the actual repo structure and be verified before release. `npx` is only an optional installation method; if it requires Node.js, do not falsely list Node.js as the Skill's own runtime dependency. When command installation is empirically unsupported, do not leave a broken command in place — explain why and provide a manual install path.

## Optional README design enhancement

After value, install command, compatibility and data boundaries are confirmed, if the user still wants to improve the GitHub landing page, you can use [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme). It can adjust the whole README, or just produce the hero visual, section headers, or flow diagrams.

First confirm whether it is "the whole README" or "only visual assets". Do not treat a recommended tool as authorization to rewrite automatically. Visual upgrade is not a substitute for fact-checking, and must not lengthen the README; when the user does not need beautification, keep the clear plain Markdown.

## Repo contents

A public repo usually contains:

```text
<skill-name>/
├── README.md
├── SKILL.md
├── scripts/       # on demand
├── references/    # on demand
├── assets/        # on demand
└── tests/         # prefer whenever there are scripts
```

The license must be chosen by the publisher; do not guess. Personal configuration, secrets, caches, virtual environments, generated results and evaluation workspaces do not enter the repo.

## Pre-release bar

- `description` covers both positive and reverse triggering;
- `SKILL.md` contains no historical cases, personal paths or change logs;
- All local resource links resolve;
- Deterministic, repeatable, mandatory steps are scripted, with regression tests;
- The README explains value, installation, configuration, usage and compatibility; the GitHub repo provides both the Agent-install and the command-install entry points;
- The README and `SKILL.md` do not duplicate the same execution instructions;
- Every `references/` document is reachable on demand from `SKILL.md`'s resource navigation; no orphan docs;
- For weaker models, it has passed the strict structural check and a dry run on the target model;
- External services, permissions, costs and data boundaries are not hidden;
- The current directory has run the rule-style scan for personal paths, plaintext secrets and high-risk credential files, and "passing" is not represented as "confirmed no secrets exist";
- Existing Git history has been checked with a historical-secret scanner, or the unverified status is explicitly marked;
- Generic Skills do not hardcode host brand, dedicated directories, dedicated commands or private APIs into the flow;
- Objective Skills have a baseline comparison;
- Subjective Skills have been handed to humans for review;
- Remediating an existing Skill kept the pre-write snapshot and comparison evidence;
- P0/P1 Review findings are handled or explicitly accepted by the user;
- Unverified platforms and capabilities are clearly marked.

## Packaging boundaries

The `.skill` publish package excludes by default:

- `.git/`;
- `.venv/`, `node_modules/` and caches;
- `evals/`;
- Test run results and Skill-sibling workspaces;
- `.DS_Store`, bytecode and temp files.

Validate before packaging. The package uses stable path ordering and fixed timestamps, so identical content produces identical archives. Existing target packages default to not overwriting.

The current file checks only cover the text and high-risk filenames the validator can read; they do not analyze binary content, archives, or encoding obfuscation, and they cannot prove Git history is safe. Before going public, supplement the scan with a mature secret scanner based on the repo content; existing repos also need full-commit history checks. When a leak is found, revoke or rotate credentials first, then scrub the history. Just deleting the secret from the current file does not eliminate the leak.

## Maintenance principles

- `SKILL.md`, `references/` and the README only describe the currently valid state.
- Version history lives in Git commits, release notes, or an external workspace.
- Before each fix, attribute the cause. Only for deterministic, recurring problems add a check or script; semantic problems change the flow and judgement principles; one-off cases do not enter the Skill.
- Do not add infinite inline branches just to preserve historical compatibility; what can be migrated programmatically goes to programs.
- Remove rules that no longer produce value, to keep tokens and maintenance cost from growing forever.
