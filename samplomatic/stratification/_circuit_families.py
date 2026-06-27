# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Circuit families for stress-testing stratification algorithms.

Each builder returns a :class:`~qiskit.circuit.QuantumCircuit` whose gates
lie within the default supported gate sets of :func:`.dag_to_instance`
(single-qubit: ``h, x, y, z, s, sdg, t, tdg, sx, sxdg, rx, ry, rz, p, u,
u1, u2, u3``; two-qubit: ``cx, cy, cz, ch, swap, iswap, ecr, dcx, rxx, ryy,
rzz, rzx, cs, csdg, cp, crx, cry, crz, xx_minus_yy, xx_plus_yy``; and also
``measure`` and ``reset``).

Usage::

    from samplomatic.stratification._circuit_families import ALL_FAMILIES, build

    for family in ALL_FAMILIES:
        qc = build(family)          # uses default_kwargs
        qc = build(family, num_qubits=12)  # overrides one kwarg
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
from numpy.random import default_rng
from qiskit.circuit import Parameter, QuantumCircuit

__all__ = [
    "CircuitFamily",
    "ALL_FAMILIES",
    "build",
]

# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CircuitFamily:
    """A named, parameterised source of circuits for stratification benchmarking.

    Attributes:
        name: Short identifier used as a section header in comparisons.
        description: One-line summary of what this family stresses.
        builder: Callable that returns a :class:`~qiskit.circuit.QuantumCircuit`.
        default_kwargs: Keyword arguments forwarded to :attr:`builder` by :func:`build`.
        expected: Known-good metrics for the default circuit, e.g.
            ``{"min_depth": 3, "min_patterns": 1}``.  Empty when not known.
    """

    name: str
    description: str
    builder: Callable[..., QuantumCircuit]
    default_kwargs: Mapping[str, object]
    expected: Mapping[str, object] = field(default_factory=dict)


def build(family: CircuitFamily, **overrides: object) -> QuantumCircuit:
    """Return the circuit for *family*, with *overrides* merged into its default kwargs."""
    kwargs = dict(family.default_kwargs)
    kwargs.update(overrides)
    return family.builder(**kwargs)


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


def empty(num_qubits: int = 4) -> QuantumCircuit:
    """Empty circuit — zero 2-qubit gates; tests zero-edge round-trip."""
    return QuantumCircuit(num_qubits)


def single_cx(num_qubits: int = 2) -> QuantumCircuit:
    """Single CX gate — one edge, trivially one layer."""
    qc = QuantumCircuit(num_qubits)
    qc.cx(0, 1)
    return qc


def linear_chain(num_qubits: int = 8) -> QuantumCircuit:
    """CX chain ``cx(0,1); cx(1,2); …`` — maximum precedence depth, single CX pattern.

    The target qubit of each gate becomes the control of the next, so no two gates
    commute.  Optimal depth equals ``num_qubits - 1`` with a single unique pattern.
    """
    qc = QuantumCircuit(num_qubits)
    for i in range(num_qubits - 1):
        qc.cx(i, i + 1)
    return qc


def star(num_qubits: int = 8) -> QuantumCircuit:
    """Star circuit: ``cx(0, k)`` for k = 1 … n-1.

    All gates share qubit 0 as control, so they *commute* (no precedence arcs), but
    every pair *conflicts* in the hypergraph.  Optimal depth equals ``num_qubits - 1``
    with ``num_qubits - 1`` distinct labels (asymmetric CX, different qubit arguments).
    Tests the "all-incomparable yet all-conflicting" regime.
    """
    qc = QuantumCircuit(num_qubits)
    for k in range(1, num_qubits):
        qc.cx(0, k)
    return qc


def complete_cz(num_qubits: int = 6) -> QuantumCircuit:
    """All CZ pairs on K_n — every pair commutes, purely an edge-colouring problem.

    Optimal depth is ``num_qubits - 1`` (n even) or ``num_qubits`` (n odd); unique
    pattern count is 1.  **Commuting-network sanity check.**
    """
    qc = QuantumCircuit(num_qubits)
    for i, j in combinations(range(num_qubits), 2):
        qc.cz(i, j)
    return qc


