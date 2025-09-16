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

"""Tests that twirling samples are produced correctly from static circuits."""

from itertools import product

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Operator, average_gate_fidelity
from qiskit.transpiler import PassManager

from samplomatic.annotations import Twirl
from samplomatic.builders import pre_build
from samplomatic.transpiler.passes import InlineBoxes


def make_circuits():
    for pair1, pair2 in product([[1, 2], [2, 1]], repeat=2):
        for op_name in ["cx", "cz", "ecr", "noop"]:
            circuit = QuantumCircuit(4)
            with circuit.box([Twirl(dressing="left")]):
                getattr(circuit, op_name)(*pair1)
            with circuit.box([Twirl(dressing="right")]):
                getattr(circuit, op_name)(*pair2)

            yield circuit, f"{op_name}_{str(pair1).replace(' ', '')}_{str(pair2).replace(' ', '')}"

    circuit = QuantumCircuit(4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(1, 0)

    circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.cx(1, 0)

    yield circuit, "prop_between_box"

    circuit = QuantumCircuit(4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(1, 0)

    circuit.cx(1, 0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.cx(1, 0)

    yield circuit, "prop_between_box2"

    circuit = QuantumCircuit(4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(0, 1)
        circuit.cx(3, 2)
        circuit.cx(2, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1, 2, 3)

    yield circuit, "multi_depth_box"

    for dressing_direction in ["left", "right"]:
        circuit = QuantumCircuit(4)
        with circuit.box([Twirl(dressing="left")]):
            circuit.cx(0, 1)
            circuit.cx(3, 2)
            circuit.cx(2, 1)

        with circuit.box([Twirl(dressing=dressing_direction)]):
            circuit.cx(0, 1)
            circuit.cx(2, 3)

        with circuit.box([Twirl(dressing=dressing_direction)]):
            circuit.cx(1, 0)
            circuit.cx(3, 2)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1, 2, 3)

        yield circuit, f"multiple_{dressing_direction}_boxes"

    for dressing_direction in ["left", "right"]:
        circuit = QuantumCircuit(4)
        with circuit.box([Twirl(dressing="left")]):
            circuit.cx(1, 0)
            circuit.cz(2, 3)

        with circuit.box([Twirl(dressing=dressing_direction)]):
            circuit.ecr(0, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1, 2, 3)

        yield circuit, f"small_{dressing_direction}_box_between_two_bigger_boxes"

    circuit = QuantumCircuit(4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(0, 1, 2)

    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(3)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(1, 2, 3)

    yield circuit, "non_overlapping_boxes_with_noops"

    circuit = QuantumCircuit(3)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(1, 2)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1, 2)

    yield circuit, "non_overlapping_boxes_with_gates"

    circuit = QuantumCircuit(1)
    with circuit.box([Twirl()]):
        circuit.h(0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0)

    yield circuit, "hadamard_left"

    circuit = QuantumCircuit(1)
    with circuit.box([Twirl()]):
        circuit.noop(0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.h(0)

    yield circuit, "hadamard_right"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)

    with circuit.box([Twirl()]):
        circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    yield circuit, "bell_state_different_boxes"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)
        circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    yield circuit, "bell_state_same_box"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.t(0)
        circuit.h(0)
        circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.t(0)
        circuit.t(1)

    yield circuit, "weird_phase_bell_state"

    circuit = QuantumCircuit(5)

    with circuit.box([Twirl()]):
        circuit.rz(np.pi / 2, 0)
        circuit.sx(0)
        circuit.rz(np.pi / 2, 0)
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

    yield circuit, "general_5q_static_circuit"

    circuit = QuantumCircuit(1)
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(0)
    circuit.x(0)
    circuit.z(0)
    circuit.y(0)
    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0)

    yield circuit, "propagate_through_invariant_gates"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(0)
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(1)
    circuit.x(0)
    circuit.x(1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    yield circuit, "propagate_through_merged_invariant_gates"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        circuits, descriptions = zip(*make_circuits())
        metafunc.parametrize("circuit", list(circuits), ids=descriptions)


def test_sampling(circuit, save_plot):
    """Test sampling.

    Casts the given ``circuit`` and the twirled circuit into operators, and it compares their
    fidelities.
    """
    save_plot(lambda: circuit.draw("mpl"), "Base Circuit", delayed=True)

    template, pre_samplex = pre_build(circuit)
    save_plot(lambda: template.template.draw("mpl"), "Template Circuit", delayed=True)
    save_plot(lambda: pre_samplex.draw(), "Unfinalized Pre-Samplex", delayed=True)

    samplex = pre_samplex.finalize()
    samplex.finalize()
    save_plot(lambda: pre_samplex.draw(), "Finalized Pre-Samplex", delayed=True)
    save_plot(lambda: samplex.draw(), "Samplex", delayed=True)

    samplex_input = samplex.inputs()
    samplex_output = samplex.sample(samplex_input, num_randomizations=10)
    parameter_values = samplex_output["parameter_values"]

    assert parameter_values.dtype == np.float32

    expected_op = Operator(PassManager([InlineBoxes()]).run(circuit))
    for row in parameter_values:
        op = Operator(template.template.assign_parameters(row))
        assert np.allclose(f := average_gate_fidelity(expected_op, op), 1), f
