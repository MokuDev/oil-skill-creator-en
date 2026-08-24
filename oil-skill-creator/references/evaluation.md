# Skill evaluation specification

## Pick the evaluation type first

- **Objective**: output can be verified by format, files, numbers, steps or programmatic requirements.
- **Subjective**: the core value hinges on aesthetics, tone, creativity or overall experience.
- **Mixed**: both explicit requirements and human preferences.

The evaluation method follows the task type. Explicit requirements and subjective conclusions must be reported separately and cannot be merged into a single score.

## Test set

Tests live in the target Skill's `evals/evals.json`. Each entry uses fixed fields:

```json
{
  "id": 1,
  "name": "descriptive-name",
  "prompt": "Real user request",
  "expected_output": "Expected-result description",
  "files": [],
  "expectations": ["Verifiable requirements"]
}
```

Start with 2-3 real requests that cover the main flow, error-prone branches and similar-task boundaries. Verifiable requirements go into `expectations`; do not repurpose other fields. Subjective preferences become human-review questions, never disguised as programmatic requirements.

## Fixed comparison baseline

- Creating a new Skill: baseline is `without_skill`, with no Skill loaded.
- Remediating an existing Skill: run `scripts/snapshot_skill.py` before the first edit; baseline is `old_skill`, which only loads `skill-snapshot`.
- The current version is always named `with_skill`.

The directory currently being edited cannot stand in for the old version, and snapshots may not be taken after the edits are done.

## Preparing the evaluation directory

Run from inside the target Skill directory:

`<python>` follows the interpreter that has already been parsed and version-checked in `SKILL.md`.

```text
<python> <oil-skill-creator>/scripts/prepare_evaluation.py . --mode create --iteration 1
<python> <oil-skill-creator>/scripts/prepare_evaluation.py . --mode improve --iteration 1
```

`improve` mode inspects `skill-snapshot` in the external workspace. When the Skill sits in a scan directory named `skills`, the default workspace is `skill-workspaces/<skill-name>-workspace/` next to it, so the snapshot is not detected as a duplicate Skill. Each round uses a fresh `iteration-N` directory; the program refuses to overwrite and produces the structure below:

```text
<workspace>/
├── skill-snapshot/               # improve mode only
└── iteration-N/
    ├── run_plan.json
    └── <eval-name>/
        ├── eval_metadata.json
        ├── with_skill/
        │   └── run-1/outputs/
        └── without_skill/         # create mode
            └── run-1/outputs/
```

In improve mode `without_skill` is replaced with `old_skill`. To measure variance, use `--repetitions` to create multiple runs; do not copy directories by hand.

## Running the current version and the baseline

An isolated executor is an Agent or runtime that does not inherit the author's working context and only receives the present request and the specified Skill.

Read `run_plan.json` and run both the current version and the baseline in the same round. Each executor receives identical requests, input files, model and environment; only the Skill loaded differs.

- Provide the Skill path explicitly so the executor actually loads the Skill;
- Do not paste the Skill body into the task prompt;
- Output only into the `outputs/` directory specified in the plan;
- Do not tell the subjective reviewer in advance which version is newer.

If you cannot run them concurrently, run sequentially, but keep the plan and environment consistent, and note this limitation in the results.

## Recording timing, tokens and objective results

Each `run-N/` saves `timing.json`:

```json
{
  "total_tokens": 1200,
  "duration_ms": 8500,
  "total_duration_seconds": 8.5
}
```

Objective runs additionally save `grading.json`:

```json
{
  "expectations": [
    {"text": "Output includes required fields", "passed": true, "evidence": "result.json"}
  ]
}
```

Every requirement a program can check must be checked by the corresponding script; do not let the Agent eyeball it. Evidence must reference real files or command output, not the executor's own description.

## Producing the comparison report and handing it to humans

Once all runs complete:

```text
<python> <oil-skill-creator>/scripts/aggregate_evaluation.py <iteration-path>
<python> <oil-skill-creator>/scripts/generate_review.py <iteration-path>
```

The aggregator produces `benchmark.json` and `benchmark.md`. Both record averages, variance and baseline deltas for pass rate, duration and tokens. It also generates a local `review.html` review page, but it does not auto-open the browser; the page can export `feedback.json`.

