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

"""Conversion between :class:`~qiskit.dagcircuit.DAGCircuit` and the stratification IR.

The forward direction :func:`.dag_to_instance` extracts a
:class:`.StratificationInstance` from a :class:`~qiskit.dagcircuit.DAGCircuit`,
along with a :class:`.ConversionContext` that holds the metadata required to
materialise a circuit again. The backward direction :func:`.stratification_to_dag`
takes a :class:`.Stratification` together with such a context and produces a
:class:`~qiskit.dagcircuit.DAGCircuit` whose layers are wrapped in
:class:`~qiskit.circuit.BoxOp` instructions.
"""

from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass, field
from typing import Literal

from qiskit.circuit import (
    BoxOp,
    ClassicalRegister,
    Clbit,
    CommutationChecker,
    ControlFlowOp,
    Instruction,
    QuantumCircuit,
    QuantumRegister,
    Qubit,
)
from qiskit.dagcircuit import DAGCircuit

from ..constants import SYMMETRIC_2Q_GATES
from .hypergraph import Hypergraph
from .instance import StratificationInstance
from .stratification import Stratification

__all__ = [
    "ConversionContext",
    "EdgeKind",
    "dag_to_instance",
    "stratification_to_dag",
]

EdgeKind = Literal["gate_2q", "measure", "reset"]
"""Op categories that :func:`.dag_to_instance` can promote to hypergraph edges."""

_DEFAULT_EDGE_FILTER: frozenset[EdgeKind] = frozenset({"gate_2q"})
"""Default: only 2-qubit unitary gates become edges (current behaviour)."""

_DEFAULT_SUPPORTED_1Q: frozenset[str] = frozenset(
    {
        "id",
        "x",
        "y",
        "z",
        "h",
        "s",
        "sdg",
        "t",
        "tdg",
        "sx",
        "sxdg",
        "rx",
        "ry",
        "rz",
        "p",
        "u",
        "u1",
        "u2",
        "u3",
    }
)
"""Default unitary single-qubit gate names accepted by :func:`.dag_to_instance`."""

_DEFAULT_SUPPORTED_2Q: frozenset[str] = frozenset(
    {
        "cx",
        "cy",
        "cz",
        "ch",
        "swap",
        "iswap",
        "ecr",
        "dcx",
        "rxx",
        "ryy",
        "rzz",
        "rzx",
        "cs",
        "csdg",
        "cp",
        "crx",
        "cry",
        "crz",
        "xx_minus_yy",
        "xx_plus_yy",
    }
)
"""Default unitary two-qubit gate names accepted by :func:`.dag_to_instance`."""


@dataclass(frozen=True)
class _EdgeOp:
    """Recorded form of a gate (or measure/reset) that became a hypergraph edge."""

    op: Instruction
    qargs: tuple[int, ...]
    cargs: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class _BareOp:
    """A bare op kept outside layer boxes: 1-qubit gate, ``measure``, ``reset``, or ``barrier``.

    ``qargs`` may have any arity for ``barrier``; for the other kinds it has length 1.
    ``anchors`` is parallel to ``qargs``: for each qubit the bare op acts on, it
    stores the id of the most recent edge to have touched that qubit (or ``None``
    if the op precedes every edge on that qubit).
    """

    op: Instruction
    qargs: tuple[int, ...]
    cargs: tuple[int, ...]
    anchors: tuple["int | None", ...]


@dataclass(frozen=True)
class _BoxRecord:
    """A pre-existing :class:`~qiskit.circuit.BoxOp` found in the input DAG.

    Treated as an absolute commutation barrier.  Its pattern (the frozenset of
    labels of the ops inside it) is stored so that it can be included in the
    :attr:`.StratificationInstance.external_patterns`.

    ``anchors`` is parallel to ``qargs``: the id of the most recent *new* edge
    to have touched each qubit prior to this box (or ``None``).
    """

    op: BoxOp
    qargs: tuple[int, ...]
    cargs: tuple[int, ...]
    pattern: "frozenset[Hashable]"
    anchors: tuple["int | None", ...]


