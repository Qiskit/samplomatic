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

"""Tests for `undress_box`"""

import pytest
from qiskit.circuit import BoxOp, ClassicalRegister, Parameter, QuantumCircuit, QuantumRegister

from samplomatic.annotations import BasisTransform, Twirl
from samplomatic.utils import undress_box


def test_empty_box():
    """Test `undress_box` for an empty box."""
    box = BoxOp(QuantumCircuit(2))
    assert undress_box(box) == box

    box = BoxOp(QuantumCircuit(2), annotations=[Twirl(dressing="left")])
    assert undress_box(box, Twirl) == box

    box = BoxOp(QuantumCircuit(2), annotations=[Twirl(dressing="right")])
    assert undress_box(box, Twirl) == box


def test_undressed_box():
    """Test `undress_box` for a box without dressing."""
    body = QuantumCircuit(QuantumRegister(3, "my_qreg"), ClassicalRegister(2, "my_creg"))
    body.h(0)
    body.rz(Parameter("theta"), 0)
    body.z(1)
    body.cx(0, 1)
    body.rz(Parameter("phi"), 1)
    body.y(2)
    box = BoxOp(body)

    assert undress_box(box) == box


def test_left_dressed_box():
    """Test `undress_box` for a left-dressed box."""
    body = QuantumCircuit(QuantumRegister(3, "my_qreg"), ClassicalRegister(2, "my_creg"))
    body.h(0)
    body.rz(Parameter("theta"), 0)
    body.z(1)
    body.cx(0, 1)
    body.rz(ph := Parameter("phi"), 1)
    body.y(2)
    box = BoxOp(body, annotations=[Twirl(dressing="left")])

    body_expected = QuantumCircuit(body.qubits + body.clbits)
    body_expected.cx(0, 1)
    body_expected.rz(ph, 1)
    box_expected = BoxOp(body_expected, annotations=[Twirl(dressing="left")])

    assert undress_box(box, Twirl) == box_expected


def test_right_dressed_box():
    """Test `undress_box` for a left-dressed box."""
    body = QuantumCircuit(QuantumRegister(3, "my_qreg"), ClassicalRegister(2, "my_creg"))
    body.h(0)
    body.rz(th := Parameter("theta"), 0)
    body.z(1)
    body.cx(0, 1)
    body.rz(Parameter("phi"), 1)
    body.y(2)
    box = BoxOp(body, annotations=[Twirl(dressing="right")])

    body_expected = QuantumCircuit(body.qubits + body.clbits)
    body_expected.h(0)
    body_expected.rz(th, 0)
    body_expected.z(1)
    body_expected.cx(0, 1)
    box_expected = BoxOp(body_expected, annotations=[Twirl(dressing="right")])

    assert undress_box(box, Twirl) == box_expected


@pytest.mark.parametrize(
    "annotations",
    [
        [],
        [Twirl(dressing="right")],
        [Twirl(decomposition="rzrx"), BasisTransform(ref="ref")],
    ],
)
def test_annotations_are_removed(annotations):
    """
    Test that `undress_box` keeps or removes the annotations depending on ``keep_annotations``.
    """
    body = QuantumCircuit(3)

    assert (
        undress_box(BoxOp(body, annotations=annotations), (Twirl, BasisTransform)).annotations
        == annotations
    )
    assert undress_box(BoxOp(body, annotations=annotations)).annotations == []
