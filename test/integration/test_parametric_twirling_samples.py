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

"""Tests that twirling samples are produced correctly from parametric circuits."""

from itertools import product

import numpy as np
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.quantum_info import Operator, average_gate_fidelity
from qiskit.transpiler import PassManager

from samplomatic.annotations import Twirl
from samplomatic.builders import pre_build
from samplomatic.transpiler.passes import InlineBoxes


def make_circuits():
    circuit = QuantumCircuit(1)
    with circuit.box([Twirl()]):
        circuit.rx(Parameter("a"), 0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0)

    yield circuit, "parametric_x_circuit"

    a = Parameter("a")
    circuit = QuantumCircuit(1)
    circuit.rz(Parameter("e") + a, 0)
    with circuit.box([Twirl()]):
        circuit.rz(a + Parameter("b"), 0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0)

    circuit.rz(2 * Parameter("c"), 0)
    circuit.rz(a, 0)

    yield circuit, "parametric_expression_circuit"

    circuit = QuantumCircuit(3)
    with circuit.box([Twirl()]):
        circuit.rx(Parameter("a"), 0)
        circuit.cx(0, 1)

    with circuit.box([Twirl()]):
        circuit.cx(1, 2)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1, 2)

    yield circuit, "parametric_entangling_circuit"

    a, b = Parameter("a"), Parameter("b")

    for idx, (x, y) in enumerate(product([a, b, a + b], [a, b, a + b])):
        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.rx(x, 0)
            circuit.rx(y, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)

        yield circuit, f"merge_parametric_gate_{idx}"

    circuit = QuantumCircuit(1)
    with circuit.box([Twirl()]):
        circuit.noop(0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.rx(Parameter("a"), 0)
        circuit.rz(2 * Parameter("b"), 0)

    yield circuit, "parametric_right_box"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        circuits, descriptions = zip(*make_circuits())
        metafunc.parametrize("circuit", list(circuits), ids=descriptions)


def test_sampling(rng, circuit, save_plot):
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

    circuit_params = rng.random(len(circuit.parameters))
    samplex_input = samplex.inputs().bind(parameter_values=circuit_params)
    samplex_output = samplex.sample(samplex_input, num_randomizations=10)
    parameter_values = samplex_output["parameter_values"]

    expected_op = Operator(
        PassManager([InlineBoxes()]).run(circuit).assign_parameters(circuit_params)
    )
    for row in parameter_values:
        op = Operator(template.template.assign_parameters(row))
        assert np.allclose(f := average_gate_fidelity(expected_op, op), 1), f
