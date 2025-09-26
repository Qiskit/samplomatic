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

"""BoxIfElseBuilder"""

from copy import deepcopy

import numpy as np
from qiskit.circuit import IfElseOp, QuantumCircuit

from ..aliases import ParamIndices, Qubit, QubitIndex
from ..partition import QubitPartition
from ..pre_samplex import DanglerMatch, PreSamplex
from ..pre_samplex.graph_data import Direction, PreCollect, PreCopy, PreEdge, PreEmit, PrePropagate
from ..synths import Synth
from .param_iter import ParamIter
from .specs import InstructionMode, InstructionSpec


class BoxIfElseBuilder:
    def __init__(
        self,
        op,
        pre_samplex: PreSamplex,
        synth: Synth,
        param_iter: ParamIter,
    ):
        self.op = op
        self.pre_samplex = pre_samplex
        self.synth = synth
        self.param_iter = param_iter

    def block_qubit_map(self, block) -> dict[Qubit, QubitIndex]:
        block_map = {i_q: b_q for i_q, b_q in zip(self.op.qubits, block.qubits)}
        qubit_map = self.pre_samplex.qubit_map
        return {block_map[i_q]: qubit_map[i_q] for i_q in qubit_map if i_q in block_map}

    def append_propagate(self, block: QuantumCircuit, new_block: QuantumCircuit):
        for instr in block:
            new_params = []
            param_mapping = []
            for param in instr.operation.params:
                param_mapping.append([self.param_iter.idx, param])
                new_params.append(next(self.param_iter))

            new_op = type(instr.operation)(*new_params) if new_params else instr.operation
            new_block.append(new_op, instr.qubits, instr.clbits)
            mode = InstructionMode.MULTIPLY if len(instr.qubits) == 1 else InstructionMode.PROPAGATE
            self.pre_samplex.add_propagate(instr, InstructionSpec(params=new_params, mode=mode))

    def append_template(self, block: QuantumCircuit, new_block: QuantumCircuit) -> ParamIndices:
        start = self.param_iter.idx
        num_params = len(block.qubits) * self.synth.num_params
        params = np.arange(start, start + num_params, dtype=np.intp)
        for qubit in new_block.qubits:
            for instr in self.synth.make_template([qubit], self.param_iter):
                new_block.append(instr)
        return params.reshape(len(block.qubits), -1)


class BoxRightIfElseBuilder(BoxIfElseBuilder):
    def build_block(self, block):
        block = (
            block
            if block is not None
            else QuantumCircuit(
                self.op.operation.params[0].qubits, self.op.operation.params[0].clbits
            )
        )

        new_block = QuantumCircuit(block.qubits, block.clbits)
        pre_samplex = self.pre_samplex.remap(qubit_map=self.block_qubit_map(block))

        qubits = QubitPartition.from_elements(new_block.qubits)
        subsystems = pre_samplex.qubits_to_indices(qubits)
        dangler_match = DanglerMatch(node_types=(PreEmit, PrePropagate))

        new_danglers = []
        for node_idx, partition in pre_samplex.find_then_remove_danglers(dangler_match, subsystems):
            copy_idx = pre_samplex.graph.add_node(PreCopy(partition, Direction.RIGHT))
            edge = PreEdge(partition, Direction.RIGHT)
            pre_samplex.graph.add_edge(node_idx, copy_idx, edge)
            new_danglers.append((copy_idx, partition))

        for node_idx, partition in new_danglers:
            pre_samplex.add_dangler(partition.all_elements, node_idx)

        self.append_propagate(block, new_block)
        params = self.append_template(block, new_block)
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

        if_else_op = IfElseOp(self.op.operation.condition, if_block, else_block, self.op.label)

        return if_else_op


class BoxLeftIfElseBuilder(BoxIfElseBuilder):
    def build_block(self, block):
        block = (
            block
            if block is not None
            else QuantumCircuit(
                self.op.operation.params[0].qubits, self.op.operation.params[0].clbits
            )
        )

        new_block = QuantumCircuit(block.qubits, block.clbits)
        params = self.append_template(block, new_block)

        pre_samplex = self.pre_samplex.remap(qubit_map=self.block_qubit_map(block))
        qubits = QubitPartition.from_elements(new_block.qubits)
        subsystems = pre_samplex.qubits_to_indices(qubits)
        dangler_match = DanglerMatch(node_types=(PreCollect, PrePropagate))

        list(pre_samplex.find_then_remove_danglers(dangler_match, subsystems))
        pre_samplex.add_collect(qubits, self.synth, params)
        self.append_propagate(block, new_block)

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

        if_else_op = IfElseOp(self.op.operation.condition, if_block, else_block, self.op.label)

        return if_else_op
