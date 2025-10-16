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


from samplomatic.annotations import VirtualType
from samplomatic.samplex.nodes import CopyNode
from samplomatic.virtual_registers import PauliRegister


def test_construction():
    """Test construction and basic attributes."""
    node = CopyNode("existing", "new", VirtualType.PAULI, 5)
    assert node.instantiates() == {"new": (5, VirtualType.PAULI)}
    assert node.reads_from() == {"existing": (set(range(5)), VirtualType.PAULI)}
    assert not node.removes()
    assert not node.writes_to()
    assert node.outgoing_register_type is VirtualType.PAULI


def test_evaluate():
    """Test the evaluation method."""
    node = CopyNode("existing", "new", VirtualType.PAULI, 5)
    registers = {"existing": PauliRegister.identity(5, 3)}
    node.evaluate(registers)
    assert registers["new"] == registers["existing"]
    assert registers["new"] is not registers["existing"]