@dataclass(frozen=True)
class ConversionContext:
    """Round-trip metadata produced by :func:`.dag_to_instance`.

    Holds the bits, the original operations per edge (so they can be
    replayed inside layer boxes), and the bare ops with their anchor edges.

    Attributes:
        qubits: All qubits of the source DAG, in order.
        clbits: All classical bits of the source DAG, in order.
        qregs: Quantum registers of the source DAG, in declaration order.
        cregs: Classical registers of the source DAG, in declaration order.
        edge_ops: One :class:`_EdgeOp` per hypergraph edge, parallel to
            ``instance.hypergraph.edges``.
        bare_ops: One :class:`_BareOp` per bare op (1q gate, ``measure``, ``reset``,
            or ``barrier``), in original DAG order.
        boxes: Pre-existing :class:`~qiskit.circuit.BoxOp` instructions from the
            source DAG, in original order.  They are reproduced verbatim by
            :func:`.stratification_to_dag` at their anchored slot.
    """

    qubits: tuple[Qubit, ...]
    clbits: tuple[Clbit, ...]
    qregs: tuple[QuantumRegister, ...]
    cregs: tuple[ClassicalRegister, ...]
    edge_ops: tuple[_EdgeOp, ...]
    bare_ops: tuple[_BareOp, ...]
    boxes: tuple[_BoxRecord, ...] = field(default_factory=tuple)


def _default_label(op: Instruction, qargs: tuple[int, ...]) -> Hashable:
    """Build the default label for a gate or measure/reset.

    For 2-qubit symmetric gates the qubit role is a frozenset; for asymmetric
    gates it is the tuple in original order.  Parameters are included verbatim.
    For ``measure`` and ``reset`` the qubit indices are **omitted** from the
    label so that all measures share one pattern label and all resets share
    another — this prevents every measure on a different qubit from introducing
    a unique pattern, which would defeat the purpose of pattern-count
    minimisation.

    Args:
        op: The instruction.
        qargs: The vertex indices the gate acts on, in original order.

    Returns:
        A hashable label.
    """
    if op.name in ("measure", "reset"):
        return (op.name, ())
    if op.name in SYMMETRIC_2Q_GATES:
        role: Hashable = frozenset(qargs)
    else:
        role = tuple(qargs)
    return (op.name, tuple(op.params), role)


def _validate_node(
    op: Instruction, num_cargs: int, sup_1q: frozenset[str], sup_2q: frozenset[str]
) -> str:
    """Validate a DAG op and classify it.

    Returns:
        ``"box"`` for a :class:`~qiskit.circuit.BoxOp`, ``"edge"`` for a 2q
        unitary gate, ``"bare"`` for a 1q unitary, ``"measure"``, ``"reset"``,
        or ``"barrier"`` for a barrier of any arity.

    Raises:
        ValueError: If the op is not supported.
    """
    # BoxOp is a ControlFlowOp subclass — handle it before the generic check.
    if isinstance(op, BoxOp):
        if getattr(op, "condition", None) is not None:
            raise ValueError("BoxOp with a classical condition is not supported.")
        return "box"

    name = op.name
    if isinstance(op, ControlFlowOp):
        raise ValueError(f"Control-flow op '{name}' is not supported.")
    if getattr(op, "condition", None) is not None:
        raise ValueError(f"Op '{name}' has a classical condition; control-flow is not supported.")
    if name == "barrier":
        if num_cargs != 0:
            raise ValueError(f"'barrier' op has {num_cargs} cargs; expected 0.")
        return "barrier"
    if op.num_qubits > 2:
        raise ValueError(
            f"Op '{name}' acts on {op.num_qubits} qubits; only 1- and 2-qubit ops are supported."
        )

    if name == "measure":
        if num_cargs != 1:
            raise ValueError(f"'measure' op has {num_cargs} cargs; expected exactly 1.")
        return "measure"
    if name == "reset":
        if num_cargs != 0:
            raise ValueError(f"'reset' op has {num_cargs} cargs; expected 0.")
        return "reset"

    if num_cargs > 0:
        raise ValueError(f"Op '{name}' has classical bits; only 'measure' may use cargs.")

    if op.num_qubits == 2:
        if name not in sup_2q:
            raise ValueError(f"2-qubit op '{name}' is not in the supported set.")
        return "edge"
    if op.num_qubits == 1:
        if name not in sup_1q:
            raise ValueError(f"1-qubit op '{name}' is not in the supported set.")
        return "bare"

    raise ValueError(f"Op '{name}' acts on {op.num_qubits} qubits; expected 1 or 2.")


