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
from samplomatic.serializable import TYPE_REGISTRY


def test_parameter_idxs(dummy_node):
    """Test the parameter index attributes."""
    node = dummy_node()
    assert node.num_parameters == 0

    node = dummy_node(parameter_idxs=[1, 2, 43])
    assert node.parameter_idxs == [1, 2, 43]
    assert node.num_parameters == 3
    assert node.outgoing_register_type is None


def test_validate_reads_from(dummy_node):
    """Test validation for reads_from() succeeds."""
    node = dummy_node(reads_from={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    register_descriptions = {
        "a": (10, VirtualType.PAULI),
        "b": (5, VirtualType.U2),
        "c": (2, VirtualType.PAULI),
    }
    node.validate_and_update(register_descriptions_copy := register_descriptions.copy())
    assert register_descriptions == register_descriptions_copy


def test_validate_reads_from_fails(dummy_node):
    """Test validation for reads_from() fails when expected."""
    node = dummy_node(reads_from={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="read from register 'b', but .* not found."):
        node.validate_and_update({"a": (10, VirtualType.PAULI)})

    with pytest.raises(SamplexConstructionError, match="at least 5 subsystems for read access"):
        node.validate_and_update({"a": (4, VirtualType.PAULI), "b": (5, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="type 'pauli' for read access"):
        node.validate_and_update({"a": (10, VirtualType.U2), "b": (5, VirtualType.U2)})


def test_validate_writes_to(dummy_node):
    """Test validation for writes_to() succeeds."""
    node = dummy_node(writes_to={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    register_descriptions = {
        "a": (10, VirtualType.PAULI),
        "b": (5, VirtualType.U2),
        "c": (2, VirtualType.PAULI),
    }
    node.validate_and_update(register_descriptions_copy := register_descriptions.copy())
    assert register_descriptions == register_descriptions_copy


def test_validate_writes_to_fails(dummy_node):
    """Test validation for writes_to() fails when expected."""
    node = dummy_node(writes_to={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="write to register 'b', but .* not found."):
        node.validate_and_update({"a": (10, VirtualType.PAULI)})

    with pytest.raises(SamplexConstructionError, match="at least 5 subsystems for write access"):
        node.validate_and_update({"a": (4, VirtualType.PAULI), "b": (5, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="type 'pauli' for write access"):
        node.validate_and_update({"a": (10, VirtualType.U2), "b": (5, VirtualType.U2)})


def test_validate_instantiates(dummy_node):
    """Test validation for instantiates() succeeds."""
    node = dummy_node(instantiates={"a": (10, VirtualType.PAULI), "b": (5, VirtualType.U2)})

    register_descriptions = {"c": (2, VirtualType.PAULI)}
    node.validate_and_update(register_descriptions)
    assert register_descriptions == {
        "a": (10, VirtualType.PAULI),
        "b": (5, VirtualType.U2),
        "c": (2, VirtualType.PAULI),
    }


def test_validate_instantiates_fails(dummy_node):
    """Test validation for instantiates() fails when expected."""
    node = dummy_node(instantiates={"a": ({2, 4}, VirtualType.PAULI), "b": ({1}, VirtualType.U2)})

    with pytest.raises(SamplexConstructionError, match="'b', but .* that name already exists"):
        node.validate_and_update({"b": (10, VirtualType.U2)})


def test_validate_removes(dummy_node):
    """Test validation for removes() succeeds."""
    node = dummy_node(removes={"a"})

    register_descriptions = {"a": (10, VirtualType.PAULI), "c": (2, VirtualType.PAULI)}
    node.validate_and_update(register_descriptions)
    assert register_descriptions == {"c": (2, VirtualType.PAULI)}


def test_validate_removes_fails(dummy_node):
    """Test validation for removes() fails when expected."""
    node = dummy_node(removes={"a", "b"})

    with pytest.raises(
        SamplexConstructionError, match="'a', but no register with that name exists"
    ):
        node.validate_and_update({"b": (10, VirtualType.PAULI)})


def test_validate_redefines(dummy_node):
    """Test validation when we instantiate and remove the same name in a single node."""
    node = dummy_node(removes={"a", "b"}, instantiates={"a": (10, VirtualType.U2)})

    node.validate_and_update(
        register_descriptions := {"a": (11, VirtualType.PAULI), "b": (12, VirtualType.U2)}
    )

    assert register_descriptions == {"a": (10, VirtualType.U2)}


def test_dummy_is_not_registered(dummy_node):
    """Test that the dummy node is in the type registry."""
    assert dummy_node in TYPE_REGISTRY


def test_no_abstract_registrations():
    """Test that the registry mechanism doesn't contain any abstract parents."""
    assert Node not in TYPE_REGISTRY
    assert SamplingNode not in TYPE_REGISTRY
    assert EvaluationNode not in TYPE_REGISTRY
    assert CollectionNode not in TYPE_REGISTRY
