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

"""InsertLayerBarriers"""

from collections.abc import Iterable, Sequence

from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass

from ..layer_inference import insert_layer_barriers


class InsertLayerBarriers(TransformationPass):
    """Insert full-width barriers at inferred 2Q layer boundaries.

    Wraps :func:`~.insert_layer_barriers` as a Qiskit transpiler pass. Intended to run before
    :class:`~.GroupGatesIntoBoxes` so that the barriers it inserts guide gate grouping. When used
    inside :func:`~.generate_boxing_pass_manager` with the default
    ``remove_barriers="after_stratification"``, the barriers are removed again before single-qubit
    absorption, leaving 1Q dressing intact.

    Args:
        layer_templates: Optional list of layer types, each a collection of
            qubit-index pairs ``(q0, q1)``. If ``None``, templates are
            inferred from any barrier-separated regions in the input.
    """

    def __init__(
        self,
        layer_templates: Sequence[Iterable[tuple[int, int]]] | None = None,
    ):
        super().__init__()
        self.layer_templates = (
            None if layer_templates is None else [list(t) for t in layer_templates]
        )

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Run the pass on a DAG."""
        circuit = dag_to_circuit(dag)
        new_circuit = insert_layer_barriers(circuit, self.layer_templates)
        return circuit_to_dag(new_circuit)
