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

"""Test AddInjectNoise"""

import pytest
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.transpiler import PassManager

from samplomatic.annotations import InjectNoise, Twirl
from samplomatic.transpiler.passes import AddInjectNoise
from samplomatic.utils import get_annotation


def test_no_modification_strategy():
    """Test `AddInjectNoise` with the ``"no_modification"`` strategy."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.z(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.rz(th := Parameter("theta"), 0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.measure_all()

    pm = PassManager([AddInjectNoise("no_modification", targets="all")])
    transpiled_circuit = pm.run(circuit)

    ref1 = get_annotation(transpiled_circuit.data[0].operation, InjectNoise).ref
    ref2 = get_annotation(transpiled_circuit.data[1].operation, InjectNoise).ref
    ref3 = get_annotation(transpiled_circuit.data[3].operation, InjectNoise).ref

    assert get_annotation(transpiled_circuit.data[0].operation, InjectNoise).modifier_ref == ""
    assert get_annotation(transpiled_circuit.data[1].operation, InjectNoise).modifier_ref == ""
    assert get_annotation(transpiled_circuit.data[3].operation, InjectNoise).modifier_ref == ""

    expected_circuit = QuantumCircuit(2)
    with expected_circuit.box([Twirl(), InjectNoise(ref1, "")]):
        expected_circuit.h(0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(dressing="right"), InjectNoise(ref2, "")]):
        expected_circuit.z(0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(), InjectNoise(ref1, "")]):
        expected_circuit.rz(th, 0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(), InjectNoise(ref3, "")]):
        expected_circuit.measure_all()

    assert transpiled_circuit == expected_circuit


def test_uniform_modification_strategy():
    """Test `AddInjectNoise` with the ``"uniform_modification"`` strategy."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.z(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.rz(th := Parameter("theta"), 0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.measure_all()

    pm = PassManager([AddInjectNoise("uniform_modification", targets="all")])
    transpiled_circuit = pm.run(circuit)

    ref1 = get_annotation(transpiled_circuit.data[0].operation, InjectNoise).ref
    ref2 = get_annotation(transpiled_circuit.data[1].operation, InjectNoise).ref
    ref3 = get_annotation(transpiled_circuit.data[3].operation, InjectNoise).ref

    assert get_annotation(transpiled_circuit.data[0].operation, InjectNoise).modifier_ref == ref1
    assert get_annotation(transpiled_circuit.data[1].operation, InjectNoise).modifier_ref == ref2
    assert get_annotation(transpiled_circuit.data[3].operation, InjectNoise).modifier_ref == ref3

    expected_circuit = QuantumCircuit(2)
    with expected_circuit.box([Twirl(), InjectNoise(ref1, ref1)]):
        expected_circuit.h(0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(dressing="right"), InjectNoise(ref2, ref2)]):
        expected_circuit.z(0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(), InjectNoise(ref1, ref1)]):
        expected_circuit.rz(th, 0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(), InjectNoise(ref3, ref3)]):
        expected_circuit.measure_all()

    assert transpiled_circuit == expected_circuit


