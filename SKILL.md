---
name: oil-skill-creator
description: Create, review, remediate and publish Skills. Use when the user wants to build a Skill from scratch, review an existing Skill, check whether it is genuinely useful, fix its trigger or execution flow, or improve first-use, stability, token overhead, file layering, weak-model readability and cross-platform compatibility. Do not use for executing the actual tasks the target Skill is responsible for, and do not trigger for ordinary coding, design or writing requests.
license: MIT
compatibility: The core scripts only use the Python 3 standard library and support macOS, Windows and Linux. Independent outcome evaluation requires a host that can launch sub-Agents, or an equivalent isolated-execution capability.
---

# oil-skill-creator

Treat Skills as tools that need long-term maintenance. First confirm they solve a recurring problem, then make them easy to start, stable to run and possible to verify, and state the compatibility scope honestly. Do not wrap a one-shot prompt as a Skill.

## Choose a mode first

| Mode | When it fits | Path | Default stop point |
| --- | --- | --- | --- |
| Create | No Skill exists yet | Product definition -> Implementation -> Validation -> Evaluation -> Publish on demand | Deliver a usable Skill |
| Remediate | A Skill exists; the user asked for fixes or improvements | Read -> Static check -> Snapshot -> Scoped edits -> Re-verify | Issues fixed with no regressions |
| Review | The user only wants a review, audit or problem hunt | Read -> Static check -> Process check -> Report | Deliver the report, then stop |

Review is read-only by default: no snapshot created, no modifications, no package built. Remediate must not use the scaffolder to rebuild an existing directory. If the user later authorizes remediation, restart from the remediate path and save a snapshot before the first write.

## Before starting

When a Skill already exists, fully read `SKILL.md` first, then load only the resources required by the current mode and the problem at hand. Inspect related directories, scripts, tests, evaluation cases, the README and platform assumptions; do not ask the user again for information that is already on disk.

"Silent" means completing checks directly when no user choice is required, not hiding the process. Briefly report the check result when finished.

Only ask when the goal or deliverable is unclear, when new permissions or services are needed, when content may be overwritten, or when a subjective direction would change the outcome. Ask all related questions at once.

Partition the work as follows:

- The Agent judges value, boundaries, architecture, exceptions and subjective quality.
- Programs execute deterministic, repeatable, verifiable, failure-sensitive steps.
- Sub-Agents isolate triggering and execution; humans judge aesthetics, copy and overall experience.

By default, build Skills that do not depend on a specific host. Formal instructions, references, the README, directory names and examples use generic terms such as "Agent, host, capability, isolated runner", never the current host's brand, dedicated directories, dedicated commands or private APIs.

If a core capability genuinely depends on a host, separate the host-only adapter from the generic flow and document the limitation and alternatives in the product definition and the compatibility section. In that case, the Skill cannot claim to support all hosts.

Below, `<python>` stands for a Python interpreter that has been located and confirmed to be at least 3.10. Internal program calls use `sys.executable`; on macOS and Linux the command line is usually `python3`, on Windows it is usually `py -3`. Do not assume that `python` exists.

## Create path

Read [Product design](references/product-design.md) first, confirm the problem is worth solving, and clarify the user, the current approach, the expected improvement, inputs, outputs, boundaries, risks and task type.

If the need is one-off, a regular Agent can already handle it stably, or you cannot describe what improves once the Skill is used, do not force a Skill into existence.

When a directory is needed, preview the minimal skeleton first:

```text
<python> <oil-skill-creator>/scripts/scaffold_skill.py <skill-name> --output-root <directory> --description <description> --public --dry-run
<python> <oil-skill-creator>/scripts/scaffold_skill.py <skill-name> --output-root <directory> --description <description> --public
```

Only add directories you actually need via `--components`, for example `--components scripts,tests`. Do not create empty resources just to look complete.

## Review and remediate path

Read [Review and remediation specification](references/review-and-remediation.md) first. Review checks both static defects and product-level problems a program cannot judge; "the validator passes" is not "the Skill is useful".

Before remediation, save an immutable baseline:

```text
<python> <oil-skill-creator>/scripts/snapshot_skill.py <skill-path>
```

The snapshot defaults to an external workspace. When the target lives in a scan directory named `skills`, place the workspace in the sibling `skill-workspaces/` so the snapshot is not detected as a duplicate Skill. The script refuses to overwrite an existing snapshot; later baselines must point to that snapshot, not to the directory currently being edited.

Report by P0, P1, P2 with evidence, impact, root cause, general fix and verification method. Ignore wording preferences that do not change behavior; do not treat reasonable trade-offs as defects.

When remediating, prefer fixing the rules, program interfaces or verification flow that caused the problem before fixing the current symptom. Keep the name, valid structure and content the user already has; do not rewrite the whole thing unless it is necessary.

## Design and authoring

### Trigger

All trigger information for the target Skill lives only in its frontmatter `description`. State what the target Skill does, when to use it, which similar requests should not trigger it, and how it shares responsibility with other Skills. Do not duplicate a separate trigger rule set in the target Skill's body.

Prepare real positive requests and easily confused negative requests. When trigger accuracy needs measuring, follow the trigger evaluation in the [Evaluation specification](references/evaluation.md); static keyword checks do not prove the trigger is reliable.

### First use and recovery

