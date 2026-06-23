# This code is a Qiskit project.
#
# (C) Copyright IBM 2025-2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""PreSamplex"""

from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from functools import lru_cache
from itertools import count
from typing import TYPE_CHECKING, Any, NamedTuple, cast

import numpy as np
from qiskit.circuit import ClassicalRegister, Qubit
from qiskit.circuit.gate import Gate
from qiskit.circuit.library import (
    IGate,
    RXGate,
    RZGate,
    SGate,
    SXGate,
    XGate,
    ZGate,
)
from rustworkx.rustworkx import (
    PyDiGraph,
    topological_generations,
    topological_sort,
    weakly_connected_components,
)

from ..aliases import (
    ClbitIndex,
    DAGOpNode,
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
from ..annotations import ChangeBasisMode, GroupMode
from ..builders.specs import FrameChangeMode, InstructionMode
from ..constants import (
    SUPPORTED_1Q_FRACTIONAL_GATES,
    Direction,
)
from ..distributions import GROUP_TO_DISTRIBUTION, UniformPauliSubset
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
    ChangeBasisNode,
    CollectTemplateValues,
    CollectZ2ToOutputNode,
    CombineRegistersNode,
    DistributionSamplingNode,
    InjectNoiseNode,
    LeftMultiplicationNode,
    LeftU2ParametricMultiplicationNode,
    PauliPastCliffordNode,
    RightMultiplicationNode,
    RightU2ParametricMultiplicationNode,
    SliceRegisterNode,
    TwirlSamplingNode,
)
from ..samplex.nodes.change_basis_node import (
    LOCAL_CLIFFORD,
    MEAS_PAULI_BASIS,
    PREP_PAULI_BASIS,
    BasisChange,
)
from ..samplex.nodes.pauli_past_clifford_node import (
    PAULI_PAST_CLIFFORD_CANONICAL_NAMES,
    PAULI_PAST_CLIFFORD_INVARIANTS,
    PAULI_PAST_CLIFFORD_LOOKUP_TABLES,
)
from ..samplex.nodes.propagate_local_c1_node import (
    LOCAL_C1_PROPAGATE_INVARIANTS,
    LOCAL_C1_PROPAGATE_LOOKUP_TABLES,
    PropagateLocalC1Node,
)
from ..samplex.nodes.propagate_local_pauli_node import PropagateLocalPauliNode
from ..samplex.nodes.utils import get_fractional_gate_register
from ..synths import Synth
from ..tensor_interface import PauliLindbladMapSpecification, TensorSpecification
from ..trace_info import TraceInfo
from ..utils import FrozenDict
from ..virtual_registers import U2Register, VirtualType
from ..visualization import plot_graph
from .graph_data import (
    PreChangeBasis,
    PreCollect,
    PreEdge,
    PreEmit,
    PreInjectNoise,
    PreMeasure,
    PreNode,
    PrePropagate,
    PreReset,
)
from .utils import merge_pre_edges

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

NO_PROPAGATE: frozenset[OperationName] = frozenset(["barrier", "delay", "id"])

FRAME_CHANGE_TO_BASIS_CHANGE: dict[FrameChangeMode, BasisChange] = FrozenDict(
    {
        "pauli_measure": MEAS_PAULI_BASIS,
        "pauli_prepare": PREP_PAULI_BASIS,
        "local_clifford": LOCAL_CLIFFORD,
    }
)


class _PropagateGroup(NamedTuple):
    """Configuration for propagating virtual gates past other gates at a given group level."""

    allowed_incoming: frozenset[VirtualType]
    """The set of virtual register types that this group can accept as input."""
    group_type: VirtualType
    """The virtual register type that this group propagates as."""
    invariants: frozenset[str]
    """Gate names for which propagation is trivial."""
    lookup_tables: dict[str, np.ndarray]
    """Maps gate names to conjugation lookup tables."""
    node_class: type
    """The evaluation node class used to perform the propagation."""


_PROPAGATE_GROUPS: tuple[_PropagateGroup, ...] = (
    _PropagateGroup(
        frozenset({VirtualType.C1, VirtualType.PAULI}),
        VirtualType.C1,
        LOCAL_C1_PROPAGATE_INVARIANTS,
        LOCAL_C1_PROPAGATE_LOOKUP_TABLES,
        PropagateLocalC1Node,
    ),
    _PropagateGroup(
        frozenset({VirtualType.PAULI}),
        VirtualType.PAULI,
        PAULI_PAST_CLIFFORD_INVARIANTS,
        PAULI_PAST_CLIFFORD_LOOKUP_TABLES,
        PauliPastCliffordNode,
    ),
)


def _resolve_to_clifford_gate(gate: Gate) -> Gate | None:
    """Return the named Clifford gate equivalent to ``gate`` at its concrete angle, or None.

    For concrete-parameter rotation gates (rz, p, rx) whose angle is a multiple of π/2,
    returns the equivalent named Clifford gate. This allows Pauli propagation via lookup tables
    even when the circuit uses rotation gates at Clifford angles.

    Returns ``None`` for symbolic (unbound) parameters, non-Clifford angles, or gate types
    not handled here.
    """
    if gate.is_parameterized():
        return None

    if not isinstance(gate, RZGate | RXGate) and gate.name != "p":
        return None

    angle = float(gate.params[0]) % (2 * np.pi)

    if gate.name in ("rz", "p"):
        candidates = [
            (0.0, IGate()),
            (np.pi / 2, SGate()),
            (np.pi, ZGate()),
            (3 * np.pi / 2, SGate()),  # sdg has same Pauli action as s; canonicalize to s
        ]
    else:  # rx
        candidates = [
            (0.0, IGate()),
            (np.pi / 2, SXGate()),
            (np.pi, XGate()),
            (3 * np.pi / 2, SXGate()),  # sxdg has same Pauli action as sx; canonicalize to sx
        ]

    for target_angle, clifford_gate in candidates:
        if np.isclose(angle, target_angle, atol=1e-10):
            return clifford_gate

    return None


