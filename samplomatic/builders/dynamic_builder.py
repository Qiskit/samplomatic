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

"""DynamicBuilder"""

import abc
from copy import deepcopy
from typing import Generic, TypeVar

import numpy as np
from qiskit.circuit import IfElseOp, QuantumCircuit

from ..aliases import CircuitInstruction, ParamIndices, Qubit, QubitIndex
from ..exceptions import BuildError
from ..partition import QubitPartition
from ..pre_samplex import DanglerMatch, PreSamplex
from ..pre_samplex.graph_data import Direction, PreCollect, PreCopy, PreEdge, PreEmit, PrePropagate
from ..synths import Synth
from .param_iter import ParamIter
from .specs import InstructionMode

T = TypeVar("T")


class DynamicBuilder(abc.ABC, Generic[T]):
    """Base class for building dressed conditional operations.

    This class does not inherit from :class:`~.Builder` as it does not add the operations to the
    template. Instead, it constructs an operation of the same type while adding nodes to the
    corresponding samplex.

    Args:
        op: The control flow operation to build.
        pre_samplex: The pre-samplex to use.
        synth: The synthesizer to use for the dressing.
        param_iter: An iterator over parameters to use in the circuit being built.
    """

    def __init__(
        self,
        op: T,
        pre_samplex: PreSamplex,
        synth: Synth,
        param_iter: ParamIter,
    ):
        self.op = op
        self.pre_samplex = pre_samplex
        self.synth = synth
        self.param_iter = param_iter

    def _block_qubit_map(self, block) -> dict[Qubit, QubitIndex]:
        block_map = {i_q: b_q for i_q, b_q in zip(self.op.qubits, block.qubits)}
        qubit_map = self.pre_samplex.qubit_map
        return {block_map[i_q]: qubit_map[i_q] for i_q in qubit_map if i_q in block_map}

    def _parse_mq_gate(self, instr: CircuitInstruction, new_block: QuantumCircuit):
        new_params = []
        param_mapping = []
        for param in instr.operation.params:
            param_mapping.append([self.param_iter.idx, param])
            new_params.append(next(self.param_iter))

        new_op = type(instr.operation)(*new_params) if new_params else instr.operation
        new_block.append(new_op, instr.qubits, instr.clbits)
        self.pre_samplex.add_propagate(instr, mode=InstructionMode.PROPAGATE, params=param_mapping)

    def _parse_sq_gate(self, instr: CircuitInstruction):
        new_params = []
        if instr.operation.is_parameterized():
            new_params.extend((None, param) for param in instr.operation.params)
        self.pre_samplex.add_propagate(instr, mode=InstructionMode.MULTIPLY, params=new_params)

    def _append_dressed_layer(self, new_block: QuantumCircuit) -> ParamIndices:
        start = self.param_iter.idx
        num_params = len(new_block.qubits) * self.synth.num_params
        params = np.arange(start, start + num_params, dtype=np.intp)
        for qubit in new_block.qubits:
            for instr in self.synth.make_template([qubit], self.param_iter):
                new_block.append(instr)
        return params.reshape(len(new_block.qubits), -1)

    @abc.abstractmethod
    def build_block(self) -> QuantumCircuit:
        """Build a block of a control flow operation."""

    @abc.abstractmethod
    def build(self) -> T:
        """Build the operation."""