def brickwork_layered(
    num_qubits: int = 10,
    num_rounds: int = 4,
    gate: str = "cx",
) -> QuantumCircuit:
    """Brickwork of disjoint 2-qubit rounds separated by full-width barriers.

    Round 0 acts on even pairs ``(0,1),(2,3),…``; round 1 on odd pairs
    ``(1,2),(3,4),…``; and so on, alternating.  **Already-layered sanity check**:
    any correct algorithm must reproduce the input layering exactly.

    Args:
        num_qubits: Number of qubits (must be >= 2).
        num_rounds: Number of brickwork rounds.
        gate: Two-qubit gate name; one of ``"cx"``, ``"cz"``, or ``"ecr"``.
    """
    qc = QuantumCircuit(num_qubits)
    for r in range(num_rounds):
        start = r % 2
        for i in range(start, num_qubits - 1, 2):
            getattr(qc, gate)(i, i + 1)
        if r < num_rounds - 1:
            qc.barrier()
    return qc


def brickwork_mixed_gates(
    num_qubits: int = 10,
    num_rounds: int = 4,
    seed: int | None = None,
) -> QuantumCircuit:
    """Brickwork where each gate is independently drawn from ``{cx, cz, rzz}``.

    Different rounds produce different gate-type mixes, creating varied layer patterns.
    Tests the depth vs. unique-pattern-count tradeoff.
    """
    rng = default_rng(seed)
    gate_choices = ["cx", "cz", "rzz"]
    qc = QuantumCircuit(num_qubits)
    for r in range(num_rounds):
        start = r % 2
        for i in range(start, num_qubits - 1, 2):
            choice = rng.choice(gate_choices)
            if choice == "rzz":
                angle = float(rng.uniform(0.1, np.pi))
                qc.rzz(angle, i, i + 1)
            else:
                getattr(qc, choice)(i, i + 1)
    return qc


def commuting_cz_random(
    num_qubits: int = 8,
    density: float = 0.5,
    seed: int | None = None,
) -> QuantumCircuit:
    """Random subset of CZ gates on K_n at the given edge density.

    Because all CZs commute, the precedence DAG has no arcs — the instance is a
    pure independent set cover / edge-colouring problem.  The ``density`` parameter
    interpolates between the sparse case and :func:`complete_cz`.
    """
    rng = default_rng(seed)
    qc = QuantumCircuit(num_qubits)
    all_pairs = list(combinations(range(num_qubits), 2))
    for i, j in all_pairs:
        if rng.random() < density:
            qc.cz(i, j)
    return qc


def random_dense(
    num_qubits: int = 8,
    num_2q_gates: int = 30,
    seed: int | None = None,
) -> QuantumCircuit:
    """Random sequence of 2-qubit gates from ``{cx, cz, rzz}`` on random qubit pairs.

    The mix of asymmetric CX (which generates non-trivial precedence) and symmetric
    CZ / RZZ (which often commute) produces irregular partial orders.  General stress
    test for all algorithms.
    """
    rng = default_rng(seed)
    gate_choices = ["cx", "cz", "rzz"]
    qc = QuantumCircuit(num_qubits)
    for _ in range(num_2q_gates):
        i, j = rng.choice(num_qubits, size=2, replace=False)
        choice = rng.choice(gate_choices)
        if choice == "rzz":
            angle = float(rng.uniform(0.1, np.pi))
            qc.rzz(angle, int(i), int(j))
        else:
            getattr(qc, choice)(int(i), int(j))
    return qc


def quantum_volume_like(
    num_qubits: int = 8,
    num_rounds: int = 4,
    seed: int | None = None,
) -> QuantumCircuit:
    """Quantum-volume-style circuit: random perfect matchings of CX + random 1q rotations.

    Each round draws a random permutation of the qubits, groups them into pairs, and
    applies CX to each pair, sandwiched by Ry(θ) rotations with random θ.  This
    mimics the structure of practical randomised benchmarking circuits, with varied
    qubit pairings per round generating non-trivial partial orders.
    """
    rng = default_rng(seed)
    qc = QuantumCircuit(num_qubits)
    n_pairs = num_qubits // 2
    for _ in range(num_rounds):
        # random 1q rotations
        for q in range(num_qubits):
            qc.ry(float(rng.uniform(0, 2 * np.pi)), q)
        # random perfect matching
        perm = rng.permutation(num_qubits)
        for k in range(n_pairs):
            ctrl, tgt = int(perm[2 * k]), int(perm[2 * k + 1])
            qc.cx(ctrl, tgt)
    # final 1q layer
    for q in range(num_qubits):
        qc.ry(float(rng.uniform(0, 2 * np.pi)), q)
    return qc


