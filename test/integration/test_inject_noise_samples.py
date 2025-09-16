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

"""Tests that twirling samples are produced correctly from static circuits with noise injection."""

import numpy as np
from qiskit.circuit import BoxOp, QuantumCircuit
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import (
    Operator,
    Pauli,
    QubitSparsePauliList,
    average_gate_fidelity,
)

from samplomatic.annotations import InjectNoise, Twirl
from samplomatic.builders import pre_build


def make_circuits():
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise")]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    paulis = {"my_noise": QubitSparsePauliList.from_list(["II"])}
    rates = {"rates.my_noise": [0.0]}
    expected = [Operator(np.identity(16))]

    yield (circuit, expected, paulis, rates), "identity"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise", "my_modifier")]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    yield (circuit, expected, paulis, rates), "identity_optional_modifiers"

    paulis = {"my_noise": QubitSparsePauliList.from_list(["XX"])}
    rates = {"rates.my_noise": [100.0]}
    expected = [Operator(np.identity(16)), Operator(Pauli("XXXX").to_matrix())]

    yield (circuit, expected, paulis, rates), "xx_noise"

    paulis = {"my_noise": QubitSparsePauliList.from_list(["XX", "ZZ"])}
    rates = {"rates.my_noise": [100.0, 100.0]}
    expected = [
        Operator(np.identity(16)),
        Operator(Pauli("XXXX").to_matrix()),
        Operator(Pauli("ZZZZ").to_matrix()),
        Operator(Pauli("YYYY").to_matrix()),
    ]

    yield (circuit, expected, paulis, rates), "two_body_noise"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise")]):
        circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    paulis = {"my_noise": QubitSparsePauliList.from_list(["XX"])}
    rates = {"rates.my_noise": [100.0]}
    noise_ops = [Operator(np.identity(16)), Operator(Pauli("XXXX").to_matrix())]
    expected = [(Operator(CXGate()) ^ Operator(CXGate())) & op for op in noise_ops]

    yield (circuit, expected, paulis, rates), "xx_noise_permuted"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise")]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(), InjectNoise("my_noise")]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    expected = [Operator(np.identity(16)), Operator(Pauli("XXXX").to_matrix())]

    yield (circuit, expected, paulis, rates), "xx_noise_twice"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise0")]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(), InjectNoise("my_noise1")]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    paulis = {
        "my_noise0": QubitSparsePauliList.from_list(["XI"]),
        "my_noise1": QubitSparsePauliList.from_list(["IX"]),
    }
    rates = {"rates.my_noise0": [100.0], "rates.my_noise1": [100.0]}
    expected = [
        Operator(np.identity(16)),
        Operator(Pauli("XIXI").to_matrix()),
        Operator(Pauli("IXIX").to_matrix()),
        Operator(Pauli("XXXX").to_matrix()),
    ]

    yield (circuit, expected, paulis, rates), "two_annotations"

    paulis = {"my_noise": QubitSparsePauliList.from_list(["XI"])}
    rates = {"rates.my_noise": [100.0]}
    expected = [Operator(np.identity(16)), Operator(Pauli("XIXI").to_matrix())]

    for idx, perm in enumerate([(0, 1), (1, 0)]):
        circuit = QuantumCircuit(2)
        with circuit.box([InjectNoise("my_noise"), Twirl()]):
            circuit.noop(*perm)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)
        yield (circuit, expected, paulis, rates), f"permuted_context_qubits_{idx}"

    for idx, (perm, pauli) in enumerate(zip([(0, 1), (1, 0)], [Pauli("XIXI"), Pauli("IXIX")])):
        expected = [Operator(np.identity(16)), Operator(pauli.to_matrix())]
        circuit = QuantumCircuit(2)
        box_op = BoxOp(QuantumCircuit(2), annotations=[InjectNoise("my_noise"), Twirl()])
        circuit.append(box_op, perm)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)
        yield (circuit, expected, paulis, rates), f"permuted_box_op_qubits_{idx}"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        args, descriptions = zip(*make_circuits())
        metafunc.parametrize("circuit,expected,paulis,rates", list(args), ids=descriptions)


def test_sampling(circuit, expected, paulis, rates, save_plot):
    """Test sampling.

    Casts the given ``circuit`` and the twirled circuit into operators, and it compares their
    fidelities.
    """
    save_plot(lambda: circuit.draw("mpl"), "Base Circuit", delayed=True)

    template, samplex_state = pre_build(circuit)
    save_plot(lambda: template.template.draw("mpl"), "Template Circuit", delayed=True)
    save_plot(lambda: samplex_state.draw(), "Unfinalized Pre-Samplex", delayed=True)

    samplex = samplex_state.finalize()
    samplex.finalize()
    save_plot(lambda: samplex_state.draw(), "Finalized Pre-Samplex", delayed=True)
    save_plot(lambda: samplex.draw(), "Samplex", delayed=True)

    samplex_input = samplex.inputs(paulis).bind(noise_maps=rates)
    samplex_output = samplex.sample(samplex_input, num_randomizations=(num_rand := 20))
    parameter_values = samplex_output["parameter_values"]

    ops = [Operator(template.template.assign_parameters(row)) for row in parameter_values]
    counts = {}
    for idx, expected_op in enumerate(expected):
        counts[idx] = len(
            [
                op
                for op in ops
                if np.allclose(average_gate_fidelity(expected_op, op.conjugate() ^ op), 1)
            ]
        )

    assert len(counts) == len(expected)
    assert sum(counts.values()) == num_rand