def test_individual_modification_strategy():
    """Test `AddInjectNoise` with the ``"individual_modification"`` strategy."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.z(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.rz(th := Parameter("theta"), 0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.measure_all()

    pm = PassManager([AddInjectNoise("individual_modification", targets="all")])
    transpiled_circuit = pm.run(circuit)

    ref1 = get_annotation(transpiled_circuit.data[0].operation, InjectNoise).ref
    ref2 = get_annotation(transpiled_circuit.data[1].operation, InjectNoise).ref
    ref3 = get_annotation(transpiled_circuit.data[2].operation, InjectNoise).ref
    ref4 = get_annotation(transpiled_circuit.data[3].operation, InjectNoise).ref

    modifier_ref1 = get_annotation(transpiled_circuit.data[0].operation, InjectNoise).modifier_ref
    modifier_ref2 = get_annotation(transpiled_circuit.data[1].operation, InjectNoise).modifier_ref
    modifier_ref3 = get_annotation(transpiled_circuit.data[2].operation, InjectNoise).modifier_ref
    modifier_ref4 = get_annotation(transpiled_circuit.data[3].operation, InjectNoise).modifier_ref

    assert len(refs := {ref1, ref2, ref3, ref4}) == 3
    assert len(modifier_ref := {modifier_ref1, modifier_ref2, modifier_ref3, modifier_ref4}) == 4
    assert refs.isdisjoint(modifier_ref)

    expected_circuit = QuantumCircuit(2)
    with expected_circuit.box([Twirl(), InjectNoise(ref1, modifier_ref1)]):
        expected_circuit.h(0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(dressing="right"), InjectNoise(ref2, modifier_ref2)]):
        expected_circuit.z(0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(), InjectNoise(ref3, modifier_ref3)]):
        expected_circuit.rz(th, 0)
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(), InjectNoise(ref4, modifier_ref4)]):
        expected_circuit.measure_all()

    assert transpiled_circuit == expected_circuit


@pytest.mark.parametrize("overwrite", [True, False])
def test_overwrite(overwrite):
    """Test `AddInjectNoise` with preset annotations and ``overwrite``."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl(), InjectNoise("my_ref")]):
        circuit.z(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.measure_all()

    pm = PassManager([AddInjectNoise("no_modification", overwrite, targets="all")])
    transpiled_circuit = pm.run(circuit)

    noise_annotations = [
        get_annotation(transpiled_circuit.data[i].operation, InjectNoise) for i in range(2)
    ]

    if overwrite is True:
        assert noise_annotations[1] == noise_annotations[0]
    else:
        assert noise_annotations[1] == InjectNoise("my_ref")
        assert noise_annotations[1] != noise_annotations[0]


@pytest.mark.parametrize("overwrite", [True, False])
def test_overwrite_when_the_box_is_encountered_for_the_first_time(overwrite):
    """Test `AddInjectNoise` with preset annotations and ``overwrite``."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("my_ref")]):
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.z(0)
        circuit.cx(0, 1)

    pm = PassManager([AddInjectNoise("no_modification", overwrite, targets="all")])
    transpiled_circuit = pm.run(circuit)

    noise_annotations = [
        get_annotation(transpiled_circuit.data[i].operation, InjectNoise) for i in range(2)
    ]

    assert noise_annotations[0] == noise_annotations[1]
    assert noise_annotations[0] == InjectNoise("my_ref")


@pytest.mark.parametrize(
    "inject_noise_strategy",
    ["no_modification", "uniform_modification", "individual_modification"],
)
def test_prefixes(inject_noise_strategy):
    """Test the prefixes generated by `AddInjectNoise`"""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.z(0)
        circuit.cz(0, 1)
    with circuit.box([Twirl()]):
        circuit.rz(Parameter("theta"), 0)
        circuit.ecr(0, 1)

    pm = PassManager([AddInjectNoise(inject_noise_strategy, targets="all")])
    transpiled_circuit = pm.run(circuit)
    for idx in range(3):
        annotation = get_annotation(transpiled_circuit.data[idx].operation, InjectNoise)
        assert annotation.ref.startswith("r")

        if inject_noise_strategy == "no_modification":
            assert annotation.modifier_ref == ""
        elif inject_noise_strategy == "uniform_modification":
            assert annotation.modifier_ref.startswith("r")
        else:
            annotation.modifier_ref.startswith("m")


@pytest.mark.parametrize(
    "inject_noise_strategy", ["no_modification", "uniform_modification", "individual_modification"]
)
def test_some_boxes_are_left_alone(inject_noise_strategy):
    """Tests that empty boxes are left alone, as well as boxes with no twirl annotation."""
    circuit = QuantumCircuit(2)
    with circuit.box():
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.z(0)

    pm = PassManager([AddInjectNoise(inject_noise_strategy, targets="all")])
    transpiled_circuit = pm.run(circuit)

    for idx in range(2):
        assert get_annotation(transpiled_circuit.data[idx].operation, InjectNoise) is None


def test_boxes_with_same_qubits_in_different_orders():
    """Test that `AddInjectNoise` returns the same keys when the order of qubits differs."""
    circuit = QuantumCircuit(4)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
        circuit.cx(2, 3)
    with circuit.box([Twirl()]):
        circuit.cx(2, 3)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.x(3)
        circuit.x(1)
        circuit.x(0)
        circuit.x(2)
        circuit.cx(2, 3)
        circuit.cx(0, 1)

    pm = PassManager([AddInjectNoise("uniform_modification", targets="all")])
    transpiled_circuit = pm.run(circuit)

    refs = [get_annotation(datum.operation, InjectNoise).ref for datum in transpiled_circuit.data]
    assert len(set(refs)) == 1


@pytest.mark.parametrize("targets", ["none", "gates", "measures", "all"])
def test_targets(targets):
    """Test the `target` input of `AddInjectNoise`."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.h(0)
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.measure_all()

    pm = PassManager([AddInjectNoise("uniform_modification", targets=targets)])
    transpiled_circuit = pm.run(circuit)

    gate_annotation = get_annotation(transpiled_circuit.data[0].operation, InjectNoise)
    assert (gate_annotation is None) == (targets in {"none", "measures"})

    measure_annotation = get_annotation(transpiled_circuit.data[1].operation, InjectNoise)
    assert (measure_annotation is None) == (targets in {"none", "gates"})