Show the candidate results, evidence and comparison report to the user first, then stop and wait for feedback. Without a GUI, walk through the same order in the dialogue and turn user comments into `feedback.json`. Do not keep editing the Skill before feedback arrives.

## Subjective and mixed types

Subjective evaluations follow this order:

1. Independent executors produce the candidates;
2. Program checks size, format, count, paths and openability;
3. Versions are displayed side by side with their identities hidden;
4. The user decides which is clearer, better matches their preference, and is more likely to be used;
5. Feedback is abstracted into general rules; candidate content is not copied.

Another model may organize the differences, but may not substitute its own scoring for the user. Mixed evaluations report objective thresholds, human preferences, duration, tokens and unverified risk separately.

## Trigger evaluation

`description` optimization must distinguish static checks from real measurement. Prepare 8-10 should-trigger requests and 8-10 easily confused but should-not-trigger requests. Confirm with the user and freeze the test set; later versions cannot change the questions.

The scoring program splits cases by ID into two groups: 60% is the training set (`train`), used while editing the description; 40% is the holdout (`holdout`), used only when finally picking a version.

### Preparing trigger data

Evaluation set:

```json
{
  "skill_name": "example-skill",
  "cases": [
    {"id": "case-1", "query": "Real request", "should_trigger": true}
  ]
}
```

Saved results after isolated execution:

```json
{
  "skill_name": "example-skill",
  "description": "The description actually loaded this round",
  "cases": [
    {"id": "case-1", "trials": [true, true, false]}
  ]
}
```

Strict mode requires at least three runs per request and the run count must be odd. The trigger tests and holdout file go to an independent sub-Agent or other isolated executor; the Skill author only sees the training report:

```text
<python> <oil-skill-creator>/scripts/score_triggers.py <eval-set> <candidate-results> --skill-path <current-skill> --phase train --strict --output <workspace>/trigger-train.json
```

The `train` output contains only the training-set summary and cases; it omits holdout IDs, results, and grouping. The program also checks that the description in the results matches the corresponding `SKILL.md` and saves a digest of the test set and description.

### Picking the final version

The isolated executor saves the baseline `select` report and keeps it away from the author during the rewrite phase. Once the candidate version is finalized, run the final selection:

```text
<python> <oil-skill-creator>/scripts/score_triggers.py <eval-set> <baseline-results> --skill-path <baseline-skill> --phase select --strict --output <workspace>/trigger-baseline-select.json
<python> <oil-skill-creator>/scripts/score_triggers.py <eval-set> <candidate-results> --skill-path <current-skill> --phase select --strict --baseline-report <workspace>/trigger-baseline-select.json --output <workspace>/trigger-candidate-select.json
```

The report only marks `recommended: true` when all of the following hold:

- Holdout accuracy increased;
- Hit rate on should-trigger requests did not drop;
- Exclusion rate on should-not-trigger requests did not drop.

Trade-offs are escalated to the user. Improvements on the training set may not mask regressions on the holdout, and accuracy cannot be claimed from keywords alone or the author's intuition.

The program can keep holdout data out of the training report accidentally, but it cannot stop an author with full file permissions from reading on purpose.

Without an isolated executor, mark "holdout not independently run" and do not claim the new description also improves on unseen requests.

## Iterate and stop

Each round writes a new `iteration-N` and uses the same frozen baseline. Only update a round's evaluation info when the test request itself changes; do not overwrite previous rounds.

When results disappoint, do not immediately bolt prohibitions or one-offs onto the Skill. First compare the baseline and the Skill-equipped runs; combine input completeness, executor drift, tool limits, environmental variance and user feedback to confirm whether the Skill caused or amplified the problem.

If the issue is in the Skill, fix the stage goal, judgement criteria, tool interfaces or verification checkpoints first. Add programmatic branches only when conditions are objective and handling is stable; afterwards, regress with the original failure type together with normal main-flow cases.

Stop when any of the following holds:

- The user confirms the real result meets their needs;
- The objective metric reaches the pre-agreed threshold with no clear regressions;
- New edits stop producing observable or measurable improvement;
- Further optimization costs more in time or tokens than it returns.

Without a sub-Agent or other isolated execution, only the author can dry-run and hand outputs to humans. State "independent verification has not been completed" explicitly; do not treat static validation or author self-test as complete outcome evidence.