class BoxLeftIfElseBuilder(DynamicBuilder[IfElseOp]):
    def build_block(self, block) -> QuantumCircuit:
        block = (
            block
            if block is not None
            else QuantumCircuit(
                self.op.operation.params[0].qubits, self.op.operation.params[0].clbits
            )
        )

        new_block = QuantumCircuit(block.qubits, block.clbits)
        params = self._append_dressed_layer(new_block)

        pre_samplex = self.pre_samplex.remap(qubit_map=self._block_qubit_map(block))
        qubits = QubitPartition.from_elements(new_block.qubits)
        subsystems = pre_samplex.qubits_to_indices(qubits)
        dangler_match = DanglerMatch(Direction.LEFT, node_types=(PreCollect, PrePropagate))

        list(pre_samplex.find_then_remove_danglers(dangler_match, subsystems))
        pre_samplex.add_collect(qubits, self.synth, params)

        entangled_qubits = set()
        for instr in block:
            if len(instr.qubits) == 1:
                if not entangled_qubits.isdisjoint(instr.qubits):
                    raise BuildError(
                        "Cannot have entanglers before single-qubit gates in a left-dressed box."
                    )
                self._parse_sq_gate(instr)
            else:
                entangled_qubits.update(instr.qubits)
                self._parse_mq_gate(instr, new_block)

        copy_idxs = []
        for node_idx, partition in pre_samplex.find_then_remove_danglers(dangler_match, subsystems):
            copy_idx = pre_samplex.graph.add_node(PreCopy(partition, Direction.LEFT))
            copy_idxs.append((copy_idx, partition))
            edge = PreEdge(partition, Direction.LEFT)
            pre_samplex.graph.add_edge(copy_idx, node_idx, edge)

        return new_block, copy_idxs

    def build(self):
        original_danglers = deepcopy(self.pre_samplex.get_all_danglers())
        if_block, if_danglers = self.build_block(self.op.params[0])
        self.pre_samplex.set_all_danglers(*original_danglers)
        else_block, else_danglers = self.build_block(self.op.params[1])

        for node_idx, subsystems in [*if_danglers, *else_danglers]:
            self.pre_samplex.add_dangler(
                subsystems.all_elements,
                node_idx,
            )

        return IfElseOp(self.op.operation.condition, if_block, else_block, self.op.label)


class BoxRightIfElseBuilder(DynamicBuilder[IfElseOp]):
    def build_block(self, block) -> QuantumCircuit:
        block = (
            block
            if block is not None
            else QuantumCircuit(
                self.op.operation.params[0].qubits, self.op.operation.params[0].clbits
            )
        )

        new_block = QuantumCircuit(block.qubits, block.clbits)
        pre_samplex = self.pre_samplex.remap(qubit_map=self._block_qubit_map(block))

        qubits = QubitPartition.from_elements(new_block.qubits)
        subsystems = pre_samplex.qubits_to_indices(qubits)
        dangler_match = DanglerMatch(Direction.RIGHT, node_types=(PreEmit, PrePropagate))

        new_danglers = []
        for node_idx, partition in pre_samplex.find_then_remove_danglers(dangler_match, subsystems):
            copy_idx = pre_samplex.graph.add_node(PreCopy(partition, Direction.RIGHT))
            edge = PreEdge(partition, Direction.RIGHT)
            pre_samplex.graph.add_edge(node_idx, copy_idx, edge)
            new_danglers.append((copy_idx, partition))

        for node_idx, partition in new_danglers:
            pre_samplex.add_dangler(partition.all_elements, node_idx)

        unentangled_qubits = set()
        for instr in block:
            if len(instr.qubits) == 1:
                unentangled_qubits.update(instr.qubits)
                self._parse_sq_gate(instr)
            else:
                if not unentangled_qubits.isdisjoint(instr.qubits):
                    raise BuildError(
                        "Cannot have entanglers after single-qubit gates in a right-dressed box."
                    )
                self._parse_mq_gate(instr, new_block)

        params = self._append_dressed_layer(new_block)
        collect_idx = pre_samplex.add_collect(qubits, self.synth, params)

        return new_block, (collect_idx, subsystems)

    def build(self):
        original_danglers = deepcopy(self.pre_samplex.get_all_danglers())
        if_block, if_dangler = self.build_block(self.op.params[0])
        self.pre_samplex.set_all_danglers(*original_danglers)
        else_block, else_dangler = self.build_block(self.op.params[1])

        for node_idx, subsystems in [if_dangler, else_dangler]:
            self.pre_samplex.add_dangler(
                subsystems.all_elements,
                node_idx,
            )

        return IfElseOp(self.op.operation.condition, if_block, else_block, self.op.label)
