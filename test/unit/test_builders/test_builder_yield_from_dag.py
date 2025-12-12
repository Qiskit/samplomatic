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

"""Test the yield_from_dag method for different builders."""

import pytest
from qiskit.circuit import QuantumCircuit
from qiskit.converters import circuit_to_dag

from samplomatic.aliases import DAGOpNode
from samplomatic.builders.box_builder import LeftBoxBuilder, RightBoxBuilder
from samplomatic.builders.passthrough_builder import PassthroughBuilder


@pytest.fixture
def dag():
    """Return a dag without barriers."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.h(1)
    return circuit_to_dag(circuit)


@pytest.fixture
def dag_barrier_after():
    """Return a dag with a barrier after the rest of its content."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.h(1)
    circuit.barrier()
    return circuit_to_dag(circuit)


@pytest.fixture
def dag_barrier_before():
    """Return a dag with a barrier before the rest of its content."""
    circuit = QuantumCircuit(2)
    circuit.barrier()
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.h(1)
    return circuit_to_dag(circuit)


def ops_equal(lhs: list[DAGOpNode], rhs: list[DAGOpNode]) -> bool:
    """Compare two lists of dag ops.

    This function is required because equality of dag op is based on instance.
    """
    if len(lhs) != len(rhs):
        return False
    for lhs_node, rhs_node in zip(lhs, rhs):
        if lhs_node is None:
            if rhs_node is None:
                continue
            return False
        if (
            lhs_node.op != rhs_node.op
            or lhs_node.qargs != rhs_node.qargs
            or lhs_node.cargs != rhs_node.cargs
        ):
            return False
    return True


def test_passthrough_builder(dag):
    """Test that yield_from_dag is equivalent to topological_op_nodes."""
    assert ops_equal(list(PassthroughBuilder.yield_from_dag(dag)), list(dag.topological_op_nodes()))


def test_left_box_builder(dag):
    """Test that yield_from_dag separates the left dressing."""
    expected = list(dag.topological_op_nodes())
    expected.insert(1, None)
    assert ops_equal(list(LeftBoxBuilder.yield_from_dag(dag)), expected)


def test_left_box_builder_barrier_before(dag_barrier_before):
    """Test that adding a barrier before the content adds no gates to the dressing."""
    expected = list(dag_barrier_before.topological_op_nodes())
    expected.insert(0, None)
    assert ops_equal(list(LeftBoxBuilder.yield_from_dag(dag_barrier_before)), expected)


def test_left_box_builder_barrier_after(dag_barrier_after):
    """Test that adding a barrier after the content does not affect the boundary."""
    expected = list(dag_barrier_after.topological_op_nodes())
    expected.insert(1, None)
    assert ops_equal(list(LeftBoxBuilder.yield_from_dag(dag_barrier_after)), expected)


def test_right_box_builder(dag):
    """Test that yield_from_dag separates the right dressing."""
    expected = list(dag.topological_op_nodes())
    expected.insert(2, None)
    assert ops_equal(list(RightBoxBuilder.yield_from_dag(dag)), expected)


def test_right_box_builder_barrier_before(dag_barrier_before):
    """Test that adding a barrier before the content does not affect the boundary."""
    expected = list(dag_barrier_before.topological_op_nodes())
    expected.insert(-1, None)
    assert ops_equal(list(RightBoxBuilder.yield_from_dag(dag_barrier_before)), expected)


def test_right_box_builder_barrier_after(dag_barrier_after):
    """Test that adding a barrier after the content adds no gates to the dressing."""
    expected = list(dag_barrier_after.topological_op_nodes())
    expected.append(None)
    assert ops_equal(list(RightBoxBuilder.yield_from_dag(dag_barrier_after)), expected)
