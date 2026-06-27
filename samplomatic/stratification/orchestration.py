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

"""High-level orchestration helpers for multi-pass stratification.

These helpers compose :func:`.dag_to_instance`, a user-supplied algorithm, and
:func:`.stratification_to_dag` to achieve two common patterns:

- :func:`.stratify_separate` — measure/reset operations and 2-qubit gates are
  placed in **separate** layer boxes via two sequential passes.
- :func:`.stratify_mixed` — measure/reset operations and 2-qubit gates may
  share a layer box in a single joint pass.
"""

from collections.abc import Callable, Hashable, Iterable
from typing import Literal

from qiskit.circuit import Instruction
from qiskit.dagcircuit import DAGCircuit

from .conversion import EdgeKind, dag_to_instance, stratification_to_dag
from .instance import StratificationInstance
from .stratification import Stratification

__all__ = [
    "stratify_mixed",
    "stratify_separate",
]


def stratify_separate(
    dag: DAGCircuit,
    algorithm: Callable[[StratificationInstance], Stratification],
    *,
    meas_first: bool = True,
    label_fn: Callable[[Instruction, tuple[int, ...]], Hashable] | None = None,
    supported_1q: Iterable[str] | None = None,
    supported_2q: Iterable[str] | None = None,
) -> DAGCircuit:
    """Stratify a circuit so that measure/reset boxes and gate boxes are kept separate.

    Runs two sequential stratification passes:

    1. First pass stratifies only the ops in the *first category* (measure/reset
       by default when ``meas_first=True``, or 2-qubit gates when
       ``meas_first=False``), wrapping each layer in its own
       :class:`~qiskit.circuit.BoxOp`.
    2. Second pass stratifies the remaining category, treating the boxes from
       pass 1 as absolute commutation barriers.  The patterns of the pass-1
       boxes are included in the pattern budget so the algorithm may reuse them.

    Args:
        dag: The source :class:`~qiskit.dagcircuit.DAGCircuit`.
        algorithm: Stratification algorithm,
            e.g. :func:`.greedy_stratify`.
        meas_first: When ``True`` (default) the first pass stratifies
            ``measure``/``reset`` ops; the second pass handles 2-qubit gates.
            When ``False`` the order is reversed.
        label_fn: Label function passed to both :func:`.dag_to_instance` calls.
        supported_1q: Supported 1-qubit gate names.
        supported_2q: Supported 2-qubit gate names.

    Returns:
        A :class:`~qiskit.dagcircuit.DAGCircuit` with both meas/reset layer
        boxes and gate layer boxes.
    """
    pass1_filter: frozenset[EdgeKind]
    pass2_filter: frozenset[EdgeKind]
    if meas_first:
        pass1_filter = frozenset({"measure", "reset"})
        pass2_filter = frozenset({"gate_2q"})
    else:
        pass1_filter = frozenset({"gate_2q"})
        pass2_filter = frozenset({"measure", "reset"})

    common_kwargs = dict(label_fn=label_fn, supported_1q=supported_1q, supported_2q=supported_2q)

    inst1, ctx1 = dag_to_instance(dag, edge_filter=pass1_filter, **common_kwargs)
    strat1 = algorithm(inst1)
    dag1 = stratification_to_dag(strat1, ctx1)

    inst2, ctx2 = dag_to_instance(dag1, edge_filter=pass2_filter, **common_kwargs)
    strat2 = algorithm(inst2)
    return stratification_to_dag(strat2, ctx2)


def stratify_mixed(
    dag: DAGCircuit,
    algorithm: Callable[[StratificationInstance], Stratification],
    *,
    edge_filter: "Iterable[EdgeKind] | None" = None,
    label_fn: Callable[[Instruction, tuple[int, ...]], Hashable] | None = None,
    supported_1q: Iterable[str] | None = None,
    supported_2q: Iterable[str] | None = None,
) -> DAGCircuit:
    """Stratify a circuit allowing measure/reset and gate ops to share layer boxes.

    Runs a single stratification pass treating ``measure``, ``reset``, and
    supported 2-qubit gates all as hypergraph edges.  The algorithm jointly
    schedules them, so a measure may be delayed to share a box with a
    concurrent gate — a strictly better arrangement than post-hoc boxing.

    Args:
        dag: The source :class:`~qiskit.dagcircuit.DAGCircuit`.
        algorithm: Stratification algorithm, e.g. :func:`.greedy_stratify`.
        edge_filter: Override the set of edge kinds.  Defaults to
            ``{"gate_2q", "measure", "reset"}``.
        label_fn: Label function passed to :func:`.dag_to_instance`.
        supported_1q: Supported 1-qubit gate names.
        supported_2q: Supported 2-qubit gate names.

    Returns:
        A :class:`~qiskit.dagcircuit.DAGCircuit` with mixed-kind layer boxes.
    """
    active_filter: Iterable[Literal["gate_2q", "measure", "reset"]]
    active_filter = (
        edge_filter if edge_filter is not None else frozenset({"gate_2q", "measure", "reset"})
    )
    inst, ctx = dag_to_instance(
        dag,
        edge_filter=active_filter,
        label_fn=label_fn,
        supported_1q=supported_1q,
        supported_2q=supported_2q,
    )
    strat = algorithm(inst)
    return stratification_to_dag(strat, ctx)