_CANONICAL_GATE_CONSTRUCTORS = {
    "s": SGate,
    "sx": SXGate,
}
"""Maps canonical gate names to their constructors, for canonicalizing non-canonical names."""


@lru_cache
def _match_propagate_group(
    op_name: str, mode: InstructionMode, incoming: frozenset[VirtualType]
) -> _PropagateGroup:
    """Find the propagate group matching the given operation, mode, and incoming register types."""
    for group in _PROPAGATE_GROUPS:
        if incoming <= group.allowed_incoming and group.group_type in incoming:
            if op_name in group.invariants or op_name in group.lookup_tables:
                return group
            raise SamplexBuildError(
                f"Encountered unsupported {op_name} propagation with mode {mode} "
                f"and incoming virtual gates {incoming}."
            )
    raise SamplexBuildError(
        f"Encountered unsupported {op_name} propagation with mode {mode} "
        f"and incoming virtual gates {incoming}."
    )


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
    indices, and operations are still declarative rather than procedural.

    Args:
        graph: The graph being built.
        qubit_map: A map from qubits in the source circuit to physical qubit indices.
        dangling: A map from qubit indices to sets of node indices that are still eligible to,
            and must, receive edges at a further point in parsing the circuit being built.
        optional_dangling: A map from qubit indices to sets of node indices that are still
            eligible to, but don't have to, receive edges at a further point in parsing the
            circuit being built.
        cregs: A list of classical registers in the order that they were added to the circuit.
        pauli_lindblad_map_count: A count of the total number of Pauli Lindblad maps.
        pauli_lindblad_maps: A map from unique identifiers of Pauli Lindblad maps to the number of
            systems the map acts on.
        basis_changes: A map from unique identifiers of basis changes to the number of
            subsystems in that basis change.
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
        pauli_lindblad_map_count: count | None = None,
        pauli_lindblad_maps: dict[str, NumSubsystems] | None = None,
        noise_modifiers: dict[str, set[str]] | None = None,
        basis_changes: dict[str, int] | None = None,
        twirled_clbits: set[ClbitIndex] | None = None,
        passthrough_params: ParamSpec | None = None,
        forced_copy_node_idxs: set[NodeIndex] | None = None,
        debug: bool = False,
    ):
        self.graph = PyDiGraph[PreNode, PreEdge](multigraph=True) if graph is None else graph
        self.qubit_map: dict[Qubit, QubitIndex] = {} if qubit_map is None else qubit_map
        self._cregs = cregs
        self._dangling: dict[QubitIndex, set[NodeIndex]] = (
            defaultdict(set) if dangling is None else dangling
        )
        self._optional_dangling: dict[QubitIndex, set[NodeIndex]] = (
            defaultdict(set) if optional_dangling is None else optional_dangling
        )
        self._pauli_lindblad_map_count = (
            count() if pauli_lindblad_map_count is None else pauli_lindblad_map_count
        )
        self._pauli_lindblad_maps = {} if pauli_lindblad_maps is None else pauli_lindblad_maps
        self._noise_modifiers = defaultdict(set) if noise_modifiers is None else noise_modifiers
        self._basis_changes = {} if basis_changes is None else basis_changes
        self._twirled_clbits = set() if twirled_clbits is None else twirled_clbits
        self.passthrough_params: ParamSpec = (
            [] if passthrough_params is None else passthrough_params
        )
        self._forced_copy_node_idxs: set[NodeIndex] = (
            set() if forced_copy_node_idxs is None else forced_copy_node_idxs
        )
        self.debug = debug

    def remap(self, qubit_map: dict[Qubit, QubitIndex]) -> "PreSamplex":
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
            self._pauli_lindblad_map_count,
            self._pauli_lindblad_maps,
            self._noise_modifiers,
            self._basis_changes,
            self._twirled_clbits,
            self.passthrough_params,
            self._forced_copy_node_idxs,
            self.debug,
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

    def enforce_no_propagation(self, instr: DAGOpNode):
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
        subsystems = QubitIndicesPartition(1, [(self.qubit_map[qubit],) for qubit in instr.qargs])

        match = DanglerMatch(node_types=(PreEmit, PrePropagate), direction=Direction.RIGHT)
        if any(True for _ in self.find_danglers(match, subsystems)):
            raise SamplexBuildError(f"Cannot propagate through {instr.op.name} instruction.")
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
        trace_info: TraceInfo | None = None,
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
            trace_info: Optional debug trace info to attach to the node.

        Returns:
            The index of the new node in the graph.
        """
        subsystems = self.qubits_to_indices(qubits)
        if node_idx is not None:
            self.graph[node_idx].add_subsystems(subsystems, param_idxs)
        else:
            node_idx = self.graph.add_node(
                PreCollect(subsystems, Direction.BOTH, synth, param_idxs, trace_info=trace_info)
            )

        # collect any nodes that need collecting and unmark them as dangling
        match = DanglerMatch(
            node_types=(PreEmit, PrePropagate, PreMeasure), direction=Direction.RIGHT
        )
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

    def add_measure_propagate(
        self, instr: DAGOpNode, clbit_idx: ClbitIndex, trace_info: TraceInfo | None = None
    ) -> int | None:
        """Add a node that propagates virtual Paulis through a measurement.

        This creates a :class:`~.PreMeasure` node that, during lowering, produces
        both a Z2 measurement flip output and a continued Pauli register with preserved X
        component and randomized Z component.

        Args:
            instr: The measurement instruction.
            clbit_idx: The global classical bit index.
            trace_info: Optional debug trace info to attach to the node.

        Returns:
            The index of the new node, or None if no rightward danglers were found.
        """
        subsystems = QubitIndicesPartition(1, [(self.qubit_map[qubit],) for qubit in instr.qargs])

        if clbit_idx in self._twirled_clbits:
            raise SamplexBuildError(
                "Cannot twirl more than one measurement on the same classical bit."
            )

        val = 0
        creg_name, creg_offset = None, None
        for reg in self._cregs:
            if clbit_idx < val + len(reg):
                creg_name, creg_offset = reg.name, clbit_idx - val
                break
            val += len(reg)
        else:
            raise SamplexBuildError(
                f"Could not resolve clbit index {clbit_idx} to a classical register."
            )

        match = DanglerMatch(
            node_types=(PreEmit, PrePropagate, PreMeasure), direction=Direction.RIGHT
        )
        found_predecessors = list(self.find_then_remove_danglers(match, subsystems))

        # cannot propagate left through a measure
        list(self.find_then_remove_danglers(DanglerMatch(direction=Direction.LEFT), subsystems))

        if not found_predecessors:
            return None

        node = PreMeasure(subsystems, [creg_name], [creg_offset], trace_info=trace_info)
        node_idx = self.graph.add_node(node)

        for pred_idx, pred_subsystems in found_predecessors:
            edge = PreEdge(
                pred_subsystems, Direction.RIGHT, pred_idx in self._forced_copy_node_idxs
            )
            self.graph.add_edge(pred_idx, node_idx, edge)

        self._twirled_clbits.add(clbit_idx)
        self.add_dangler(subsystems.all_elements, node_idx, DanglerType.OPTIONAL)

        return node_idx

    def add_reset_propagate(self, instr: DAGOpNode, trace_info: TraceInfo | None = None):
        """Add a node that propagates virtual Paulis through a reset.

        Args:
            instr: The reset instruction.
            trace_info: Optional debug trace info to attach to the node.

        Returns:
            The index of the new node, or None if no rightward danglers were found.
        """
        subsystems = QubitIndicesPartition(1, [(self.qubit_map[qubit],) for qubit in instr.qargs])

        match = DanglerMatch(
            node_types=(PreEmit, PrePropagate, PreMeasure), direction=Direction.RIGHT
        )
        found_predecessors = list(self.find_then_remove_danglers(match, subsystems))

        if not found_predecessors:
            return None

        # cannot propagate left through a reset
        list(self.find_then_remove_danglers(DanglerMatch(direction=Direction.LEFT), subsystems))

        pre_reset = PreReset(subsystems, trace_info=trace_info)
        node_idx = self.graph.add_node(pre_reset)
        self.add_dangler(pre_reset.subsystems.all_elements, node_idx, DanglerType.OPTIONAL)

        return node_idx

    def add_emit_twirl(
        self,
        qubits: QubitPartition,
        register_type: GroupMode,
        twirl_gate: str | None = None,
        trace_info: TraceInfo | None = None,
    ) -> NodeIndex:
        """Add a node that emits virtual gates left and right of the same type.

        Args:
            qubits: The qubits to emit virtual gates on.
            register_type: The type of virtual gate to emit.
            twirl_gate: The 2Q gate name for ``UniformLocalC1`` sampling, or ``None``.
            trace_info: Optional debug trace info to attach to the node.

        Raises:
            SamplexBuildError: When `qubits` has overlap with a hanging emit node with a different
                virtual gate type.
            SamplexBuildError: When any of the elements of `qubits` is not dangling.

        Returns:
            The index of the new node in the graph.
        """
        subsystems = self.qubits_to_indices(qubits)
        node_idx = self.graph.add_node(
            PreEmit(
                subsystems,
                Direction.BOTH,
                register_type,
                twirl_gate=twirl_gate,
                trace_info=trace_info,
            )
        )

        # find collectors (or propagators leading to collectors) for right-to-left emission and
        # connect this emission there. we do NOT want to remove them as dangling because they
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
        self,
        qubits: QubitPartition,
        noise_ref: StrRef,
        modifier_ref: StrRef = "",
        trace_info: TraceInfo | None = None,
    ) -> NodeIndex:
        """Add a node that emits virtual gates for noise injection to the left.

        Args:
            qubits: The qubits to emit virtual gates on.
            noise_ref: Unique identifier of the noise to inject.
            modifier_ref: Unique identifier for modifiers to apply to this Pauli Lindblad map.
            trace_info: Optional debug trace info to attach to the node.

        Raises:
            SamplexBuildError: If a Pauli Lindblad map with the same `noise_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._pauli_lindblad_maps.get(noise_ref)) and num_subsys != len(qubits):
            raise SamplexBuildError(
                f"Cannot add Pauli Lindblad map with reference `{noise_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._pauli_lindblad_maps[noise_ref] = len(qubits)

        if modifier_ref:
            self._noise_modifiers[noise_ref].add(modifier_ref)

        subsystems = self.qubits_to_indices(qubits)
        node = PreInjectNoise(
            subsystems,
            Direction.LEFT,
            VirtualType.PAULI,
            noise_ref,
            modifier_ref,
            next(self._pauli_lindblad_map_count),
            trace_info=trace_info,
        )
        return self._add_emit_left(node)

    def add_emit_noise_right(
        self,
        qubits: QubitPartition,
        noise_ref: StrRef,
        modifier_ref: StrRef = "",
        trace_info: TraceInfo | None = None,
    ) -> NodeIndex:
        """Add a node that emits virtual gates for noise injection to the right.

        Args:
            qubits: The qubits to emit virtual gates on.
            noise_ref: Unique identifier of the noise to inject.
            modifier_ref: Unique identifier for modifiers to apply to this Pauli Lindblad map.
            trace_info: Optional debug trace info to attach to the node.

        Raises:
            SamplexBuildError: If a Pauli Lindblad map with the same `noise_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._pauli_lindblad_maps.get(noise_ref)) and (num_subsys) != len(qubits):
            raise SamplexBuildError(
                f"Cannot add Pauli Lindblad map with reference `{noise_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._pauli_lindblad_maps[noise_ref] = len(qubits)

        if modifier_ref:
            self._noise_modifiers[noise_ref].add(modifier_ref)

        subsystems = self.qubits_to_indices(qubits)
        node = PreInjectNoise(
            subsystems,
            Direction.LEFT,
            VirtualType.PAULI,
            noise_ref,
            modifier_ref,
            next(self._pauli_lindblad_map_count),
            trace_info=trace_info,
        )
        return self._add_emit_right(node)

    def add_emit_left_basis_change(
        self,
        qubits: QubitPartition,
        basis_ref: StrRef,
        basis_change: FrameChangeMode,
        trace_info: TraceInfo | None = None,
    ) -> NodeIndex:
        """Add a node that emits virtual gates left to change frames.

        Args:
            qubits: The qubits to emit virtual gates on.
            basis_ref: Unique identifier of this basis change.
            basis_change: What basis change to use.

        Raises:
            SamplexBuildError: If a basis change with the same `basis_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._basis_changes.get(basis_ref)) and num_subsys != len(qubits):
            raise SamplexBuildError(
                f"Cannot add basis change `{basis_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._basis_changes[basis_ref] = len(qubits)

        subsystems = self.qubits_to_indices(qubits)
        virtual_type = VirtualType.U2 if type(basis_change) is ChangeBasisMode else VirtualType.C1
        node = PreChangeBasis(
            subsystems,
            Direction.LEFT,
            virtual_type,
            basis_ref,
            basis_change,
            trace_info=trace_info,
        )
        return self._add_emit_left(node)

    def add_emit_right_basis_change(
        self,
        qubits: QubitPartition,
        basis_ref: StrRef,
        basis_change: FrameChangeMode,
        trace_info: TraceInfo | None = None,
    ) -> NodeIndex:
        """Add a node that emits virtual gates right to change frames.

        Args:
            qubits: The qubits to emit virtual gates on.
            basis_ref: Unique identifier of this basis change.
            basis_change: What basis change to use.

        Raises:
            SamplexBuildError: If a basis change with the same `basis_ref` but of different
                length has already been added.

        Returns:
            The index of the new node in the graph.
        """
        if (num_subsys := self._basis_changes.get(basis_ref)) and num_subsys != len(qubits):
            raise SamplexBuildError(
                f"Cannot add basis change `{basis_ref}` on `{qubits}` and a "
                f"different subsystem with length `{num_subsys}`."
            )
        else:
            self._basis_changes[basis_ref] = len(qubits)

        subsystems = self.qubits_to_indices(qubits)
        virtual_type = VirtualType.U2 if type(basis_change) is ChangeBasisMode else VirtualType.C1
        node = PreChangeBasis(
            subsystems,
            Direction.RIGHT,
            virtual_type,
            basis_ref,
            basis_change,
            trace_info=trace_info,
        )
        return self._add_emit_right(node)

    def add_propagate(
        self,
        instr: DAGOpNode,
        mode: InstructionMode,
        params: ParamSpec,
        trace_info: TraceInfo | None = None,
        commutant_twirl: bool = False,
    ):
        """Add a node that propagates virtual gates through an operation.

        This method deduces which direction to propagate virtual gates by inspecting the previous
        nodes on the dangling qubits that overlap with the instruction's qubits.

        Args:
            instr: The circuit instruction to propagate through.
            mode: What mode to use for propagation.
            params: The parameters of the instruction.
            trace_info: Optional debug trace info to attach to the node.
            commutant_twirl: Whether to twirl fractional gates with their commutants.

        Raises:
            SamplexBuildError: If the qubits of ``instr`` have partial overlap with dangling qubits
                of the pre-samplex.

        Returns:
            The index of the new node in the graph.
        """
        op = instr.op
        if op.name in NO_PROPAGATE:
            return

        # For PROPAGATE-mode single-qubit rotations at Clifford angles, resolve to the equivalent
        # named Clifford gate. This must happen before PrePropagate creation so that the
        # PrePropagateKey uses the resolved name, preventing incorrect merging of nodes with
        # different rotation angles (e.g., rz(π/2) and rz(π) must not be merged).
        if mode is InstructionMode.PROPAGATE and op.num_qubits == 1:
            resolved = _resolve_to_clifford_gate(op)
            if resolved is not None:
                op = resolved
            elif op.name in PAULI_PAST_CLIFFORD_CANONICAL_NAMES:
                op = _CANONICAL_GATE_CONSTRUCTORS[PAULI_PAST_CLIFFORD_CANONICAL_NAMES[op.name]]()

        # in the future when we have multi-qubit virtual groups, this can't be hard-coded to 1
        subsystems = QubitIndicesPartition(1, [(self.qubit_map[qubit],) for qubit in instr.qargs])

        if op.name.startswith("meas"):
            return

        # Track passthrough parameters (even if no node is created)
        # These parameters appear in the template (InstructionMode.PROPAGATE) and must
        # be accounted for during sampling, even though they might not take part in
        # virtual gate propagation.
        if mode == InstructionMode.PROPAGATE and params is not None:
            self.passthrough_params.extend(params)

        # recall that this is indexing out of `subsystems`, not qubits
        num_qubits = instr.num_qubits
        partition = SubsystemIndicesPartition(num_qubits, [tuple(range(num_qubits))])

        # time ordering: (emit> | propagate>) --> new propagate>
        rightward_node_candidate = NodeCandidate(
            self.graph,
            PrePropagate(
                subsystems,
                Direction.RIGHT,
                op,
                partition,
                mode,
                params,
                commutant_twirl=commutant_twirl,
                trace_info=trace_info,
            ),
        )
        all_found_qubit_idxs = set()
        match = DanglerMatch(
            node_types=(PreEmit, PrePropagate, PreMeasure), direction=Direction.RIGHT
        )
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
            self.graph,
            PrePropagate(
                subsystems,
                Direction.LEFT,
                op,
                partition,
                mode,
                params,
                commutant_twirl=commutant_twirl,
                trace_info=trace_info,
            ),
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

    def merge_parallel_nodes(
        self, node_type: type[PrePropagate] | type[PreMeasure] | type[PreReset]
    ):
        """Merge parallel nodes of a given type acting on disjoint subsystems.

        Nodes are merged when they belong to the same topological generation, share at least one
        predecessor, have disjoint subsystems, and return the same clustering key from
        ``to_key()``.

        Args:
            node_type: The pre-node type to merge. Must implement ``to_key()`` and
                ``from_cluster()`` methods.
        """
        for generation in topological_generations(self.graph):
            for node_idxs in self._cluster_nodes(generation, node_type):
                if len(node_idxs) == 1:
                    continue

                nodes = [self.graph[node_idx] for node_idx in node_idxs]
                merged_node = node_type.from_cluster(nodes)
                new_node_idx = replace_nodes_with_one_node(self.graph, node_idxs, merged_node)

                for successor_idx in set(self.graph.successor_indices(new_node_idx)):
                    new_edge = merge_pre_edges(self.graph, new_node_idx, successor_idx)
                    replace_edges_with_one_edge(self.graph, new_node_idx, successor_idx, new_edge)

                for predecessor_idx in set(self.graph.predecessor_indices(new_node_idx)):
                    new_edge = merge_pre_edges(self.graph, predecessor_idx, new_node_idx)
                    replace_edges_with_one_edge(self.graph, predecessor_idx, new_node_idx, new_edge)

    def _cluster_nodes(self, generation: list[NodeIndex], node_type: type) -> list[list[NodeIndex]]:
        """Cluster nodes of ``node_type`` within a topological generation."""
        clusters: dict[Any, list[dict[str, Any]]] = defaultdict(list)

        for node_idx in generation:
            node = self.graph[node_idx]
            if not isinstance(node, node_type):
                continue
            key = node.to_key()
            for cluster in clusters[key]:
                if not cluster["subsystems"].overlaps_with(node.subsystems.all_elements) and (
                    not (pred_idxs := self.graph.predecessor_indices(node_idx))
                    and node_type is PreReset
                    or not cluster["predecessors"].isdisjoint(pred_idxs)
                ):
                    cluster["nodes"].append(node_idx)
                    for subsystem in node.subsystems:
                        cluster["subsystems"].add(subsystem)
                    cluster["predecessors"].update(self.graph.predecessor_indices(node_idx))
                    break
            else:
                clusters[key].append(
                    {
                        "nodes": [node_idx],
                        "subsystems": QubitIndicesPartition.from_elements(
                            node.subsystems.all_elements
                        ),
                        "predecessors": set(self.graph.predecessor_indices(node_idx)),
                    }
                )
        return [c["nodes"] for key_clusters in clusters.values() for c in key_clusters]

    def sorted_predecessor_idxs(
        self, pre_node_idx: NodeIndex, order: dict[NodeIndex, int]
    ) -> list[NodeIndex]:
        """Return the predecessors of a node in edge-sorted order.

        Edge-sorted order
         * places all nodes connected by :class:`~.Direction.LEFT` edges before
           :class:`~.Direction.RIGHT` edges, and
         * the :class:`~.Direction.LEFT` edges connected to twirl emissions before other emissions
           sorted according to reverse ``order``,
         * while the :class:`~.Direction.RIGHT` place emissions in order.

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
            pred_node = self.graph.get_node_data(pred_idx)
            direction = self.graph.get_edge_data(pred_idx, pre_node_idx).direction
            from_twirl = type(pred_node) is PreEmit
            pred_order = order[pred_idx]
            if direction is Direction.LEFT:
                pred_order = -pred_order if from_twirl else pred_order
            edge_sort_keys[pred_idx] = (direction, pred_order)

        return sorted(edge_sort_keys.keys(), key=lambda x: edge_sort_keys[x])

    def prune_prenodes_unreachable_from_emission(self):
        """Prune all pre-nodes that are unreachable from pre-emit nodes."""
        emission_nodes = self.graph.filter_nodes(lambda node: isinstance(node, PreEmit))
        unreachable = find_unreachable_nodes(self.graph, emission_nodes)

        self.graph.remove_nodes_from(unreachable)

    def prune_uncollected_prenodes(self):
        """Prune all pre-nodes that are not collected by pre-measure or pre-collect nodes."""
        if not self.graph.filter_nodes(lambda node: isinstance(node, PreReset)):
            return

        collected = set()
        for node_idx in reversed(topological_sort(self.graph)):
            node = self.graph[node_idx]
            if isinstance(node, PreCollect | PreMeasure):
                collected.add(node_idx)
            elif any(s in collected for s in self.graph.successor_indices(node_idx)):
                collected.add(node_idx)

        uncollected = set(self.graph.node_indices()) - collected
        if uncollected:
            self.graph.remove_nodes_from(list(uncollected))

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
                f"The condition depends on bits {clbits}, at least one of which is twirled."
            )

    @property
    def max_param_idx(self) -> int | None:
        """The maximum template parameter index over all nodes."""
        max_value = None
        for node in self.graph.nodes():
            if isinstance(node, PreCollect) and node.param_idxs.size:
                max_value = max(max_value or 0, node.param_idxs.max())
            elif isinstance(node, PrePropagate) and node.params:
                max_value = max(max_value or 0, max(idx or 0 for idx, _ in node.params))
        return max_value

    def finalize(self):
        """Finalize the pre-samplex.

        Raises:
            SamplexBuildError: If there are any emission nodes that are not collected.
        """
        # Validation
        self.validate_no_rightward_danglers()

        # Optimization
        self.prune_prenodes_unreachable_from_emission()
        self.prune_uncollected_prenodes()
        for mergeable_type in [PrePropagate, PreMeasure, PreReset]:
            self.merge_parallel_nodes(mergeable_type)

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

            # Track nodes present before lowering so we can attach trace info to new ones.
            existing_node_idxs = set(samplex.graph.node_indices())

            if isinstance(pre_node, PreChangeBasis):
                self.add_change_basis_node(
                    samplex, pre_node_idx, pre_nodes_to_nodes, order, register_names
                )
            elif isinstance(pre_node, PreInjectNoise):
                self.add_inject_noise_node(
                    samplex, pre_node_idx, pre_nodes_to_nodes, order, register_names
                )
            elif isinstance(pre_node, PreReset):
                self.add_reset_propagate_node(
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
            elif isinstance(pre_node, PreMeasure):
                self.add_measure_propagate_node(
                    samplex,
                    pre_node_idx,
                    pre_nodes_to_nodes,
                    order,
                    register_names,
                )
            else:
                raise SamplexBuildError(f"No lowering method found for {pre_node}.")

            # Propagate trace info to all newly created samplex nodes.
            if self.debug:
                # Merge the pre_node's own trace_info with that of its direct predecessors so that
                # collection nodes (which receive virtual gate contributions from other boxes) carry
                # the full set of contributing box refs, not just the owning box's ref.
                merged_trace_info: TraceInfo | None = pre_node.trace_info
                for pred_idx in self.graph.predecessor_indices(pre_node_idx):
                    pred_trace = self.graph[pred_idx].trace_info
                    if pred_trace is not None:
                        if merged_trace_info is None:
                            merged_trace_info = pred_trace.copy()
                        elif merged_trace_info is pre_node.trace_info:
                            merged_trace_info = merged_trace_info.copy().merge(pred_trace)
                        else:
                            merged_trace_info.merge(pred_trace)
                if merged_trace_info is not None:
                    for new_node_idx in set(samplex.graph.node_indices()) - existing_node_idxs:
                        samplex.graph[new_node_idx].trace_info = merged_trace_info

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

        for basis_ref, length in self._basis_changes.items():
            description = (
                "Basis changing gates, in the symplectic ordering I=0, Z=1, X=2, and Y=3."
                if basis_ref.startswith("basis_changes")
                else "Local Clifford gates, where each non-negative value c less than 24 "
                "corresponds to the unitary (HS)^i H^j P(k) with k = c % 4, j = c // 4 % 2, and "
                "i = c // 8 % 3, and P(k) is the k^th Pauli in symplectic order."
            )

            samplex.add_input(
                TensorSpecification(basis_ref, (length,), np.dtype(np.uint8), description)
            )

        for noise_ref, num_qubits in self._pauli_lindblad_maps.items():
            num_terms = f"num_terms_{noise_ref}"
            samplex.add_input(
                PauliLindbladMapSpecification(
                    f"pauli_lindblad_maps.{noise_ref}", num_qubits, num_terms
                )
            )
            for noise_modifier in self._noise_modifiers.get(noise_ref, []):
                samplex.add_input(
                    TensorSpecification(
                        f"noise_scales.{noise_modifier}",
                        (),
                        np.dtype(np.float64),
                        "A scalar factor by which to scale rates of a Pauli Lindblad map.",
                        optional=True,
                    )
                )
                samplex.add_input(
                    TensorSpecification(
                        f"local_scales.{noise_modifier}",
                        (num_terms,),
                        np.dtype(np.float64),
                        "An array of factors by which to scale individual rates of a Pauli "
                        "Lindblad map, where the order should match the corresponding list of "
                        "terms.",
                        optional=True,
                    )
                )

        parameter_values_shape = (
            "num_randomizations",
            0 if max_param_idx is None else max_param_idx + 1,
        )
        samplex.add_output(
            TensorSpecification(
                "parameter_values",
                parameter_values_shape,
                np.dtype(np.float32),
                "Parameter values valid for an associated template circuit.",
            )
        )

        if self._twirled_clbits:
            for reg in self._cregs:
                samplex.add_output(
                    TensorSpecification(
                        f"measurement_flips.{reg.name}",
                        ("num_randomizations", 1, len(reg)),
                        np.dtype(np.bool_),
                        "Bit-flip corrections for measurement twirling.",
                    )
                )

        if (num_signs := next(self._pauli_lindblad_map_count)) > 0:
            samplex.add_output(
                TensorSpecification(
                    "pauli_signs",
                    ("num_randomizations", num_signs),
                    np.dtype(np.bool_),
                    "Signs from sampled Pauli Lindblad maps, where boolean values represent the "
                    "parity of the number of non-trivial factors in the sampled error that arise "
                    "from negative rates. In other words, in order to implement basic PEC, the "
                    "sign used to correct expectation values should be ``(-1)**bool_value``. The "
                    "order matches the iteration order of boxes in the original circuit with noise "
                    "injection annotations.",
                )
            )

        return samplex

    def add_change_basis_node(
        self,
        samplex: Samplex,
        pre_basis_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ) -> None:
        """Add basis transform node to a samplex, mutating it in place.

        Args:
            samplex: The samplex to add nodes to.
            pre_basis_idx: The index of the pre-basis node to turn into a basis change node.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to integers representing their position in a
                topological sort of the samplex state graph.
            register_names: A map such that ``register_names[a][b]`` is the name of the register
                implied by the edge (a, b) in the samplex state graph.
        """
        pre_basis = cast(PreChangeBasis, self.graph[pre_basis_idx])
        reg_idx = order[pre_basis_idx]
        node = ChangeBasisNode(
            reg_name := f"basis_change_{reg_idx}",
            FRAME_CHANGE_TO_BASIS_CHANGE[pre_basis.basis_change],
            pre_basis.basis_ref,
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

        if pre_emit.twirl_gate is not None:
            distribution = GROUP_TO_DISTRIBUTION[pre_emit.register_type](
                len(pre_emit.subsystems), pre_emit.twirl_gate
            )
        else:
            distribution = GROUP_TO_DISTRIBUTION[pre_emit.register_type](len(pre_emit.subsystems))

        node = TwirlSamplingNode(
            lhs_reg_name := f"lhs_{reg_idx}",
            rhs_reg_name := f"rhs_{reg_idx}",
            distribution,
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
    ) -> tuple[NodeIndex, RegisterName]:
        """Add a node that combines all the predecessor nodes of a given pre-node.

        This function adds a :class:`~.SliceRegisterNode` if the given pre-node has a single
        predecessor, or a :class:`~.CombineRegistersNode` if it has multiple predecessors.
        If the pre-node has a single predecessor and the slice is trivial (same type, identity
        index mapping, no forced copy), the slice node is skipped entirely and the predecessor's
        node index and register name are returned directly.

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
            A tuple containing the node index and register name to use for downstream nodes.
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

        if len(operands) == 1 and len(source_idxs) == len(subsystems):
            input_register_name, (source_idxs, destination_idxs, input_type) = next(
                iter(operands.items())
            )
            pre_edge = pre_edges[0]

            # Skip trivial slices: same type, identity index mapping, no forced copy,
            # and the predecessor's register has the same number of subsystems.
            if (
                input_type == combined_register_type
                and not pre_edge.force_register_copy
                and np.array_equal(source_idxs, destination_idxs)
                and len(destination_idxs) == len(subsystems)
                and len(source_idxs) == len(self.graph[pred_idxs[0]].subsystems)
            ):
                return pre_nodes_to_nodes[pred_idxs[0]], input_register_name

            slice_idxs = np.empty(len(destination_idxs))
            slice_idxs[destination_idxs] = source_idxs
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
        return combine_node_idx, combined_register_name

    def add_propagate_node(
        self,
        samplex: Samplex,
        pre_propagate_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ):
        """Add propagation node to a samplex, mutating it in place.

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
        mode = pre_propagate.mode
        incoming = set()
        for predecessor_idx in self.graph.predecessor_indices(pre_propagate_idx):
            incoming.add(samplex.graph[pre_nodes_to_nodes[predecessor_idx]].outgoing_register_type)

        # Determine the combined register type.
        if mode is InstructionMode.MULTIPLY and pre_propagate.operation.num_qubits == 1:
            combined_register_type = VirtualType.U2
            propagate_group = None
        elif mode is InstructionMode.PROPAGATE:
            propagate_group = _match_propagate_group(op_name, mode, frozenset(incoming))
            combined_register_type = propagate_group.group_type
        else:
            raise SamplexBuildError(
                f"Encountered unsupported {op_name} propagation with mode {mode} and "
                f"incoming virtual gates {incoming}."
            )

        # Add combine/slice node (may be skipped for trivial slices).
        combine_node_idx, actual_register_name = self.add_combine_node(
            samplex,
            pre_propagate_idx,
            pre_nodes_to_nodes,
            order,
            register_names,
            combined_register_name,
            combined_register_type,
        )

        # Create the propagation node using the actual register name.
        if mode is InstructionMode.MULTIPLY and pre_propagate.operation.num_qubits == 1:
            if pre_propagate.operation.is_parameterized():
                param_idxs = [
                    samplex.append_parameter_expression(param) for _, param in pre_propagate.params
                ]
                if pre_propagate.direction is Direction.LEFT:
                    propagate_node = RightU2ParametricMultiplicationNode(
                        op_name, actual_register_name, param_idxs
                    )
                else:
                    propagate_node = LeftU2ParametricMultiplicationNode(
                        op_name, actual_register_name, param_idxs
                    )
            else:
                if op_name in SUPPORTED_1Q_FRACTIONAL_GATES:
                    register = get_fractional_gate_register(
                        op_name, np.array(pre_propagate.bounded_params)
                    )
                else:
                    register = U2Register(np.array(pre_propagate.operation).reshape(1, 1, 2, 2))
                if pre_propagate.direction is Direction.LEFT:
                    propagate_node = RightMultiplicationNode(register, actual_register_name)
                else:
                    propagate_node = LeftMultiplicationNode(register, actual_register_name)
        else:
            if op_name in propagate_group.invariants:
                propagate_node = None
            else:
                node_class = (
                    PropagateLocalPauliNode
                    if pre_propagate.commutant_twirl
                    else propagate_group.node_class
                )
                propagate_node = node_class(
                    op_name,
                    actual_register_name,
                    np.array(list(pre_propagate.partition), dtype=np.intp),
                )

        if propagate_node is not None:
            node_idx = samplex.add_node(propagate_node)
            samplex.add_edge(combine_node_idx, node_idx)
        else:
            node_idx = combine_node_idx

        pre_nodes_to_nodes[pre_propagate_idx] = node_idx

        for pre_successor_idx in self.graph.successor_indices(pre_propagate_idx):
            register_names[pre_successor_idx][pre_propagate_idx] = actual_register_name

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
        combine_node_idx, actual_register_name = self.add_combine_node(
            samplex,
            pre_node_idx,
            pre_nodes_to_nodes,
            order,
            register_names,
            combined_name,
            VirtualType.U2,
        )

        collect = CollectTemplateValues(
            "parameter_values",
            pre_node.param_idxs,
            actual_register_name,
            VirtualType.U2,
            np.arange(len(all_subsystems)),
            pre_node.synth,
        )

        samplex.add_edge(combine_node_idx, samplex.add_node(collect))

    def add_measure_propagate_node(
        self,
        samplex: Samplex,
        pre_node_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ):
        """Lower a :class:`~.PreMeasure` node to samplex nodes.

        Args:
            samplex: The samplex to add nodes to.
            pre_node_idx: The index of the PreMeasure node.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to topological order.
            register_names: A map for register name tracking between nodes.
        """
        pre_node = cast(PreMeasure, self.graph[pre_node_idx])
        reg_idx = order[pre_node_idx]
        num_subsystems = len(pre_node.subsystems)

        # Combine incoming registers into a single Pauli register
        combined_name = f"meas_prop_{reg_idx}"
        combine_node_idx, actual_register_name = self.add_combine_node(
            samplex,
            pre_node_idx,
            pre_nodes_to_nodes,
            order,
            register_names,
            combined_name,
            VirtualType.PAULI,
        )

        z2_name_a = f"meas_prop_z2a_{reg_idx}"
        pauli_to_z2_a = SliceRegisterNode(
            VirtualType.PAULI,
            VirtualType.Z2,
            actual_register_name,
            z2_name_a,
            np.arange(num_subsystems),
        )
        p2z_a_idx = samplex.add_node(pauli_to_z2_a)
        samplex.add_edge(combine_node_idx, p2z_a_idx)

        creg_groups: dict[str, tuple[list[int], list[int]]] = {}
        for i, (name, offset) in enumerate(zip(pre_node.creg_names, pre_node.creg_offsets)):
            creg_groups.setdefault(name, ([], []))[0].append(i)
            creg_groups[name][1].append(offset)

        for creg_name, (sub_idxs, out_idxs) in creg_groups.items():
            z2_collect = CollectZ2ToOutputNode(
                z2_name_a,
                np.array(sub_idxs, dtype=np.uint32),
                f"measurement_flips.{creg_name}",
                out_idxs,
            )
            samplex.add_edge(p2z_a_idx, samplex.add_node(z2_collect))

        if not self.graph.successors(pre_node_idx):
            return

        z2_name_b = f"meas_prop_z2b_{reg_idx}"

        pauli_to_z2_b = SliceRegisterNode(
            VirtualType.PAULI,
            VirtualType.Z2,
            actual_register_name,
            z2_name_b,
            np.arange(num_subsystems),
        )
        p2z_b_idx = samplex.add_node(pauli_to_z2_b)
        samplex.add_edge(p2z_a_idx, p2z_b_idx)

        x_only_name = f"meas_prop_x_{reg_idx}"
        z2_to_pauli = SliceRegisterNode(
            VirtualType.Z2, VirtualType.PAULI, z2_name_b, x_only_name, np.arange(num_subsystems)
        )
        z2p_idx = samplex.add_node(z2_to_pauli)
        samplex.add_edge(p2z_b_idx, z2p_idx)

        phase_name = f"meas_prop_phase_{reg_idx}"
        phase_dist = UniformPauliSubset.from_name(num_subsystems, "phase")
        phase_sampler = DistributionSamplingNode(phase_name, phase_dist)
        phase_idx = samplex.add_node(phase_sampler)

        output_name = f"meas_prop_out_{reg_idx}"
        idxs = list(range(num_subsystems))
        combine_output = CombineRegistersNode(
            output_type=VirtualType.PAULI,
            output_register_name=output_name,
            num_output_subsystems=num_subsystems,
            operands={
                x_only_name: (idxs, idxs, VirtualType.PAULI),
                phase_name: (idxs, idxs, VirtualType.PAULI),
            },
        )
        combine_out_idx = samplex.add_node(combine_output)
        samplex.add_edge(z2p_idx, combine_out_idx)
        samplex.add_edge(phase_idx, combine_out_idx)

        pre_nodes_to_nodes[pre_node_idx] = combine_out_idx
        for pre_successor_idx in self.graph.successor_indices(pre_node_idx):
            register_names[pre_successor_idx][pre_node_idx] = output_name

    def add_reset_propagate_node(
        self,
        samplex: Samplex,
        pre_reset_idx: NodeIndex,
        pre_nodes_to_nodes: dict[NodeIndex, NodeIndex],
        order: dict[NodeIndex, int],
        register_names: dict[NodeIndex, dict[NodeIndex, RegisterName]],
    ):
        """Lower a :class:`~.PreReset` node to samplex nodes.

        Args:
            samplex: The samplex to add nodes to.
            pre_node_idx: The index of the PreReset node.
            pre_nodes_to_nodes: A map from pre-node indices to node indices.
            order: A map from pre-node indices to topological order.
            register_names: A map for register name tracking between nodes.
        """
        pre_reset = cast(PreReset, self.graph[pre_reset_idx])
        reg_idx = order[pre_reset_idx]

        node = DistributionSamplingNode(
            reg_name := f"reset_prop_phase_{reg_idx}",
            UniformPauliSubset.from_name(len(pre_reset.subsystems), "phase"),
        )
        node_idx = samplex.add_node(node)

        pre_nodes_to_nodes[pre_reset_idx] = node_idx

        for pre_successor_idx in self.graph.successor_indices(pre_reset_idx):
            register_names[pre_successor_idx][pre_reset_idx] = reg_name

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
    ) -> "Figure":
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
