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

"""StratificationInstance: hypergraph + partial order + labelling."""

from collections.abc import Hashable, Iterable

import rustworkx as rx

from .hypergraph import Hypergraph


class StratificationInstance:
    """The full stratification math object ``(H, ≺, σ)``.

    Combines a :class:`.Hypergraph` ``H = (Q, E)`` with:

    - a partial order ``≺`` on the edge set ``E``, stored internally as its Hasse diagram
      (transitive reduction) in a :class:`rustworkx.PyDiGraph`; and
    - a labelling ``σ : E → Σ`` mapping each edge to an element of some label alphabet ``Σ``.

    Vertex indices are ``0, ..., num_vertices - 1``; edge indices are ``0, ..., num_edges - 1``.

    Args:
        hypergraph: The underlying hypergraph ``H = (Q, E)``.
        precedence: The partial order on ``E``.  Either a :class:`rustworkx.PyDiGraph` whose
            ``num_nodes()`` equals ``hypergraph.num_edges`` and whose node payloads are the
            integers ``0, ..., num_edges - 1``; or an iterable of ``(predecessor_id,
            successor_id)`` pairs representing ``predecessor ≺ successor`` relations.  In either
            case the graph must be acyclic, and it is reduced to its Hasse diagram on
            construction.
        labels: An iterable of hashable labels, one per edge (same order as
            ``hypergraph.edges``).
        external_patterns: Optional iterable of additional patterns (each a
            :class:`frozenset` of labels) that are known to appear in the materialised output
            *outside* the stratification layers — for example from pre-existing
            :class:`~qiskit.circuit.BoxOp` instructions in the source circuit.  These patterns
            are included in :attr:`.Stratification.unique_pattern_count` so that algorithms
            minimising pattern count naturally prefer reusing them.

    Raises:
        ValueError: If the number of labels does not match ``num_edges``, if the precedence
            graph has the wrong shape, or if the precedence relation contains a cycle.
    """

    def __init__(
        self,
        hypergraph: Hypergraph,
        precedence: "rx.PyDiGraph | Iterable[tuple[int, int]]",
        labels: Iterable[Hashable],
        external_patterns: "Iterable[frozenset[Hashable]] | None" = None,
    ) -> None:
        self._hypergraph = hypergraph
        n = hypergraph.num_edges

        # Normalise external patterns.
        if external_patterns is None:
            self._external_patterns: frozenset[frozenset[Hashable]] = frozenset()
        else:
            self._external_patterns = frozenset(
                p if isinstance(p, frozenset) else frozenset(p) for p in external_patterns
            )

        # Normalise labels.
        self._labels: tuple[Hashable, ...] = tuple(labels)
        if len(self._labels) != n:
            raise ValueError(f"Expected {n} labels (one per edge), got {len(self._labels)}.")
        self._alphabet: frozenset[Hashable] = frozenset(self._labels)

        # Build the precedence PyDiGraph.
        if isinstance(precedence, rx.PyDiGraph):
            dag = precedence
            if dag.num_nodes() != n:
                raise ValueError(
                    f"Precedence graph has {dag.num_nodes()} nodes but hypergraph has {n} edges."
                )
            # Verify node payloads are 0..n-1.
            for node_idx in dag.node_indices():
                payload = dag[node_idx]
                if payload != node_idx:
                    raise ValueError(
                        f"Precedence graph node {node_idx} has unexpected payload "
                        f"{payload!r}; payloads must equal the node index."
                    )
        else:
            # Build from arc pairs.
            dag = rx.PyDiGraph()
            dag.add_nodes_from(range(n))
            for u, v in precedence:
                dag.add_edge(u, v, None)

        if not rx.is_directed_acyclic_graph(dag):
            raise ValueError("Precedence relation contains a cycle; it must be a partial order.")

        # Reduce to the Hasse diagram.
        self._precedence: rx.PyDiGraph = rx.transitive_reduction(dag)[0]

        # Canonicalise arc set for hashing / equality / public access.
        self._arc_set: frozenset[tuple[int, int]] = frozenset(
            (u, v) for u, v, _ in self._precedence.weighted_edge_list()
        )

        # Precompute chain heights: h(e) = length of the longest chain from e to any sink.
        # We do a reverse-topological DP (process sinks first).
        topo = list(rx.topological_sort(self._precedence))
        chain_heights = [0] * n
        for node in reversed(topo):
            succs = self._precedence.successors(node)
            if succs:
                chain_heights[node] = 1 + max(chain_heights[s] for s in succs)
        self._chain_heights: tuple[int, ...] = tuple(chain_heights)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def hypergraph(self) -> Hypergraph:
        """The underlying hypergraph ``H = (Q, E)``."""
        return self._hypergraph

    @property
    def labels(self) -> tuple[Hashable, ...]:
        """The labelling ``σ``, as a tuple parallel to ``hypergraph.edges``."""
        return self._labels

    @property
    def alphabet(self) -> frozenset[Hashable]:
        """The label alphabet ``Σ = {σ(e) : e ∈ E}``."""
        return self._alphabet

    @property
    def external_patterns(self) -> "frozenset[frozenset[Hashable]]":
        """Patterns from pre-existing boxes."""
        return self._external_patterns

    @property
    def num_vertices(self) -> int:
        """Number of vertices ``|Q|``."""
        return self._hypergraph.num_vertices

    @property
    def num_edges(self) -> int:
        """Number of edges ``|E|``."""
        return self._hypergraph.num_edges

    # ------------------------------------------------------------------
    # Order queries
    # ------------------------------------------------------------------

    def predecessors(self, e: int) -> frozenset[int]:
        """Return all edges that strictly precede ``e`` in ``≺``.

        That is, ``pred(e) = {e' : e' ≺ e}``.

        Args:
            e: An edge ID.
        """
        return frozenset(rx.ancestors(self._precedence, e))

    def successors(self, e: int) -> frozenset[int]:
        """Return all edges that strictly succeed ``e`` in ``≺``.

        Args:
            e: An edge ID.
        """
        return frozenset(rx.descendants(self._precedence, e))

    def immediate_predecessors(self, e: int) -> frozenset[int]:
        """Return the immediate predecessors of ``e`` in the Hasse diagram.

        Args:
            e: An edge ID.
        """
        return frozenset(self._precedence.predecessors(e))

    def immediate_successors(self, e: int) -> frozenset[int]:
        """Return the immediate successors of ``e`` in the Hasse diagram.

        Args:
            e: An edge ID.
        """
        return frozenset(self._precedence.successors(e))

    def is_comparable(self, e: int, e_prime: int) -> bool:
        """Return ``True`` if ``e ≺ e'`` or ``e' ≺ e``.

        Args:
            e: An edge ID.
            e_prime: An edge ID.
        """
        return e_prime in rx.ancestors(self._precedence, e) or e in rx.ancestors(
            self._precedence, e_prime
        )

    def chain_height(self, e: int) -> int:
        """Return the length of the longest chain from ``e`` to any sink in ``≺``.

        A sink has chain height 0.  Used as the priority heuristic in Algorithm B.

        Args:
            e: An edge ID.
        """
        return self._chain_heights[e]

    def linear_extension(self) -> tuple[int, ...]:
        """Return a linear extension of ``≺`` as a tuple of edge IDs.

        Any topological sort of the Hasse diagram is a valid linear extension.
        """
        return tuple(rx.topological_sort(self._precedence))

    def precedence_arcs(self) -> frozenset[tuple[int, int]]:
        """Return the Hasse diagram arcs as a frozenset of ``(predecessor, successor)`` pairs."""
        return self._arc_set

    # ------------------------------------------------------------------
    # Layer / stratification queries
    # ------------------------------------------------------------------

    def is_antichain(self, edge_ids: Iterable[int]) -> bool:
        """Return ``True`` if no two edges in ``edge_ids`` are comparable in ``≺``.

        Args:
            edge_ids: An iterable of edge IDs.
        """
        ids = list(edge_ids)
        for i, e in enumerate(ids):
            for e_prime in ids[i + 1 :]:
                if self.is_comparable(e, e_prime):
                    return False
        return True

    def is_strong_matching(self, edge_ids: Iterable[int]) -> bool:
        """Return ``True`` if the edges are pairwise vertex-disjoint.

        Delegates to :meth:`.Hypergraph.is_strong_matching`.

        Args:
            edge_ids: An iterable of edge IDs.
        """
        return self._hypergraph.is_strong_matching(edge_ids)

    def is_layer(self, edge_ids: Iterable[int]) -> bool:
        """Return ``True`` if the edges form a valid layer (antichain and strong matching).

        Args:
            edge_ids: An iterable of edge IDs.
        """
        ids = list(edge_ids)
        return self.is_antichain(ids) and self.is_strong_matching(ids)

    def pattern_of(self, edge_ids: Iterable[int]) -> frozenset[Hashable]:
        """Return ``pat(L) = {σ(e) : e ∈ L}`` for a set of edges.

        Args:
            edge_ids: An iterable of edge IDs.
        """
        return frozenset(self._labels[e] for e in edge_ids)

    def vertices_of(self, edge_ids: Iterable[int]) -> frozenset[int]:
        """Return the union of vertex sets of the given edges.

        Args:
            edge_ids: An iterable of edge IDs.
        """
        result: set[int] = set()
        for e in edge_ids:
            result |= self._hypergraph.edges[e]
        return frozenset(result)

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StratificationInstance):
            return NotImplemented
        return (
            self._hypergraph == other._hypergraph
            and self._arc_set == other._arc_set
            and self._labels == other._labels
            and self._external_patterns == other._external_patterns
        )

    def __hash__(self) -> int:
        return hash((self._hypergraph, self._arc_set, self._labels, self._external_patterns))

    def __repr__(self) -> str:
        return (
            f"StratificationInstance("
            f"num_vertices={self.num_vertices}, "
            f"num_edges={self.num_edges}, "
            f"arcs={sorted(self._arc_set)!r}, "
            f"labels={list(self._labels)!r})"
        )
