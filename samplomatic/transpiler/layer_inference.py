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

"""Pattern-free 2Q layer inference for transpiled circuits.

When a layered circuit (e.g. a Trotter circuit ``(ABCCBA)^n``) is transpiled
with some of its layer barriers removed, the transpiler is free to reorder
commuting 2Q gates and fuse same-pair occurrences across layer boundaries.
The greedy box-grouping algorithm in :class:`~.GroupGatesIntoBoxes` then has
no way to recover the intended layer structure.

This module provides :func:`infer_layers` and :func:`insert_layer_barriers`,
which detect 2Q layer boundaries by walking the circuit DAG in topological
order and placing each 2Q gate into the **earliest layer** whose qubits are
free *and* whose accumulated set of tenable layer types still contains the
gate's pair. After detection, the circuit is re-emitted with full-width
barriers at layer boundaries. The barriers guide
:class:`~.GroupGatesIntoBoxes` and are removed before
:class:`~.AbsorbSingleQubitGates` when used with the default
``remove_barriers="after_stratification"`` setting of
:func:`~.generate_boxing_pass_manager`.

Unlike the earlier prototype, the algorithm requires neither the layer
*sequence* nor a per-pair gate-block size. It tolerates same-pair fusion at
step boundaries (the fused block is just one block on a fresh layer of that
type), and reorderings the transpiler effects via disjoint-qubit
commutation (a gate that doesn't fit any open layer simply opens a new
one). Reorderings exploiting gate-level commutation between gates that
share a qubit are not undone by this algorithm, so supply explicit
``layer_templates`` whenever the circuit may exhibit such reorderings.
"""

import heapq
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from qiskit.circuit import Barrier, QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit

from ..aliases import DAGOpNode


class LayerInferenceError(ValueError):
    """Raised when the layer-inference algorithm cannot make progress."""


@dataclass(frozen=True)
class _InferredLayer:
    """A detected 2Q layer."""

    nodes: tuple[DAGOpNode, ...]
    """The 2Q :class:`DAGOpNode` instances assigned to this layer."""

    pairs: frozenset[frozenset[int]]
    """The qubit-index pairs covered by this layer, as length-2 frozensets."""

    tenable: frozenset[int]
    """Indices into the ``layer_templates`` argument.

    These specify the template types still consistent with this layer. In a "well-formed" circuit
    this is a singleton; a length greater than 1 means the layer is locally type-ambiguous.
    """


def infer_layers(
    circuit: QuantumCircuit,
    layer_templates: Sequence[Iterable[tuple[int, int]]] | None = None,
) -> list[_InferredLayer]:
    """Detect 2Q layer structure of a (transpiled) circuit.

    Args:
        circuit: The circuit to analyse. Qubit indices in ``layer_templates``
            refer to positions in ``circuit.qubits``. For an ISA circuit,
            translate logical pairs through
            ``isa.layout.final_index_layout(filter_ancillas=True)`` first.
        layer_templates: Optional list of layer types, each a collection of
            qubit-index pairs ``(q0, q1)``. Pair direction is irrelevant
            (``(0, 1)`` and ``(1, 0)`` are the same). If ``None``, templates
            are inferred from any barrier-separated regions in the circuit
            (best-effort).

    Returns:
        A list of :class:`InferredLayer` instances in execution order.

    Raises:
        LayerInferenceError: If a 2Q gate's pair is not in any layer
            template (e.g. a SWAP introduced by routing).
    """
    if layer_templates is None:
        layer_templates = _infer_templates_from_barriers(circuit)

    templates = [frozenset(frozenset(pair) for pair in t) for t in layer_templates]
    qubit_index = {q: i for i, q in enumerate(circuit.qubits)}
    dag = circuit_to_dag(circuit)
    layers, _ = _assign_layers(dag, templates, qubit_index)
    return layers


def insert_layer_barriers(
    circuit: QuantumCircuit,
    layer_templates: Sequence[Iterable[tuple[int, int]]] | None = None,
) -> QuantumCircuit:
    """Insert full-width barriers at inferred 2Q layer boundaries.

    The result is suitable for feeding into
    :func:`~.generate_boxing_pass_manager` with the default
    ``remove_barriers="after_stratification"``.

    Args:
        circuit: The circuit to barrier-stratify.
        layer_templates: As in :func:`infer_layers`. ``None`` enables
            barrier-region inference.

    Returns:
        A new :class:`QuantumCircuit` with original barriers dropped and a
        full-width :class:`~qiskit.circuit.Barrier` inserted at every
        detected layer boundary.

    Raises:
        LayerInferenceError: If layer detection cannot make progress.
    """
    if layer_templates is None:
        layer_templates = _infer_templates_from_barriers(circuit)

    templates = [frozenset(frozenset(pair) for pair in t) for t in layer_templates]
    qubit_index = {q: i for i, q in enumerate(circuit.qubits)}
    dag = circuit_to_dag(circuit)
    layers, node_layer = _assign_layers(dag, templates, qubit_index)
    return _emit_with_layer_barriers(dag, layers, node_layer)


