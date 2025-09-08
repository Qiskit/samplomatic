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
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import Operator, Pauli, PauliLindbladMap, QubitSparsePauliList

from samplomatic.annotations import InjectNoise, Twirl
from samplomatic.builders import pre_build


def make_circuits():
    model = QubitSparsePauliList.from_list(["XX"])
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise", model)]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    expected = Operator(np.identity(16))

    yield (circuit, expected, {"my_noise": np.array([0.0])}), "identity"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise", model, "my_modifier")]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    yield (circuit, expected, {"my_noise": np.array([0.0])}), "identity_optional_modifiers"

    prob = next(iter(PauliLindbladMap.from_list([("XX", 100)]).probabilities()))
    expected = prob * Operator(np.identity(16)) + (1 - prob) * Operator(Pauli("XXXX").to_matrix())

    yield (circuit, expected, {"my_noise": np.array([100.0])}), "xx_noise"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise", model)]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(), InjectNoise("my_noise", model)]):
        circuit.noop(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    expected = expected & expected

    yield (circuit, expected, {"my_noise": np.array([100.0])}), "xx_noise_twice"

    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_noise", model)]):
        circuit.cx(0, 1)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    expected = prob * Operator(np.identity(16)) + (1 - prob) * Operator(Pauli("XXXX").to_matrix())
    expected = (Operator(CXGate()) ^ Operator(CXGate())) & expected

    yield (circuit, expected, {"my_noise": np.array([100.0])}), "xx_noise_permuted"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        args, descriptions = zip(*make_circuits())
        metafunc.parametrize("circuit,expected,noise_maps", list(args), ids=descriptions)


def test_sampling(circuit, expected, noise_maps, save_plot):
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

    samplex_input = samplex.inputs().bind(noise_maps=noise_maps)
    samplex_output = samplex.sample(samplex_input, num_randomizations=1000)
    parameter_values = samplex_output["parameter_values"]

    superops = []
    for row in parameter_values:
        op = Operator(template.template.assign_parameters(row))
        superops.append(op.conjugate() ^ op)

    avg_op = sum(superops) / len(superops)
    assert np.allclose(avg_op, expected, 0.1)
