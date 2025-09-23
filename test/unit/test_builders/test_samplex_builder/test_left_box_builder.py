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

"""Test PreSamplex"""

import numpy as np
import pytest
from qiskit.circuit import CircuitInstruction, ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import Measure, XGate

from samplomatic import Twirl
from samplomatic.annotations import VirtualType
from samplomatic.builders import pre_build
from samplomatic.builders.samplex_builder.box_samplex_builder import LeftBoxSamplexBuilder
from samplomatic.builders.specs import CollectionSpec, EmissionSpec, InstructionSpec
from samplomatic.constants import Direction
from samplomatic.exceptions import SamplexBuildError
from samplomatic.partition import QubitIndicesPartition, QubitPartition
from samplomatic.pre_samplex import PreSamplex
from samplomatic.pre_samplex.graph_data import PreCollect, PreEmit, PreZ2Collect
from samplomatic.synths.rzsx_synth import RzSxSynth


class TestLeftBoxBuilder:
    """Test Box Builders"""

    def get_builder(self, qreg, creg=None):
        """Return left box builder with empty PreSamplex."""
        cregs = [ClassicalRegister(len(qreg)) if creg is None else creg]
        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(qreg)}, cregs=cregs)
        qubits = QubitPartition.from_elements(qreg)
        builder = LeftBoxSamplexBuilder(
            CollectionSpec(qubits, "Left", RzSxSynth()),
            EmissionSpec(qubits, "Right", VirtualType.PAULI),
        )
        builder.set_state(pre_samplex)
        return builder

    def test_parse_measurement(self):
        """Test parsing of measurement"""
        qreg = QuantumRegister(2)
        builder = self.get_builder(qreg)
        builder.parse(CircuitInstruction(Measure(), [qreg[0]]), InstructionSpec())

        assert builder.state.graph.num_nodes() == 1
        assert len(builder.measured_qubits) == 1
        assert builder.measured_qubits.overlaps_with([qreg[0]])

    def test_rhs_with_measurements(self):
        """Test rhs of left box with measurements"""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(3)
        builder = self.get_builder(qreg, creg)
        builder.lhs(InstructionSpec())
        builder.parse(
            CircuitInstruction(Measure(), qreg),
            InstructionSpec(clbit_idxs=[0, 2], param_idxs=np.array([0])),
        )
        builder.rhs(InstructionSpec())
        subsystem_idxs = QubitIndicesPartition.from_elements(
            [builder.state.qubit_map[q] for q in qreg]
        )

        assert builder.state.graph.num_nodes() == 3
        assert builder.state.graph.nodes()[0] == PreCollect(
            subsystem_idxs, Direction.BOTH, RzSxSynth(), [0]
        )
        assert builder.state.graph.nodes()[1] == PreEmit(
            subsystem_idxs, Direction.BOTH, VirtualType.PAULI
        )
        assert builder.state.graph.nodes()[2] == PreZ2Collect(
            subsystem_idxs, clbit_idxs={creg.name: [0, 2]}, subsystems_idxs={creg.name: [0, 1]}
        )

    def test_rhs_no_measurements(self):
        """Test rhs of left box with no measurements"""
        qreg = QuantumRegister(2)
        builder = self.get_builder(qreg)
        builder.lhs(InstructionSpec())
        builder.rhs(InstructionSpec(param_idxs=np.array([0])))
        subsystem_idxs = QubitIndicesPartition.from_elements(
            [builder.state.qubit_map[q] for q in qreg]
        )
        assert builder.state.graph.num_nodes() == 2
        assert builder.state.graph.nodes()[0] == PreCollect(
            subsystem_idxs, Direction.BOTH, RzSxSynth(), [0]
        )
        assert builder.state.graph.nodes()[1] == PreEmit(
            subsystem_idxs, Direction.BOTH, VirtualType.PAULI
        )

    def test_gate_after_measurement_error(self):
        """Test that error is raised if a gate is encountered after a measurement"""
        qreg = QuantumRegister(2)
        builder = self.get_builder(qreg)
        builder.parse(CircuitInstruction(Measure(), qreg), InstructionSpec())

        with pytest.raises(SamplexBuildError, match="No operations allowed after a measurement"):
            builder.parse(CircuitInstruction(XGate(), [qreg[0]]), InstructionSpec())

    def test_wrong_twirl_type_for_measurement(self):
        """Test that error is raised if a measurement exists, but the twirl type is wrong"""
        qreg = QuantumRegister(2)
        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(qreg)})
        qubits = QubitPartition.from_elements(qreg)
        builder = LeftBoxSamplexBuilder(
            CollectionSpec(qubits, "Left", RzSxSynth()),
            EmissionSpec(qubits, "Right", VirtualType.U2),
        )
        builder.set_state(pre_samplex)
        builder.lhs(InstructionSpec())
        builder.parse(CircuitInstruction(Measure(), qreg), InstructionSpec())

        with pytest.raises(
            SamplexBuildError, match="Cannot use u2 twirl in a box with measurements"
        ):
            builder.rhs(InstructionSpec())

    def test_two_measurements_on_the_same_qubit_error(self):
        """Test that error is raised if the same qubit is measured twice in the box"""
        qreg = QuantumRegister(2)
        builder = self.get_builder(qreg)
        builder.parse(CircuitInstruction(Measure(), qreg), InstructionSpec())

        with pytest.raises(
            SamplexBuildError, match="Cannot measure the same qubit twice in a twirling box"
        ):
            builder.parse(CircuitInstruction(Measure(), qreg), InstructionSpec())

    def test_if_else(self):
        """Test the build result of if-else.

        Because it is a bit difficult to do by hand, we use the full pre_build.
        """
        circuit = QuantumCircuit(1, 1)
        circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.x(0)
            with _else:
                circuit.sx(0)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0)

        _, pre_samplex = pre_build(circuit)
        graph = pre_samplex.graph
        for emit_node in [4, 5]:
            assert not graph.get_edge_data(emit_node, 1).force_register_copy
            assert graph.get_edge_data(emit_node, 3).force_register_copy
        assert graph[1].operation.name == "x"
        assert graph[3].operation.name == "sx"
