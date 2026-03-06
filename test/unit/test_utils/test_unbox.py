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

"""Tests for `unbox`"""

from qiskit.circuit import BoxOp, QuantumCircuit

from samplomatic.utils import unbox


def test_unbox_inlines_box():
    """Test that `unbox` inlines box operations."""
    body = QuantumCircuit(2)
    body.cx(0, 1)
    body.h(0)

    circuit = QuantumCircuit(2)
    circuit.append(BoxOp(body=body), [0, 1])

    result = unbox(circuit)

    assert not any(isinstance(inst.operation, BoxOp) for inst in result)
    assert result.num_qubits == 2
    op_names = [inst.operation.name for inst in result]
    assert "cx" in op_names
    assert "h" in op_names


def test_unbox_no_boxes():
    """Test that `unbox` passes through a circuit with no boxes unchanged."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)

    result = unbox(circuit)

    assert result == circuit
