# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
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

from samplomatic.exceptions import SamplexConstructionError
from samplomatic.samplex import SamplexOutput
from samplomatic.samplex.nodes import CollectZ2ToOutputNode
from samplomatic.tensor_interface import TensorSpecification
from samplomatic.virtual_registers import VirtualType, Z2Register


def test_construction():
    """Test simple construction and simple attributes."""
    node = CollectZ2ToOutputNode("reg", [0, 2], "out", [1, 3])

    assert node.outputs_to() == {"out": ({1, 3}, VirtualType.Z2)}
    assert node.num_parameters == 0
    assert node.reads_from() == {"reg": ({0, 2}, VirtualType.Z2)}
    assert not node.writes_to() and not node.instantiates() and not node.removes()
    assert node.outgoing_register_type is None


def test_equality(dummy_collection_node):
    """Test equality."""
    node = CollectZ2ToOutputNode("reg", [0, 2], "out", [1, 3])
    assert node == node
    assert node == CollectZ2ToOutputNode("reg", [0, 2], "out", [1, 3])
    assert node != dummy_collection_node()
    assert node != CollectZ2ToOutputNode("my_reg", [0, 2], "out", [1, 3])
    assert node != CollectZ2ToOutputNode("reg", [1, 2], "out", [1, 3])
    assert node != CollectZ2ToOutputNode("reg", [0, 2], "my_out", [1, 3])
    assert node != CollectZ2ToOutputNode("reg", [0, 2], "out", [4, 5])
    assert node != CollectZ2ToOutputNode("reg", [0, 2, 4], "out", [1, 3, 5])
    assert node != CollectZ2ToOutputNode("reg", [0, 2], "out", [1, 3], output_axis=2)


def test_validate_fails():
    """Test the extra validation logic introduced by this node."""
    node = CollectZ2ToOutputNode("reg", [0, 2], "out", [1, 3])

    with pytest.raises(SamplexConstructionError, match="'z2' .* but found .* 'pauli'"):
        node.validate_and_update({"reg": (10, VirtualType.PAULI)})


def test_collect(rng):
    """Test the collect method."""
    reg1 = Z2Register([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1], [0, 1, 1]])
    reg2 = Z2Register([[0, 0, 0], [1, 1, 1], [1, 1, 1], [1, 0, 1], [1, 1, 0]])

    node1 = CollectZ2ToOutputNode("reg1", [0, 1, 2, 3, 4], "out", [0, 2, 4, 6, 8])
    node2 = CollectZ2ToOutputNode("reg2", [4, 3, 2, 1, 0], "out", [1, 3, 5, 7, 9])

    outputs = SamplexOutput(
        [
            TensorSpecification(
                "out",
                (3, 10),
                np.uint8,
                "A ten-qubit array",
            )
        ]
    ).bind(out=np.empty((3, 10), dtype=np.uint8))

    registers = {"reg1": reg1, "reg2": reg2}
    node1.collect(registers, outputs, rng)
    node2.collect(registers, outputs, rng)

    assert outputs["out"].tolist() == [
        [1, 1, 0, 1, 0, 1, 1, 1, 0, 0],
        [0, 1, 1, 0, 0, 1, 1, 1, 1, 0],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 0],
    ]


def test_collect_with_output_axis(rng):
    """Test the collect method with non-default output axis."""
    data0 = np.array([[1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0]], dtype=np.uint8)
    data1 = np.array([[0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1]], dtype=np.uint8)
    reg0 = Z2Register(data0)
    reg1 = Z2Register(data1)

    node0 = CollectZ2ToOutputNode("reg0", [0], "hist", [0], output_axis=2)
    node1 = CollectZ2ToOutputNode("reg1", [0], "hist", [1], output_axis=2)

    outputs = SamplexOutput([TensorSpecification("hist", (3, 2, 4), np.uint8, "History")]).bind(
        hist=np.zeros((3, 2, 4), dtype=np.uint8)
    )

    registers = {"reg0": reg0, "reg1": reg1}
    node0.collect(registers, outputs, rng)
    node1.collect(registers, outputs, rng)

    expected0 = data0.reshape(3, 4)
    expected1 = data1.reshape(3, 4)
    np.testing.assert_array_equal(outputs["hist"][:, 0, :], expected0)
    np.testing.assert_array_equal(outputs["hist"][:, 1, :], expected1)


def test_collect_with_dummy_axes(rng):
    """Test the collect method."""
    reg1 = Z2Register([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1], [0, 1, 1]])
    reg2 = Z2Register([[0, 0, 0], [1, 1, 1], [1, 1, 1], [1, 0, 1], [1, 1, 0]])

    node1 = CollectZ2ToOutputNode("reg1", [0, 1, 2, 3, 4], "out", [0, 2, 4, 6, 8])
    node2 = CollectZ2ToOutputNode("reg2", [4, 3, 2, 1, 0], "out", [1, 3, 5, 7, 9])

    outputs = SamplexOutput(
        [
            TensorSpecification(
                "out",
                (3, 1, 10),
                np.uint8,
                "A ten-qubit array",
            )
        ]
    ).bind(out=np.empty((3, 1, 10), dtype=np.uint8))

    registers = {"reg1": reg1, "reg2": reg2}
    node1.collect(registers, outputs, rng)
    node2.collect(registers, outputs, rng)

    assert outputs["out"].tolist() == [
        [[1, 1, 0, 1, 0, 1, 1, 1, 0, 0]],
        [[0, 1, 1, 0, 0, 1, 1, 1, 1, 0]],
        [[0, 0, 0, 1, 1, 1, 1, 1, 1, 0]],
    ]
