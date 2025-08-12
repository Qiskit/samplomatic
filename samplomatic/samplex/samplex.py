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

"""Samplex"""

from collections.abc import Iterable, Sequence
from concurrent.futures import FIRST_EXCEPTION, Future, ThreadPoolExecutor, wait
from typing import TYPE_CHECKING

from numpy.random import Generator, SeedSequence, default_rng
from qiskit.circuit import Parameter, ParameterExpression
from qiskit.quantum_info import PauliLindbladMap
from rustworkx.rustworkx import PyDiGraph, topological_generations

from ..aliases import (
    EdgeIndex,
    InterfaceName,
    LayoutMethod,
    LayoutPresets,
    NodeIndex,
    NumSubsystems,
    ParamIndex,
    ParamSpec,
    RegisterName,
    StrRef,
)
from ..annotations import VirtualType
from ..exceptions import SamplexConstructionError, SamplexRuntimeError
from ..virtual_registers import VirtualRegister
from ..visualization import plot_graph
from .interfaces import MetadataOutput, SamplexInput, SamplexOutput, TensorSpecification
from .nodes import CollectionNode, EvaluationNode, Node, SamplingNode
from .parameter_expression_table import ParameterExpressionTable

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

RNG: Generator = default_rng()
"""The default randomness generator."""


