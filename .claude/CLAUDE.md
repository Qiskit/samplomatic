# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Samplomatic is a Python library for sampling randomizations of quantum circuits (e.g. Pauli twirling). Users annotate Qiskit circuits with box instructions (`Twirl`, `ChangeBasis`, `InjectNoise`), then call `build()` to get a parameterized template circuit and a **samplex** (DAG) that generates randomization samples.

## Commands

```bash
# Install for development
pip install -e ".[dev,vis]"

# Run tests (excludes test/performance and runs doctest-modules)
pytest

# Run a single test file or test
pytest test/unit/test_samplex/test_samplex.py
pytest test/unit/test_samplex/test_samplex.py::TestClassName::test_method

# Run with reproducible seed
pytest --seed=12345

# Performance benchmarks (excluded from default pytest run)
pytest test/performance

# Lint and format
ruff check .
ruff format .

# Pre-commit hooks
pre-commit run --all-files

# Build docs (output in docs/_build/html/)
cd docs && make html
```

## Architecture

The core pipeline is: **annotated circuit** → `build()` → **(template circuit, samplex)**

- `samplomatic/__init__.py` exports only `build`, `Twirl`, `ChangeBasis`, `InjectNoise`, `Tag`
- `builders/` — `build(circuit, debug=False)` and `pre_build()` orchestrate the transformation; `debug=True` populates nodes with box trace info
- `pre_samplex/` — intermediate graph built during `pre_build()`, then finalized into a samplex
- `samplex/` — the final DAG (`Samplex`) with `sample()` method; contains typed nodes in `samplex/nodes/`
- `annotations/` — box instruction types users attach to circuits
- `distributions/` — probability distributions over virtual groups (`UniformPauli`, `BalancedUniformPauli`, `HaarU2`, `UniformC1`)
- `virtual_registers/` — algebraic group types (`PauliRegister`, `U2Register`, `C1Register`, `Z2Register`) with composition/commutation rules
- `synths/` — gate synthesis for virtual group elements
- `transpiler/` — Qiskit transpiler passes, notably `generate_boxing_pass_manager()`
- `serialization/` — versioned JSON serialization (SSV) for samplex objects
- `tensor_interface/` — abstraction over numpy array operations used in sampling
- `utils/` — utilities for editing circuit box annotations (`map_annotations`, `filter_annotations`, `extend_annotations`, `replace_annotations`, `strip_annotations`, `unbox`, `undress_box`, `get_annotation`, `find_unique_box_instructions`, `BoxKey`)
- `visualization/` — Graphviz/Plotly-based graph visualization helpers for samplex

## Code Style

- **Line length**: 100
- **Ruff rules**: pydocstyle (D), pycodestyle (E), pyflakes (F), isort (I), private-member-access (SLF), pyupgrade (UP)
- All files require Apache 2.0 license headers (enforced by pre-commit)
- When modifying a file, update its copyright year to the current calendar year (e.g. `(C) Copyright IBM 2025, 2026.`)
- Python 3.10+ (use `X | Y` union syntax, etc.)
- **Import removal hazard**: The pre-commit hook runs `ruff --fix`, which auto-removes unused imports (rule F401). When adding new imports, always add the corresponding usage in the same edit to avoid the import being stripped at commit time. If you need to add imports incrementally, use a `# noqa: F401` comment and remove it once the usage is in place.

## Testing

- `test/unit/` and `test/integration/` are run by default; `test/performance/` is excluded via `addopts`
- The `rng` fixture provides a seeded `numpy.random.Generator` deterministic per-test regardless of execution order
- Docstrings with doctest syntax inside `.. plot::` directives are tested during `pytest` (SciPy-style doctests)
- `run_snippet` fixture runs Python code in a subprocess

## Documentation

- Sphinx with `sphinx-automodapi`; auto-generated stubs go in `docs/api/auto/` (gitignored)
- Hand-maintained RST files in `docs/api/` — one per submodule, plus `index.rst` toctree
- When adding/removing a module, update both the RST file and the toctree in `docs/api/index.rst`
- Code examples must be testable — use `.. plot::` or `.. plotly::` directives, never `.. code-block:: python`
- Changelog via Towncrier: `towncrier create -c "Description" <PR#>.<type>.md` in `changelog.d/`
