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

import pytest

from samplomatic.annotations import VirtualType
from samplomatic.exceptions import SamplexConstructionError
from samplomatic.samplex.nodes import CollectionNode, EvaluationNode, Node, SamplingNode

from .dummy_nodes import DummyNode


def test_parameter_idxs():
    """Test the parameter index attributes."""
    node = DummyNode()
    assert node.num_parameters == 0

    node = DummyNode(parameter_idxs=[1, 2, 43])
    assert node.parameter_idxs == [1, 2, 43]
    assert node.num_parameters == 3
    assert node.outgoing_register_type is None


def test_validate_reads_from():
    """Test validation for reads_from() succeeds."""
    node = DummyNode(reads_from={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    register_descriptions = {
        "a": (10, VirtualType.PAULI),
        "b": (5, VirtualType.U2),
        "c": (2, VirtualType.PAULI),
    }
    node.validate_and_update(register_descriptions_copy := register_descriptions.copy())
    assert register_descriptions == register_descriptions_copy


def test_validate_reads_from_fails():
    """Test validation for reads_from() fails when expected."""
    node = DummyNode(reads_from={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="read from register 'b', but .* not found."):
        node.validate_and_update({"a": (10, VirtualType.PAULI)})

    with pytest.raises(SamplexConstructionError, match="at least 5 subsystems for read access"):
        node.validate_and_update({"a": (4, VirtualType.PAULI), "b": (5, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="type 'pauli' for read access"):
        node.validate_and_update({"a": (10, VirtualType.U2), "b": (5, VirtualType.U2)})


def test_validate_writes_to():
    """Test validation for writes_to() succeeds."""
    node = DummyNode(writes_to={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    register_descriptions = {
        "a": (10, VirtualType.PAULI),
        "b": (5, VirtualType.U2),
        "c": (2, VirtualType.PAULI),
    }
    node.validate_and_update(register_descriptions_copy := register_descriptions.copy())
    assert register_descriptions == register_descriptions_copy


def test_validate_writes_to_fails():
    """Test validation for writes_to() fails when expected."""
    node = DummyNode(writes_to={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="write to register 'b', but .* not found."):
        node.validate_and_update({"a": (10, VirtualType.PAULI)})

    with pytest.raises(SamplexConstructionError, match="at least 5 subsystems for write access"):
        node.validate_and_update({"a": (4, VirtualType.PAULI), "b": (5, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="type 'pauli' for write access"):
        node.validate_and_update({"a": (10, VirtualType.U2), "b": (5, VirtualType.U2)})


def test_validate_instantiates():
    """Test validation for instantiates() succeeds."""
    node = DummyNode(instantiates={"a": (10, VirtualType.PAULI), "b": (5, VirtualType.U2)})

    register_descriptions = {"c": (2, VirtualType.PAULI)}
    node.validate_and_update(register_descriptions)
    assert register_descriptions == {
        "a": (10, VirtualType.PAULI),
        "b": (5, VirtualType.U2),
        "c": (2, VirtualType.PAULI),
    }


def test_validate_instantiates_fails():
    """Test validation for instantiates() fails when expected."""
    node = DummyNode(instantiates={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="'b', but .* that name already exists"):
        node.validate_and_update({"b": (10, VirtualType.U2)})


def test_validate_removes():
    """Test validation for removes() succeeds."""
    node = DummyNode(removes={"a"})

    register_descriptions = {"a": (10, VirtualType.PAULI), "c": (2, VirtualType.PAULI)}
    node.validate_and_update(register_descriptions)
    assert register_descriptions == {"c": (2, VirtualType.PAULI)}


def test_validate_removes_fails():
    """Test validation for removes() fails when expected."""
    node = DummyNode(removes={"a", "b"})

    with pytest.raises(
        SamplexConstructionError, match="'a', but no register with that name exists"
    ):
        node.validate_and_update({"b": (10, VirtualType.PAULI)})


def test_validate_redefines():
    """Test validation when we instantiate and remove the same name in a single node."""
    node = DummyNode(removes={"a", "b"}, instantiates={"a": (10, VirtualType.U2)})

    node.validate_and_update(
        register_descriptions := {"a": (11, VirtualType.PAULI), "b": (12, VirtualType.U2)}
    )

    assert register_descriptions == {"a": (10, VirtualType.U2)}


def test_dummy_is_registered():
    """Test that the dummy node is in the node registry."""
    assert DummyNode in Node.NODE_REGISTRY


def test_no_abstract_registrations():
    """Test that the registry mechanism doesn't contain any abstract parents."""
    assert Node not in Node.NODE_REGISTRY
    assert SamplingNode not in Node.NODE_REGISTRY
    assert EvaluationNode not in Node.NODE_REGISTRY
    assert CollectionNode not in Node.NODE_REGISTRY