def trotter_chain(
    num_qubits: int = 8,
    num_steps: int = 3,
    dt: float = 0.25,
) -> QuantumCircuit:
    """Heisenberg-chain Trotterisation: alternating ZZ, XX, YY interactions.

    Each Trotter step applies ``rzz(dt)``, ``rxx(dt)``, and ``ryy(dt)`` on all
    nearest-neighbour pairs, in two sub-rounds (even pairs first, then odd pairs).
    Repeated for ``num_steps``.  This is a practical use-case: the same coupling
    constant throughout gives one pattern per (gate-type, parity) combination.
    """
    qc = QuantumCircuit(num_qubits)
    for _ in range(num_steps):
        for gate in ("rzz", "rxx", "ryy"):
            # even pairs
            for i in range(0, num_qubits - 1, 2):
                getattr(qc, gate)(dt, i, i + 1)
            # odd pairs
            for i in range(1, num_qubits - 1, 2):
                getattr(qc, gate)(dt, i, i + 1)
    return qc


def _heavy_hex_rounds(
    num_qubits: int,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int]]]:
    """Return three edge-coloring rounds for a heavy-hex-like 2-row layout.

    Qubits 0 … n//2-1 form row 0; qubits n//2 … n-1 form row 1.
    Vertical connections join odd-indexed row-0 qubits to their row-1 counterparts.
    """
    n_row = num_qubits // 2
    # even horizontal pairs in both rows
    round_a = [(i, i + 1) for i in range(0, n_row - 1, 2)] + [
        (n_row + i, n_row + i + 1) for i in range(0, n_row - 1, 2)
    ]
    # odd horizontal pairs in both rows
    round_b = [(i, i + 1) for i in range(1, n_row - 1, 2)] + [
        (n_row + i, n_row + i + 1) for i in range(1, n_row - 1, 2)
    ]
    # vertical connections: odd-column row-0 qubits → row-1
    round_c = [(i, n_row + i) for i in range(1, n_row, 2)]
    return round_a, round_b, round_c


def heavy_hex_brickwork(
    num_qubits: int = 12,
    num_rounds: int = 4,
    seed: int | None = None,
) -> QuantumCircuit:
    """CX brickwork on a heavy-hex-like 2-row coupling graph.

    The coupling graph has two horizontal chains connected by vertical links at every
    other column, matching the connectivity of IBM heavy-hex processors.  There are
    three distinct round types (even-horizontal, odd-horizontal, vertical); they are
    cycled for ``num_rounds`` rounds with optional random per-gate resampling.

    Args:
        num_qubits: Total qubits (must be even and >= 4).
        num_rounds: Number of CX rounds to apply.
        seed: Unused (reserved for future random-gate variant). Accepted for API
            consistency with the other random families.
    """
    if num_qubits % 2 != 0 or num_qubits < 4:
        raise ValueError(f"heavy_hex_brickwork requires even num_qubits >= 4, got {num_qubits}")
    qc = QuantumCircuit(num_qubits)
    rounds = _heavy_hex_rounds(num_qubits)
    for r in range(num_rounds):
        for i, j in rounds[r % 3]:
            qc.cx(i, j)
    return qc


def parametric_mixed(
    num_qubits: int = 6,
    num_rounds: int = 4,
) -> QuantumCircuit:
    """Brickwork with one fresh :class:`~qiskit.circuit.Parameter` per RZZ round.

    Even rounds use CX; odd rounds use RZZ with a distinct ``Parameter`` per round
    (→ distinct labels, since different ``Parameter`` objects hash differently).
    Barriers between rounds prevent qiskit's commutation checker from comparing
    parameterised gates across rounds, which it cannot yet handle.  Within a round
    all pairs are disjoint so no commutation check is needed either.

    Exercises label sensitivity: the same ``Parameter`` object shared across all
    gates *within* an odd round produces one shared label for that round, while
    different ``Parameter`` objects in different rounds produce distinct labels.
    """
    # One unique Parameter per round; gates in the same round share it → same label.
    params = [Parameter(f"θ_{r}") for r in range(num_rounds)]
    qc = QuantumCircuit(num_qubits)
    for r in range(num_rounds):
        start = r % 2
        for i in range(start, num_qubits - 1, 2):
            if r % 2 == 0:
                qc.cx(i, i + 1)
            else:
                qc.rzz(params[r], i, i + 1)
        if r < num_rounds - 1:
            qc.barrier()
    return qc


