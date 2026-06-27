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

"""Hypergraph representation."""

from collections.abc import Iterable


class Hypergraph:
    """A finite hypergraph ``H = (Q, E)``.

    Vertices are canonicalised to contiguous integers ``0, 1, ..., num_vertices - 1``.
    Edges are a multiset of non-empty subsets of the vertex set, stored in the order they are
    supplied (so edge identity is by index).

    Args:
        num_vertices: Number of vertices ``|Q|``.  Vertices are ``range(num_vertices)``.
        edges: The edge multiset.  Each element is an iterable of vertex indices; each is
            converted to a :class:`frozenset` internally.

    Raises:
        ValueError: If ``num_vertices`` is negative, if any edge is empty, or if any vertex
            index is outside ``range(num_vertices)``.
    """

    def __init__(self, num_vertices: int, edges: Iterable[Iterable[int]]) -> None:
        if num_vertices < 0:
            raise ValueError(f"num_vertices must be non-negative, got {num_vertices}")
        self._num_vertices = num_vertices

        edges_list: list[frozenset[int]] = []
        for i, raw_edge in enumerate(edges):
            e = frozenset(raw_edge)
            if not e:
                raise ValueError(f"Edge {i} is empty; all edges must be non-empty.")
            for v in e:
                if v < 0 or v >= num_vertices:
                    raise ValueError(
                        f"Edge {i} contains vertex {v}, which is outside "
                        f"range(0, {num_vertices})."
                    )
            edges_list.append(e)
        self._edges: tuple[frozenset[int], ...] = tuple(edges_list)

        # Precompute incidence lists: _incidence[v] = tuple of edge IDs containing v.
        incidence: list[list[int]] = [[] for _ in range(num_vertices)]
        for edge_id, edge in enumerate(self._edges):
            for v in edge:
                incidence[v].append(edge_id)
        self._incidence: tuple[tuple[int, ...], ...] = tuple(tuple(inc) for inc in incidence)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def num_vertices(self) -> int:
        """Number of vertices ``|Q|``."""
        return self._num_vertices

    @property
    def num_edges(self) -> int:
        """Number of edges ``|E|`` (counting multiplicity)."""
        return len(self._edges)

    @property
    def edges(self) -> tuple[frozenset[int], ...]:
        """The edge multiset as a tuple of :class:`frozenset` s, indexed by edge ID."""
        return self._edges

    @property
    def vertices(self) -> range:
        """The vertex set as ``range(num_vertices)``."""
        return range(self._num_vertices)

    # ------------------------------------------------------------------
    # Combinatorial queries
    # ------------------------------------------------------------------

    def incident(self, v: int) -> tuple[int, ...]:
        """Return the IDs of all edges that contain vertex ``v``.

        Args:
            v: A vertex index in ``range(num_vertices)``.

        Returns:
            A tuple of edge IDs (in insertion order) whose vertex sets contain ``v``.
        """
        return self._incidence[v]

    def conflict(self, e: int, e_prime: int) -> bool:
        """Return ``True`` if edges ``e`` and ``e_prime`` share at least one vertex.

        Args:
            e: An edge ID.
            e_prime: An edge ID.
        """
        return bool(self._edges[e] & self._edges[e_prime])

    def is_strong_matching(self, edge_ids: Iterable[int]) -> bool:
        """Return ``True`` if the given edges are pairwise vertex-disjoint.

        Args:
            edge_ids: An iterable of edge IDs to test.
        """
        seen: set[int] = set()
        for eid in edge_ids:
            verts = self._edges[eid]
            if seen & verts:
                return False
            seen |= verts
        return True

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self.num_edges

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hypergraph):
            return NotImplemented
        return self._num_vertices == other._num_vertices and self._edges == other._edges

    def __hash__(self) -> int:
        return hash((self._num_vertices, self._edges))

    def __repr__(self) -> str:
        edges_repr = [set(e) for e in self._edges]
        return f"Hypergraph(num_vertices={self._num_vertices}, edges={edges_repr!r})"
