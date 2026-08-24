# Compatibility and runtime boundaries

This file is for designing and Reviewing the target Skill. It lays out the cross-platform and credential boundaries the target Skill should meet; `oil-skill-creator` is responsible for checking the design and known static risks, and does not stand in for the target Skill's business runtime or system-credential adapter.

## Compatibility scope to verify

Check each item:

- Operating systems: macOS, Windows, Linux;
- Agent host: can it launch sub-Agents, does it provide browser, image, audio/video or GUI capability;
- Runtime: Python, Node, Java or system tool versions;
- Shell: bash, zsh, PowerShell, cmd;
- Filesystem: path separator, case sensitivity, permissions, symlinks and line endings;
- External services: network, authentication, region, cost and rate limits.

State only the platforms you have actually verified. Unverified platforms get "unverified". When a capability is required, explain what to substitute when it is missing.

## Host neutrality

- By default, write a Skill that any Agent host with the required capability can understand.
- Core flow uses capability descriptions. Do not substitute host brand names, proprietary tool names, proprietary config directories or private commands for capability descriptions.
- Use real checks to decide whether the host offers sub-Agent, browser, GUI, filesystem or statistics support; do not guess from the host's name.
- Host-specific metadata or adapters must be separated from `SKILL.md`'s core flow; after removing the adapter the generic capability should still stand.
- When the product genuinely only serves one host, mark "host-only" explicitly, explain why and what is not supported, and do not pretend to be a generic Skill.

## Cross-platform scripting rules

- Prefer the Python 3 standard library and `pathlib`.
- Use `sys.executable` when invoking the current Python; do not guess the `python3` path.
- On first run, check `sys.version_info >= (3, 10)`; the command-line docs should mention `python3` on macOS/Linux and `py -3` on Windows.
- Pass argument lists to `subprocess`; never concatenate Shell strings.
- Read and write text with UTF-8 explicitly.
- Use the system temp directory for temp files.
- Do not hardcode `/Users/...`, `~/.config` or `C:\\Users\\...` in programs.
- Resolve user-config paths through env vars, platform directories or explicit parameters.
- Do not rely on `open`, `brew`, `which`, `chmod` or other single-platform commands for the core flow.
- When platform-specific scripts are necessary, split the implementation and detect capability at the entry point.

## Pre-run checks

Before execution, check programmatically:

- Required commands and runtimes exist;
- Versions satisfy the constraints;
- Inputs are readable, outputs are writable;
- Configuration and credentials can be parsed;
- The current host has the tools the task needs;
- Outputs may already exist.

The checks themselves should be read-only, fast and repeatable. Be concise in the happy path; on failure, list what is missing and how to fix it.

## Configuration and migration

- Regular configuration lives in the user directory, not the Skill repo.
- Allow env-var overrides of default paths.
- Keep a compatibility window when reading old configuration; migration does not delete the original file.
- Configuration updates use merge-write and never overwrite unknown fields.
- Writes use a temp file plus atomic replace to avoid corruption from interruption.
- Logs and final replies do not display full secrets.

Specific user directories cannot be hardcoded in the Skill. Paths come from command arguments, env vars, `Path.home()` and similar platform-directory resolution, or from configuration examples with explicit placeholders.

## Credential storage

JSON, YAML and regular config files only hold non-sensitive settings and credential references, such as service name, account name or `credential_ref`. They never store secret values.

Pick the credential source in this order:

1. Reuse the secure credential capability that the target environment already provides;
2. On the desktop, use a mature adapter against macOS Keychain, Windows Credential Manager or Linux Secret Service;
3. In CI, containers or headless environments, use runtime environment variables;
4. When no secure storage exists, stop and document the limitation; never silently downgrade to a plaintext file.

When using a cross-platform credential library, first confirm the current backend is actually connected to the system encrypted store. Refuse plaintext backends and offer an alternative when initialization fails.

The Agent only handles credential references and missing-state. Programs read secrets at runtime and call the target service directly; secrets never go into command arguments, stdout, logs, caches, snapshots, evaluation directories, or Agent context.

First-time save, replacement, migration and deletion of credentials require authorization. Repeated initialization should reuse the existing credential reference; it must not create duplicates or overwrite another account.

When the target Skill implements a credential adapter, it must at minimum provide read, save and delete, and:

- The interface locates records through the credential reference and the returned result and error info must not contain the secret value;
- Save and delete require authorization; read only happens inside the program that actually calls the service;
- Startup checks distinguish secure backend, plaintext backend and backend unavailable, and stop immediately when insecure;
- Tests use fake credentials and verify that command arguments, logs, output, caches and evaluation directories never leak.

## Platform-specific capability

A Skill may depend on a specific platform, but it must say so. When core functionality depends on a platform:

- Declare it in `description` or `compatibility`;
- It must be visible in the README before installation;
- The initializer checks before writing and stops immediately when unsupported;
- Do not half-attempt the unsupported platform before failing;
- If other workable approaches exist, describe their effect and cost differences.

## Verification matrix

When releasing, record:

| Dimension | Status |
| --- | --- |
| Current development platform | Tested / Untested |
| Other operating systems | Tested / Static-checked / Unverified |
| No sub-Agent environment | Supported / Degraded / Unsupported |
| No browser or GUI | Supported / Degraded / Unsupported |
| Offline environment | Supported / Partial / Unsupported |

Static checks are not real runs. When reporting, separate "no platform assumption detected in code" from "actually executed successfully on this platform".