def with_measurements(
    num_qubits: int = 6,
    num_rounds: int = 2,
    seed: int | None = None,
) -> QuantumCircuit:
    """Brickwork with mid-circuit measurements and resets on ancilla qubits.

    The last qubit acts as an ancilla: measured and reset after each round.  Tests
    bare-op anchor placement (measurements and resets sit between box layers) and
    the ``ClassicalRegister`` round-trip path through :func:`.stratification_to_dag`.
    """
    rng = default_rng(seed)
    qc = QuantumCircuit(num_qubits, 1)
    ancilla = num_qubits - 1
    for r in range(num_rounds):
        start = r % 2
        for i in range(start, num_qubits - 2, 2):  # leave ancilla out of 2q gates
            qc.cx(i, i + 1)
        # entangle ancilla to qubit 0
        qc.cx(0, ancilla)
        qc.measure(ancilla, 0)
        qc.reset(ancilla)
        # random single-qubit rotation on data qubits
        for q in range(num_qubits - 1):
            qc.ry(float(rng.uniform(0, 2 * np.pi)), q)
    return qc


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_FAMILIES: tuple[CircuitFamily, ...] = (
    CircuitFamily(
        name="empty",
        description="Zero 2-qubit gates — edge-case round-trip.",
        builder=empty,
        default_kwargs={"num_qubits": 4},
        expected={"min_depth": 0, "min_patterns": 0},
    ),
    CircuitFamily(
        name="single_cx",
        description="One CX gate — trivially one layer.",
        builder=single_cx,
        default_kwargs={"num_qubits": 2},
        expected={"min_depth": 1, "min_patterns": 1},
    ),
    CircuitFamily(
        name="linear_chain",
        description="CX chain with maximum precedence depth; single pattern.",
        builder=linear_chain,
        default_kwargs={"num_qubits": 8},
        expected={"min_depth": 7, "min_patterns": 1},
    ),
    CircuitFamily(
        name="star",
        description="All CX(0,k) — commute but all conflict on qubit 0.",
        builder=star,
        default_kwargs={"num_qubits": 8},
        expected={"min_depth": 7},
    ),
    CircuitFamily(
        name="complete_cz",
        description="All CZ on K_n — commuting network, pure edge-colouring.",
        builder=complete_cz,
        default_kwargs={"num_qubits": 6},
        expected={"min_depth": 5, "min_patterns": 1},
    ),
    CircuitFamily(
        name="brickwork_layered",
        description="Barrier-separated brickwork — algorithm must recover input layering.",
        builder=brickwork_layered,
        default_kwargs={"num_qubits": 10, "num_rounds": 4, "gate": "cx"},
        expected={"min_depth": 4, "min_patterns": 2},
    ),
    CircuitFamily(
        name="brickwork_mixed_gates",
        description="Brickwork with random {cx,cz,rzz} per gate — varied pattern mix.",
        builder=brickwork_mixed_gates,
        default_kwargs={"num_qubits": 10, "num_rounds": 5, "seed": 42},
    ),
    CircuitFamily(
        name="commuting_cz_random",
        description="Random K_n CZ subset at 50% density — all commuting, edge-colouring only.",
        builder=commuting_cz_random,
        default_kwargs={"num_qubits": 8, "density": 0.5, "seed": 42},
        expected={"min_patterns": 1},
    ),
    CircuitFamily(
        name="random_dense",
        description="Random {cx,cz,rzz} gates on random pairs — irregular partial orders.",
        builder=random_dense,
        default_kwargs={"num_qubits": 8, "num_2q_gates": 30, "seed": 42},
    ),
    CircuitFamily(
        name="quantum_volume_like",
        description="QV-style random perfect matchings + 1q rotations — varied pairings per round.",
        builder=quantum_volume_like,
        default_kwargs={"num_qubits": 8, "num_rounds": 4, "seed": 42},
    ),
    CircuitFamily(
        name="trotter_chain",
        description="Heisenberg-chain Trotter steps (ZZ+XX+YY) — practical repeated structure.",
        builder=trotter_chain,
        default_kwargs={"num_qubits": 8, "num_steps": 3, "dt": 0.25},
        expected={"min_patterns": 6},  # 3 gate types × 2 parities
    ),
    CircuitFamily(
        name="heavy_hex_brickwork",
        description="CX brickwork on a 2-row heavy-hex-like coupling — device-realistic topology.",
        builder=heavy_hex_brickwork,
        default_kwargs={"num_qubits": 12, "num_rounds": 6},
        expected={"min_patterns": 3},  # 3 round types
    ),
    CircuitFamily(
        name="parametric_mixed",
        description="Per-round symbolic RZZ Parameters mixed with CX — tests label sensitivity.",
        builder=parametric_mixed,
        default_kwargs={"num_qubits": 6, "num_rounds": 4},
    ),
    CircuitFamily(
        name="with_measurements",
        description="Brickwork + mid-circuit measure/reset on ancilla — tests bare-op anchoring.",
        builder=with_measurements,
        default_kwargs={"num_qubits": 6, "num_rounds": 2, "seed": 42},
    ),
)
