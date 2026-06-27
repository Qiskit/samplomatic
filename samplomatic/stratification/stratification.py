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

"""Layer and Stratification representations."""

from collections.abc import Hashable, Iterable, Iterator

from .instance import StratificationInstance


class Layer:
    """A single layer in a stratification.

    A layer is an antichain in the partial order ``≺`` that is also a strong matching
    (pairwise vertex-disjoint set of edges).  Validity is checked on construction.

    Args:
        instance: The :class:`.StratificationInstance` this layer belongs to.
        edges: The edge IDs that form the layer.

    Raises:
        ValueError: If the edges are not pairwise incomparable in ``≺`` or not pairwise
            vertex-disjoint.
    """

    def __init__(self, instance: StratificationInstance, edges: Iterable[int]) -> None:
        self._instance = instance
        self._edges: frozenset[int] = frozenset(edges)

        if not instance.is_antichain(self._edges):
            raise ValueError(
                f"Edges {sorted(self._edges)} do not form an antichain: at least two are "
                "comparable in the partial order."
            )
        if not instance.is_strong_matching(self._edges):
            raise ValueError(
                f"Edges {sorted(self._edges)} do not form a strong matching: at least two "
                "share a vertex."
            )

        # Precompute derived values.
        self._pattern: frozenset[Hashable] = instance.pattern_of(self._edges)
        self._vertices: frozenset[int] = instance.vertices_of(self._edges)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def instance(self) -> StratificationInstance:
        """The :class:`.StratificationInstance` this layer belongs to."""
        return self._instance

    @property
    def edges(self) -> frozenset[int]:
        """The edge IDs in this layer."""
        return self._edges

    @property
    def pattern(self) -> frozenset[Hashable]:
        """The pattern ``pat(L) = {σ(e) : e ∈ L}``."""
        return self._pattern

    @property
    def vertices(self) -> frozenset[int]:
        """The union of vertex sets of all edges in this layer."""
        return self._vertices

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._edges)

    def __iter__(self) -> Iterator[int]:
        return iter(self._edges)

    def __contains__(self, edge_id: object) -> bool:
        return edge_id in self._edges

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Layer):
            return NotImplemented
        return self._instance is other._instance and self._edges == other._edges

    def __hash__(self) -> int:
        # Use identity (not value) for the instance to keep hashing cheap, since
        # StratificationInstance equality already uses value semantics on its own hash.
        return hash((id(self._instance), self._edges))

    def __repr__(self) -> str:
        return f"Layer(edges={sorted(self._edges)!r}, pattern={self._pattern!r})"


class Stratification:
    """A stratification of a :class:`.StratificationInstance`.

    A stratification is a sequence of :class:`.Layer` objects ``L_1, …, L_m`` that are
    pairwise disjoint, cover all edges ``E``, and whose order is consistent with the partial
    order ``≺``.  For every arc ``e ≺ e'`` in the instance, the layer containing ``e`` must
    appear strictly before the layer containing ``e'``.

    Two summary statistics are computed:

    - **depth** ``m = len(layers)``.
    - **unique-pattern count** ``|Λ| = |{pat(L_1), …, pat(L_m)}|``.

    Args:
        instance: The :class:`.StratificationInstance` being stratified.
        layers: The ordered sequence of layers.

    Raises:
        ValueError: If any layer belongs to a different instance, if the layers are not
            pairwise disjoint, if they do not cover all edges, or if the ordering violates
            the partial order ``≺``.
    """

    def __init__(self, instance: StratificationInstance, layers: Iterable[Layer]) -> None:
        self._instance = instance
        self._layers: tuple[Layer, ...] = tuple(layers)

        # All layers must belong to the same instance.
        for i, layer in enumerate(self._layers):
            if layer.instance is not instance:
                raise ValueError(f"Layer {i} belongs to a different StratificationInstance.")

        # Layers must be pairwise disjoint and cover all edges.
        layer_index: dict[int, int] = {}
        for k, layer in enumerate(self._layers):
            for e in layer:
                if e in layer_index:
                    raise ValueError(
                        f"Edge {e} appears in both layer {layer_index[e]} and layer {k}."
                    )
                layer_index[e] = k

        all_edges = set(range(instance.num_edges))
        covered = set(layer_index)
        if covered != all_edges:
            missing = sorted(all_edges - covered)
            raise ValueError(
                f"The stratification does not cover all edges.  Missing edge IDs: {missing}."
            )

        # Order must be ≺-consistent: for every arc (u, v) in the Hasse diagram,
        # the layer containing u must come strictly before the layer containing v.
        for u, v in instance.precedence_arcs():
            if layer_index[u] >= layer_index[v]:
                raise ValueError(
                    f"Precedence violated: edge {u} (layer {layer_index[u]}) must be placed "
                    f"strictly before edge {v} (layer {layer_index[v]})."
                )

        # Precompute derived values, merging in patterns from pre-existing boxes.
        self._patterns: frozenset[frozenset[Hashable]] = (
            frozenset(layer.pattern for layer in self._layers) | instance.external_patterns
        )

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def instance(self) -> StratificationInstance:
        """The :class:`.StratificationInstance` being stratified."""
        return self._instance

    @property
    def layers(self) -> tuple[Layer, ...]:
        """The ordered sequence of layers ``(L_1, …, L_m)``."""
        return self._layers

    @property
    def depth(self) -> int:
        """The depth ``m = len(layers)``."""
        return len(self._layers)

    @property
    def unique_pattern_count(self) -> int:
        """The unique-pattern count ``|Λ| = |{pat(L_1), …, pat(L_m)}|``."""
        return len(self._patterns)

    @property
    def patterns(self) -> frozenset[frozenset[Hashable]]:
        """The set of distinct patterns ``{pat(L_1), …, pat(L_m)} ∪ external_patterns``."""
        return self._patterns

    @property
    def key_depth_first(self) -> tuple[int, int]:
        """Comparison key ``(depth, unique_pattern_count)`` for depth-first preference."""
        return (self.depth, self.unique_pattern_count)

    @property
    def key_pattern_first(self) -> tuple[int, int]:
        """Comparison key ``(unique_pattern_count, depth)`` for pattern-first preference."""
        return (self.unique_pattern_count, self.depth)

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self.depth

    def __iter__(self) -> Iterator[Layer]:
        return iter(self._layers)

    def __getitem__(self, index: int) -> Layer:
        return self._layers[index]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stratification):
            return NotImplemented
        return self._instance is other._instance and self._layers == other._layers

    def __hash__(self) -> int:
        return hash((id(self._instance), self._layers))

    def __repr__(self) -> str:
        return (
            f"Stratification(depth={self.depth}, "
            f"unique_pattern_count={self.unique_pattern_count}, "
            f"layers={self._layers!r})"
        )