Handle first use, configuration, operations that need user confirmation and failure recovery per the decision table in [Product design](references/product-design.md). Preparation work that can be auto-discovered, is low-risk and is reversible is done silently.

Login, secrets, system install, overwrite, delete and external write must get authorization first.

When the target Skill needs persistent configuration or credentials, design regular configuration, credential references and secret storage separately per [Compatibility](references/compatibility.md). Do not put secret values into JSON, Skill files, logs or the Agent context. This is a design and acceptance requirement of the target Skill; it does not mean this Skill ships with a business credential adapter.

Repeated initialization or migration runs must not corrupt existing configuration and must not produce duplicate results. On failure, keep any still-usable intermediate artifacts and explain the failure location, recovery method and required steps that have not yet run.

### Information architecture

Read [Information architecture](references/information-architecture.md) before splitting files. The main flow lives in `SKILL.md`; stage details live in `references/`; steps with fixed results live in `scripts/`; run results and Review notes live outside the Skill.

If the target Skill will produce large artifacts that are hard to complete at once or to edit locally, or if it needs complex configuration, repeated previews and human adjustments, design split artifacts, programmatic assembly or reusable operation pages per [Product design](references/product-design.md).

Each step expresses one primary action. Branches sit next to the step they belong to. Terminology stays consistent. Do not write specific tasks, personal directories, single candidates, Review notes, change logs or version histories; only write rules, programs and regression tests reusable for similar tasks.

Skills describe the goal, judgement principles, main flow, required branches and stopping conditions; they do not enumerate specific scenarios into a rule tree. Finite, stable, verifiable branches go to programs; semantic and context-dependent choices stay with the Agent.

A Skill must not contain hidden behavior that contradicts its description, misleading capability claims, unauthorized access or data exfiltration. Compatibility may only state scope that is actually implemented or genuinely verified.

## Programmatic validation

During development, run:

```text
<python> <oil-skill-creator>/scripts/validate_skill.py <skill-path>
```

Before public release or before declaring remediation done, run:

```text
<python> <oil-skill-creator>/scripts/validate_skill.py <skill-path> --public --strict --weak-model --universal
```

The validator only handles problems programs can confirm. After validation passes, process meaning and real effect still need review. Only omit `--universal` when the product explicitly depends on a specific host, and document the reason in the compatibility section.

`--weak-model` enforces stricter structural limits; `--universal` checks whether a generic Skill hardcodes a host's brand or its dedicated paths.

## Outcome evaluation

When creating, when remediation changes actual behavior, when the user asks to prove an effect, or when preparing a public release, read the [Evaluation specification](references/evaluation.md) first. Create mode compares against a regular Agent; remediate mode compares against the pre-write `skill-snapshot`.

Fixed steps are prepared by the program:

```text
<python> <oil-skill-creator>/scripts/prepare_evaluation.py <skill-path> --mode create --iteration 1
<python> <oil-skill-creator>/scripts/prepare_evaluation.py <skill-path> --mode improve --iteration 1
```

The program inspects `evals/evals.json`, creates fixed `with_skill`, `without_skill` or `old_skill` directories, and emits `run_plan.json`. The Agent runs the current version and the baseline per the plan and does not invent extra directories or fields.

When runs complete, the program aggregates the data and emits a static review page:

```text
<python> <oil-skill-creator>/scripts/aggregate_evaluation.py <iteration-path>
<python> <oil-skill-creator>/scripts/generate_review.py <iteration-path>
```

Hand the candidate results, evidence and comparison report to the user first; do not keep editing the Skill before feedback arrives. Subjective results must be judged by humans; AI may only check what was explicitly asked or summarize differences.

Without isolated execution, declare the evaluation capability limited and do not claim an independent comparison was completed.

When results are poor, follow the [Evaluation specification](references/evaluation.md) to find the cause first; do not just append rules. Only when the Skill's flow, judgement principles or interfaces are actually responsible do you change rules intended to apply to similar tasks, and re-verify with the same failure type.

## Compatibility and publishing

Before release, read [Compatibility](references/compatibility.md) and [GitHub publishing](references/publishing.md). The README is for end users: state the value, installation, configuration, compatibility scope, data boundaries and output; do not copy the Agent's internal execution steps. The GitHub install section provides both "hand the repo URL to the Agent" and `npx skills add` as entry points.

After strict validation passes, package:

```text
<python> <oil-skill-creator>/scripts/package_skill.py <skill-path> --public --strict --weak-model --universal
```

Packaging uses stable ordering and fixed timestamps; by default it excludes `.git`, virtual environments, caches, `evals` and the run workspace. Review mode must not publish; remediate mode only publishes when the user asks for a release package.

## Definition of done

- Create: the value holds, the main flow is executable, static validation passes, the outcome evidence and the items that remain unverified are documented.
- Remediate: a snapshot exists, P0/P1 items have been handled or explicitly accepted, related regression tests and comparison evaluation are complete, and unrelated content has not been overwritten.
- Review: each conclusion has evidence, defects and trade-offs are separated, a priority-ordered minimum remediation plan is provided, and no external state has been modified.

On delivery, report only the file paths, main capabilities, program and test results, confirmed compatibility scope, outcome evidence and remaining risk. Do not restate the whole Skill, and do not write the execution process back into the formal files.
