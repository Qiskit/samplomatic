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

import numpy as np
from qiskit.circuit import IfElseOp, QuantumCircuit
from rustworkx import PyDiGraph

from ..aliases import ParamIndices, Qubit, QubitIndex
from ..partition import QubitIndicesPartition, QubitPartition
from ..pre_samplex import PreSamplex
from ..pre_samplex.graph_data import Direction, PreEdge, PreNode
from ..synths import Synth
from .param_iter import ParamIter
from .specs import InstructionMode, InstructionSpec


class BoxIfElseBuilder:
    def __init__(self, op, synth: Synth, param_iter: ParamIter, qubit_map: dict[Qubit, QubitIndex]):
        self.op = op
        self.synth = synth
        self.param_iter = param_iter
        self.qubit_map = qubit_map

    def block_qubit_map(self, block) -> dict[Qubit, QubitIndex]:
        block_map = {i_q: b_q for i_q, b_q in zip(self.op.qubits, block.qubits)}
        return {block_map[i_q]: self.qubit_map[i_q] for i_q in self.qubit_map if i_q in block_map}

    def append_propagate(
        self, block: QuantumCircuit, new_block: QuantumCircuit, pre_samplex: PreSamplex
    ):
        for instr in block:
            new_params = []
            param_mapping = []
            for param in instr.operation.params:
                param_mapping.append([self.param_iter.idx, param])
                new_params.append(next(self.param_iter))

            new_op = type(instr.operation)(*new_params) if new_params else instr.operation
            new_block.append(new_op, instr.qubits, instr.clbits)
            pre_samplex.add_propagate(
                instr, InstructionSpec(params=new_params, mode=InstructionMode.PROPAGATE)
            )

    def append_template(self, block: QuantumCircuit, new_block: QuantumCircuit) -> ParamIndices:
        start = self.param_iter.idx
        num_params = len(block.qubits) * self.synth.num_params
        params = np.arange(start, start + num_params, dtype=np.intp)
        for qubit in new_block.qubits:
            for instr in self.synth.make_template([qubit], self.param_iter):
                new_block.append(instr)
        return params


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
        qubit_map = self.block_qubit_map(block)
        pre_samplex = PreSamplex(qubit_map=qubit_map)
        pre_samplex.add_copy(
            qubits := QubitPartition.from_elements(new_block.qubits), Direction.RIGHT
        )
        self.append_propagate(block, new_block, pre_samplex)
        params = self.append_template(block, new_block)
        pre_samplex.add_collect(qubits, self.synth, params)

        return new_block, pre_samplex

    def build(self):
        if_block, if_samplex = self.build_block(self.op.params[0])
        else_block, else_samplex = self.build_block(self.op.params[1])

        if_else_op = IfElseOp(self.op.operation.condition, if_block, else_block, self.op.label)

        graph = PyDiGraph(multigraph=True)
        qubits = QubitIndicesPartition.from_elements(
            v for k, v in self.qubit_map.items() if k in self.op.qubits
        )

        base_idx = graph.add_node(PreNode(qubits, Direction.RIGHT))
        if_idx = graph.add_node(PreNode(qubits, Direction.RIGHT))
        graph.add_edge(base_idx, if_idx, PreEdge(qubits, Direction.RIGHT))
        graph.substitute_node_with_subgraph(
            if_idx,
            if_samplex.graph,
            lambda source, target, weight: if_samplex.graph.node_indices()[0],
        )

        else_idx = graph.add_node(PreNode(qubits, Direction.RIGHT))
        graph.add_edge(base_idx, else_idx, PreEdge(qubits, Direction.RIGHT))
        graph.substitute_node_with_subgraph(
            else_idx,
            else_samplex.graph,
            lambda source, target, weight: else_samplex.graph.node_indices()[0],
        )

        return if_else_op, graph


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
        pre_samplex = PreSamplex(qubit_map=self.block_qubit_map(block))

        pre_samplex.add_collect(
            qubits := QubitPartition.from_elements(new_block.qubits), self.synth, params
        )
        self.append_propagate(block, new_block, pre_samplex)
        pre_samplex.add_copy(qubits, Direction.LEFT)

        return new_block, pre_samplex

    def build(self):
        if_block, if_samplex = self.build_block(self.op.params[0])
        else_block, else_samplex = self.build_block(self.op.params[1])

        if_else_op = IfElseOp(self.op.operation.condition, if_block, else_block, self.op.label)

        graph = PyDiGraph(multigraph=True)
        qubits = QubitIndicesPartition.from_elements(
            v for k, v in self.qubit_map.items() if k in self.op.qubits
        )

        base_idx = graph.add_node(PreNode(qubits, Direction.LEFT))
        if_idx = graph.add_node(PreNode(qubits, Direction.LEFT))
        graph.add_edge(base_idx, if_idx, PreEdge(qubits, Direction.LEFT))
        graph.substitute_node_with_subgraph(
            if_idx,
            if_samplex.graph,
            lambda source, target, weight: if_samplex.graph.node_indices()[-1],
        )

        else_idx = graph.add_node(PreNode(qubits, Direction.LEFT))
        graph.add_edge(base_idx, else_idx, PreEdge(qubits, Direction.LEFT))
        graph.substitute_node_with_subgraph(
            else_idx,
            else_samplex.graph,
            lambda source, target, weight: else_samplex.graph.node_indices()[-1],
        )

        return if_else_op, graph
