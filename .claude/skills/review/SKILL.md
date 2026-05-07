---
name: review
description: Review the current branch as a PR, analyzing changes against main
disable-model-invocation: true
---

# Review Current Branch

Treat the current branch as a PR and write a thorough code review of the changes relative to `main`.

## Steps

1. **Gather context.** Run all of the following:
   - `git log main..HEAD --oneline` to see the commit history
   - `git diff main...HEAD --stat` to see which files changed and by how much
   - `git diff main...HEAD` to see the full diff

2. **Read surrounding context.** For each changed file, use the Read tool to read enough of the file to understand the context around the changes (not just the diff hunks). Pay attention to:
   - How the changed code fits into the broader module
   - Whether callers/consumers of changed APIs are updated
   - Whether tests cover the new or changed behavior

3. **Write the review.** Output a structured review with these sections:

   ### Summary
   A 2-3 sentence overview of what the PR does and why.

   ### Review

   Organize feedback into comments, each with:
   - **File and line reference** (e.g. `src/foo.py:42`)
   - **Severity**: one of `nit`, `suggestion`, `concern`, `issue`
     - `nit` — style/cosmetic, non-blocking
     - `suggestion` — a possible improvement, non-blocking
     - `concern` — something worth discussing, possibly blocking
     - `issue` — a bug, correctness problem, or missing handling that should be fixed
   - **Description** of the observation and, if applicable, a suggested fix

   If there are no comments in a severity category, omit it. Order comments by file, then by line number.

   ### Testing
   Comment on test coverage: are the changes tested? Are edge cases covered? Suggest specific tests if any are missing.

   ### Overall
   A short verdict: approve, request changes, or comment-only. Be direct.

## Guidelines

- Focus on correctness, clarity, and maintainability — not style preferences already enforced by linting.
- Point out actual bugs, logic errors, missing error handling at boundaries, and race conditions.
- If the diff is large, prioritize depth on the riskiest or most complex changes over exhaustive coverage of trivial ones.
- Reference the project's conventions from CLAUDE.md (line length, union syntax, license headers, etc.) only if the PR violates them.
- Be constructive and specific. Every concern or issue should explain *why* it matters.
- **Serialization compatibility (SSV).** If the diff changes anything that affects the serialized representation of a samplex (see examples below), flag it as an `issue` unless the PR also:
  1. Bumps `SSV` in `samplomatic/ssv.py`.
  2. Adds a new `DataSerializer` inner class with `MIN_SSV` set to the new SSV in the relevant `TypeSerializer`.
  3. Sets `MAX_SSV` on the previous `DataSerializer` so it raises when asked to serialize new-only values at the old SSV.

  Examples of changes that affect serialization:
  - Expanding the valid set of values for a serialized field (e.g., new entries in lookup tables like `PAULI_PAST_CLIFFORD_LOOKUP_TABLES`, `LOCAL_C1_PROPAGATE_LOOKUP_TABLES`, `SUPPORTED_1Q_FRACTIONAL_GATES`; new `VirtualType` enum members; new synth classes in `samplomatic/synths/`)
  - Adding, removing, or renaming fields in a node's serialized dict
  - Changing the type or semantics of an existing serialized field
  - Adding new `Serializable` classes (nodes, distributions, virtual registers) — these need a corresponding `TypeSerializer` in `samplomatic/serialization/`

  When in doubt, check whether the change could produce JSON that an older samplomatic would fail to deserialize.
