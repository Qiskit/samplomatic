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

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Operator, average_gate_fidelity

from samplomatic.annotations import InjectLocalClifford, Twirl
from samplomatic.builders import pre_build


def make_circuits():
    circuit = QuantumCircuit(1)
    with circuit.box([InjectLocalClifford("c1")]):
        circuit.measure_all()

    expected = QuantumCircuit(1)
    expected.x(0)

    local_cliff = np.array([2], dtype=np.uint8)
    yield (circuit, expected, {"c1": local_cliff}), "inject_x"

    expected = QuantumCircuit(1)
    expected.h(0)

    local_cliff = np.array([4], dtype=np.uint8)
    yield (circuit, expected, {"c1": local_cliff}), "inject_h"

    num_layers = 8

    circuit = QuantumCircuit(2)
    for i in range(num_layers):
        with circuit.box([InjectLocalClifford(f"c{i}"), Twirl()]):
            circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(range(2))

    local_cliffords = {f"c{i}": np.array([0, 0]) for i in range(num_layers)}
    yield (circuit, QuantumCircuit(2), local_cliffords), "pauli_lindblad_like"

    expected = QuantumCircuit(2)
    expected.h(0)
    expected.h(1)

    local_cliffords = {f"c{i}": np.array([0, 0]) for i in range(num_layers)}
    local_cliffords["c0"] = np.array([4, 4])
    yield (circuit, expected, local_cliffords), "pauli_lindblad_like_x_basis"

    expected = QuantumCircuit(2)
    for i in range(num_layers // 2):
        expected.cz(0, 1)
        expected.cx(0, 1)

    # inserting IH on every layer transforms all even indexed CXs to CZs
    local_cliffords = {f"c{i}": np.array([0, 4]) for i in range(num_layers)}
    yield (circuit, expected, local_cliffords), "pauli_lindblad_like_cx_to_cz"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        args, descriptions = zip(*make_circuits())
        metafunc.parametrize("circuit,expected,local_cliffords", list(args), ids=descriptions)


def test_sampling(circuit, expected, local_cliffords, save_plot):
    """Test sampling.

    Casts the given ``circuit`` and the twirled circuit into operators, and it compares their
    fidelities.
    """
    save_plot(lambda: circuit.draw("mpl"), "Base Circuit", delayed=True)

    template_state, samplex_state = pre_build(circuit)
    template = template_state.finalize()
    save_plot(lambda: template.draw("mpl"), "Template Circuit", delayed=True)
    save_plot(lambda: samplex_state.draw(), "Unfinalized Pre-Samplex", delayed=True)

    samplex = samplex_state.finalize()
    samplex.finalize()
    save_plot(lambda: samplex_state.draw(), "Finalized Pre-Samplex", delayed=True)
    save_plot(lambda: samplex.draw(), "Samplex", delayed=True)

    samplex_input = samplex.inputs().bind(local_cliffords=local_cliffords)
    samplex_output = samplex.sample(samplex_input, num_randomizations=10)
    parameter_values = samplex_output["parameter_values"]

    expected_op = Operator(expected)
    template.remove_final_measurements()
    for row in parameter_values:
        op = Operator(template.assign_parameters(row))
        assert np.allclose(f := average_gate_fidelity(expected_op, op), 1), f
