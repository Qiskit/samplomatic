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

"""PreSamplex"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from itertools import count
from typing import TYPE_CHECKING, Any, cast

import numpy as np
from qiskit.circuit import ClassicalRegister, Qubit
from rustworkx.rustworkx import (
    PyDiGraph,
    topological_generations,
    topological_sort,
    weakly_connected_components,
)

from ..aliases import (
    CircuitInstruction,
    ClbitIndex,
    LayoutMethod,
    LayoutPresets,
    NodeIndex,
    NumSubsystems,
    OperationName,
    ParamIndices,
    ParamSpec,
    QubitIndex,
    RegisterName,
    StrRef,
)
from ..annotations import VirtualType
from ..builders.specs import InstructionMode, InstructionSpec
from ..constants import Direction
from ..distributions import Distribution, HaarU2, UniformPauli
from ..exceptions import SamplexBuildError
from ..graph_utils import (
    NodeCandidate,
    find_unreachable_nodes,
    replace_edges_with_one_edge,
    replace_nodes_with_one_node,
)
from ..partition import QubitIndicesPartition, QubitPartition, SubsystemIndicesPartition
from ..samplex import Samplex
from ..samplex.nodes import (
    BasisTransformNode,
    CollectTemplateValues,
    CollectZ2ToOutputNode,
    CombineRegistersNode,
    InjectNoiseNode,
    LeftMultiplicationNode,
    LeftU2ParametricMultiplicationNode,
    PauliPastCliffordNode,
    RightMultiplicationNode,
    RightU2ParametricMultiplicationNode,
    SliceRegisterNode,
    TwirlSamplingNode,
)
from ..samplex.nodes.basis_transform_node import MEAS_PAULI_BASIS, PREP_PAULI_BASIS
from ..samplex.nodes.pauli_past_clifford_node import (
    PAULI_PAST_CLIFFORD_INVARIANTS,
    PAULI_PAST_CLIFFORD_LOOKUP_TABLES,
)
from ..samplex.noise_model_requirement import NoiseModelRequirement
from ..synths import Synth
from ..tensor_interface import TensorSpecification
from ..virtual_registers import U2Register
from ..visualization import plot_graph
from .graph_data import (
    PreBasisTransform,
    PreCollect,
    PreEdge,
    PreEmit,
    PreInjectNoise,
    PreNode,
    PrePropagate,
    PrePropagateKey,
    PreZ2Collect,
)
from .utils import merge_pre_edges

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

NO_PROPAGATE: frozenset[OperationName] = frozenset(["barrier", "delay", "id"])

REG_TO_DISTRIBUTION: dict[VirtualType, type[Distribution]] = {
    VirtualType.U2: HaarU2,
    VirtualType.PAULI: UniformPauli,
}


class DanglerType(Enum):
    """A helper Enum to indicate the type of danglers."""

    REQUIRED = auto()
    OPTIONAL = auto()


@dataclass
class DanglerMatch:
    """A helper class to specify conditions on danglers."""

    direction: Direction | None = None
    """The desired direction of the node.

    Set to `None` to get all node directions. Note that setting to `BOTH` will only match nodes
    with `BOTH` direction."""

    node_types: tuple[type[PreNode], ...] | None = None
    """The desired type of the node.

    Set to `None` to get all node types."""

    dangler_type: DanglerType | None = None
    """The desired type of dangler.

    Set to `None` to get both required and optional danglers."""

    def match_node(self, node: PreNode) -> bool:
        """Check if a node matches the conditions specified in the object"""
        return (self.direction is None or node.direction in (self.direction, Direction.BOTH)) and (
            self.node_types is None or isinstance(node, self.node_types)
        )


class PreSamplex:
    """The sampling IR between a boxed-up circuit and a :class:`~.Samplex`.

    In this IR, as in the lower :class:`~.Samplex`, sampling operations are described as a graph.
    Operations describe actions like sampling from distributions and propagating virtual gates
    past other gates. However, unlike the lower IR, this IR still maintains the notion of qubit
    indices, and operations are still declarative rather than procudural.

    Args:
        graph: The graph being built.
        qubit_map: A map from qubits in the source circuit to physical qubit indices.
        dangling: A map from qubit indices to sets of node indices that are still eligible to,
            and must, receive edges at a further point in parsing the circuit being built.
        optional_dangling: A map from qubit indices to sets of node indices that are still
            eligible to, but don't have to, receive edges at a further point in parsing the
            circuit being built.
        cregs: A list of classical registers in the order that they were added to the circuit.
        noise_map_count: A count of the total number of noise maps.
        noise_maps: A map from unique identifiers of noise maps to the number of systems the map
            acts on.
        basis_transforms: A map from unique identifiers of basis transforms to the number of
            subsystems in that basis transform.
        twirled_clbits: A set of all classical bit indices which were previously twirled in the
            circuit.
        passthrough_params: List of :class:`~.ParamSpec` for parameters which exist in the template
            but are not generated in the collectors.
        forced_copy_node_idxs: List of node indices for which copying of registers will be forced.
            The nodes behave differently for edges with left/right direction. For left direction,
            the incoming node is checked against `forced_copy_node_idxs`, while for right direction,
            the outgoing node is.
    """

    def __init__(
        self,
        graph: PyDiGraph[PreNode, PreEdge] | None = None,
        qubit_map: dict[Qubit, QubitIndex] | None = None,
        dangling: dict[QubitIndex, set[NodeIndex]] | None = None,
        optional_dangling: dict[QubitIndex, set[NodeIndex]] | None = None,
        cregs: list[ClassicalRegister] | None = None,
        noise_map_count: count | None = None,
        noise_maps: dict[str, NumSubsystems] | None = None,
        noise_modifiers: dict[str, set[str]] | None = None,
        basis_transforms: dict[str, int] | None = None,
        twirled_clbits: set[ClbitIndex] | None = None,
        passthrough_params: ParamSpec | None = None,
        forced_copy_node_idxs: set[NodeIndex] | None = None,
    ):
        self.graph = PyDiGraph[PreNode, PreEdge](multigraph=True) if graph is None else graph
        self.qubit_map: dict[Qubit, QubitIndex] = {} if qubit_map is None else qubit_map
        self._dangling: dict[QubitIndex, set[NodeIndex]] = (
            defaultdict(set) if dangling is None else dangling
        )
        self._optional_dangling: dict[QubitIndex, set[NodeIndex]] = (
            defaultdict(set) if optional_dangling is None else optional_dangling
        )
        self._cregs = cregs
        self._noise_map_count = count() if noise_map_count is None else noise_map_count
        self._noise_maps = {} if noise_maps is None else noise_maps
        self._noise_modifiers = defaultdict(set) if noise_modifiers is None else noise_modifiers
        self._basis_transforms = {} if basis_transforms is None else basis_transforms
        self._twirled_clbits = set() if twirled_clbits is None else twirled_clbits
        self.passthrough_params: ParamSpec = (
            [] if passthrough_params is None else passthrough_params
        )
        self._forced_copy_node_idxs: set[NodeIndex] = (
            set() if forced_copy_node_idxs is None else forced_copy_node_idxs
        )

    def remap(self, qubit_map: dict[Qubit, QubitIndex]) -> PreSamplex:
        """Remap the object to a new :class:`~.PreSamplex` object.

        Args:
            qubit_map: A new map from qubits in the source circuit to physical qubit indices.

        Returns:
            A :class:`~.PreSamplex` object which is identical, except for `qubit_map`.
        """
        return PreSamplex(
            self.graph,
            qubit_map,
            self._dangling,
            self._optional_dangling,
            self._cregs,
            self._noise_map_count,
            self._noise_maps,
            self._noise_modifiers,
            self._basis_transforms,
            self._twirled_clbits,
            self.passthrough_params,
            self._forced_copy_node_idxs,
        )

    def find_danglers(
        self,
        match: DanglerMatch,
        subsystems: QubitIndicesPartition,
    ) -> Iterator[tuple[NodeIndex, QubitIndicesPartition]]:
        """Look through the dangling nodes and yield matches overlapping on ``subsystems``.

        .. note::
           The ``match`` function is only called on those nodes that overlap the given subsystems.

        Args:
            match: A :class:`~.DanglerMatch` object specifying the conditions on the danglers.
            subsystems: Subsystems of the virtual registers we are interested in.

        Yields:
            Pairs ``node_idx, intersecting_subsystems`` representing a matching node along with
            the subsystems on which it overlaps with the provided subsystems.
        """
        # first loop through and find out which qubits each matching node is involved with
        # the visited set is used only so that we only need to call the match function once per node
        visited_node_idxs: set[NodeIndex] = set()
        matches: dict[NodeIndex, set[QubitIndex]] = {}
        for qubit_idx in subsystems.all_elements:
            dangling = set()
            if match.dangler_type in {None, DanglerType.REQUIRED}:
                dangling |= self._dangling[qubit_idx]
            if match.dangler_type in {None, DanglerType.OPTIONAL}:
                dangling |= self._optional_dangling[qubit_idx]
            for node_idx in dangling:
                if node_idx not in visited_node_idxs:
                    visited_node_idxs.add(node_idx)
                    if match.match_node(self.graph[node_idx]):
                        matches[node_idx] = {qubit_idx}
                elif node_idx in matches:
                    matches[node_idx].add(qubit_idx)

        # now that know everybody involved, we can compute intersections and return
        for node_idx, relevant_qubit_idxs in matches.items():
            node = self.graph[node_idx]
            intersection = subsystems.restrict(relevant_qubit_idxs).intersection(node.subsystems)
            yield node_idx, intersection

    def add_dangler(
        self,
        qubit_idxs: Iterable[QubitIndex],
        node_idx: NodeIndex,
        dangler_type: DanglerType = DanglerType.REQUIRED,
    ):
        """Mark a node as dangling.

        A dangling node is one that is eligible to be connected to subsequently added nodes.

        Args:
            qubit_idxs: The qubits on which the node is dangling.
            node_idx: The index of the node within the pre-samplex graph.
            dangler_type: Specifies the behavior of the dangler.

        Raises:
            SamplexBuildError: If the dangler type is invalid.
        """
        if dangler_type == DanglerType.REQUIRED:
            for qubit in qubit_idxs:
                self._dangling[qubit].add(node_idx)
        elif dangler_type == DanglerType.OPTIONAL:
            for qubit in qubit_idxs:
                self._optional_dangling[qubit].add(node_idx)
        else:
            raise SamplexBuildError("When adding a dangler, type has to be REQUIRED or OPTIONAL")

    def find_then_remove_danglers(
        self,
        match: DanglerMatch,
        subsystems: QubitIndicesPartition,
    ) -> Iterator[tuple[NodeIndex, QubitIndicesPartition]]:
        """Extend :meth:`~.find_danglers` to also remove dangling nodes.

        .. note::
           Nodes are removed only after all of them have been yielded.

        Args:
            match: A :class:`~.DanglerMatch` object specifying the conditions on the danglers.
            subsystems: Subsystems of the virtual registers we are interested in.

        Yields:
            Pairs ``node_idx, intersecting_subsystems`` representing a matching node along with
            the subsystems on which it overlaps with the provided subsystems.
        """
        if match.dangler_type in {None, DanglerType.REQUIRED}:
            to_remove = {}
            for found_idx, found_subsystems in self.find_danglers(match, subsystems):
                to_remove[found_idx] = found_subsystems
                yield found_idx, found_subsystems

            for found_idx, found_subsystems in to_remove.items():
                for qubit_idx in found_subsystems.all_elements:
                    self._dangling[qubit_idx].discard(found_idx)

        if match.dangler_type in {None, DanglerType.OPTIONAL}:
            to_remove = {}
            for found_idx, found_subsystems in self.find_danglers(match, subsystems):
                to_remove[found_idx] = found_subsystems
                yield found_idx, found_subsystems

            for found_idx, found_subsystems in to_remove.items():
                for qubit_idx in found_subsystems.all_elements:
                    self._optional_dangling[qubit_idx].discard(found_idx)

    def enforce_no_propagation(self, instr: CircuitInstruction):
        """Make sure the instruction doesn't participate in virtual gate propagation.

        We check to see if there are left-to-right danglers, and error if they exist.
        We remove right-to-left danglers, which will cause an error later when an emission
        can't reach a collection on its left.

        Args:
            instr: The circuit instruction that can't be propagated through.

        Raises:
            SamplexBuildError: If `instr` involves active left-to-right danglers.
        """
        # in the future when we have multi-qubit virtual groups, this can't be hard-coded to 1
        subsystems = QubitIndicesPartition(1, [(self.qubit_map[qubit],) for qubit in instr.qubits])

        match = DanglerMatch(node_types=(PreEmit, PrePropagate), direction=Direction.RIGHT)
        if any(True for _ in self.find_danglers(match, subsystems)):
            raise SamplexBuildError(f"Cannot propagate through {instr.operation.name} instruction.")
        match = DanglerMatch(direction=Direction.LEFT)
        all(self.find_then_remove_danglers(match, subsystems))

    def get_all_danglers(
        self,
    ) -> tuple[dict[QubitIndex, set[NodeIndex]], dict[QubitIndex, set[NodeIndex]]]:
        """Return the danglers information"""
        return (self._dangling, self._optional_dangling)

    def set_all_danglers(
        self,
        dangling: dict[QubitIndex, set[NodeIndex]],
        optional_dangling: dict[QubitIndex, set[NodeIndex]],
    ):
        """Set the danglers information in place"""
        self._dangling.clear()
        self._dangling.update(dangling)
        self._optional_dangling.clear()
        self._optional_dangling.update(optional_dangling)

    def _filter_nodes(
        self, node_idxs: Iterable[NodeIndex], node_type: type[PreNode]
    ) -> Iterator[tuple[NodeIndex, PreNode]]:
        """Yield the nodes of type `node_type` from those in `node_idxs`."""
        for node_idx in node_idxs:
            if isinstance((node := self.graph[node_idx]), node_type):
                yield node_idx, node

    def qubits_to_indices(self, qubits: QubitPartition) -> QubitIndicesPartition:
        """Convert uniform subsystems on qubits to uniform subsystems on qubit indices."""
        return QubitIndicesPartition(
            qubits.num_elements_per_part, [tuple(self.qubit_map[q] for q in sys) for sys in qubits]
        )

    def add_force_copy_nodes(self, node_idxs: Iterable[NodeIndex]):
        """Add node indices for which a register will be forced to copy."""
        self._forced_copy_node_idxs.update(node_idxs)

    def remove_force_copy_nodes(self, node_idxs: Iterable[NodeIndex]):
        """Remove node indices for which a register will be forced to copy."""
        self._forced_copy_node_idxs.difference_update(node_idxs)

    def add_collect(
        self,
        qubits: QubitPartition,
        synth: Synth,
        param_idxs: ParamIndices,
        node_idx: NodeIndex | None = None,
    ):
        """Add or extend a node to collect virtual gates of types allowed by the ``synth``.

        If ``node_idx`` is None, a new node is added. If ``node_idx`` is provided, the
        :class:`~.PreCollect` node at that index will be extended to include the given
        qubits. Note that the function does not verify the compatibility of the node at
        ``node_idx`` - it is assumed that it's type is appropriate, and that the ``synth``
        is the same.

        Args:
            qubits: The qubits to collect virtual gates on.
            synth: The synthesizer to generate gate parameters.
            param_idxs: The indices of the parameters in the corresponding template.
            node_idx: The index of the node to be extended to include the provided qubits.

        Returns:
            The index of the new node in the graph.
        """
        subsystems = self.qubits_to_indices(qubits)
        if node_idx is not None:
            self.graph[node_idx].add_subsystems(subsystems, param_idxs)
        else:
            node_idx = self.graph.add_node(
                PreCollect(subsystems, Direction.BOTH, synth, param_idxs)
            )

        # collect any nodes that need collecting and unmark them as dangling
        match = DanglerMatch(node_types=(PreEmit, PrePropagate), direction=Direction.RIGHT)
        for found_idx, found_subsystems in self.find_then_remove_danglers(match, subsystems):
            if self.graph.has_edge(found_idx, node_idx):
                # The force_register_copy stays the same and doesn't need update.
                self.graph.get_edge_data(found_idx, node_idx).add_subsystems(found_subsystems)
            else:
                self.graph.add_edge(
                    found_idx,
                    node_idx,
                    PreEdge(
                        found_subsystems, Direction.RIGHT, found_idx in self._forced_copy_node_idxs
                    ),
                )

        # prevent dangling pre-propagate left nodes from catching any further action because
        # this collection is in the way
        all(
            self.find_then_remove_danglers(
                DanglerMatch(node_types=(PreCollect, PrePropagate)), subsystems
            )
        )

        # mark the new node as dangling
        self.add_dangler(subsystems.all_elements, node_idx)

        return node_idx

    def add_z2_collect(self, qubits: QubitPartition, clbit_idxs: Sequence[ClbitIndex]) -> int:
        """Add a node to collect virtual gates to Z2 output.

        Args:
            qubits: The qubits to collect virtual gates on.
            clbit_idxs: The indices of the clbits measured to (in the same order as qubits).

        Raises:
            SamplexBuildError if number of qubits doesn't match number of clbits
            SamplexBuildError if not all measured qubits receive emissions
        Returns:
            The index of the new node in the graph.
        """
        if len(qubits) != len(clbit_idxs):
            raise SamplexBuildError("Number of qubits != number of clbits.")
        if len(self._twirled_clbits.intersection(clbit_idxs)) != 0:
            raise SamplexBuildError(
                "Cannot twirl more than one measurement on the same classical bit"
            )
        self._twirled_clbits.update(clbit_idxs)
        subsystems = self.qubits_to_indices(qubits)

        clbit_dict = defaultdict(list)
        subsystems_dict = defaultdict(list)
        for idx, clbit_idx in enumerate(clbit_idxs):
            val = 0
            for reg in self._cregs:
                if clbit_idx < val + len(reg):
                    clbit_dict[reg.name].append(clbit_idx - val)
                    subsystems_dict[reg.name].append(idx)
                    break
                val += len(reg)

        node_idx = self.graph.add_node(PreZ2Collect(subsystems, clbit_dict, subsystems_dict))

        collected_subsystems = QubitIndicesPartition(1, [])
        # Collect relevant nodes which are an optional dangler, and leave them optionally dangling
        # This needs to happen first, so the new optional danglers created later won't be counted.
        match = DanglerMatch(
            node_types=(PreEmit, PrePropagate),
            direction=Direction.RIGHT,
            dangler_type=DanglerType.OPTIONAL,
        )
        for found_idx, found_subsystems in self.find_danglers(match, subsystems):
            self.graph.add_edge(found_idx, node_idx, PreEdge(found_subsystems, Direction.RIGHT))
            for subsystem in found_subsystems.all_elements:
                collected_subsystems.add((subsystem,))

        # Collect every relevant node which is a required dangler,
        # then convert it to an optional dangler.
        match = DanglerMatch(
            node_types=(PreEmit, PrePropagate),
            direction=Direction.RIGHT,
            dangler_type=DanglerType.REQUIRED,
        )
        for found_idx, found_subsystems in self.find_then_remove_danglers(match, subsystems):
            self.graph.add_edge(found_idx, node_idx, PreEdge(found_subsystems, Direction.RIGHT))
            for subsystem in found_subsystems.all_elements:
                collected_subsystems.add((subsystem,))
            self.add_dangler(found_subsystems.all_elements, found_idx, DanglerType.OPTIONAL)

        # Remove previous Pre-Collects from the danglers. They can no longer be reached,
        # because the measurement blocks the way.
        match = DanglerMatch(node_types=(PreCollect,), direction=Direction.RIGHT)
        all(self.find_then_remove_danglers(match, subsystems))

        # Verify that all measurements were reached by an emission
        if len(subsystems) != len(collected_subsystems.intersection(subsystems)):
            raise SamplexBuildError(
                f"Can not add PreZ2Collect on qubits {qubits}, as some qubits are missing "
                "corresponding emissions."
            )

        return node_idx

    def add_emit_twirl(self, qubits: QubitPartition, register_type: VirtualType) -> NodeIndex:
        """Add a node that emits virtual gates left and right of the same type.

        Args:
            qubits: The qubits to emit virtual gates on.
            register_type: The type of virtual gate to emit.

        Raises:
            SamplexBuildError: When `qubits` has overlap with a hanging emit node with a different
                virtual gate type.
            SamplexBuildError: When any of the elements of `qubits` is not dangling.

        Returns:
            The index of the new node in the graph.
        """
        subsystems = self.qubits_to_indices(qubits)
        node_idx = self.graph.add_node(PreEmit(subsystems, Direction.BOTH, register_type))

        # find collectors (or propagators leading to collectors) for right-to-left emission and
        # connect this emmision there. we do NOT want to remove them as dangling because they
        # might need to be used again for future emissions, for example, a Pauli twirl followed by
        # a noise injection.
        match = DanglerMatch(node_types=(PreCollect, PrePropagate), direction=Direction.LEFT)

        aggregate_found_subsystems = set()
        for found_idx, found_subsystems in self.find_danglers(match, subsystems):
            aggregate_found_subsystems.update(found_subsystems)
            self.graph.add_edge(
                node_idx,
                found_idx,
                PreEdge(found_subsystems, Direction.LEFT, found_idx in self._forced_copy_node_idxs),
            )

        if aggregate_found_subsystems != set(subsystems):
            without_collector = set(subsystems).difference(aggregate_found_subsystems)
            raise SamplexBuildError(
                f"Found an emission without a collector on subsystems {without_collector}."
            )

        # mark the new node as dangling
        self.add_dangler(subsystems.all_elements, node_idx)

        return node_idx

    def _add_emit_left(self, node: PreEmit):
        """Add a pre-emit with `Direction.LEFT`.

        This method adds edges to any node that is dangling with overlapping subsystems.
        """
        node_idx = self.graph.add_node(node)
        match = DanglerMatch(node_types=(PreCollect, PrePropagate), direction=Direction.LEFT)
        for found_idx, found_subsystems in self.find_danglers(match, node.subsystems):
            self.graph.add_edge(node_idx, found_idx, PreEdge(found_subsystems, Direction.LEFT))

        return node_idx

    def _add_emit_right(self, node: PreEmit):
        """Add a pre-emit with `Direction.RIGHT`.

        This method sets the pre-emit as dangling.
        """
        node_idx = self.graph.add_node(node)
        self.add_dangler(node.subsystems.all_elements, node_idx)

        return node_idx

    def add_emit_noise_left(
        self, qubits: QubitPartition, noise_ref: StrRef, modifier_ref: StrRef = ""
    ) -> NodeIndex:
        """Add a node that emits virtual gates for noise injection to the left.

        Args:
            qubits: The qubits to emit virtual gates on.
            noise_ref: Unique identifier of the noise to inject.
            modifier_ref: Unique identifier for modifiers to apply to this noise map.

        Raises:
            SamplexBuildError: If a noise map with the same `noise_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._noise_maps.get(noise_ref)) and num_subsys != len(qubits):
            raise SamplexBuildError(
                f"Cannot add noise map `{noise_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._noise_maps[noise_ref] = len(qubits)

        if modifier_ref:
            self._noise_modifiers[noise_ref].add(modifier_ref)

        subsystems = self.qubits_to_indices(qubits)
        node = PreInjectNoise(
            subsystems,
            Direction.LEFT,
            VirtualType.PAULI,
            noise_ref,
            modifier_ref,
            next(self._noise_map_count),
        )
        return self._add_emit_left(node)

    def add_emit_noise_right(
        self, qubits: QubitPartition, noise_ref: StrRef, modifier_ref: StrRef = ""
    ) -> NodeIndex:
        """Add a node that emits virtual gates for noise injection to the right.

        Args:
            qubits: The qubits to emit virtual gates on.
            noise_ref: Unique identifier of the noise to inject.
            modifier_ref: Unique identifier for modifiers to apply to this noise map.

        Raises:
            SamplexBuildError: If a noise map with the same `noise_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._noise_maps.get(noise_ref)) and (num_subsys) != len(qubits):
            raise SamplexBuildError(
                f"Cannot add noise map `{noise_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._noise_maps[noise_ref] = len(qubits)

        if modifier_ref:
            self._noise_modifiers[noise_ref].add(modifier_ref)

        subsystems = self.qubits_to_indices(qubits)
        node = PreInjectNoise(
            subsystems,
            Direction.LEFT,
            VirtualType.PAULI,
            noise_ref,
            modifier_ref,
            next(self._noise_map_count),
        )
        return self._add_emit_right(node)

    def add_emit_meas_basis_transform(self, qubits: QubitPartition, basis_ref: StrRef) -> NodeIndex:
        """Add a node that emits virtual gates left to measure in a basis.

        Args:
            qubits: The qubits to emit virtual gates on.
            basis_ref: Unique identifier of this basis transform.

        Raises:
            SamplexBuildError: If a basis transform with the same `basis_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._basis_transforms.get(basis_ref)) and num_subsys != len(qubits):
            raise SamplexBuildError(
                f"Cannot add basis transform `{basis_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._basis_transforms[basis_ref] = len(qubits)

        subsystems = self.qubits_to_indices(qubits)
        node = PreBasisTransform(subsystems, Direction.LEFT, VirtualType.U2, basis_ref)
        return self._add_emit_left(node)

    def add_emit_prep_basis_transform(self, qubits: QubitPartition, basis_ref: StrRef) -> NodeIndex:
        """Add a node that emits virtual gates right to prepare a basis.

        Args:
            qubits: The qubits to emit virtual gates on.
            basis_ref: Unique identifier of this basis transformation.

        Raises:
            SamplexBuildError: If a basis transform with the same `basis_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._basis_transforms.get(basis_ref)) and num_subsys != len(qubits):
            raise SamplexBuildError(
                f"Cannot add basis transform `{basis_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._basis_transforms[basis_ref] = len(qubits)

        subsystems = self.qubits_to_indices(qubits)
        node = PreBasisTransform(subsystems, Direction.RIGHT, VirtualType.U2, basis_ref)
        return self._add_emit_right(node)

    def add_propagate(self, instr: CircuitInstruction, spec: InstructionSpec):
        """Add a node that propagates virtual gates through an operation.

        This method deduces which direction to propagate virtual gates by inspecting the previous
        nodes on the dangling qubits that overlap with the instruction's qubits.

        Args:
            instr: The circuit instruction to propagate through.
            spec: The specification for how to propagate with the instruction.

        Raises:
            SamplexBuildError: If the qubits of ``instr`` have partial overlap with dangling qubits
                of the pre-samplex.

        Returns:
            The index of the new node in the graph.
        """
        op = instr.operation
        if op.name in NO_PROPAGATE:
            return

        # in the future when we have multi-qubit virtual groups, this can't be hard-coded to 1
        subsystems = QubitIndicesPartition(1, [(self.qubit_map[qubit],) for qubit in instr.qubits])

        if op.name.startswith("meas"):
            self.enforce_no_propagation(instr)
            return

        # Track passthrough parameters (even if no node is created)
        # These parameters appear in the template (InstructionMode.PROPAGATE) and must
        # be accounted for during sampling, even though they might not take part in
        # virtual gate propagation.
        if spec.mode == InstructionMode.PROPAGATE and spec.params is not None:
            self.passthrough_params.extend(spec.params)

        # recall that this is indexing out of `subsystems`, not qubits
        num_qubits = instr.operation.num_qubits
        partition = SubsystemIndicesPartition(num_qubits, [tuple(range(num_qubits))])

        # time ordering: (emit> | propagate>) --> new propagate>
        rightward_node_candidate = NodeCandidate(
            self.graph, PrePropagate(subsystems, Direction.RIGHT, op, partition, spec)
        )
        match = DanglerMatch(node_types=(PreEmit, PrePropagate), direction=Direction.RIGHT)
        all_found_qubit_idxs = set()
        for found_idx, found_subsystems in self.find_then_remove_danglers(match, subsystems):
            all_found_qubit_idxs.update(found_subsystems.all_elements)
            edge = PreEdge(
                found_subsystems, Direction.RIGHT, found_idx in self._forced_copy_node_idxs
            )
            # if the node candidate hasn't been added to the graph yet, it will be here:
            self.graph.add_edge(found_idx, rightward_node_candidate.node_idx, edge)

        if all_found_qubit_idxs and subsystems.all_elements != all_found_qubit_idxs:
            raise SamplexBuildError(
                f"Cannot propagate '{op.name}' on {subsystems} that overlaps partially with "
                "existing left-to-right virtual. Did you forget to add emission on qubit indices "
                f"{all_found_qubit_idxs.intersection(subsystems.all_elements)}?"
            )

        # time ordering: (collect< | propagate<) <-- new propagate<
        leftward_node_candidate = NodeCandidate(
            self.graph, PrePropagate(subsystems, Direction.LEFT, op, partition, spec)
        )
        all_found_qubit_idxs = set()
        match = DanglerMatch(node_types=(PreCollect, PrePropagate), direction=Direction.LEFT)
        for found_idx, found_subsystems in self.find_then_remove_danglers(match, subsystems):
            all_found_qubit_idxs.update(found_subsystems.all_elements)
            edge = PreEdge(
                found_subsystems, Direction.LEFT, found_idx in self._forced_copy_node_idxs
            )
            # if the node candidate hasn't been added to the graph yet, it will be here:
            self.graph.add_edge(leftward_node_candidate.node_idx, found_idx, edge)

        if all_found_qubit_idxs and subsystems.all_elements != all_found_qubit_idxs:
            raise SamplexBuildError(
                f"Cannot propagate '{op.name}' on {subsystems} that overlaps partially with the "
                "existing collectors on its left. Did you forget to add collectors on qubit "
                f"indices {all_found_qubit_idxs.intersection(subsystems.all_elements)}?"
            )

        # mark the new nodes as dangling
        if rightward_node_candidate.is_added:
            self.add_dangler(subsystems.all_elements, rightward_node_candidate.node_idx)
        if leftward_node_candidate.is_added:
            self.add_dangler(subsystems.all_elements, leftward_node_candidate.node_idx)

    def merge_parallel_pre_propagate_nodes(self):
        """Merge parallel pre-propagate nodes acting on disjoint subsystems with the same operation.

        .. note ::
            Given a list of topological generations of the nodes in a graph, a gate acting in
            parallel on :math:`N` disjoint subsystems appears as :math:`N` pre-propagate nodes that
            are part of the same generation, and have identical directions and operation names, and
            have predecessors in common.
        """
        for generation in topological_generations(self.graph):
            for node_idxs in self._cluster_pre_propagate_nodes(generation):
                if len(node_idxs) == 1:
                    # Nothing to merge
                    continue

                nodes = [self.graph[node_idx] for node_idx in node_idxs]

                combined_subsystems = QubitIndicesPartition.union(
                    *(node.subsystems for node in nodes)
                )

                num_elements = nodes[0].partition.num_elements_per_part
                num_parts = len(combined_subsystems) // num_elements
                combined_partition = SubsystemIndicesPartition(
                    num_elements,
                    [
                        tuple(range(i * num_elements, (i + 1) * num_elements))
                        for i in range(num_parts)
                    ],
                )

                params = [param for node in nodes for param in node.spec.params]

                # This merges the node but not the edges
                new_node_idx = replace_nodes_with_one_node(
                    self.graph,
                    node_idxs,
                    PrePropagate(
                        combined_subsystems,
                        self.graph[node_idxs[0]].direction,  # all nodes have same direction
                        self.graph[node_idxs[0]].operation,  # all nodes have same operation
                        combined_partition,
                        InstructionSpec(params=params, mode=nodes[0].spec.mode),
                    ),
                )

                for successor_idx in set(self.graph.successor_indices(new_node_idx)):
                    new_edge = merge_pre_edges(self.graph, new_node_idx, successor_idx)
                    replace_edges_with_one_edge(self.graph, new_node_idx, successor_idx, new_edge)

                for predecessor_idx in set(self.graph.predecessor_indices(new_node_idx)):
                    new_edge = merge_pre_edges(self.graph, predecessor_idx, new_node_idx)
                    replace_edges_with_one_edge(self.graph, predecessor_idx, new_node_idx, new_edge)

    def _cluster_pre_propagate_nodes(self, generation: list[NodeIndex]) -> list[list[NodeIndex]]:
        """Cluster ``PrePropagate`` nodes within a topological generation."""
        clusters: dict[PrePropagateKey, list[dict[str, Any]]] = defaultdict(list)

        for node_idx in generation:
            node = self.graph[node_idx]
            if isinstance(node, PrePropagate):
                cluster_type_key = PrePropagateKey(
                    mode=node.spec.mode,
                    operation_name=node.operation.name,
                    direction=node.direction,
                )
                for cluster in clusters[cluster_type_key]:
                    if not cluster["subsystems"].overlaps_with(
                        node.subsystems.all_elements
                    ) and not cluster["predecessors"].isdisjoint(
                        self.graph.predecessor_indices(node_idx)
                    ):
                        # Add to existing cluster
                        cluster["nodes"].append(node_idx)
                        for subsystem in node.subsystems:
                            cluster["subsystems"].add(subsystem)
                        cluster["predecessors"].update(self.graph.predecessor_indices(node_idx))
                        break
                else:
                    clusters[cluster_type_key].append(
                        {
                            "nodes": [node_idx],
                            "subsystems": QubitIndicesPartition.from_elements(
                                node.subsystems.all_elements
                            ),
                            "predecessors": set(self.graph.predecessor_indices(node_idx)),
                        }
                    )

        return [cluster["nodes"] for cluster_type in clusters.values() for cluster in cluster_type]

    def sorted_predecessor_idxs(
        self, pre_node_idx: NodeIndex, order: dict[NodeIndex, int]
    ) -> list[NodeIndex]:
        """Return the predecessors of a node in edge-sorted order.

        Edge-sorted order
         * places all nodes connected by :class:`~.Direction.LEFT` edges before
           :class:`~.Direction.RIGHT` edges, and
         * the :class:`~.Direction.LEFT` edges connected to twirl emissions before other emissions,
            * the twirl emissions sorted according to reverse ``order``,
            * the others according to ``order``,
         * while the :class:`~.Direction.RIGHT` place twirl emissions after other emissions, both
           individually sorted according to ``order``.

        This order scheme is designed so that it corresponds to circuit-temporal precedence of
        predecessors. For example, a pre-collector will have inbound edges marked both left and
        right. We need to know in which order to multiply them together. This method is that order.

        Args:
            pre_node_idx: The pre-node to get the predecessors of.
            order: A dictionary specifying an integer for at least the predecessors of
                ``pre_node_idx``. These integers are referenced in the second two bullets above.

        Returns:
            The predecessors of ``pre_node_idx`` in edge-sorted order.
        """
        edge_sort_keys = {}
        for pred_idx in self.graph.predecessor_indices(pre_node_idx):
            direction = self.graph.get_edge_data(pred_idx, pre_node_idx).direction
            from_twirl = type(self.graph.get_node_data(pred_idx)) is PreEmit
            pred_order = order[pred_idx]
            if direction is Direction.LEFT:
                pred_order = -pred_order if from_twirl else pred_order
                from_twirl = not from_twirl
            edge_sort_keys[pred_idx] = (direction, from_twirl, pred_order)

        return sorted(edge_sort_keys.keys(), key=lambda x: edge_sort_keys[x])

    def prune_prenodes_unreachable_from_emission(self):
        """Prune all pre-nodes that are unreachable from pre-emit nodes."""
        emission_nodes = self.graph.filter_nodes(lambda node: isinstance(node, PreEmit))
        unreachable = find_unreachable_nodes(self.graph, emission_nodes)

        self.graph.remove_nodes_from(unreachable)

    def validate_no_rightward_danglers(self):
        """Validate that there are no nodes that require termination but are still dangling.

        Optional danglers are ignored.

        Raises:
            SamplexBuildError: If any nodes are expecting collections.
        """
        match = DanglerMatch(node_types=(PreEmit, PrePropagate), direction=Direction.RIGHT)
        uncollected_qubit_idxs = set()
        for qubit_idx, node_idxs in self._dangling.items():
            for node_idx in node_idxs:
                if node_idx not in uncollected_qubit_idxs and match.match_node(
                    self.graph[node_idx]
                ):
                    uncollected_qubit_idxs.add(qubit_idx)
                    break

        if uncollected_qubit_idxs:
            raise SamplexBuildError(
                "There are unterminated virtual gates travelling to the right on qubit indices "
                f"{sorted(uncollected_qubit_idxs)}. Did you forget to add collectors?"
            )

    def verify_no_twirled_clbits(self, clbits: list[ClbitIndex]):
        """Verify the given classical bits are not twirled, for classical conditions validation.

        Args:
            clbits: list of classical bits indices.

        Raises:
            SamplexBuildError: if any classical bit is twirled.
        """
        if self._twirled_clbits.intersection(clbits):
            raise SamplexBuildError(
                "Cannot use twirled classical bits in classical conditions. "
                f"The condition depends on bits {clbits}, at leaset one of which is twirled."
            )

    @property
    def max_param_idx(self) -> int | None:
        """The maximum template parameter index over all nodes."""
        max_value = None
        for node in self.graph.nodes():
            if isinstance(node, PreCollect) and node.param_idxs.size:
                max_value = max(max_value or 0, node.param_idxs.max())
            elif isinstance(node, PrePropagate) and node.spec.params:
                max_value = max(max_value or 0, max(idx or 0 for idx, _ in node.spec.params))
        return max_value

    def finalize(self):
        """Finalize the pre-samplex.

        Raises:
            SamplexBuildError: If there are any emission nodes that are not collected.
        """
        # Validation
        self.validate_no_rightward_danglers()

        # Optmization
        self.prune_prenodes_unreachable_from_emission()
        self.merge_parallel_pre_propagate_nodes()

        samplex = Samplex()

        # This is needed because we need to know the parent/child relationships between
        # prenodes to figure out the parent/child relationship between nodes
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex] = {}

        # A map from pre-node indices to integers representing their position in a topological
        # sort of the pre-samplex graph
        order: dict[NodeIndex, int] = {}

        # A map such that ``register_names[a][b]`` is the name of the register implied by
        # the edge (a, b) in the pre-samplex graph
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]] = defaultdict(dict)

        for topological_idx, pre_node_idx in enumerate(topological_sort(self.graph)):
            pre_node = self.graph[pre_node_idx]
            order[pre_node_idx] = topological_idx
            if isinstance(pre_node, PreBasisTransform):
                self.add_basis_transform_node(
                    samplex, pre_node_idx, pre_nodes_to_nodes, order, register_names
                )
            elif isinstance(pre_node, PreInjectNoise):
                self.add_inject_noise_node(
                    samplex, pre_node_idx, pre_nodes_to_nodes, order, register_names
                )
            elif isinstance(pre_node, PreEmit):
                self.add_twirl_sampling_node(
                    samplex, pre_node_idx, pre_nodes_to_nodes, order, register_names
                )
            elif isinstance(pre_node, PrePropagate):
                self.add_propagate_node(
                    samplex, pre_node_idx, pre_nodes_to_nodes, order, register_names
                )
            elif isinstance(pre_node, PreCollect):
                self.add_collect_node(
                    samplex, pre_node_idx, pre_nodes_to_nodes, order, register_names
                )
            elif isinstance(pre_node, PreZ2Collect):
                self.add_collect_z2_to_output_node(
                    samplex,
                    pre_node_idx,
                    pre_nodes_to_nodes,
                    order,
                    register_names,
                )
            else:
                raise SamplexBuildError(f"No lowering method found for {pre_node}.")

        max_param_idx = self.max_param_idx
        if self.passthrough_params:
            max_passthrough_param_idx = samplex.set_passthrough_params(self.passthrough_params)
            max_param_idx = (
                max(max_param_idx, max_passthrough_param_idx)
                if max_param_idx is not None
                else max_passthrough_param_idx
            )

        if num_params := samplex.num_parameters:
            samplex.add_input(
                TensorSpecification(
                    "parameter_values",
                    (num_params,),
                    np.dtype(np.float64),
                    "Input parameter values to use during sampling.",
                )
            )

        for basis_ref, length in self._basis_transforms.items():
            samplex.add_input(
                TensorSpecification(
                    f"basis_changes.{basis_ref}",
                    (length,),
                    np.dtype(np.uint8),
                    "Basis changing gates.",
                )
            )

        for noise_ref, num_qubits in self._noise_maps.items():
            samplex.add_noise_model_requirement(
                NoiseModelRequirement(noise_ref, num_qubits, self._noise_modifiers[noise_ref])
            )

        if max_param_idx is not None:
            samplex.add_output(
                TensorSpecification(
                    "parameter_values",
                    (max_param_idx + 1,),
                    np.dtype(np.float32),
                    "Parameter values for the template circuit.",
                )
            )

        if self._twirled_clbits:
            for reg in self._cregs:
                samplex.add_output(
                    TensorSpecification(
                        f"measurement_flips.{reg.name}",
                        (1, len(reg)),
                        np.dtype(np.bool_),
                        "Bit-flip corrections for measurement twirling.",
                    )
                )

        if (num_signs := next(self._noise_map_count)) > 0:
            samplex.add_output(
                TensorSpecification(
                    "pauli_signs",
                    (num_signs,),
                    np.dtype(np.bool_),
                    "Signs from sampled noise maps. The order matches the iteration order of "
                    "injected noise in the circuit.",
                )
            )

        return samplex

    def add_basis_transform_node(
        self,
        samplex: Samplex,
        pre_basis_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ) -> None:
        """Add basis tranform node to a samplex, mutating it in place.

        Args:
            samplex: The samplex to add nodes to.
            pre_basis_idx: The index of the pre-basis node to turn into a basis transform node.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the samplex state graph.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the samplex state graph.
        """
        pre_basis = cast(PreBasisTransform, self.graph[pre_basis_idx])
        reg_idx = order[pre_basis_idx]
        node = BasisTransformNode(
            reg_name := f"basis_change_{reg_idx}",
            MEAS_PAULI_BASIS if pre_basis.direction is Direction.LEFT else PREP_PAULI_BASIS,
            "basis_changes." + pre_basis.basis_ref,
            len(pre_basis.subsystems),
        )
        node_idx = samplex.add_node(node)

        pre_nodes_to_nodes[pre_basis_idx] = node_idx

        for pre_successor_idx in self.graph.successor_indices(pre_basis_idx):
            register_names[pre_successor_idx][pre_basis_idx] = reg_name

    def add_inject_noise_node(
        self,
        samplex: Samplex,
        pre_inject_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ) -> None:
        """Add an inject noise node to a samplex, mutating it in place.

        Args:
            samplex: The samplex to add nodes to.
            pre_inject_idx: The index of the pre-inject noise node to turn into an inject noise
                node.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the samplex state graph.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the samplex state graph.
        """
        pre_inject = cast(PreInjectNoise, self.graph[pre_inject_idx])
        reg_idx = order[pre_inject_idx]
        reg_name = f"inject_noise_{reg_idx}"
        sign_reg_name = f"sign_{reg_idx}"
        node = InjectNoiseNode(
            reg_name,
            sign_reg_name,
            pre_inject.ref,
            len(pre_inject.subsystems),
            pre_inject.modifier_ref,
        )
        node_idx = samplex.add_node(node)

        pre_nodes_to_nodes[pre_inject_idx] = node_idx

        for pre_successor_idx in self.graph.successor_indices(pre_inject_idx):
            register_names[pre_successor_idx][pre_inject_idx] = reg_name

        collect_signs_node = CollectZ2ToOutputNode(
            sign_reg_name, [0], "pauli_signs", [pre_inject.sign_idx]
        )
        samplex.add_edge(node_idx, samplex.add_node(collect_signs_node))

    def add_twirl_sampling_node(
        self,
        samplex: Samplex,
        pre_emit_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ):
        """Add sampling nodes to a samplex, mutating it in place.

        Args:
            samplex: The samplex to add nodes to.
            pre_emit_idx: The index of the pre-emit node to turn into a twirl sampling node.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the pre-samplex graph.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the pre-samplex graph.
        """
        pre_emit = cast(PreEmit, self.graph[pre_emit_idx])
        reg_idx = order[pre_emit_idx]
        node = TwirlSamplingNode(
            lhs_reg_name := f"lhs_{reg_idx}",
            rhs_reg_name := f"rhs_{reg_idx}",
            REG_TO_DISTRIBUTION[pre_emit.register_type](len(pre_emit.subsystems)),
        )
        node_idx = samplex.add_node(node)

        pre_nodes_to_nodes[pre_emit_idx] = node_idx

        for pre_successor_idx in self.graph.successor_indices(pre_emit_idx):
            direction = self.graph.get_edge_data(pre_emit_idx, pre_successor_idx).direction
            reg_name = lhs_reg_name if direction is Direction.LEFT else rhs_reg_name
            register_names[pre_successor_idx][pre_emit_idx] = reg_name

    def add_combine_node(
        self,
        samplex: Samplex,
        pre_node_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
        combined_register_name: str,
        combined_register_type: VirtualType,
    ) -> NodeIndex:
        """Add a node that combines all the predecessor nodes of a given pre-node.

        This function adds a :class:`~.SliceRegisterNode` if the given pre-node has a single
        predecessor, or a :class:`~.CombineRegistersNode` if it has multiple predecessors.

        Args:
            samplex: The samplex to add nodes to.
            pre_node_idx: The index of the pre-node whose predecessors are to be combined.
            pre_nodes_to_nodes: A map from pre-node indices to node indices. The indices of
                the pre-node's predecessors must be included.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the pre-samplex graph. The indices of the pre-node and
                its predecessors must be included.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the pre-samplex graph.
            combined_register_name: The prefix of the name of the combined node.
            combined_register_type: The type of register to combine the predecessor registers into.

        Returns:
            A tuple containing the combine node's index and the new register name.
        """
        pred_idxs = self.sorted_predecessor_idxs(pre_node_idx, order)
        pre_edges = [self.graph.get_edge_data(pred_idx, pre_node_idx) for pred_idx in pred_idxs]
        subsystems = self.graph[pre_node_idx].subsystems

        operands = {}
        for pre_node_predecessor_idx, pre_edge in zip(pred_idxs, pre_edges):
            pre_node_predecessor = self.graph[pre_node_predecessor_idx]
            register_name = register_names[pre_node_idx][pre_node_predecessor_idx]
            source_idxs = pre_node_predecessor.subsystems.get_indices(pre_edge.subsystems)
            destination_idxs = subsystems.get_indices(pre_edge.subsystems)
            node_predecessor = samplex.graph[pre_nodes_to_nodes[pre_node_predecessor_idx]]
            if register_name in node_predecessor.writes_to():
                virtual_type = node_predecessor.writes_to()[register_name][1]
            else:
                virtual_type = node_predecessor.instantiates()[register_name][1]
            operands[register_name] = (source_idxs, destination_idxs, virtual_type)

        if len(operands) == 1:
            input_register_name, (source_idxs, destination_idxs, input_type) = next(
                iter(operands.items())
            )
            slice_idxs = [source_idxs[idx] for idx in destination_idxs]
            combine_node = SliceRegisterNode(
                input_type=input_type,
                output_type=combined_register_type,
                input_register_name=input_register_name,
                output_register_name=combined_register_name,
                slice_idxs=slice_idxs,
                force_copy=pre_edge.force_register_copy,
            )
        else:
            combine_node = CombineRegistersNode(
                output_type=combined_register_type,
                output_register_name=combined_register_name,
                num_output_subsystems=len(subsystems),
                operands=operands,
            )
        combine_node_idx = samplex.add_node(combine_node)

        for pred_idx in pred_idxs:
            samplex.add_edge(pre_nodes_to_nodes[pred_idx], combine_node_idx)
        return combine_node_idx

    def add_propagate_node(
        self,
        samplex: Samplex,
        pre_propagate_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ):
        """Add evaluation nodes to a samplex, mutating it in place.

        Args:
            samplex: The samplex to add nodes to.
            pre_propagate_idx: The index of the pre-propagate node to turn into nodes in the
                samplex.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the pre-samplex graph.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the pre-samplex graph.

        Raises:
            SamplexBuildError: If a pre-propagate contains an unsupported operation.
        """
        pre_propagate = cast(PrePropagate, self.graph[pre_propagate_idx])
        prefix = "leftwards" if pre_propagate.direction is Direction.LEFT else "rightwards"
        combined_register_name = f"{prefix}_{order[pre_propagate_idx]}"

        op_name = pre_propagate.operation.name
        mode = pre_propagate.spec.mode
        incoming = set()
        for predecssor_idx in self.graph.predecessor_indices(pre_propagate_idx):
            incoming.add(samplex.graph[pre_nodes_to_nodes[predecssor_idx]].outgoing_register_type)
        if mode is InstructionMode.MULTIPLY and pre_propagate.operation.num_qubits == 1:
            combined_register_type = VirtualType.U2
            if pre_propagate.operation.is_parameterized():
                param_idxs = [
                    samplex.append_parameter_expression(param)
                    for _, param in pre_propagate.spec.params
                ]
                if pre_propagate.direction is Direction.LEFT:
                    propagate_node = RightU2ParametricMultiplicationNode(
                        op_name, combined_register_name, param_idxs
                    )
                else:
                    propagate_node = LeftU2ParametricMultiplicationNode(
                        op_name, combined_register_name, param_idxs
                    )
            else:
                register = U2Register(np.array(pre_propagate.operation).reshape(1, 1, 2, 2))
                if pre_propagate.direction is Direction.LEFT:
                    propagate_node = RightMultiplicationNode(register, combined_register_name)
                else:
                    propagate_node = LeftMultiplicationNode(register, combined_register_name)
        elif (
            mode is InstructionMode.PROPAGATE
            and incoming == {VirtualType.PAULI}
            and op_name in PAULI_PAST_CLIFFORD_INVARIANTS
        ):
            # No node is needed since this is an invariant, but we do need to track
            # mappings of register names and nodes. This will be done later.
            combined_register_type = VirtualType.PAULI
            propagate_node = None
        elif (
            mode is InstructionMode.PROPAGATE
            and incoming == {VirtualType.PAULI}
            and op_name in PAULI_PAST_CLIFFORD_LOOKUP_TABLES
        ):
            combined_register_type = VirtualType.PAULI
            propagate_node = PauliPastCliffordNode(
                op_name,
                combined_register_name,
                np.array(list(pre_propagate.partition), dtype=np.intp),
            )
        else:
            raise SamplexBuildError(
                f"Encountered unsupported {op_name} propragation with mode {mode} and "
                f"incoming virtual gates {incoming}."
            )

        combine_node_idx = self.add_combine_node(
            samplex,
            pre_propagate_idx,
            pre_nodes_to_nodes,
            order,
            register_names,
            combined_register_name,
            combined_register_type,
        )

        if propagate_node is not None:
            node_idx = samplex.add_node(propagate_node)
            samplex.add_edge(combine_node_idx, node_idx)
        else:
            # TODO: It should be possible to not add a slice node in this case, if there is
            # a single predecessor.
            node_idx = combine_node_idx

        pre_nodes_to_nodes[pre_propagate_idx] = node_idx

        for pre_successor_idx in self.graph.successor_indices(pre_propagate_idx):
            register_names[pre_successor_idx][pre_propagate_idx] = combined_register_name

    def add_collect_node(
        self,
        samplex: Samplex,
        pre_node_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ):
        """Add evaluation nodes to a samplex, mutating it in place.

        Args:
            samplex: The samplex to add nodes to.
            pre_node_idx: The index of the pre-collect node to turn into a collection node in the
                samplex.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the pre-samplex graph.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the pre-samplex graph.
        """
        pre_node = cast(PreCollect, self.graph[pre_node_idx])
        all_subsystems = pre_node.subsystems
        combined_name = f"collect_{order[pre_node_idx]}"
        combine_node_idx = self.add_combine_node(
            samplex,
            pre_node_idx,
            pre_nodes_to_nodes,
            order,
            register_names,
            combined_name,
            VirtualType.U2,
        )

        param_reorder = pre_node.subsystems.get_indices(all_subsystems)
        collect = CollectTemplateValues(
            "parameter_values",
            pre_node.param_idxs[param_reorder, :],
            combined_name,
            VirtualType.U2,
            np.arange(len(all_subsystems)),
            pre_node.synth,
        )

        samplex.add_edge(combine_node_idx, samplex.add_node(collect))

    def add_collect_z2_to_output_node(
        self,
        samplex: Samplex,
        pre_node_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ):
        """Add :class:`~.CollectZ2ToOutput` to the Samplex graph.

        Args:
            samplex: The samplex to add nodes to.
            pre_node_idx: The index of the :class:`~.PreZ2Collect` node to turn into a collection
                node in the samplex.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the pre-samplex graph.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the pre-samplex graph.
        """
        pre_node = cast(PreZ2Collect, self.graph[pre_node_idx])
        combined_name = f"z2_collect_{order[pre_node_idx]}"
        combine_node_idx = self.add_combine_node(
            samplex,
            pre_node_idx,
            pre_nodes_to_nodes,
            order,
            register_names,
            combined_name,
            VirtualType.Z2,
        )

        for reg_name, clbit_idxs in pre_node.clbit_idxs.items():
            z2collect = CollectZ2ToOutputNode(
                combined_name,
                np.array(pre_node.subsystems_idxs[reg_name]),
                f"measurement_flips.{reg_name}",
                clbit_idxs,
            )

            samplex.add_edge(combine_node_idx, samplex.add_node(z2collect))

    def subgraphs(self) -> list[PyDiGraph[PreNode, PreEdge]]:
        """Return a list of disconnected components."""
        return [
            self.graph.subgraph(list(node_idxs))
            for node_idxs in weakly_connected_components(self.graph)
        ]

    def draw(
        self,
        cols: int = 2,
        subgraph_idxs: None | int | Sequence[int] = None,
        layout_method: LayoutPresets | LayoutMethod = "auto",
    ) -> Figure:
        """Draw the graph in this pre-samplex using the :meth:`~plot_graph` method.

        Args:
            cols: The number of columns in the returned figure.
            subgraph_idxs: The indices of the subgraphs to include in the plot, or ``None``
                to include all of the subgraphs.
            layout_method: A predefined layout method by name, or a callable implementing a layout.

        Returns:
            A Plotly figure.
        """

        def _node_ranker(node: PreNode) -> int:
            if isinstance(node, PreEmit):
                return 0
            if isinstance(node, PreCollect):
                return 1
            return None

        return plot_graph(
            graph=self.graph,
            cols=cols,
            subgraph_idxs=subgraph_idxs,
            layout_method=layout_method,
            ranker=_node_ranker,
        )
