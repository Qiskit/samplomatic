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

"""Graph Data"""

from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from qiskit.circuit.gate import Gate

from ..aliases import OutputIndex, ParamIndices, ParamSpec, StrRef
from ..annotations import GroupMode
from ..builders.specs import FrameChangeMode, InstructionMode
from ..constants import SUPPORTED_FRACTIONAL_GATES, Direction
from ..exceptions import SamplexBuildError
from ..partition import QubitIndicesPartition, SubsystemIndicesPartition
from ..synths import Synth
from ..trace_info import TraceInfo
from ..virtual_registers import VirtualType
from ..visualization.hover_style import EdgeStyle, NodeStyle


def _merge_trace_info(nodes: list["PreNode"]) -> "TraceInfo | None":
    """Merge trace info from a list of nodes into a single TraceInfo, or None."""
    merged: TraceInfo | None = None
    for node in nodes:
        if node.trace_info is not None:
            if merged is None:
                merged = TraceInfo({k: set(v) for k, v in node.trace_info.trace_refs.items()})
            else:
                merged.merge(node.trace_info)
    return merged


@dataclass
class PreNode:
    """The node type used during samplex building, different than the type in the final samplex."""

    subsystems: QubitIndicesPartition
    """The subsystems that virtual gates act on."""

    direction: Direction
    """The direction of virtual gates that can interact with this node."""

    trace_info: TraceInfo | None = field(default=None, compare=False, repr=False, kw_only=True)
    """Debug trace information, populated when building with ``debug=True``."""

    def get_style(self) -> NodeStyle:
        """Summarizes the style of this node when plotted via :func:`~.plot_graph`."""
        style = NodeStyle(title=type(self).__name__).append_list_data(
            "Subsystems", list(self.subsystems)
        )
        if self.trace_info is not None:
            style.append_dict_data("trace_refs", self.trace_info.style_data())
        return style


@dataclass
class PreEdge:
    """Edge data on a samplex builder's graph."""

    subsystems: QubitIndicesPartition
    """The subsystems that virtual gates act on."""

    direction: Direction
    """Whether the edge is moving forwards or backwards in circuit-time."""

    force_register_copy: bool = False
    """Whether the edge should force the receiving node to get a copy of the register."""

    def get_style(self) -> EdgeStyle:
        """Summarizes the style of this node when plotted via :func:`~.plot_graph`."""
        return (
            EdgeStyle(
                title=type(self).__name__,
            )
            .append_data("Subsystems", list(self.subsystems))
            .append_data("Direction", self.direction.name)
            .append_data("Force copy", self.force_register_copy)
        )

    def add_subsystems(self, new_subsystems: QubitIndicesPartition):
        """Add subsystems to an existing ``PreEdge``"""
        for new_subsystem in new_subsystems:
            self.subsystems.add(new_subsystem)


@dataclass
class PreCollect(PreNode):
    """The collection node type used during samplex building."""

    synth: Synth
    """The synthesizer to convert virtual to physical gates."""

    param_idxs: ParamIndices
    """The indices of the template circuit to write the synthesis results to.

    This should be ordered according to :attr:`~PreCollect.subsystems`.
    """

    def get_style(self):
        style = super().get_style().append_data("Direction", self.direction.name)
        style.marker = "bowtie"
        style.color = "blue"
        style.size = 30
        return style

    def __eq__(self, other):
        return (
            isinstance(other, PreCollect)
            and self.subsystems == other.subsystems
            and self.direction == other.direction
            and type(self.synth) is type(other.synth)
            and np.array_equal(self.param_idxs, other.param_idxs)
        )

    def add_subsystems(self, new_subsystems: QubitIndicesPartition, new_param_idxs: ParamIndices):
        """Add subsystems to existing ``PreCollect`` node."""
        # Switch to a list for dynamic sizing?
        self.param_idxs = np.concatenate((self.param_idxs, new_param_idxs))
        for new_subsystem in new_subsystems:
            self.subsystems.add(new_subsystem)


