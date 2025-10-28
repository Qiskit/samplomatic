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

import orjson
import pytest

from samplomatic.samplex.nodes import ChangeBasisNode
from samplomatic.samplex.nodes.change_basis_node import MEAS_PAULI_BASIS, PREP_PAULI_BASIS
from samplomatic.serialization.node_serializers import ChangeBasisNodeSerializer
from samplomatic.serialization.type_serializer import TypeSerializer


@pytest.mark.parametrize("basis_change", [MEAS_PAULI_BASIS, PREP_PAULI_BASIS])
@pytest.mark.parametrize("ssv", ChangeBasisNodeSerializer.SSVS)
def test_change_basis_serializer_round_trip(basis_change, ssv):
    node = ChangeBasisNode("x", basis_change, "ref", 6)
    data = ChangeBasisNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)
