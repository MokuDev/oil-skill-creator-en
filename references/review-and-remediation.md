# Review and remediation specification

## What Review is for

Review judges whether a Skill is worth keeping, whether it can reliably do what it promises, and which problems need remediation. It does not only check formatting, and it must not promote the reviewer's personal preferences into enforced rules.

Read-only by default. Unless the user explicitly asks for remediation, do not modify files, create snapshots, publish, or change any external state.

## Inspection order

1. Read `SKILL.md` in full. Confirm the description's promises and reverse boundaries.
2. Follow the resource navigation to load the relevant `references`, `scripts`, `tests`, `evals` and the README.
3. Run `scripts/validate_skill.py` to harvest the issues a program can confirm.
4. Inspect what a program cannot judge: whether the Skill is useful, whether the flow is sound, how the subjective quality holds up, and whether compatibility claims are real.
5. Report confirmed defects, reasonable trade-offs and unverified risks separately.

Do not rule against a Skill just because it has many directories, lots of text, or an unusual implementation. Only report a problem when you are sure it causes false triggers, missed steps, instability, extra tokens, platform failure, unverifiability or comprehension difficulty.

## Review dimensions

| Dimension | Core question |
| --- | --- |
| Product value | Is there an observable or measurable improvement over a regular Agent; is it worth installing and maintaining |
| Trigger and boundaries | Are the should-trigger requests, the confusing should-not-trigger requests, and the division of labor with other Skills clear |
| Main flow | Are the modes, ordering, branches, stop conditions and recovery entry points complete |
| Over-constraint | Does it offer a flow and judgement principles, rather than replacing contextual judgement with case lists and many branches |
| Programmable | Are deterministic and mandatory steps still being improvised by the Agent |
| Artifacts and UI | Are large artifacts hard to generate reliably or edit locally; are complex configuration or human preview still handled through dialogue or ad-hoc pages |
| Onboarding | Is reversible, auto-discoverable preparation done silently, and are high-risk actions confirmed |
| Stability | Are repeated runs safe; does it refuse accidental overwrite, keep intermediates, support recovery |
| Outcome evidence | Is there real triggering data, baselines, check results, duration, tokens and human review |
| Weak model | Can the entry, branches, terminology and resource reads be understood in one pass |
| Layering and tokens | Does each rule live in exactly one place; are references read on demand; are there empty directories or resources without an entry point |
| Compatibility | Are platforms, hosts, dependencies, paths, shells and fallbacks declared honestly |
| Host neutrality | Does the Skill mistake the current host's brand, directories, commands or private capabilities for a generic flow |
| README | Does it explain value, installation, configuration, usage, data and boundaries |
| Security and credentials | Does behavior match the description; are personal paths hardcoded, plaintext secrets committed, high-risk credential files used, or secrets allowed into logs and Agent context |

## Severity levels

- **P0**: breaks the core result, security, data, permissions, or recoverability, or makes the main flow unrunnable. Must not ship before remediation.
- **P1**: causes errors, clear regressions, false triggers, result instability or noticeably higher maintenance cost in common scenarios. Handle in the current remediation.
- **P2**: does not block the core flow, but raises comprehension, token, compatibility or maintenance risk. May be handled later.

Wording preferences that do not change behavior are not defects. When you cannot confirm, mark "unverified"; do not force-rank to fill P0/P1/P2.

## Evidence requirements

Each issue includes:

1. A short title and severity level;
2. The file, section, command output or recurring behavior that proves it;
3. The impact on users, Agent, platform or release;
4. The rule, default, interface or verification gap that produced it;
5. The minimum reusable fix;
6. A check or test that proves the issue will not reappear.

When adding a check rule, construct files or data starting from a real entry point and prove the rule is reachable along the full call chain; do not only test a regex or function detached from any entry.

Distinguish three conclusion types:

- **Confirmed defect**: existing files or runtime evidence prove it directly;
- **Reasonable trade-off**: aligns with goal and compatibility scope; no need to change for the sake of stylistic uniformity;
- **Unverified risk**: missing real platform, host, weak-model or user-feedback evidence.

Only write a host's brand when the core function genuinely depends on it. In that case, split the host-only content from the generic flow and document the incompatible scope.

Using a host in the current session does not mean it should be written into the rules.

## Review output

Lead with a one-sentence overall judgement, then list P0/P1/P2 issues. When a level has no issues, explicitly write "none" — do not pad with summary or praise.

Follow up with:

- Capabilities worth keeping;
- Remediation order and dependencies;
- Validation that has run and has not;
- Subjective or product trade-offs that need the user's call.

The Review report lives in the dialogue or the external workspace; it does not enter the Skill scan directory or the formal Skill. Do not write specific candidates, single-fix narratives, or version histories.

## Remediating an existing Skill

Remediation is the write phase after Review:

1. Inspect the workspace and existing user changes; avoid overwriting unrelated content.
2. Before the first edit, run `scripts/snapshot_skill.py`.
3. Fix P0 first, then P1; P2 only when it serves the current goal.
4. Prefer fixing the underlying rule, program interface, default or test that caused the symptom, not only the surface result.
5. Steps stable enough for a program become scripts plus regression tests; semantic or subjective problems become judgement principles, never hardcoded branches.
6. Keep the original name and valid resources; do not rebuild directories or rewrite the whole thing without need.
7. Run static validation, the relevant program tests, and the outcome comparison.
8. Only the currently valid rules get written back into the Skill; the review process and before/after diffs stay in the workspace or Git.

If the user only authorized partial remediation, report remaining issues and impact and do not widen scope on your own. If a fix needs new permissions, external services, destructive operations, or a product-direction choice, ask for authorization first.