def _compute_box_pattern(
    box: BoxOp,
    box_outer_qargs: tuple[int, ...],
    label_fn: Callable[[Instruction, tuple[int, ...]], Hashable],
    sup_1q: frozenset[str],
) -> "frozenset[Hashable]":
    """Compute the pattern of ops inside a :class:`~qiskit.circuit.BoxOp`.

    Includes labels for all 2-qubit gates and for ``measure``/``reset`` ops.
    Pure 1-qubit unitary gates and barriers are excluded because they do not
    form hypergraph edges in any pass.

    Args:
        box: The box instruction.
        box_outer_qargs: Outer-circuit qubit indices parallel to the box's body
            qubits (body qubit 0 → ``box_outer_qargs[0]``, etc.).
        label_fn: Label function (same as used for the current conversion pass).
        sup_1q: The set of supported 1q unitary op names (used to identify which
            1q ops to skip).

    Returns:
        A frozenset of labels representing the box's pattern.
    """
    labels: set[Hashable] = set()
    body = box.body
    for instr in body.data:
        iop = instr.operation
        if iop.name == "barrier" or isinstance(iop, ControlFlowOp):
            continue
        if iop.num_qubits == 1 and iop.name in sup_1q:
            continue  # pure 1q unitaries don't contribute to pattern
        local_q = tuple(body.find_bit(q).index for q in instr.qubits)
        outer_q = tuple(box_outer_qargs[i] for i in local_q)
        labels.add(label_fn(iop, outer_q))
    return frozenset(labels)


