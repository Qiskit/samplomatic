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

from qiskit.circuit import Parameter, QuantumCircuit

from samplomatic.annotations import Twirl
from samplomatic.builders import pre_build


class TestTemplateBuilder:
    """Test strictly the template aspects of build."""

    def test_empty(self):
        """Test building an empty circuit."""
        template_state, _ = pre_build(QuantumCircuit())
        template = template_state.template

        assert template.num_qubits == 0
        assert template.num_clbits == 0
        assert template.num_parameters == 0
        assert not template.data

    def test_no_box(self):
        """Test building a circuit with no boxes."""
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.rz(Parameter("a") + Parameter("b"), 0)
        circuit.barrier(0, 1)
        circuit.cx(0, 1)
        circuit.measure_all()

        template_state, _ = pre_build(circuit)
        template = template_state.template

        assert template.num_qubits == 2
        assert template.num_clbits == 2
        assert [p.name for p in template.parameters] == ["p00"]

        for instr0, instr1 in zip(circuit, template):
            assert instr0.operation.name == instr1.operation.name

            for q0, q1 in zip(instr0.qubits, instr1.qubits):
                assert circuit.find_bit(q0).index == template.find_bit(q1).index

            for q0, q1 in zip(instr0.clbits, instr1.clbits):
                assert circuit.find_bit(q0).index == template.find_bit(q1).index

    def test_box_no_annotations(self):
        """Test building a circuit with a box that has no annotations."""
        circuit = QuantumCircuit(2)

        with circuit.box():
            circuit.h(0)

        circuit.rz(Parameter("a") + Parameter("b"), 0)

        with circuit.box():
            circuit.cx(0, 1)

        circuit.measure_all()

        template_state, _ = pre_build(circuit)
        template = template_state.template

        assert template.num_qubits == 2
        assert template.num_clbits == 2
        assert [p.name for p in template.parameters] == ["p00"]

        expected_circuit = QuantumCircuit(2)
        expected_circuit.barrier(0)
        expected_circuit.h(0)
        expected_circuit.barrier(0)
        expected_circuit.rz(Parameter("a") + Parameter("b"), 0)
        expected_circuit.barrier(0, 1)
        expected_circuit.cx(0, 1)
        expected_circuit.barrier(0, 1)
        expected_circuit.measure_all()

        for instr0, instr1 in zip(expected_circuit, template):
            assert instr0.operation.name == instr1.operation.name

            for q0, q1 in zip(instr0.qubits, instr1.qubits):
                assert circuit.find_bit(q0).index == template.find_bit(q1).index

            for q0, q1 in zip(instr0.clbits, instr1.clbits):
                assert circuit.find_bit(q0).index == template.find_bit(q1).index

    def test_box_left_right(self):
        """Test putting the dressing on different sides of a box."""
        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.cx(0, 1)
        with circuit.box([Twirl(dressing="right")]):
            circuit.cx(0, 1)
        circuit.measure_all()

        template_state, _ = pre_build(circuit)
        template = template_state.template

        assert template.num_qubits == 2
        assert template.num_clbits == 2
        assert [p.name for p in template.parameters] == [f"p{str(i).zfill(2)}" for i in range(12)]

        expected_names = ["barrier"]
        expected_names += ["rz", "sx", "rz", "sx", "rz"]
        expected_names += ["rz", "sx", "rz", "sx", "rz"]
        expected_names += ["barrier", "cx", "barrier"]
        expected_names += ["barrier", "cx", "barrier"]
        expected_names += ["rz", "sx", "rz", "sx", "rz"]
        expected_names += ["rz", "sx", "rz", "sx", "rz"]
        expected_names += ["barrier"]

        for idx, (instr, name) in enumerate(zip(template, expected_names)):
            assert instr.name == name, f"Instruction {idx}"

    def test_box_decomposition(self):
        """Test decomposition modes of a box."""
        circuit = QuantumCircuit(2)
        circuit.h(0)
        with circuit.box([Twirl(decomposition="rzrx")]):
            circuit.cx(0, 1)

        circuit.rz(Parameter("c"), 0)

        with circuit.box([Twirl(decomposition="rzsx", dressing="right")]):
            circuit.cx(0, 1)

        circuit.measure_all()

        template_state, _ = pre_build(circuit)
        template = template_state.template

        assert template.num_qubits == 2
        assert template.num_clbits == 2
        assert [p.name for p in template.parameters] == [f"p{str(i).zfill(2)}" for i in range(13)]

        expected_names = ["h"]

        expected_names += ["barrier"]
        expected_names += ["rz", "rx", "rz"] * 2 + ["barrier", "cx"]
        expected_names += ["barrier"]

        expected_names += ["rz"]

        expected_names += ["barrier"]
        expected_names += ["cx", "barrier"] + ["rz", "sx", "rz", "sx", "rz"] * 2
        expected_names += ["barrier"]

        expected_names += ["barrier"] + ["measure"] * 4

        for idx, (instr, name) in enumerate(zip(template, expected_names)):
            assert instr.operation.name == name, f"Instruction {idx}"

    def test_general_5q_static_circuit(self):
        """Test with a general static circuit of 5 qubits"""
        circuit = QuantumCircuit(5)
        with circuit.box([Twirl()]):
            circuit.rz(0.5, 0)
            circuit.sx(0)
            circuit.rz(0.5, 0)
            circuit.cx(0, 3)
            circuit.noop(range(5))

        circuit.cx(0, 1)

        with circuit.box([Twirl(decomposition="rzrx")]):
            circuit.rz(0.123, 2)
            circuit.cx(3, 4)
            circuit.cx(3, 2)
            circuit.noop(1)

        with circuit.box([Twirl()]):
            circuit.cx(0, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(range(5))

        circuit.measure_all()

        template_state, _ = pre_build(circuit)
        template = template_state.template

        assert template.num_qubits == 5
        assert template.num_clbits == 5

        # Verify that we get the expected number of operations
        ops_count = template.count_ops()
        # 3 boxes of rzsx for a total of 12 qubits, 1 box of rzrx for a total of 4 qubits.
        assert ops_count["rz"] == 44  # 12 * 3 + 4 * 2
        assert ops_count["rx"] == 4  # 4 * 1
        assert ops_count["sx"] == 24  # 12 * 2
        assert ops_count["barrier"] == 13  # 3 * 4 boxes + 1 for measure all
        assert ops_count["cx"] == 5  # as in the original circuit
        assert ops_count["measure"] == 5  # as in the original circuit
        assert len(ops_count) == 6

        # Verify that we get the expected number of parameters
        assert len(template.parameters) == 48  # One parameter per rz\rx gate
