# This code is a Qiskit project.
#
# (C) Copyright IBM 2025.
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
from qiskit.circuit import CircuitInstruction, ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import Measure

from samplomatic.annotations import VirtualType
from samplomatic.builders.box_builder import LeftBoxBuilder
from samplomatic.builders.param_iter import ParamIter
from samplomatic.builders.specs import CollectionSpec, EmissionSpec
from samplomatic.builders.template_state import TemplateState
from samplomatic.constants import Direction
from samplomatic.exceptions import BuildError
from samplomatic.partition import QubitIndicesPartition, QubitPartition
from samplomatic.pre_samplex import PreSamplex
from samplomatic.pre_samplex.graph_data import PreCollect, PreEmit, PreZ2Collect
from samplomatic.synths.rzsx_synth import RzSxSynth


class TestBoxBuilder:
    """Test Box Builders"""

    def get_builder(self, qreg, creg=None):
        """Return left box builder with empty PreSamplex."""
        creg = ClassicalRegister(len(qreg)) if creg is None else creg
        qubit_map = {q: idx for idx, q in enumerate(qreg)}
        template_state = TemplateState(QuantumCircuit(qreg, creg), qubit_map, ParamIter(), [0])
        pre_samplex = PreSamplex(qubit_map=qubit_map, cregs=[creg])
        qubits = QubitPartition.from_elements(qreg)
        builder = LeftBoxBuilder(
            CollectionSpec(qubits, "Left", RzSxSynth()),
            EmissionSpec(qubits, "Right", VirtualType.PAULI),
        )
        builder.set_samplex_state(pre_samplex).set_template_state(template_state)
        return builder

    def test_parse_measurement(self):
        """Test parsing of measurement"""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(2)
        builder = self.get_builder(qreg, creg)
        builder.parse(CircuitInstruction(Measure(), [qreg[0]], [creg[0]]))

        assert builder.samplex_state.graph.num_nodes() == 0
        assert len(builder.measured_qubits) == 1
        assert builder.measured_qubits.overlaps_with([qreg[0]])

    def test_rhs_with_measurements(self):
        """Test rhs of left box with measurements"""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(3)
        builder = self.get_builder(qreg, creg)
        builder.lhs()
        builder.parse(CircuitInstruction(Measure(), qreg, [creg[0], creg[2]]))
        builder.rhs()
        idxs = QubitIndicesPartition.from_elements(builder.samplex_state.qubit_map.values())

        assert builder.samplex_state.graph.num_nodes() == 3
        assert builder.samplex_state.graph.nodes()[0] == PreCollect(
            idxs, Direction.BOTH, RzSxSynth(), [[0, 1, 2], [3, 4, 5]]
        )
        assert builder.samplex_state.graph.nodes()[1] == PreEmit(
            idxs, Direction.BOTH, VirtualType.PAULI
        )
        assert builder.samplex_state.graph.nodes()[2] == PreZ2Collect(
            idxs, clbit_idxs={creg.name: [0, 2]}, subsystems_idxs={creg.name: [0, 1]}
        )

    def test_rhs_no_measurements(self):
        """Test rhs of left box with no measurements"""
        qreg = QuantumRegister(2)
        builder = self.get_builder(qreg)
        builder.lhs()
        builder.rhs()
        idxs = QubitIndicesPartition.from_elements(builder.samplex_state.qubit_map.values())
        assert builder.samplex_state.graph.num_nodes() == 2
        assert builder.samplex_state.graph.nodes()[0] == PreCollect(
            idxs, Direction.BOTH, RzSxSynth(), [[0, 1, 2], [3, 4, 5]]
        )
        assert builder.samplex_state.graph.nodes()[1] == PreEmit(
            idxs, Direction.BOTH, VirtualType.PAULI
        )

    def test_wrong_twirl_type_for_measurement(self):
        """Test that error is raised if a measurement exists, but the twirl type is wrong"""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(2)
        qubit_map = {q: idx for idx, q in enumerate(qreg)}
        pre_samplex = PreSamplex(qubit_map=qubit_map)
        qubits = QubitPartition.from_elements(qreg)
        builder = LeftBoxBuilder(
            CollectionSpec(qubits, "Left", RzSxSynth()),
            EmissionSpec(qubits, "Right", VirtualType.U2),
        )
        builder.set_samplex_state(pre_samplex)
        builder.set_template_state(
            TemplateState(QuantumCircuit(qreg, creg), qubit_map, ParamIter(), [0])
        )
        builder.lhs()
        builder.parse(CircuitInstruction(Measure(), qreg, creg))

        with pytest.raises(BuildError, match="Cannot use u2 twirl in a box with measurements"):
            builder.rhs()

    def test_two_measurements_on_the_same_qubit_error(self):
        """Test that error is raised if the same qubit is measured twice in the box"""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(2)
        builder = self.get_builder(qreg)
        builder.set_template_state(TemplateState.construct_for_circuit(QuantumCircuit(qreg, creg)))
        builder.parse(CircuitInstruction(Measure(), qreg, creg))

        with pytest.raises(
            BuildError, match="Cannot measure the same qubit more than once in a dressed box"
        ):
            builder.parse(CircuitInstruction(Measure(), qreg, creg))
