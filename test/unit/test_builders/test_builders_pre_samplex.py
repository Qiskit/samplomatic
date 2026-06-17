# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test BoxBuilder for PreSamplex"""

import pytest
from qiskit.circuit import ClassicalRegister, QuantumRegister
from qiskit.circuit.library import Measure
from qiskit.dagcircuit import DAGCircuit, DAGOpNode

from samplomatic.builders.box_builder import LeftBoxBuilder
from samplomatic.builders.param_iter import ParamIter
from samplomatic.builders.specs import CollectionSpec, EmissionSpec
from samplomatic.builders.template_state import TemplateState
from samplomatic.constants import Direction
from samplomatic.exceptions import BuildError
from samplomatic.partition import QubitIndicesPartition, QubitPartition
from samplomatic.pre_samplex import PreSamplex
from samplomatic.pre_samplex.graph_data import PreCollect, PreEmit, PreMeasure
from samplomatic.synths.rzsx_synth import RzSxSynth
from samplomatic.virtual_registers import VirtualType


class TestBoxBuilder:
    """Test Box Builders"""

    def get_builder(self, qreg, creg=None):
        """Return left box builder with empty PreSamplex."""
        creg = ClassicalRegister(len(qreg)) if creg is None else creg
        qubit_map = {q: idx for idx, q in enumerate(qreg)}
        circuit = DAGCircuit()
        circuit.add_qreg(qreg)
        circuit.add_creg(creg)
        template_state = TemplateState(circuit, qubit_map, ParamIter(), [0])
        pre_samplex = PreSamplex(qubit_map=qubit_map, cregs=[creg])
        qubits = QubitPartition.from_elements(qreg)
        builder = LeftBoxBuilder(
            CollectionSpec(qubits, "Left", RzSxSynth()),
            EmissionSpec(qubits, "Right", VirtualType.PAULI),
        )
        builder.set_samplex_state(pre_samplex).set_template_state(template_state)
        return builder

    def test_parse_measurement(self):
        """Test parsing of measurement records the qubit and creates PreMeasure."""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(2)
        builder = self.get_builder(qreg, creg)
        builder.lhs()
        builder.parse(None)
        builder.parse(DAGOpNode(Measure(), [qreg[0]], [creg[0]]))

        measure_nodes = [
            n for n in builder.samplex_state.graph.nodes() if isinstance(n, PreMeasure)
        ]
        assert len(measure_nodes) == 1

    def test_measurement_propagation(self):
        """Test left box with measurements creates PreMeasure nodes during parse."""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(3)
        builder = self.get_builder(qreg, creg)
        builder.lhs()
        builder.parse(None)
        builder.parse(DAGOpNode(Measure(), qreg, [creg[0], creg[2]]))
        builder.rhs()
        idxs = QubitIndicesPartition.from_elements(builder.samplex_state.qubit_map.values())

        nodes = builder.samplex_state.graph.nodes()
        assert nodes[0] == PreCollect(idxs, Direction.BOTH, RzSxSynth(), [[0, 1, 2], [3, 4, 5]])
        assert nodes[1] == PreEmit(idxs, Direction.BOTH, VirtualType.PAULI)
        measure_nodes = [n for n in nodes if isinstance(n, PreMeasure)]
        assert len(measure_nodes) == 2
        assert measure_nodes[0].creg_names == [creg.name]
        assert measure_nodes[0].creg_offsets == [0]
        assert measure_nodes[1].creg_names == [creg.name]
        assert measure_nodes[1].creg_offsets == [2]

    def test_rhs_no_measurements(self):
        """Test rhs of left box with no measurements"""
        qreg = QuantumRegister(2)
        builder = self.get_builder(qreg)
        builder.lhs()
        builder.parse(None)
        builder.rhs()
        idxs = QubitIndicesPartition.from_elements(builder.samplex_state.qubit_map.values())
        assert builder.samplex_state.graph.num_nodes() == 2
        assert builder.samplex_state.graph.nodes()[0] == PreCollect(
            idxs, Direction.BOTH, RzSxSynth(), [[0, 1, 2], [3, 4, 5]]
        )
        assert builder.samplex_state.graph.nodes()[1] == PreEmit(
            idxs, Direction.BOTH, VirtualType.PAULI
        )

    def test_two_measurements_on_the_same_qubit_error(self):
        """Test that error is raised if the same qubit is measured twice in the box"""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(2)
        builder = self.get_builder(qreg, creg)
        builder.lhs()
        builder.parse(None)
        builder.parse(DAGOpNode(Measure(), qreg, creg))

        with pytest.raises(BuildError, match="Cannot twirl more than one measurement"):
            builder.parse(DAGOpNode(Measure(), qreg, creg))