def dag_to_instance(
    dag: DAGCircuit,
    *,
    edge_filter: "Iterable[EdgeKind] | None" = None,
    label_fn: Callable[[Instruction, tuple[int, ...]], Hashable] | None = None,
    supported_1q: Iterable[str] | None = None,
    supported_2q: Iterable[str] | None = None,
) -> tuple[StratificationInstance, ConversionContext]:
    """Convert a :class:`~qiskit.dagcircuit.DAGCircuit` into a stratification instance.

    Which op categories become hypergraph edges is controlled by *edge_filter*:

    - ``"gate_2q"`` — supported 2-qubit unitary gates become edges (the default
      and current behaviour when *edge_filter* is omitted).
    - ``"measure"`` — ``measure`` instructions become 1-qubit edges.
    - ``"reset"`` — ``reset`` instructions become 1-qubit edges.

    Any op category not listed in *edge_filter* is recorded as a bare op.

    Pre-existing :class:`~qiskit.circuit.BoxOp` instructions in the input DAG
    are treated as absolute commutation barriers (like ``barrier``): no op may be
    reordered across a box on any of the box's qubits.  Each box's pattern (the
    frozenset of labels of its constituent ops) is extracted and stored in
    :attr:`.StratificationInstance.external_patterns` so that algorithms
    minimising unique-pattern count will naturally prefer reusing those patterns.

    Args:
        dag: The input DAG. Must contain only the supported ops; control flow
            (except :class:`~qiskit.circuit.BoxOp`), unitary ops on >2 qubits,
            ``delay``, and unknown gates are rejected with :class:`ValueError`.
            ``barrier`` of any width is accepted.
        edge_filter: Iterable of :data:`EdgeKind` values specifying which op
            categories become hypergraph edges.  Defaults to ``{"gate_2q"}``
            (current behaviour).
        label_fn: Override for the default label function. Receives the op and a
            tuple of the gate's qubit indices and returns any hashable. Defaults
            to :func:`_default_label`.
        supported_1q: Override for the set of allowed 1q unitary gate names.
        supported_2q: Override for the set of allowed 2q unitary gate names.

    Returns:
        ``(instance, context)``: the :class:`.StratificationInstance` and the
        round-trip metadata required by :func:`.stratification_to_dag`.

    Raises:
        ValueError: If the DAG contains an unsupported op.
    """
    label_fn = label_fn if label_fn is not None else _default_label
    sup_1q = frozenset(supported_1q) if supported_1q is not None else _DEFAULT_SUPPORTED_1Q
    sup_2q = frozenset(supported_2q) if supported_2q is not None else _DEFAULT_SUPPORTED_2Q
    active_filter: frozenset[EdgeKind] = (
        frozenset(edge_filter) if edge_filter is not None else _DEFAULT_EDGE_FILTER
    )

    qubit_index: dict[Qubit, int] = {q: i for i, q in enumerate(dag.qubits)}
    clbit_index: dict[Clbit, int] = {c: i for i, c in enumerate(dag.clbits)}

    nodes = list(dag.topological_op_nodes())
    n_nodes = len(nodes)

    # Per-node classification — parallel to nodes.
    kinds: list[str] = [""] * n_nodes
    edge_id_of_node: list[int] = [-1] * n_nodes  # -1 if not an edge

    edges_list: list[frozenset[int]] = []
    edge_ops_list: list[_EdgeOp] = []
    labels: list[Hashable] = []
    bare_ops_list: list[_BareOp] = []
    box_records_list: list[_BoxRecord] = []

    last_edge_on_qubit: list[int | None] = [None] * len(dag.qubits)

    # Per-qubit op history (most recent last) for commutation analysis. Stores node indices.
    prev_per_qubit: list[list[int]] = [[] for _ in range(len(dag.qubits))]

    checker = CommutationChecker()

    # Commutation DAG: parents[v] is the set of node indices whose ops do not commute with v.
    parents: list[set[int]] = [set() for _ in range(n_nodes)]

    for idx, node in enumerate(nodes):
        op = node.op
        kind = _validate_node(op, len(node.cargs), sup_1q, sup_2q)
        kinds[idx] = kind

        q_idx = tuple(qubit_index[q] for q in node.qargs)
        c_idx = tuple(clbit_index[c] for c in node.cargs)

        # Compute commutation blockers: walk back per-qubit, recording every
        # prior op that does not commute with the current op (or that shares
        # cargs).  Only absolute barriers (`barrier` / `BoxOp`) terminate the
        # walk on a given qubit, since they truly shadow all earlier ops on
        # that qubit.  Stopping at non-barrier blockers would be incorrect
        # when commutation is non-monotonic along the per-qubit history (an
        # earlier op may not commute with the current op even though it
        # commutes with the intermediate blocker, in which case transitivity
        # would not recover the missing arc).
        blockers: set[int] = set()
        is_absolute_blocker = op.name == "barrier" or kind == "box"
        for q in q_idx:
            for prev_idx in reversed(prev_per_qubit[q]):
                prev_node = nodes[prev_idx]
                prev_kind = kinds[prev_idx]
                # Barriers and boxes truly shadow all earlier ops on this
                # qubit, so the walk on q can stop here.  This check must
                # fire before the in-blockers short-circuit below, because
                # an absolute barrier added via another qubit's walk is
                # still terminal on this qubit.
                if is_absolute_blocker or prev_node.op.name == "barrier" or prev_kind == "box":
                    blockers.add(prev_idx)
                    break
                # Non-barrier blocker already recorded from another qubit:
                # keep walking past it on this qubit, because earlier ops
                # may not commute with the current node even if they commute
                # with this intermediate blocker.
                if prev_idx in blockers:
                    continue
                # Conservative: shared cargs => non-commuting.
                if set(prev_node.cargs) & set(node.cargs):
                    blockers.add(prev_idx)
                    continue
                if not checker.commute(
                    prev_node.op,
                    prev_node.qargs,
                    prev_node.cargs,
                    op,
                    node.qargs,
                    node.cargs,
                ):
                    blockers.add(prev_idx)
                    continue
        parents[idx] = blockers

        for q in q_idx:
            prev_per_qubit[q].append(idx)

        # Record per-kind data.
        if kind == "box":
            # Compute pattern from box body, then store as a _BoxRecord.
            pattern = _compute_box_pattern(op, q_idx, label_fn, sup_1q)
            anchors = tuple(last_edge_on_qubit[q] for q in q_idx)
            box_records_list.append(
                _BoxRecord(op=op, qargs=q_idx, cargs=c_idx, pattern=pattern, anchors=anchors)
            )
            # Boxes don't update last_edge_on_qubit (they aren't edges themselves).
        elif _is_edge_for_filter(kind, active_filter):
            edge_id = len(edges_list)
            edges_list.append(frozenset(q_idx))
            edge_ops_list.append(_EdgeOp(op=op, qargs=q_idx, cargs=c_idx))
            labels.append(label_fn(op, q_idx))
            edge_id_of_node[idx] = edge_id
            for q in q_idx:
                last_edge_on_qubit[q] = edge_id
        else:
            # "bare", "measure" (filtered out), "reset" (filtered out), or "barrier".
            anchors = tuple(last_edge_on_qubit[q] for q in q_idx)
            bare_ops_list.append(_BareOp(op=op, qargs=q_idx, cargs=c_idx, anchors=anchors))

    # Project the commutation DAG onto edges. For each edge node, BFS backwards
    # through bare-op ancestors (including barriers and boxes) to find ancestor
    # edge nodes.  Barriers and boxes already impose precedence via the blocker
    # logic; here we simply follow parent links transitively.
    precedence_arcs: list[tuple[int, int]] = []
    for desc_idx in range(n_nodes):
        if edge_id_of_node[desc_idx] == -1:
            continue
        desc_edge_id = edge_id_of_node[desc_idx]
        visited: set[int] = set()
        stack: list[int] = list(parents[desc_idx])
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            if edge_id_of_node[cur] != -1:
                precedence_arcs.append((edge_id_of_node[cur], desc_edge_id))
                # Don't recurse past edge ancestors: when those edges are processed
                # as descendants, their own arcs are added; the resulting set is the
                # transitive closure (which StratificationInstance reduces).
                continue
            stack.extend(parents[cur])

    external_patterns: list[frozenset[Hashable]] = [r.pattern for r in box_records_list]

    hypergraph = Hypergraph(num_vertices=len(dag.qubits), edges=edges_list)
    instance = StratificationInstance(
        hypergraph, precedence_arcs, labels, external_patterns=external_patterns
    )

    context = ConversionContext(
        qubits=tuple(dag.qubits),
        clbits=tuple(dag.clbits),
        qregs=tuple(dag.qregs.values()),
        cregs=tuple(dag.cregs.values()),
        edge_ops=tuple(edge_ops_list),
        bare_ops=tuple(bare_ops_list),
        boxes=tuple(box_records_list),
    )
    return instance, context


