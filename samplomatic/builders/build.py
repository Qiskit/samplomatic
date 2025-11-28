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
from .get_builder import get_builder
from .template_state import TemplateState


def _build_stream(stream: CircuitInstruction, builder: Builder) -> Iterator[CircuitInstruction]:
    """Build while iterating an instruction stream, but halting to yield each ``box``.

    Args:
        stream: A stream of instructions to build from.
        builder: The builder to build with.

    Yields:
        Box circuit instruction objects.
    """
    builder.lhs()

    for instr in stream:
        if instr.operation.name == "box":
            yield instr
        else:
            builder.parse(instr)

    builder.rhs()


def _build(stream: CircuitInstruction, builder: Builder):
    """Recursively builds from a stream of instructions.

    Args:
        stream: A stream of instructions to build from.
        builder: The builder to build with.
    """
    for idx, nested_instr in enumerate(_build_stream(stream, builder)):
        # assume the nested instruction is a box for now, handle other control flow ops later
        inner_builder = get_builder(nested_instr, builder.template_state.qubit_map)
        qubit_remapping = dict(zip(nested_instr.qubits, nested_instr.operation.body.qubits))

        remapped_template_state = builder.template_state.remap(qubit_remapping, idx)
        remapped_pre_samplex = builder.samplex_state.remap(remapped_template_state.qubit_map)
        inner_builder = inner_builder.set_template_state(remapped_template_state).set_samplex_state(
            remapped_pre_samplex
        )

        _build(nested_instr.operation.body, inner_builder)


def pre_build(circuit: QuantumCircuit) -> tuple[TemplateState, PreSamplex]:
    """Build a template state and a pre-samplex for the given boxed-up circuit.

    This is a helper method to :func:`build` and is not intended to be useful in standard workflows.

    Args:
        circuit: The circuit to build.

    Returns:
        The built template state and the corresponding pre-samplex.
    """
    template_state = TemplateState.construct_for_circuit(circuit)
    pre_samplex = PreSamplex(qubit_map=template_state.qubit_map, cregs=circuit.cregs)
    builder = get_builder(None, template_state.qubit_map.keys())
    builder.set_template_state(template_state).set_samplex_state(pre_samplex)
    _build(circuit, builder)

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
