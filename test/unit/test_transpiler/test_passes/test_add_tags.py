# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test AddTags"""

import copy

import pytest
from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import PassManager

from samplomatic.annotations import Tag, Twirl
from samplomatic.transpiler.passes import AddTags
from samplomatic.utils import get_annotation


def test_tags_added_to_all_boxes():
    """Test that ``AddTags`` adds a :class:`~.Tag` annotation to every box."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.z(0)
    with circuit.box():
        circuit.h(0)
        circuit.cx(0, 1)

    pm = PassManager([AddTags()])
    transpiled = pm.run(circuit)

    for datum in transpiled.data:
        assert datum.operation.name == "box"
        tag = get_annotation(datum.operation, Tag)
        assert tag is not None
        assert tag.ref != ""
        assert tag.ref.startswith("t")


def test_consistent_naming():
    """Test that structurally equivalent boxes get the same tag ref."""
    circuit0 = QuantumCircuit(2)
    with circuit0.box([Twirl()]):
        circuit0.cx(0, 1)
    with circuit0.box([Twirl()]):
        circuit0.cx(0, 1)

    circuit1 = QuantumCircuit(2)
    with circuit1.box([Twirl()]):
        circuit1.cx(0, 1)

    pm = PassManager([AddTags()])
    transpiled0, transpiled1 = pm.run([circuit0, circuit1])

    tag00 = get_annotation(transpiled0.data[0].operation, Tag)
    tag01 = get_annotation(transpiled0.data[1].operation, Tag)
    tag10 = get_annotation(transpiled1.data[0].operation, Tag)

    # Equivalent boxes (same structure) share the same ref across circuits
    assert tag00.ref == tag01.ref
    assert tag00.ref == tag10.ref


def test_different_boxes_get_different_refs():
    """Test that structurally different boxes get different tag refs."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.cz(0, 1)

    pm = PassManager([AddTags()])
    transpiled = pm.run(circuit)

    tag0 = get_annotation(transpiled.data[0].operation, Tag)
    tag1 = get_annotation(transpiled.data[1].operation, Tag)
    assert tag0.ref != tag1.ref


@pytest.mark.parametrize("overwrite", [True, False])
def test_overwrite(overwrite):
    """Test ``AddTags`` with pre-existing :class:`~.Tag` and ``overwrite``."""
    manual_ref = "my_tag"
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    with circuit.box([Twirl(), Tag(manual_ref)]):
        circuit.cz(0, 1)

    pm = PassManager([AddTags(overwrite=overwrite)])
    transpiled = pm.run(circuit)

    tag0 = get_annotation(transpiled.data[0].operation, Tag)
    tag1 = get_annotation(transpiled.data[1].operation, Tag)

    assert tag0 is not None
    if overwrite:
        assert tag1.ref != manual_ref
    else:
        assert tag1.ref == manual_ref


def test_custom_prefix_ref():
    """Test that a custom prefix is respected."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)

    pm = PassManager([AddTags(prefix_ref="box")])
    transpiled = pm.run(circuit)

    tag = get_annotation(transpiled.data[0].operation, Tag)
    assert tag.ref.startswith("box")


def test_annotation_persistence():
    """Check that Tag annotations persist through a deep copy.

    Since annotation containers live in the qiskit rust data model, this test checks that we are
    adding to the annotations in a robust way, rather than to any transient python object that
    doesn't communicate back to the source of truth.
    """
    circuit = QuantumCircuit(2)
    with circuit.box([twirl := Twirl()]):
        circuit.cx(0, 1)

    pm = PassManager([AddTags()])
    transpiled = pm.run(circuit)

    copied = copy.deepcopy(transpiled)

    assert len(copied[0].operation.annotations) == 2
    assert copied[0].operation.annotations[0] == twirl
    assert isinstance(copied[0].operation.annotations[1], Tag)


def test_unique_instance_all_unique():
    """Test that ``unique_instance`` mode assigns unique refs to all boxes."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.cz(0, 1)

    pm = PassManager([AddTags(mode="unique_instance")])
    transpiled = pm.run(circuit)

    refs = [get_annotation(datum.operation, Tag).ref for datum in transpiled.data]
    assert len(refs) == len(set(refs))


def test_unique_instance_incrementing():
    """Test that ``unique_instance`` mode uses incrementing refs ``t0``, ``t1``, ..."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.cz(0, 1)
    with circuit.box():
        circuit.h(0)

    pm = PassManager([AddTags(mode="unique_instance")])
    transpiled = pm.run(circuit)

    refs = [get_annotation(datum.operation, Tag).ref for datum in transpiled.data]
    assert refs == ["t0", "t1", "t2"]


def test_unique_instance_resets_per_circuit():
    """Test that the ``unique_instance`` counter resets on each call to ``run()``."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    with circuit.box([Twirl()]):
        circuit.cz(0, 1)

    pm = PassManager([AddTags(mode="unique_instance")])
    transpiled0, transpiled1 = pm.run([circuit, circuit])

    refs0 = [get_annotation(datum.operation, Tag).ref for datum in transpiled0.data]
    refs1 = [get_annotation(datum.operation, Tag).ref for datum in transpiled1.data]

    assert refs0 == ["t0", "t1"]
    assert refs1 == ["t0", "t1"]
