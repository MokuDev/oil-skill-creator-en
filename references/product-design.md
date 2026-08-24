# Skill product design

## Judge value first

A Skill should improve at least one of the following:

- A regular Agent often misses critical steps;
- The same workflow happens repeatedly, with the solution re-discovered every time;
- The output needs a stable format, file or validation;
- Dependencies, configuration, permissions, and the fallback after failure are complex;
- Personal experience needs to be turned into reusable judgement rules;
- Explicit human-AI collaboration checkpoints are needed.

If the need is one-shot, a simple reminder, or something a regular Agent already handles stably, prefer a short doc, a template, or a standalone script. A Skill is not the default answer.

## Clarify before creating

Answer these questions before creating. Do not ask again for answers you can already derive from existing context; ask everything missing that actually affects the result in one batch.

| Item | Question to answer |
| --- | --- |
| User | Who will use this, in which environment |
| Problem | Which recurring problem is worth solving |
| Current approach | What becomes unstable or inefficient without a Skill |
| Expected improvement | What observable or measurable change comes from using it |
| Inputs | What the user must provide |
| Outputs | What gets delivered, and where it lands |
| Boundaries | What is explicitly out of scope, and who owns it |
| Risks | Permissions, privacy, overwrite, cost and platform limits |
| Type | Objective, subjective, or mixed |

Do not mechanically paste this table into every Skill. It is for design decisions; only what truly affects usage enters the published docs.

## First use

By default, silently complete preparation work that can be auto-discovered, is low-risk, and is reversible. Only ask the user when a real decision is missing.

| Behavior | Default handling |
| --- | --- |
| Detect OS, commands, versions, directories and existing config | Run silently |
| Create conflict-free working directories and caches | Run automatically |
| Read existing preferences and reuse them | Run automatically |
| Migrate config while keeping the original file | Run automatically and report |
| Sign in, enter secrets, install system software | Explain impact and ask first |
| Overwrite, delete, upload, publish or external write | Require explicit authorization |
| Subjective direction that materially changes the result | Ask once, grouped |

Silent is not hidden. Say in one sentence what was completed automatically; on failure, say where it stopped.

## Agent vs. program boundary

Signals that favor programs:

- Inputs and outputs can be described precisely;
- Same input should produce the same output;
- Must be executed every time;
- Success or failure can be judged by an explicit result;
- Missing the step causes significant loss;
- Multiple executors are reimplementing the same logic.

Signals reserved for the Agent:

- Understanding the underlying problem the user means to solve;
- Multiple reasonable strategies that depend on context;
- Semantic, aesthetic or editorial judgement;
- Exceptions that cannot be exhaustively enumerated;
- Trade-offs that must be negotiated with the user.

When rules are fixed, programs run them; when semantics or trade-offs matter, the Agent judges. Do not make the Agent restate a script's internal steps line by line, and do not dress subjective judgement up as deterministic code.

## Flow over rule trees

A Skill should offer a context-adaptable workflow rather than enumerate increasingly specific cases.

- State the stage goal, inputs and outputs, judgement criteria, required branches, recovery and stop conditions;
- Only fix into a program or decision table when branches are finite, conditions are objective, and handling is stable;
- When semantics, strategy or aesthetic judgement matters, give the principle and evidence requirement, and let the Agent combine with context;
- For new problems look for an existing-flow gap first; do not add a product name, fixed wording, special path or one-shot exception for a single failure;
- When rules keep growing without improving real outcomes, fall back to a simpler flow and reassess.

## Large artifacts

A long artifact does not in itself mean splitting is needed. Consider partitioned generation only when:

- Single-shot generation often fails, drops content, or contradicts itself across sections;
- Editing a local section requires rewriting the whole artifact;
- The artifact has stable, relatively independent components;
- The final combination can be assembled deterministically.

When you split:

1. Define section boundaries, inputs and outputs, and stable identifiers;
2. Let each section be generated, checked and redone independently;
3. Save usable intermediates early;
4. Validate and assemble the final artifact with scripts;
5. Local edits only redo affected sections.

Do not split mechanically by line count. When parts strongly depend on each other, use a fixed skeleton with content slots to keep the whole consistent; do not force arbitrary fragments.

## Reusable operation pages

When users need to configure several related options, repeatedly preview and adjust, or carry out a subjective confirmation, ship a reusable config page, editor or preview page with the Skill.

- The page reads a stable config file or manifest and does not rely on the Agent to assemble data ad hoc;
- The program launches the page, loads data, saves results and checks save status;
- The Agent explains the entry point and resumes the flow once the user is done;
- Pages and data are maintained separately; do not have the Agent regenerate the page every time;
- For simple choices, keep using the dialogue or a config file; do not add a page just for the sake of completeness.

Prefer local, repeatedly relaunchable pages. When the page genuinely depends on a specific platform UI, document it under compatibility and provide a viable alternative.

## Token control

- `description` only handles triggering; never restate the full workflow;
- `SKILL.md` keeps only the main path, key branches and resource navigation;
- `references/` is read at decision points, not loaded in full at the start;
- Script output is concise by default; detailed diagnostics go to a file or are requested via `--json`;
- Do not duplicate the same rule across files; pick a single source of truth;
- Large data formats, platform details and templates go in separate resources;
- When measuring tokens, look at input context, tool output and rework cycles together; do not judge by `SKILL.md` character count alone.

Shorter is not always cheaper in tokens. A program that reduces exploration, errors and rework may lower total cost even if it adds some prose.

## Improving a Skill from outcome feedback

When task outcomes are poor, first save the inputs, outputs, runtime, tool results and user feedback, then decide where the problem comes from:

1. Trigger or boundary error;
2. First-use flow missing;
3. Unreasonable defaults;
4. A step that should be a program was delegated to the Agent;
5. Missing validation, missing fallback, or repeated runs corrupt existing results;
6. Platform or host assumption is wrong;
7. The README did not explain it clearly;
8. The test set does not cover this risk class;
9. Insufficient input, executor drift or external capability limits — not a Skill defect.

Only modify the Skill when its design causes or amplifies the problem:

- For semantic problems, change the flow or the judgement principle;
- For fixed-result problems, change the program or the check;
- For subjective problems, adjust from human feedback.

After the change, re-verify with similar requests and confirm reasonable handling has not been unnecessarily restricted.

One-off anomalies stay in the external workspace. Only experience that remains true when the task changes earns its way into a general principle, a script, or a regression test. Specific tasks, product names, user paths and change histories do not enter the formal Skill.
