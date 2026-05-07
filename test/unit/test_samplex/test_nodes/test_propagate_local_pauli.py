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


import numpy as np
import pytest

from samplomatic.exceptions import SamplexRuntimeError
from samplomatic.samplex.nodes import PropagateLocalPauliNode
from samplomatic.virtual_registers import PauliRegister, VirtualType


def test_rzz_gate():
    """Test propagating Pauli register past an RZZ gate."""
    node = PropagateLocalPauliNode("rzz", "my_reg", [(0, 1)])
    assert node.outgoing_register_type is VirtualType.PAULI

    reg = PauliRegister(np.array([[0, 1, 3], [0, 0, 2]], dtype=np.uint8))
    node.evaluate({"my_reg": reg}, np.empty(()))

    assert reg.virtual_gates.tolist() == [[0, 1, 3], [0, 0, 2]]


def test_invalid_input_errors():
    """Test that non-local conjugation raises SamplexRuntimeError."""
    node = PropagateLocalPauliNode("rzz", "my_reg", [(0, 1)])
    reg = PauliRegister(np.array([[2], [0]], dtype=np.uint8))

    with pytest.raises(SamplexRuntimeError, match="Pauli values are not in the commutant of"):
        node.evaluate({"my_reg": reg}, np.empty(()))


def test_init_error():
    """Test init error."""
    with pytest.raises(ValueError, match="Unsupported operation 'rx'."):
        PropagateLocalPauliNode("rx", "my_reg", [(3,), (1,), (0,)])


def test_equality(dummy_evaluation_node):
    node = PropagateLocalPauliNode("rzz", "my_reg", [(0, 3), (1, 4), (2, 5)])
    assert node == node
    assert node == PropagateLocalPauliNode("rzz", "my_reg", [(0, 3), (1, 4), (2, 5)])
    assert node != dummy_evaluation_node()
    assert node != PropagateLocalPauliNode("rzz", "my_reg", [(3, 0), (1, 4), (2, 5)])
    assert node != PropagateLocalPauliNode("rzz", "my_other_reg", [(0, 3), (1, 4), (2, 5)])


def test_reads_from():
    """Test ``reads_from``."""
    node = PropagateLocalPauliNode("rzz", "my_reg", [(0, 1), (4, 2)])
    assert node.reads_from() == {"my_reg": ({0, 1, 2, 4}, VirtualType.PAULI)}


def test_writes_to():
    """Test ``writes_to`` method."""
    node = PropagateLocalPauliNode("rzz", "my_reg", [(0, 1), (4, 2)])
    assert node.writes_to() == {"my_reg": ({0, 1, 2, 4}, VirtualType.PAULI)}