@dataclass
class PreMeasure(PreNode):
    """The propagation node type used for measurements during samplex building."""

    creg_names: list[str]
    """The classical register names this measurement writes to, one per subsystem."""

    creg_offsets: list[int]
    """The indices within the classical registers, one per subsystem."""

    direction: Direction = field(init=False)

    def __post_init__(self):
        self.direction = Direction.RIGHT

    def to_key(self) -> Hashable:
        return "measure"

    @classmethod
    def from_cluster(cls, nodes: list["PreMeasure"]) -> "PreMeasure":
        combined_subsystems = QubitIndicesPartition.union(*(n.subsystems for n in nodes))
        creg_names = [name for node in nodes for name in node.creg_names]
        creg_offsets = [off for node in nodes for off in node.creg_offsets]
        merged_trace_info = _merge_trace_info(nodes)
        return cls(combined_subsystems, creg_names, creg_offsets, trace_info=merged_trace_info)

    def get_style(self) -> NodeStyle:
        creg_str = ", ".join(
            f"{name}[{off}]" for name, off in zip(self.creg_names, self.creg_offsets)
        )
        style = (
            super()
            .get_style()
            .append_data("Direction", self.direction.name)
            .append_data("Classical Registers", creg_str)
        )
        style.marker = "diamond"
        style.color = "green"
        style.size = 30
        return style

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, PreMeasure)
            and self.subsystems == other.subsystems
            and self.creg_names == other.creg_names
            and self.creg_offsets == other.creg_offsets
        )


@dataclass
class PreEmit(PreNode):
    """The emission node type used during samplex building."""

    register_type: GroupMode
    """The type and distribution of virtual gates to emit."""

    twirl_gate: str | None = field(default=None, kw_only=True)
    """The gate name used for gate-dependent sampling, or ``None``."""

    def get_style(self):
        style = (
            super()
            .get_style()
            .append_data("Direction", self.direction.name)
            .append_data("Register Type", self.register_type)
        )
        style.marker = "star"
        style.color = "red"
        style.size = 30
        return style

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, PreEmit)
            and self.subsystems == other.subsystems
            and self.register_type is other.register_type
            and self.twirl_gate == other.twirl_gate
        )


@dataclass
class PreReset(PreEmit):
    """The emit node type used for resets during samplex building."""

    direction: Direction = field(init=False, kw_only=True)
    register_type: GroupMode = field(init=False, kw_only=True)

    def __post_init__(self):
        self.direction = Direction.RIGHT
        self.register_type = GroupMode.PHASE

    def to_key(self) -> Hashable:
        return "reset"

    @classmethod
    def from_cluster(cls, nodes: list["PreReset"]) -> "PreReset":
        combined_subsystems = QubitIndicesPartition.union(*(n.subsystems for n in nodes))
        merged_trace_info = _merge_trace_info(nodes)
        return cls(combined_subsystems, trace_info=merged_trace_info)

    def get_style(self) -> NodeStyle:
        style = super().get_style().append_data("Direction", self.direction.name)
        style.marker = "hexagon2"
        style.color = "orange"
        style.size = 30
        return style

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, PreReset) and self.subsystems == other.subsystems


