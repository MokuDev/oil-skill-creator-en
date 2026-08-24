# oil-skill-creator

`oil-skill-creator` is used to create, review, remediate and publish Agent Skills. What it cares about is not whether the docs are written, but whether the Skill is worth installing, whether it runs reliably, whether it stays usable by weaker models, and whether real design causes can be found when results disappoint.

> A passing static check only proves the known structure has no problems — it does not prove the Skill is actually useful.

## What you get

- A minimal, clear Skill file structure with no empty directories created just to feel "complete";
- Explicit trigger and reverse boundaries, reducing false triggers and missed triggers;
- Silent, recoverable first-use flow;
- Deterministic, repeatable, failure-sensitive steps fixed by programs;
- Immutable pre-remediation snapshots, plus a basis for comparing the new version against the old;
- Trigger tests, result aggregation, a local review page, and a repeatable publish package;
- Checks for tokens, weak-model readability, host neutrality and cross-platform scope.

## Three usage modes

| Mode | When to use | Default result |
| --- | --- | --- |
| Create | Designing a reusable Skill from scratch | An executable, verifiable Skill |
| Review | Just want to know what is wrong with an existing Skill | A read-only report ordered by P0, P1, P2 |
| Remediate | Already decided to fix or improve | Baseline kept, scoped edits made, re-verified |

Review does not modify files by default. Files are only saved and the writer starts once remediation is explicitly requested.

## Installation

### Let the Agent install

Copy the repo URL below and tell the Agent you are using: "Please install this Skill."

```text
https://github.com/MokuDev/oil-skill-creator-en
```

### Install via command

```shell
npx skills add MokuDev/oil-skill-creator-en
```

This installation method requires `npx` to be available locally, but Node.js is not a runtime dependency for the Skill.

The core scripts require Python 3.10 or higher, only use the standard library, need no extra dependencies, and need no secrets or initial configuration.

Below, `<python>` stands for a Python interpreter confirmed to be at least 3.10: on macOS and Linux this is usually `python3`, on Windows it is usually `py -3`.

## Getting started

Describe the goal and the write permissions directly in natural language:

```text
Use oil-skill-creator to create a publishable Skill.
```

```text
Only review this Skill; provide evidence by priority, do not modify files.
```

```text
Remediate this existing Skill; keep the old baseline first, then fix and re-verify.
```

```text
Verify whether the new version is more effective than a regular Agent or the old version.
```

If existing files already specify the user, inputs, outputs or platform constraints, the Skill reads them directly and does not ask again. Only decisions that change the result, require new permissions, or could overwrite existing content are asked up front.

## What it focuses on checking

### Whether the Skill is worth building

First confirm it solves a recurring problem and produces visible improvement over a regular Agent. One-off tasks, simple reminders, or work that is already stable are not forcibly wrapped into a Skill.

### Whether Agent and program are partitioned sensibly

Semantics, strategy, exceptions and subjective quality are left to the Agent or the user; deterministic flows such as structure, format, snapshots, statistics, assembly and packaging are left to programs. This reduces omissions and avoids hardcoding subjective judgement into rule trees.

### Whether large artifacts are easy to generate and modify

When the target Skill easily produces hard-to-maintain monolithic files, check whether the artifacts can be split along stable boundaries, validated and redone locally, then assembled deterministically by scripts. Splitting is never done by a fixed line count.

### Whether reusable operation pages are needed

Complex configuration, repeated previews and human confirmation should not require ad-hoc interfaces every time. When appropriate, the Skill uses fixed pages that read a manifest; the program handles load and save, and the Agent only chains the operation flow.

### Whether weaker models can understand it

Check the entry point, modes, terminology, where branches sit and when resources are read. The main file only keeps the main flow; stage details are read on demand and the same rule is not duplicated across multiple files.

## Stable tooling

| Tool | Purpose |
| --- | --- |
| `scaffold_skill.py` | Preview and create a minimal Skill skeleton, without empty directories; refuses to overwrite an existing directory |
| `validate_skill.py` | Checks structure, links, empty directories, duplication, personal paths, plaintext secrets, weak-model risk and host neutrality |
| `snapshot_skill.py` | Saves an immutable pre-remediation baseline of the old version |
| `prepare_evaluation.py` | Creates fixed comparison directories for the new version, a regular Agent or the old version |
| `aggregate_evaluation.py` | Aggregates execution results, timings and inspection data |
| `generate_review.py` | Generates a local static review page that does not auto-open the browser |
| `score_triggers.py` | Tallies trigger performance on the positive, negative and held-out sets |
| `package_skill.py` | Generates a content-stable `.skill` publish package, defaulting to not overwriting |

View any tool's arguments:

```text
<python> scripts/validate_skill.py --help
```

Run the strict check before public release or before declaring remediation done:

```text
<python> scripts/validate_skill.py <skill-path> --public --strict --weak-model --universal
```

Only omit `--universal` when the product explicitly depends on a specific host, and document the incompatible scope honestly.

## Outcome evaluation

Create mode compares "Skill in use" against "regular Agent"; remediate mode compares the current version against the pre-write snapshot. The program prepares fixed directories, checks data formats and aggregates results; an isolated runner runs each candidate; humans own subjective conclusions such as aesthetics, copy and overall experience.

```text
<python> scripts/prepare_evaluation.py <skill-path> --mode create --iteration 1
<python> scripts/aggregate_evaluation.py <iteration-path>
<python> scripts/generate_review.py <iteration-path>
```

Without a sub-Agent or equivalent isolated-execution capability, static review, programmatic tests and author trials can still be completed, but you cannot claim to have finished an independent comparison.

## Compatibility

| Scope | Current status |
| --- | --- |
| Python | 3.10+, core scripts only use the standard library |
| macOS / Linux | Automated tests have run |
| Windows | Implemented with the standard library and cross-platform paths; real-platform runs still pending verification |
| No browser or GUI | Core flow works; review page only generates files, it does not auto-open |
| No sub-Agent | Create, static review and programmatic tests work; independent comparison degrades |
| Offline environment | Core scripts only handle local files and do not make network calls |

The scripts use `pathlib` and UTF-8 and do not depend on bash, PowerShell, Homebrew or single-platform open commands. Compatibility only describes scope that has been implemented or verified.

## Data and security boundaries

- Only processes local files explicitly specified by the user; regular configuration and secrets are stored separately;
- The project itself needs no secrets and provides no generic credential adapter; it requires target Skills to prefer system credential storage, with JSON holding only non-sensitive configuration and credential references;
- Refuses by default to overwrite existing Skills, snapshots, review pages, iterations and publish packages;
- Packaging excludes by default `.git`, virtual environments, caches, evaluation data and run workspaces;
- Does not execute the target Skill's actual business tasks;
- Does not use AI self-scoring as a substitute for subjective reviews such as visuals and copy;
- Reviews, feedback, version diffs and single-task notes are never written back into the formal Skill.

## Development and verification

```text
<python> -m unittest discover -s tests -v
<python> scripts/validate_skill.py . --public --strict --weak-model --universal
```

Run both commands from this Skill directory. The tests also run from a parent directory with `<python> -m unittest discover -s <skill-path>/tests -t .`.

Tests cover file protection, snapshots, basic structure, resource links, secrets, host neutrality, content duplication, weak-model structure, outcome evaluation, trigger tests and repeatable packaging.

If you continue to design the GitHub home page, you can use [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme) to adjust reading order or produce visual assets; it is not an installation or runtime dependency.

## License

[MIT](./LICENSE)
