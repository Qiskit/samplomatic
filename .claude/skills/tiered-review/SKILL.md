---
name: tiered-review
description: >-
  Perform a tiered review of the current branch as a PR, analyzing changes against main.
  Runs ONE review tier per invocation — design → architecture → correctness → polish —
  each assuming the previous tiers are already settled. Invoke as
  `/tiered-review <tier> [scope] [effort]` (e.g. `/tiered-review design`,
  `/tiered-review correctness serialization high`).
disable-model-invocation: true
---

# Tiered review

A review workflow proceeding in four tiers, one per invocation. Each tier is a fresh run (it
re-diffs the current tree), and each tier **assumes the tiers above it are already settled** and
refuses to drift downward.

```
Tier 1  design       — approach & intent      (chat only)
Tier 2  architecture — structure & API         (chat only)
Tier 3  correctness  — bugs, tests, SSV compat  (chat only; may edit only if --fix)
Tier 4  polish       — conventions & docs       (chat only; may edit only if --fix)
```

The user controls the transitions between tiers: they invoke a tier, resolve what it surfaces on
their own time, then invoke the next tier. Do **not** run multiple tiers in one invocation — do
exactly the one requested and recommend the next.

## What this package is

Samplomatic samples randomizations of quantum circuits (e.g. Pauli twirling). Users annotate
Qiskit circuits with box instructions (`Twirl`, `ChangeBasis`, `InjectNoise`), then call `build()`
to get a parameterized **template circuit** and a **samplex** (a DAG) that generates randomization
samples. The public API is deliberately tiny: `build`, `Twirl`, `ChangeBasis`, `InjectNoise`,
`Tag`. The core pipeline is: **annotated circuit → `pre_build()` → (TemplateState, PreSamplex) →
`finalize()` → Samplex**, and `Samplex.sample()` runs the DAG to produce samples.

## Arguments

`/tiered-review <tier> [scope] [effort] [--fix]`

- **tier** (required): one of `design`, `architecture`, `correctness`, `polish`. Accept obvious
  synonyms (`arch`→architecture, `bugs`→correctness, `nits`/`style`→polish). If no tier is given,
  default to `design` and say so.
- **scope** (optional): a git ref or diff range. Default `main...HEAD` (merge-base diff of the
  current branch against `main` — only what this branch changed). A bare branch name `X` means
  `main...X`. Accept an explicit range verbatim.
- **effort** (optional): `low` | `medium` | `high` | `xhigh` | `max`. Default `high`. Scales how
  deeply you trace call paths, sampling logic, and serialization round-trips.
- **--fix** (optional, tiers 3–4 only): after presenting ranked findings, apply the safe,
  mechanical ones. Never edit files in tiers 1–2.

## Step 0 — set up (every tier)

Do this first, regardless of tier:

1. **Resolve scope.** Compute the diff range (default `main...HEAD`). Run
   `git diff --stat <range>` and `git diff <range>` to get the change. If the diff is empty, say so
   and stop.
2. **Frame intent.** In 2–4 sentences, state what the change is *trying to accomplish*, inferred
   from the diff, commit messages (`git log main..HEAD --oneline`), and any touched docstrings.
   Every tier judges the change against this intent.
3. **Read surrounding context.** For each changed file, read enough of the file (not just the diff
   hunks) to understand how the change fits its module, whether callers/consumers of changed APIs
   are updated, and where it sits in the build → finalize → sample pipeline.
