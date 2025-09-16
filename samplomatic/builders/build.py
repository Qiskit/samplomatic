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

"""build"""

from collections.abc import Iterator

from qiskit.circuit import QuantumCircuit

from ..aliases import CircuitInstruction
from ..pre_samplex import PreSamplex
from ..samplex import Samplex
from .builder import Builder
from .get_builders import get_builders
from .specs import InstructionSpec
from .template_builder import TemplateState


def _build_stream(
    stream: CircuitInstruction,
    template_builder: Builder[TemplateState, InstructionSpec],
    samplex_builder: Builder[PreSamplex, None],
) -> Iterator[CircuitInstruction]:
    """Build while iterating an instruction stream, but halting to yield each ``box``.

    Args:
        stream: A stream of instructions to build from.
        template_builder: The template builder to build with.
        samplex_builder: The samplex builder to build with.

    Yields:
        Box circuit instruction objects.
    """
    instruction_spec = template_builder.lhs()
    samplex_builder.lhs(instruction_spec)

    for instr in stream:
        if instr.operation.name == "box":
            yield instr
        else:
            instruction_spec = template_builder.parse(instr)
            samplex_builder.parse(instr, instruction_spec)

    instruction_spec = template_builder.rhs()
    samplex_builder.rhs(instruction_spec)


def _build(
    stream: CircuitInstruction,
    template_builder: Builder[TemplateState, InstructionSpec],
    samplex_builder: Builder[PreSamplex, None],
):
    """Recursively builds from a stream of instructions.

    Args:
        stream: A stream of instructions to build from.
        template_builder: The template builder to build with.
        samplex_builder: The samplex builder to build with.
    """
    for idx, nested_instr in enumerate(_build_stream(stream, template_builder, samplex_builder)):
        # assume the nested instruction is a box for now, handle other control flow ops later
        inner_template_builder, inner_samplex_builder = get_builders(
            nested_instr, template_builder.state.qubit_map
        )
        qubit_remapping = dict(zip(nested_instr.qubits, nested_instr.operation.body.qubits))

        remapped_template_state = template_builder.state.remap(qubit_remapping, idx)
        inner_template_builder = inner_template_builder.set_state(remapped_template_state)

        remapped_pre_samplex = samplex_builder.state.remap(remapped_template_state.qubit_map)
        inner_samplex_builder = inner_samplex_builder.set_state(remapped_pre_samplex)

        _build(nested_instr.operation.body, inner_template_builder, inner_samplex_builder)


def pre_build(circuit: QuantumCircuit) -> tuple[TemplateState, PreSamplex]:
    """Build a template state and a pre-samplex for the given boxed-up circuit.

    This is a helper method to :func:`build` and is not intended to be useful in standard workflows.

    Args:
        circuit: The circuit to build.

    Returns:
        The built template state and the corresponding pre-samplex.
    """
    template_state = TemplateState.construct_for_circuit(circuit)
    template_builder, samplex_builder = get_builders(None, template_state.qubit_map.keys())
    template_builder = template_builder.set_state(template_state)

    pre_samplex = PreSamplex(qubit_map=template_state.qubit_map, cregs=circuit.cregs)
    samplex_builder = samplex_builder.set_state(pre_samplex)

    _build(circuit, template_builder, samplex_builder)

    return template_state, pre_samplex


def build(circuit: QuantumCircuit) -> tuple[QuantumCircuit, Samplex]:
    """Build a circuit template and samplex for the given boxed-up circuit.

    Args:
        circuit: The circuit to build.

    Returns:
        The built template circuit and the corresponding samplex.
    """
    template_state, pre_samplex = pre_build(circuit)
    return template_state.template, pre_samplex.finalize().finalize()