def _qpair_indices(node: DAGOpNode, qubit_index: dict) -> frozenset[int]:
    """Return the unordered pair of qubit indices for a 2Q op node."""
    return frozenset(qubit_index[q] for q in node.qargs)


def _is_2q_gate(node: DAGOpNode) -> bool:
    """Whether a DAG op node is a standard 2Q gate (not barrier/measure/box)."""
    if node.op.name in ("barrier", "measure", "reset", "box"):
        return False
    return getattr(node.op, "num_qubits", 0) == 2


def _assign_layers(
    dag: DAGCircuit,
    templates: list[frozenset[frozenset[int]]],
    qubit_index: dict,
) -> tuple[list[_InferredLayer], dict[DAGOpNode, int]]:
    """Walk ``dag`` and place each 2Q gate in the earliest tenable layer.

    Each "layer" carries:
      * a *tenable* set of template-type indices — narrowed as gates are
        placed so the layer never mixes incompatible types,
      * a *used qubits* set,
      * a list of placed gate nodes.

    Per-qubit "next-available-layer" indices are maintained so that two gates sharing a qubit always
    land in different layers (and the later one lands no earlier than ``next_available + 1``).

    Returns the ordered list of detected layers (containing only non-empty ones) and a map from node
    to its layer index in that list.
    """
    n_types = len(templates)
    if n_types == 0:
        return _assign_layers_no_templates(dag, qubit_index)

    # Compute, for each qubit pair, the set of compatible layer-type indices.
    pair_to_types: dict[frozenset[int], frozenset[int]] = {}
    for t_idx, template in enumerate(templates):
        for pair in template:
            existing = pair_to_types.get(pair, frozenset())
            pair_to_types[pair] = existing | {t_idx}

    # Per-layer state.
    layer_tenable: list[frozenset[int]] = []
    layer_used: list[set[int]] = []
    layer_nodes: list[list[DAGOpNode]] = []
    layer_pairs: list[list[frozenset[int]]] = []

    next_available: dict[int, int] = defaultdict(int)
    node_layer: dict[DAGOpNode, int] = {}

    def _ensure_layer(idx: int) -> None:
        while len(layer_tenable) <= idx:
            layer_tenable.append(frozenset(range(n_types)))
            layer_used.append(set())
            layer_nodes.append([])
            layer_pairs.append([])

    for node in dag.topological_op_nodes():
        if node.op.name == "barrier":
            qidxs = [qubit_index[q] for q in node.qargs]
            fresh = max((next_available[q] for q in qidxs), default=0)
            fresh = max(fresh, len(layer_tenable))
            for q in qidxs:
                next_available[q] = fresh
            continue
        if not _is_2q_gate(node):
            continue

        pair = _qpair_indices(node, qubit_index)
        compatible = pair_to_types.get(pair)
        if compatible is None:
            sorted_pair = tuple(sorted(pair))
            raise LayerInferenceError(
                f"2Q gate '{node.op.name}' on qubits {sorted_pair} does not match any "
                f"layer template. (If this is a SWAP from routing, that case is out of "
                f"scope; otherwise add the pair to layer_templates.)"
            )

        qidxs = [qubit_index[q] for q in node.qargs]
        target = max((next_available[q] for q in qidxs), default=0)
        while True:
            _ensure_layer(target)
            new_tenable = layer_tenable[target] & compatible
            qubit_free = not (set(qidxs) & layer_used[target])
            if qubit_free and new_tenable:
                layer_tenable[target] = new_tenable
                layer_used[target].update(qidxs)
                layer_nodes[target].append(node)
                layer_pairs[target].append(pair)
                node_layer[node] = target
                for q in qidxs:
                    next_available[q] = target + 1
                break
            target += 1

    layers: list[_InferredLayer] = []
    layer_remap: dict[int, int] = {}
    for old_idx, nodes in enumerate(layer_nodes):
        if not nodes:
            continue
        layer_remap[old_idx] = len(layers)
        layers.append(
            _InferredLayer(
                tuple(nodes),
                frozenset(layer_pairs[old_idx]),
                layer_tenable[old_idx],
            )
        )

    node_layer = {n: layer_remap[i] for n, i in node_layer.items()}
    return layers, node_layer


