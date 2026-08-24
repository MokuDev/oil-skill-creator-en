# Information architecture and weak-model readability

## One place per type of content

| Layer | Sole responsibility |
| --- | --- |
| frontmatter | When to trigger, when not to, and required compatibility conditions |
| `SKILL.md` | Modes, ordering, decisions, branches, stop conditions and when to read resources |
| `references/` | Checklists, data formats, explanations and platform details only used in specific stages |
| `scripts/` | Deterministic, repeatable, verifiable execution |
| `assets/` | Reusable pages, styles, static templates and other non-instruction resources |
| `README.md` | The user-facing value, installation, configuration, usage and boundaries |
| External workspace | Output, feedback, comparison reports, reviews and version diffs |

Reading only `SKILL.md` should already let the Agent pick the correct path, without having to load every reference first. `SKILL.md` does not copy detailed checklists or data formats; references do not re-state trigger conditions; the README does not copy the Agent's internal flow.

Splitting files does not automatically save tokens. Layering only helps when the entry point is clear, references are read on demand, and the same content is not restated.

## When to split into a new file

Only create a new file when:

- Content is only used in one mode, stage, platform or framework;
- A program can execute it without loading source code;
- A reusable page or static template needs independent maintenance, preview or copy-as-is;
- The program needs its own regression test;
- The main file cannot keep branches and stop conditions clear without splitting.

Do not create empty `references/`, `assets/`, `tests/` or `evals/` directories just to look complete. When a resource has no explicit read entry, execution entry or user purpose, add the entry or delete it.

## Writing for weaker models

- One instruction carries one primary action;
- Make the subject, input, output and stop condition explicit;
- Place branches and prohibitions next to the step they belong to;
- Use the same name for the same concept every time;
- Control heading depth and list nesting; avoid multi-level jumps;
- Do not rely on implicit references like "as above" or "same as before";
- Examples use minimal safe defaults; do not show full configurations that establish wrong defaults;
- Programs return explicit status and the next step, not long logs for the model to parse.

Shorter is not automatically clearer. Cutting conditions, subjects or outputs invites guessing and rework; restating the full rule also leaves the model unsure which version is current.

## Program vs. Agent boundary

Programs are well suited to checking structure, links, data formats, naming, duplication, paths, secrets, fixed directories, statistics, and reproducible archives. Agents judge value, semantic conflict, over-constraint, subjective quality and unaddressed exceptions.

A passing program check only means known machine rules did not fail. Review must keep checking product promises and real behavior; zero warnings is not proof of effect.

## Static complexity check

`scripts/validate_skill.py` checks:

- `SKILL.md` line count, section length, paragraph length, heading depth and list nesting;
- Whether `references/` can be reached from `SKILL.md`;
- Whether large references provide a table of contents;
- Whether the root directory is piled with Markdown whose role is unclear;
- Long, exact or near-exact duplication across Markdown documents;
- Concrete user directories, common secret formats, private key blocks and suspicious plaintext credential assignments in the text, source and config files the validator can read;
- High-risk credential files that should not enter a Skill, such as `.env`, `credentials.json`, private key files;
- Evaluation data format and rough token scale of the docs.

These signals only surface comprehension risk. The program cannot prove a model will pick the right mode or make the correct semantic judgement.

## Weak-model dry run

Run the lowest-capability model the plan supports, independently and without author context:

1. One full main flow;
2. One error-prone remediation or stop branch;
3. One easily confused but should-not-trigger task.

Check that it picks the right mode, reads only the required resources, calls the prescribed scripts, does not re-implement program logic, and stops where it should. On failure, fix the entry, naming, branch placement or program interface first; do not append more explanation immediately.

When the weak model is not within supported scope, document it clearly in the README and `compatibility`; do not endlessly expand the Skill just to claim compatibility.
