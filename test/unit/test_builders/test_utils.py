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
from qiskit.circuit.library import HGate, SXGate
from rustworkx import PyDiGraph

from samplomatic.builders.specs import InstructionSpec
from samplomatic.constants import Direction
from samplomatic.exceptions import SamplexConstructionError
from samplomatic.partition import QubitIndicesPartition, SubsystemIndicesPartition
from samplomatic.pre_samplex.graph_data import PreEdge, PreEmit, PrePropagate
from samplomatic.pre_samplex.utils import merge_pre_edges, pre_propagate_nodes_are_mergeable
from samplomatic.virtual_registers import PauliRegister


class TestPrePropagateNodesAreMergeable:
    """Test the `pre_propagate_nodes_are_mergeable` method."""

    def test_two_connected_pre_propagates(self):
        """Test with a graph that contains two mergeable pre-propagate nodes."""
        graph = PyDiGraph()
        n0 = graph.add_node(
            PreEmit(PauliRegister, Direction.BOTH, QubitIndicesPartition(2, [(0, 1)]))
        )
        n1 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(0,)]),
                Direction.LEFT,
                HGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )
        n2 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(1,)]),
                Direction.LEFT,
                HGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )

        graph.add_edge(n0, n1, None)
        graph.add_edge(n0, n2, None)

        assert not pre_propagate_nodes_are_mergeable(graph, 0, 1)
        assert not pre_propagate_nodes_are_mergeable(graph, 1, 0)

        assert not pre_propagate_nodes_are_mergeable(graph, 0, 2)
        assert not pre_propagate_nodes_are_mergeable(graph, 2, 0)

        assert pre_propagate_nodes_are_mergeable(graph, 1, 2)
        assert pre_propagate_nodes_are_mergeable(graph, 2, 1)

    def test_two_disconnected_pre_propagates(self):
        """Test with a graph that contains two non-mergeable (disconnected) pre-propagate nodes."""
        graph = PyDiGraph()
        n0 = graph.add_node(
            PreEmit(PauliRegister, Direction.BOTH, QubitIndicesPartition(2, [(0, 1)]))
        )
        n1 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(0,)]),
                Direction.LEFT,
                HGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )
        n2 = graph.add_node(
            PreEmit(PauliRegister, Direction.BOTH, QubitIndicesPartition(2, [(0, 1)]))
        )
        n3 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(0,)]),
                Direction.LEFT,
                HGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )

        graph.add_edge(n0, n1, None)
        graph.add_edge(n2, n3, None)

        assert not pre_propagate_nodes_are_mergeable(graph, 2, 1)

    def test_two_connected_pre_propagates_with_different_directions(self):
        """Test with a graph with two non-mergeable (different direction) pre-propagate nodes."""
        graph = PyDiGraph()
        n0 = graph.add_node(
            PreEmit(PauliRegister, Direction.BOTH, QubitIndicesPartition(2, [(0, 1)]))
        )
        n1 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(0,)]),
                Direction.RIGHT,
                HGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )
        n2 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(0,)]),
                Direction.LEFT,
                HGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )

        graph.add_edge(n0, n1, None)
        graph.add_edge(n0, n2, None)

        assert not pre_propagate_nodes_are_mergeable(graph, 2, 1)

    def test_two_connected_pre_propagates_with_different_operations(self):
        """Test with a graph with two non-mergeable (different operations) pre-propagates."""
        graph = PyDiGraph()
        n0 = graph.add_node(
            PreEmit(PauliRegister, Direction.BOTH, QubitIndicesPartition(2, [(0, 1)]))
        )
        n1 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(0,)]),
                Direction.LEFT,
                SXGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )
        n2 = graph.add_node(
            PrePropagate(
                QubitIndicesPartition(1, [(1,)]),
                Direction.LEFT,
                HGate(),
                SubsystemIndicesPartition(1, [(0,)]),
                InstructionSpec(),
            )
        )

        graph.add_edge(n0, n1, None)
        graph.add_edge(n0, n2, None)

        assert not pre_propagate_nodes_are_mergeable(graph, 2, 1)


class TestMergePreEdges:
    """Test the `merge_pre_edges` method."""

    def test_merge_single_edge(self):
        """Test `merge_pre_edges` when there is a single edge between source and dest nodes."""
        graph = PyDiGraph()
        source_idx = graph.add_node("source")
        destination_idx = graph.add_node("destination")

        edge = PreEdge(SubsystemIndicesPartition(1, [(1,)]), Direction.LEFT)
        graph.add_edge(source_idx, destination_idx, edge)

        assert merge_pre_edges(graph, source_idx, destination_idx) == edge

    @pytest.mark.parametrize("direction", [Direction.LEFT, Direction.RIGHT])
    def test_merge_multiple_edges(self, direction):
        """Test `merge_pre_edges` when there are multiple edges between source and dest nodes."""
        graph = PyDiGraph()
        source_idx = graph.add_node("source")
        destination_idx = graph.add_node("destination")

        edge_0 = PreEdge(SubsystemIndicesPartition(1, [(0,)]), direction)
        edge_1 = PreEdge(SubsystemIndicesPartition(1, [(1,)]), direction)
        edge_87 = PreEdge(SubsystemIndicesPartition(1, [(87,)]), direction)
        edge_2 = PreEdge(SubsystemIndicesPartition(1, [(2,)]), direction)

        graph.add_edge(source_idx, destination_idx, edge_0)
        graph.add_edge(source_idx, destination_idx, edge_1)
        graph.add_edge(source_idx, destination_idx, edge_87)
        graph.add_edge(source_idx, destination_idx, edge_2)

        expected = PreEdge(SubsystemIndicesPartition(1, [(2,), (87,), (1,), (0,)]), direction)
        assert merge_pre_edges(graph, source_idx, destination_idx) == expected

    def test_raises(self):
        """Test that `merge_pre_edges` raises."""
        graph = PyDiGraph()
        source_idx = graph.add_node("source")
        destination_idx = graph.add_node("destination")

        with pytest.raises(SamplexConstructionError, match="No edges to merge"):
            merge_pre_edges(graph, source_idx, destination_idx)

        right_edge = PreEdge(SubsystemIndicesPartition(1, [(0,)]), Direction.RIGHT)
        left_edge = PreEdge(SubsystemIndicesPartition(1, [(1,)]), Direction.LEFT)

        graph.add_edge(source_idx, destination_idx, right_edge)
        graph.add_edge(source_idx, destination_idx, left_edge)

        with pytest.raises(SamplexConstructionError, match="different directions"):
            merge_pre_edges(graph, source_idx, destination_idx)