class Samplex:
    """Performs sampling and parameter generation.

    This is achieved by traversing a graph where each node represents a different task, such as
    sampling random virtual group members, propagating Pauli group members past Clifford operations,
    composing single-qubit gate operations, and so on.
    """

    _RESERVED_INPUTS: frozenset[InterfaceName] = frozenset()
    _RESERVED_OUTPUTS: frozenset[InterfaceName] = frozenset()

    def __init__(self):
        self.graph = PyDiGraph[Node, None]()
        self._finalized = False
        self._param_table = ParameterExpressionTable()
        self._passthrough_params = None
        self._evaluation_streams: list[list[EvaluationNode]] = []
        self._sampling_nodes: list[SamplingNode] = []
        self._collection_nodes: list[CollectionNode] = []
        self._input_specifications: dict[InterfaceName, TensorSpecification] = {}
        self._output_specifications: dict[InterfaceName, TensorSpecification] = {}

    @property
    def parameters(self) -> list[Parameter]:
        """The sorted parameters expecting values at sampling time."""
        return self._param_table.parameters

    @property
    def num_parameters(self) -> int:
        """The number of parameters expected at sampling time."""
        return self._param_table.num_parameters

    def append_parameter_expression(self, expression: ParameterExpression) -> ParamIndex:
        """Add a parameter expression to the samplex.

        An expression needs to be added to a samplex before a node can be added that references it.

        Args:
            expression: A parameter or parameter expression.

        Returns:
            An index that parametric nodes can reference.
        """
        return self._param_table.append(expression)

    def set_passthrough_params(self, passthrough_params: ParamSpec) -> int:
        """Set the mapping for passthrough parameters.

        Some parameters are not influenced by virtual gate propagation and are not set
        by collection nodes. These parameters are only mapped from the original circuit
        parameters, to the template circuit parameters. This function sets the mapping
        for these parameters.

        Args:
            passthrough_params: `ParamSpec` for the passthrough parameters.

        Returns: The maximum template parameter index in `passthrough_params`.
        """
        param_idxs = []
        param_exp_idxs = []
        for idx, exp in passthrough_params:
            param_idxs.append(idx)
            param_exp_idxs.append(self.append_parameter_expression(exp))
        self._passthrough_params = (param_idxs, param_exp_idxs)
        return max(param_idxs)

    def add_input(self, specification: TensorSpecification):
        """Add a sampling input to this samplex.

        Args:
            specification: A specification of the input name and type.
        """
        if specification.name in self._RESERVED_INPUTS:
            raise SamplexConstructionError(
                f"Input name '{specification.name}' is reserved and cannot be used."
            )
        if (name := specification.name) in self._input_specifications:
            raise SamplexConstructionError(f"An input with name '{name}' already exists.")
        self._input_specifications[name] = specification

    def add_output(self, specification: TensorSpecification):
        """Add a sampling output to this samplex.

        Args:
            specification: A specification of the ouput name and type.
        """
        if specification.name in self._RESERVED_OUTPUTS:
            raise SamplexConstructionError(
                f"Output name '{specification.name}' is reserved and cannot be used."
            )
        if (name := specification.name) in self._output_specifications:
            raise SamplexConstructionError(f"An output with name '{name}' already exists.")
        self._output_specifications[name] = specification

    def add_node(self, node: Node) -> NodeIndex:
        """Add a node to the samplex graph.

        Args:
            node: The node to add.

        Returns:
            The integer index of the added node.
        """
        if node.num_parameters and max(node.parameter_idxs) >= self._param_table.num_expressions:
            raise SamplexConstructionError(
                f"{node} expects to use parameter index {max(node.parameter_idxs)} but "
                f"this samplex only has {self._param_table.num_expressions} parameter "
                "expressions so far."
            )
        self._finalized = False
        return self.graph.add_node(node)

    def add_edge(self, a: NodeIndex, b: NodeIndex) -> EdgeIndex:
        """Add an edge to the samplex graph.

        Args:
            a: The node index of the source node.
            b: The node index of the destination node.

        Returns:
            The integer index of the added edge.
        """
        self._finalized = False
        return self.graph.add_edge(a, b, None)

    def _validate_evaluation_strategy(self):
        register_descriptions: dict[RegisterName, tuple[NumSubsystems, VirtualType]] = {}
        for sampling_node in self._sampling_nodes:
            sampling_node.validate_and_update(register_descriptions)

        for evaluation_stream in self._evaluation_streams:
            for evaluation_node in evaluation_stream:
                evaluation_node.validate_and_update(register_descriptions)

        for collection_node in self._collection_nodes:
            collection_node.validate_and_update(register_descriptions)

    def finalize(self):
        """Signal that all nodes and edges have been added, and determine node traversal order.

        Raises:
            SamplexError: If node dependency conflicts are discovered.
        """
        cut_graph = self.graph.copy()

        sampling_nodes: list[SamplingNode] = []
        collection_nodes: list[CollectionNode] = []
        for node_idx in cut_graph.node_indices():
            if isinstance(node := cut_graph[node_idx], SamplingNode):
                sampling_nodes.append(node)
                cut_graph.remove_node(node_idx)
            elif isinstance(node := cut_graph[node_idx], CollectionNode):
                collection_nodes.append(node)
                cut_graph.remove_node(node_idx)

        evaluation_streams: list[list[EvaluationNode]] = []
        for node_idxs in topological_generations(cut_graph):
            evaluation_streams.append([cut_graph[node_idx] for node_idx in node_idxs])

        self._sampling_nodes = sampling_nodes
        self._evaluation_streams = evaluation_streams
        self._collection_nodes = collection_nodes

        self._validate_evaluation_strategy()

        self._finalized = True

    def sample(
        self,
        noise_maps: dict[StrRef, PauliLindbladMap] | None = None,
        noise_scales: dict[StrRef, float] | None = None,
        local_scales: dict[StrRef, Sequence[float]] | None = None,
        size: int = 1,
        keep_registers: bool = False,
        rng: int | SeedSequence | Generator | None = None,
        max_workers: int | None = None,
        **kwargs,
    ) -> SamplexOutput:
        """Sample.

        Args:
            noise_maps: A dictionary from unique identifiers of noise maps to the noise maps
                themselves.
            noise_scales: A dictionary from unique identifier of noise modifiers to values by which
                to scale the noise.
            local_scales: A dictionary from unique identifiers of noise modifiers to lists of values
                by which to scale the terms of the noise.
            size: How many randomizations to sample.
            keep_registers: Whether to keep the virtual registers used during sampling and include
                them in the output under the metadata key ``"registers"``.
            rng: An integer for seeding a randomness generator, a generator itself, or ``None``
                to use the default generator owned by the module.
            max_workers: The maximum number of threads that can be used to execute the
                parallel execution of sampling, evaluation, and collection nodes.
        """
        if not self._finalized:
            # this raises instead of calling finalize() to make it impossible
            # to accidentally affect timing benchmarks of sample()
            raise SamplexRuntimeError("The samplex has not been finalized yet, call `finalize()`.")

        inputs = SamplexInput(self._input_specifications.values(), size)
        inputs.validate_and_update(**kwargs)

        extra_outputs = []
        if keep_registers:
            extra_outputs.append(MetadataOutput("registers", "Final state of internal registers."))
        outputs = SamplexOutput(self._output_specifications.values(), extra_outputs, size)

        parameter_values = inputs.get("parameter_values", [])
        evaluated_values = self._param_table.evaluate(parameter_values)
        if self._passthrough_params:
            outputs["parameter_values"][:, self._passthrough_params[0]] = evaluated_values[
                self._passthrough_params[1]
            ]

        if (measurement_flips := outputs.get("measurement_flips")) is not None:
            measurement_flips[:] = 0

        noise_maps = {} if noise_maps is None else noise_maps
        noise_scales = {} if noise_scales is None else noise_scales
        local_scales = {} if local_scales is None else local_scales
        rng = default_rng(rng) if isinstance(rng, int | SeedSequence) else (rng or RNG)

        registers: dict[RegisterName, VirtualRegister] = outputs.metadata.get("registers", {})

        with ThreadPoolExecutor(max_workers) as pool:
            # use rng.spawn() to ensure determinism of PRNG even when there is a thread pool
            wait_with_raise(
                pool.submit(
                    node.sample,
                    registers,
                    child_rng,
                    inputs,
                    noise_maps=noise_maps,
                    noise_scales=noise_scales,
                    local_scales=local_scales,
                )
                for child_rng, node in zip(
                    rng.spawn(len(self._sampling_nodes)), self._sampling_nodes
                )
            )

            for stream in self._evaluation_streams:
                wait_with_raise(
                    pool.submit(node.evaluate, registers, evaluated_values[node.parameter_idxs])
                    for node in stream
                )

            wait_with_raise(
                pool.submit(node.collect, registers, outputs, child_rng)
                for child_rng, node in zip(
                    rng.spawn(len(self._collection_nodes)), self._collection_nodes
                )
            )

        return outputs

    def draw(
        self,
        cols: int = 2,
        subgraph_idxs: None | int | Sequence[int] = None,
        layout_method: LayoutPresets | LayoutMethod = "auto",
    ) -> "Figure":
        """Draw the graph in this samplex using the :meth:`~plot_graph` method.

        Args:
            cols: The number of columns in the returned figure.
            subgraph_idxs: The indices of the subgraphs to include in the plot, or ``None``
                to include all of the subgraphs.
            layout_method: A predefined layout method by name, or a callable implementing a layout.

        Returns:
            A Plotly graph.
        """

        def _node_ranker(node: Node) -> int:
            if isinstance(node, SamplingNode):
                return 0
            if isinstance(node, CollectionNode):
                return 1
            return None

        return plot_graph(
            graph=self.graph,
            cols=cols,
            subgraph_idxs=subgraph_idxs,
            layout_method=layout_method,
            ranker=_node_ranker,
        )


def wait_with_raise(futures: Iterable[Future]):
    """Wait for all provided futures to complete, and raise if any of them fail.

    Args:
        futures: The futures to wait for.

    Raises:
         Exception: The first exception found in the provided futures.
    """
    completed_futures, _ = wait(futures, return_when=FIRST_EXCEPTION)
    for future in completed_futures:
        if exception := future.exception():
            raise exception