@dataclass
class PrePropagate(PreNode):
    """The propagation node type used during samplex building."""

    operation: Gate
    """The operation to propagate through.

    Even when the ``PrePropagate`` represents more than one subsystem (i.e more than one operation)
    only a single common ``Gate`` object is stored, and possible parameters are stored elsewhere.
    """

    partition: SubsystemIndicesPartition
    """A partition of subsystem indices, each of which is propagated jointly.

    For example, a CX gate propagates pairs of single-qubit subsystems jointly. In this case,
    a partition would be a list of pairs of subsystem indices, where pairs are disjoint from
    each other.
    """

    mode: InstructionMode
    """How the operation acts on virtual gates."""

    params: ParamSpec
    """The parameters required by the node."""

    bounded_params: list[float] | None = None
    """List of bounded params if ``operation`` is a fractional gate with a bounded parameter.

    If the node involves a relevant operation with a single subsystem, the parameter is
    automatically extracted from the operation.
    """

    commutant_twirl: bool = False
    """Whether this operation should be twirled with its commutant.

    If the operation is not a fractional gate, this value will be ``False``. If it is a
    fractional gate, ``True`` signals that it should be twirled by its commutant, while
    ``False`` signals that its angle has been bound to a Clifford.
    """

    def __post_init__(self):
        # Current construction assumes one parameter per gate.
        if (
            self.operation.name in SUPPORTED_FRACTIONAL_GATES
            and not self.operation.is_parameterized()
        ):
            if self.bounded_params is None:
                self.bounded_params = self.operation.params
            if len(self.bounded_params) != len(self.partition):
                raise SamplexBuildError(
                    "The number of bounded parameters does not match the number of subsystems."
                )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Direction", self.direction.name)
            .append_data("Operation", self.operation.name)
            .append_data("Partition", str(self.partition))
        )

    def to_key(self) -> "PrePropagateKey":
        return PrePropagateKey(
            mode=self.mode,
            operation_name=self.operation.name,
            direction=self.direction,
            is_parameterized=self.operation.is_parameterized(),
            commutant_twirl=self.commutant_twirl,
        )

    @classmethod
    def from_cluster(cls, nodes: list["PrePropagate"]) -> "PrePropagate":
        combined_subsystems = QubitIndicesPartition.union(*(n.subsystems for n in nodes))
        num_elements = nodes[0].partition.num_elements_per_part
        num_parts = len(combined_subsystems) // num_elements
        combined_partition = SubsystemIndicesPartition(
            num_elements,
            [tuple(range(i * num_elements, (i + 1) * num_elements)) for i in range(num_parts)],
        )
        merged_trace_info = _merge_trace_info(nodes)

        if any(
            n.operation.name in SUPPORTED_FRACTIONAL_GATES and not n.operation.is_parameterized()
            for n in nodes
        ):
            params = [p for node in nodes for p in node.operation.params]
            return cls(
                combined_subsystems,
                nodes[0].direction,
                nodes[0].operation,
                combined_partition,
                nodes[0].mode,
                params=[],
                bounded_params=params,
                commutant_twirl=nodes[0].commutant_twirl,
                trace_info=merged_trace_info,
            )
        else:
            params = [p for node in nodes for p in node.params]
            return cls(
                combined_subsystems,
                nodes[0].direction,
                nodes[0].operation,
                combined_partition,
                nodes[0].mode,
                params=params,
                commutant_twirl=nodes[0].commutant_twirl,
                trace_info=merged_trace_info,
            )

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, PrePropagate)
            and self.subsystems == other.subsystems
            and self.operation == other.operation
            and self.direction == other.direction
        )


@dataclass
class PrePropagateKey:
    """A key used to identify the "type" of ``PrePropagate`` nodes for clustering purposes.

    The key includes only properties of the node for which a difference between two nodes
    would make the nodes unmergeable. This, however, doesn't automatically mean that a matching key
    makes nodes mergable. Other considerations in determining the mergeability include the
    subsystems and predecessor nodes.
    """

    mode: InstructionMode
    """The mode of the ``PrePropagate`` node."""

    operation_name: str
    """The name of the operation of the ``PrePropagate`` node."""

    direction: Direction
    """The direction of the ``PrePropagate`` node."""

    is_parameterized: bool
    """Whether or not the operation is parameterized."""

    commutant_twirl: bool = False
    """Whether this operation should be twirled with its commutant."""

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, PrePropagateKey)
            and self.mode == other.mode
            and self.operation_name == other.operation_name
            and self.direction == other.direction
            and self.is_parameterized == other.is_parameterized
            and self.commutant_twirl == other.commutant_twirl
        )

    def __hash__(self):
        return hash(
            (
                self.mode,
                self.operation_name,
                self.direction,
                self.is_parameterized,
                self.commutant_twirl,
            )
        )


@dataclass
class PreChangeBasis(PreEmit):
    """The basis emit node type used during samplex building."""

    register_type: VirtualType
    """The virtual register type of the basis change."""

    basis_ref: StrRef
    """Unique identifier of this basis change."""

    basis_change: FrameChangeMode
    """What kind of basis change to use."""

    def get_style(self) -> NodeStyle:
        return super().get_style().append_data("Basis Identifier", self.basis_ref)


@dataclass
class PreInjectNoise(PreEmit):
    """The inject noise emit node type used during samplex building."""

    register_type: VirtualType
    """The virtual register type of the noise injection."""

    ref: StrRef
    """Unique identifier of the Pauli Lindblad map to use for noise injection."""

    modifier_ref: StrRef
    """Unique identifier for modifiers to apply to the Pauli Lindblad map on this node."""

    sign_idx: OutputIndex
    """The index of the output array to write the sign to."""

    def get_style(self) -> NodeStyle:
        return super().get_style().append_data("ref", self.ref)