4. **Load context.** Read the root `CLAUDE.md`, then work through the section for the requested tier
   under [Tier logic](#tier-logic) below.
5. **Review cold.** Judge the diff on its own merits. Do not make assumptions based on other
   branches or external context unless the diff, CLAUDE.md, or the user says so.

## The escalation contract

Each tier stays in its lane. This is what keeps the phases from collapsing into one undifferentiated
review:

- **A tier assumes every higher tier is settled.** `correctness` does not relitigate the API shape;
  `polish` does not raise design concerns.
- **A tier refuses to drift downward.** If while doing `design` you notice a bug, do **not** report
  it as a design finding — note in one line that lower tiers exist for it and move on. The `design`
  tier explicitly does **not** flag bugs, style, or nitpicks.
- If you believe a *higher* tier was mis-resolved (e.g. during `correctness` you realize the whole
  approach is wrong), that IS worth raising — surface it briefly and suggest re-running the higher
  tier, rather than reviewing downward on a foundation you doubt.

## Finding format (all tiers)

Produce a **ranked** list, most important first. Rank by impact on the change's goal, not by how
easy it is to describe. Each finding gets:

- a **`file:line` anchor**,
- a **severity** — `nit` | `suggestion` | `concern` | `issue`
  (`nit` = cosmetic/non-blocking; `suggestion` = optional improvement; `concern` = worth
  discussing, possibly blocking; `issue` = a bug/correctness/compat problem that should be fixed),
- a one-line summary, a short rationale (*why it matters*), and — where useful — a concrete
  alternative or fix.

If a tier finds nothing, say so plainly.

## Tier logic

### Tier 1 — `design` (chat only)
Judge strategy and design choices harshly, but do not comment on code details.

- **Do the changes make conceptual sense?** Do they fit the build → finalize → sample pipeline
  without adding unnecessary complexity or duplicating existing abstractions (a new distribution vs.
  reusing `distributions/`; a new virtual group vs. reusing `virtual_registers/`; a new node vs.
  composing existing `samplex/nodes/`)? Is there a simpler approach?
- **Does it belong here?** Distinguish work that belongs upstream in Qiskit (`quantum_info`,
  transpiler primitives, circuit construction) from work that genuinely belongs in samplomatic
  (twirling/injection, virtual-group algebra, samplex sampling). Prefer reusing upstream primitives.
- **Does the public surface stay small?** New top-level exports beyond `build` + the annotation
  types must earn their place; most new capability should be reachable through annotations and
  `build()`.

Report to chat. Do not edit files. Anchors: `builders/build.py`, `pre_samplex/`, `samplex/`,
`annotations/`, `samplomatic/__init__.py`, `README`.

### Tier 2 — `architecture` (chat only)
Concrete structure and public surface, **assuming design is settled**. Judge:

- **Placement of responsibility.** Does new logic live in the right subpackage (see
  [subpackage roles](#reference-subpackage-roles))? PreNode vs. Samplex node; distribution vs.
  virtual register vs. synth.
- **Contracts & typing.** ABC/`Generic`/`TypeVar` contracts on node/register/distribution base
  classes; hashing and equality correctness for key-like objects; enum discipline (`VirtualType`,
  modes, directions).
- **Serialization convention (structural).** If a new `Serializable` type is introduced (node,
  distribution, virtual register), it needs a corresponding `TypeSerializer` in
  `serialization/`. Judge *whether* it should be serializable and *whether the shape is right*;
  the mechanical versioning discipline is a Tier 3 gate.
- **Tensor abstraction.** Sampling/evaluation paths should go through `tensor_interface` rather
  than reaching for raw numpy, so alternative array backends keep working.
- **Naming & backward-compat.** Public names mirror Qiskit conventions where relevant; changes to
  existing signatures/behavior are called out.

Report to chat. Do not edit files. Anchors: `samplex/nodes/`, `pre_samplex/`,
`virtual_registers/`, `distributions/`, `synths/`, `serialization/`, `tensor_interface.py`.

### Tier 3 — `correctness` (bugs, tests, SSV compat)
Bugs and logic errors, **assuming design and architecture are settled**. Trace the riskiest paths:
virtual-group composition/commutation rules, propagation direction through box content, node
lowering in `finalize()`, and the three `sample()` phases. Look for off-by-one indexing into
register arrays, broadcasting bugs across `(num_subsystems, num_randomizations)`, and unhandled
boundary inputs (empty boxes, 0-qubit / 1-qubit instructions, unparameterized gates).

**Test coverage of the change itself** is part of correctness: new or changed behavior, branches,
and edge cases must be exercised — an untested path is a latent correctness gap, not a style nit.
(Whether the *existing* tests follow project conventions is Tier 4.) Confirm new behavior has a
seeded (`rng` fixture) deterministic test, and that serialization changes have a round-trip test.

**SSV serialization compatibility (hard gate).** If the diff changes anything that affects the
serialized representation of a samplex, flag it as an `issue` unless the PR also:
  1. Bumps `SSV` in `samplomatic/ssv.py`.
  2. Adds a new `DataSerializer` inner class with `MIN_SSV` set to the new SSV in the relevant
     `TypeSerializer`.
  3. Sets `MAX_SSV` on the previous `DataSerializer` so it raises when asked to serialize
     new-only values at the old SSV.

Changes that affect serialization include:
  - Expanding the valid set of values for a serialized field (e.g. new entries in lookup tables
    like `PAULI_PAST_CLIFFORD_LOOKUP_TABLES`, `LOCAL_C1_PROPAGATE_LOOKUP_TABLES`,
    `SUPPORTED_1Q_FRACTIONAL_GATES`; new `VirtualType` enum members; new synth classes in
    `samplomatic/synths/`).
  - Adding, removing, or renaming fields in a node's serialized dict.
  - Changing the type or semantics of an existing serialized field.
  - Adding new `Serializable` classes (nodes, distributions, virtual registers) — these need a
    corresponding `TypeSerializer` in `samplomatic/serialization/`.

When in doubt, ask whether the change could produce JSON that an older samplomatic would fail to
deserialize. The metaclass in `serialization/type_serializer.py` enforces contiguous, disjoint SSV
ranges at import time — a broken versioning setup usually fails fast there, but silent data-loss
(new values squeezed into an old format) will not, so trace it by hand.

Report ranked findings to chat. With `--fix`, apply only unambiguous bug fixes and add the missing
tests; leave design/architecture alone.

### Tier 4 — `polish` (conventions & docs)
Conventions, nits, docs, and micro-cleanups, **assuming everything above is settled**.

Do **not** spend findings on anything `ruff` + pre-commit already enforce — they fail CI on their
own: Apache license headers, formatting and the 100-char line length, import order (isort),
`Optional`/`Union` → PEP 604 (UP), private-member access (SLF), pydocstyle (D), unused imports
(F401), and trailing-whitespace/EOF. The checklist below is deliberately the *residue* those tools
cannot catch:

- **Copyright year:** a modified file must carry the current calendar year (e.g.
  `(C) Copyright IBM 2025, 2026.`). pre-commit checks the header exists, not that the year was
  bumped.
- **`from __future__ import annotations`:** CLAUDE.md forbids it — flag if introduced; use
  string-literal forward references instead.
- **Docstrings:** `__init__` args documented in the **class** docstring; classes/functions
  referenced as Sphinx cross-refs (`:class:`~.X``), not bare backticks in rendered docstrings.
- **Docs examples are testable:** use `.. plot::` / `.. plotly::` directives, never
  `.. code-block:: python`. Doctests inside `.. plot::` run during `pytest`.
- **Docs wiring:** adding/removing a module must update both its hand-written RST in `docs/api/`
  and the toctree in `docs/api/index.rst`.
- **Changelog fragment:** the PR should include a Towncrier fragment in `changelog.d/`
  (`<PR#>.<type>.md`). If it is missing, flag it and point to the sibling `changelog` skill.
- **Errors:** `ValueError` with an f-string naming the offending value/stage; `TypeError` for
  wrong-type guards; `NotImplementedError` for unsupported physics.
- **Optional deps** (visualization backends, etc.) gated through `optionals.py`, with heavy imports
  behind `TYPE_CHECKING` or local to the method.
- **Test-writing conventions** (`test/unit/`, mirrors the package tree) — *how* the tests are
  written, not *whether* the change is covered (that is Tier 3): public-API imports where possible;
  the `conftest.py` fixture hierarchy; the `rng` fixture for seeded randomness; the `run_snippet`
  fixture for subprocess snippets; `@pytest.mark.parametrize`; `np.isclose`/`allclose` with an
  explicit `atol`.

Present ranked findings; with `--fix`, apply the safe mechanical ones.

## Closing every run

End with a **next-tier recommendation**: name the next tier and the exact command (e.g. "Design
looks settled — when ready, run `/tiered-review architecture`"). If the current tier surfaced
blocking concerns, recommend resolving them and re-running the *current* tier rather than advancing.

## Reference: subpackage roles

| Subpackage | Role |
|---|---|
| `annotations/` | Box instruction types users attach to circuits (`Twirl`, `ChangeBasis`, `InjectNoise`, `Tag`). |
| `builders/` | `build()` / `pre_build()` orchestration; recursive box processing into a PreSamplex + template. |
| `pre_samplex/` | Intermediate graph (`PreEmit`, `PrePropagate`, `PreCollect`, …) built during `pre_build()`, then optimized and lowered in `finalize()`. |
| `samplex/` | The final DAG (`Samplex`) with `sample()`; typed nodes live in `samplex/nodes/` (sampling / evaluation / collection). |
| `distributions/` | Probability distributions over virtual groups (`UniformPauli`, `BalancedUniformPauli`, `HaarU2`, `UniformC1`). |
| `virtual_registers/` | Algebraic group types (`PauliRegister`, `U2Register`, `C1Register`, `Z2Register`) with composition/commutation rules. |
| `synths/` | Gate synthesis for virtual-group elements. |
| `transpiler/` | Qiskit transpiler passes, notably `generate_boxing_pass_manager()`. |
| `serialization/` | Versioned JSON serialization (SSV): `TypeSerializer` / `DataSerializer` per type. |
| `tensor_interface.py` | Abstraction over array operations used in sampling. |
| `utils/` | Helpers for editing circuit box annotations (`map_annotations`, `filter_annotations`, `unbox`, `BoxKey`, …). |
| `visualization/` | Graphviz/Plotly-based samplex visualization helpers. |