def _assign_layers_no_templates(
    dag: DAGCircuit, qubit_index: dict
) -> tuple[list[_InferredLayer], dict[DAGOpNode, int]]:
    """Qubit-conflict-only layer assignment (no template constraint).

    Used as the inference primitive on barrier-separated regions, and as
    the degenerate fallback when no templates are available.
    """
    layer_used: list[set[int]] = []
    layer_nodes: list[list[DAGOpNode]] = []
    layer_pairs: list[list[frozenset[int]]] = []
    next_available: dict[int, int] = defaultdict(int)
    node_layer: dict[DAGOpNode, int] = {}

    def _ensure_layer(idx: int) -> None:
        while len(layer_used) <= idx:
            layer_used.append(set())
            layer_nodes.append([])
            layer_pairs.append([])

    for node in dag.topological_op_nodes():
        if node.op.name == "barrier":
            qidxs = [qubit_index[q] for q in node.qargs]
            fresh = max((next_available[q] for q in qidxs), default=0)
            fresh = max(fresh, len(layer_used))
            for q in qidxs:
                next_available[q] = fresh
            continue
        if not _is_2q_gate(node):
            continue

        pair = _qpair_indices(node, qubit_index)
        qidxs = [qubit_index[q] for q in node.qargs]
        target = max((next_available[q] for q in qidxs), default=0)
        while True:
            _ensure_layer(target)
            if not (set(qidxs) & layer_used[target]):
                layer_used[target].update(qidxs)
                layer_nodes[target].append(node)
                layer_pairs[target].append(pair)
                node_layer[node] = target
                for q in qidxs:
                    next_available[q] = target + 1
                break
            target += 1

    layers: list[_InferredLayer] = []
    layer_remap: dict[int, int] = {}
    for old_idx, nodes in enumerate(layer_nodes):
        if not nodes:
            continue
        layer_remap[old_idx] = len(layers)
        layers.append(_InferredLayer(tuple(nodes), frozenset(layer_pairs[old_idx]), frozenset()))

    node_layer = {n: layer_remap[i] for n, i in node_layer.items()}
    return layers, node_layer


# ---------------------------------------------------------------------------
# Template inference fallback
# ---------------------------------------------------------------------------


def _infer_templates_from_barriers(
    circuit: QuantumCircuit,
) -> list[set[tuple[int, int]]]:
    """Infer layer templates by running qubit-conflict-only detection.

    Each closed layer's pair-set is collected as a candidate template type and deduplicated.
    Best-effort: relies on the transpiler having preserved at least one clean barrier-separated
    region per type.
    """
    qubit_index = {q: i for i, q in enumerate(circuit.qubits)}
    dag = circuit_to_dag(circuit)
    layers, _ = _assign_layers_no_templates(dag, qubit_index)

    seen: list[frozenset[frozenset[int]]] = []
    for layer in layers:
        if layer.pairs not in seen:
            seen.append(layer.pairs)

    return [{tuple(sorted(p)) for p in pair_set} for pair_set in seen]


# ---------------------------------------------------------------------------
# Re-emission with barriers
# ---------------------------------------------------------------------------


def _emit_with_layer_barriers(
    dag: DAGCircuit,
    layers: list[_InferredLayer],
    node_layer: dict[DAGOpNode, int],
) -> QuantumCircuit:
    """Re-linearise the DAG, emitting full-width barriers at boundaries.

    A priority-driven topological sort: each 2Q gate's priority is its detected layer index, 1Q
    gates emit ASAP (priority -1), existing barriers are dropped (priority -2). A full-width barrier
    is inserted whenever the popped 2Q gate's layer is strictly greater than the
    most-recently-emitted layer.
    """
    op_nodes = list(dag.op_nodes())
    in_degree: dict[DAGOpNode, int] = {n: 0 for n in op_nodes}
    op_node_set = set(op_nodes)
    successors: dict[DAGOpNode, list[DAGOpNode]] = {n: [] for n in op_nodes}
    for u in op_nodes:
        for v in dag.successors(u):
            if v in op_node_set:
                successors[u].append(v)
                in_degree[v] += 1

    counter = 0
    heap: list[tuple[int, int, int, DAGOpNode]] = []

    def priority(node: DAGOpNode) -> int:
        if node.op.name == "barrier":
            return -2
        if node in node_layer:
            return node_layer[node]
        return -1

    def push(node: DAGOpNode) -> None:
        nonlocal counter
        heapq.heappush(heap, (priority(node), counter, id(node), node))
        counter += 1

    for n in op_nodes:
        if in_degree[n] == 0:
            push(n)

    new_dag = dag.copy_empty_like()
    num_qubits = len(dag.qubits)
    qubit_list = list(dag.qubits)
    last_layer_emitted: int | None = None

    while heap:
        _, _, _, node = heapq.heappop(heap)
        if node.op.name == "barrier":
            pass  # drop existing barriers
        else:
            if node in node_layer:
                cur = node_layer[node]
                if last_layer_emitted is not None and cur > last_layer_emitted:
                    new_dag.apply_operation_back(Barrier(num_qubits), qubit_list, [])
                last_layer_emitted = cur
            new_dag.apply_operation_back(node.op, node.qargs, node.cargs)
        for s in successors[node]:
            in_degree[s] -= 1
            if in_degree[s] == 0:
                push(s)

    return dag_to_circuit(new_dag)