def _is_edge_for_filter(kind: str, active_filter: frozenset[EdgeKind]) -> bool:
    """Return True if *kind* should be treated as a hypergraph edge given *active_filter*."""
    if kind == "edge":
        return "gate_2q" in active_filter
    if kind == "measure":
        return "measure" in active_filter
    if kind == "reset":
        return "reset" in active_filter
    return False


def stratification_to_dag(
    stratification: Stratification,
    context: ConversionContext,
) -> DAGCircuit:
    """Materialise a :class:`.Stratification` as a :class:`~qiskit.dagcircuit.DAGCircuit`.

    Each layer is wrapped in a single :class:`~qiskit.circuit.BoxOp` whose body
    contains all ops in that layer (in ascending edge-id order for determinism).
    Layers may contain edges of any arity — 2-qubit gates, ``measure``, and
    ``reset`` are all supported.

    Bare ops (1-qubit gates, barriers, and any ``measure``/``reset`` that were not
    promoted to edges by :func:`.dag_to_instance`) are emitted between layer boxes
    at the position determined by their anchor edges.  Pre-existing
    :class:`~qiskit.circuit.BoxOp` instructions from the source circuit
    (recorded in ``context.boxes``) are reproduced verbatim at their anchored slot.

    Args:
        stratification: The stratification to materialise.
        context: Round-trip metadata produced by :func:`.dag_to_instance`.

    Returns:
        A :class:`~qiskit.dagcircuit.DAGCircuit` with the same qubits, clbits,
        and registers as the source DAG.

    Raises:
        ValueError: If the stratification's edge count does not match the
            context's.
    """
    if stratification.instance.num_edges != len(context.edge_ops):
        raise ValueError(
            f"Stratification has {stratification.instance.num_edges} edges but the "
            f"context records {len(context.edge_ops)}."
        )

    out = DAGCircuit()
    for qreg in context.qregs:
        out.add_qreg(qreg)
    for creg in context.cregs:
        out.add_creg(creg)

    # Loose bits not part of any register are added directly.
    qubits_in_regs: set[Qubit] = set()
    for qreg in context.qregs:
        qubits_in_regs.update(qreg)
    loose_qubits = [q for q in context.qubits if q not in qubits_in_regs]
    if loose_qubits:
        out.add_qubits(loose_qubits)

    clbits_in_regs: set[Clbit] = set()
    for creg in context.cregs:
        clbits_in_regs.update(creg)
    loose_clbits = [c for c in context.clbits if c not in clbits_in_regs]
    if loose_clbits:
        out.add_clbits(loose_clbits)

    # Map each edge id to the layer index that contains it.
    layer_of_edge: dict[int, int] = {}
    for k, layer in enumerate(stratification.layers):
        for e in layer:
            layer_of_edge[e] = k

    def _slot_of(anchors: tuple["int | None", ...]) -> int:
        """Return the layer-slot for a bare op or box record given its anchors."""
        anchored_layers = [layer_of_edge[a] for a in anchors if a is not None]
        return max(anchored_layers) if anchored_layers else -1

    # Bucket bare ops and box records by their slot.
    bare_by_slot: dict[int, list[_BareOp]] = {}
    for bare in context.bare_ops:
        slot = _slot_of(bare.anchors)
        bare_by_slot.setdefault(slot, []).append(bare)

    box_by_slot: dict[int, list[_BoxRecord]] = {}
    for rec in context.boxes:
        slot = _slot_of(rec.anchors)
        box_by_slot.setdefault(slot, []).append(rec)

    def _emit_bare(bare: _BareOp) -> None:
        qubits = [context.qubits[q] for q in bare.qargs]
        clbits = [context.clbits[c] for c in bare.cargs]
        out.apply_operation_back(bare.op, qubits, clbits)

    def _emit_box_record(rec: _BoxRecord) -> None:
        out.apply_operation_back(
            rec.op,
            [context.qubits[q] for q in rec.qargs],
            [context.clbits[c] for c in rec.cargs],
        )

    def _emit_layer_box(k: int) -> None:
        """Wrap all ops in layer *k* in a BoxOp and emit it."""
        layer = stratification.layers[k]
        # Collect all qubits and clbits spanned by this layer.
        all_q: list[int] = sorted({q for e in layer for q in context.edge_ops[e].qargs})
        all_c: list[int] = sorted({c for e in layer for c in context.edge_ops[e].cargs})
        q_to_local = {q: i for i, q in enumerate(all_q)}
        c_to_local = {c: i for i, c in enumerate(all_c)}
        body = QuantumCircuit(len(all_q), len(all_c))
        for edge_id in sorted(layer.edges):
            eop = context.edge_ops[edge_id]
            body.append(
                eop.op,
                [q_to_local[q] for q in eop.qargs],
                [c_to_local[c] for c in eop.cargs],
            )
        box = BoxOp(body=body, annotations=[])
        out.apply_operation_back(
            box,
            [context.qubits[q] for q in all_q],
            [context.clbits[c] for c in all_c],
        )

    def _emit_slot(slot: int) -> None:
        """Emit all bare ops and pre-existing boxes anchored to *slot*."""
        for bare in bare_by_slot.get(slot, []):
            _emit_bare(bare)
        for rec in box_by_slot.get(slot, []):
            _emit_box_record(rec)

    # Pre-layer slot (-1): bare ops and pre-existing boxes before the first layer.
    _emit_slot(-1)

    for k in range(stratification.depth):
        _emit_layer_box(k)
        _emit_slot(k)

    return out
