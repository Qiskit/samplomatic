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

"""Graph Data"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from qiskit.circuit.gate import Gate

from ..aliases import ClbitIndex, OutputIndex, ParamIndices, StrRef, SubsystemIndex
from ..annotations import VirtualType
from ..builders.specs import InstructionMode, InstructionSpec
from ..constants import Direction
from ..partition import QubitIndicesPartition, SubsystemIndicesPartition
from ..synths import Synth
from ..visualization.hover_style import EdgeStyle, NodeStyle


@dataclass
class PreNode:
    """The node type used during samplex building, different than the type in the final samplex."""

    subsystems: QubitIndicesPartition
    """The subsystems that virtual gates act on."""

    direction: Direction
    """The direction of virtual gates that cat interact with this node."""

    def get_style(self) -> NodeStyle:
        """Summarizes the style of this node when plotted via :func:`~.plot_graph`."""
        return NodeStyle(title=type(self).__name__).append_data("Subsystems", list(self.subsystems))


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
            and self.param_idxs == other.param_idxs
        )

    def add_subsystems(self, new_subsystems: QubitIndicesPartition, new_param_idxs: ParamIndices):
        """Add subsystems to existing ``PreCollect`` node."""
        # Switch to a list for dynamic sizing?
        self.param_idxs = np.concatenate((self.param_idxs, new_param_idxs))
        for new_subsystem in new_subsystems:
            self.subsystems.add(new_subsystem)


@dataclass
class PreZ2Collect(PreNode):
    """The Z2-collection node type used during samplex building."""

    direction: Direction = field(init=False)

    clbit_idxs: dict[str, list[ClbitIndex]]
    """A dictionary from classical register names to indices this node writes to."""

    subsystems_idxs: dict[str, list[SubsystemIndex]]
    """A dictionary from classical register names to subsystem indices from which to collect."""

    def __post_init__(self):
        self.direction = Direction.RIGHT

    def get_style(self):
        style = super().get_style().append_data("Direction", self.direction.name)
        style.marker = "bowtie"
        style.color = "purple"
        style.size = 30
        return style

    def __eq__(self, other):
        return (
            isinstance(other, PreZ2Collect)
            and self.subsystems == other.subsystems
            and self.direction == other.direction
            and self.clbit_idxs == other.clbit_idxs
            and self.subsystems_idxs == other.subsystems_idxs
        )


@dataclass
class PreEmit(PreNode):
    """The emission node type used during samplex building."""

    register_type: VirtualType
    """The type of virtual gates to emit."""

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
        )


@dataclass
class PrePropagate(PreNode):
    """The propagation node type used during samplex building."""

    operation: Gate
    """The operation to propagate through."""

    partition: SubsystemIndicesPartition
    """A partition of subsystem indices, each of which is propagated jointly.

    For example, a CX gate propagates pairs of single-qubit subsystems jointly. In this case,
    a partition would be a list of pairs of subsystem indices, where pairs are disjoint from
    each other.
    """

    spec: InstructionSpec
    """Specification for how the operation acts on virtual gates."""

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Direction", self.direction.name)
            .append_data("Operation", self.operation.name)
            .append_data("Partition", str(self.partition))
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

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, PrePropagateKey)
            and self.mode == other.mode
            and self.operation_name == other.operation_name
            and self.direction == other.direction
        )

    def __hash__(self):
        return hash((self.mode, self.operation_name, self.direction))


@dataclass
class PreBasisTransform(PreEmit):
    """The basis emit node type used during samplex building."""

    basis_ref: StrRef
    """Unique identifier of this basis transform."""

    def get_style(self) -> NodeStyle:
        return super().get_style().append_data("Basis Identifier", self.basis_ref)


@dataclass
class PreInjectNoise(PreEmit):
    """The inject noise emit node type used during samplex building."""

    ref: StrRef
    """Unique identifier of this noise map."""

    modifier_ref: StrRef
    """Unique identifier for modifiers applied to this noise map."""

    sign_idx: OutputIndex
    """The index of the output array to write the sign to."""

    def get_style(self) -> NodeStyle:
        return super().get_style().append_data("ref", self.ref)
