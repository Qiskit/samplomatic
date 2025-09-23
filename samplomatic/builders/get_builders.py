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

"""get_builders"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from qiskit.circuit import Annotation, Qubit

from ..aliases import CircuitInstruction, TypeAlias
from ..annotations import (
    BasisTransform,
    BasisTransformMode,
    DressingMode,
    InjectNoise,
    Twirl,
    VirtualType,
)
from ..exceptions import BuildError
from ..partition import QubitPartition
from ..pre_samplex import PreSamplex
from ..synths import get_synth
from .builder import Builder
from .samplex_builder import (
    LeftBoxSamplexBuilder,
    PassthroughSamplexBuilder,
    RightBoxSamplexBuilder,
)
from .specs import CollectionSpec, EmissionSpec, InstructionSpec
from .template_builder import (
    LeftBoxTemplateBuilder,
    PassthroughTemplateBuilder,
    RightBoxTemplateBuilder,
    TemplateState,
)

SamplexBuilder: TypeAlias = Builder[PreSamplex, None]
TemplateBuilder: TypeAlias = Builder[TemplateState, InstructionSpec]


def get_builders(
    instr: CircuitInstruction | None, qubits: Sequence[Qubit]
) -> tuple[TemplateBuilder, SamplexBuilder]:
    """Get the builders of a box.

    Args:
        instr: The box instrucion.
        qubits: The qubits of the circuit containing the instruction.

    Raises:
        BuildError: If any of the annotations are unsupported.
        BuildError: If there are duplicates of any supported annotations.
        BuildError: If there is an inject noise annotation without a twirling annotation.

    Returns:
        A tuple containing a template and samplex builder.
    """
    if instr is None or not (annotations := instr.operation.annotations):
        return PassthroughTemplateBuilder(), PassthroughSamplexBuilder()

    qubits = QubitPartition.from_elements(q for q in qubits if q in instr.qubits)
    collection = CollectionSpec(qubits)
    emission = EmissionSpec(qubits)

    seen_annotations: set[type[Annotation]] = set()
    for annotation in annotations:
        if (parser := SUPPORTED_ANNOTATIONS.get(annotation_type := type(annotation))) is None:
            raise BuildError(
                f"Cannot get a builder for {annotations}. {annotation_type} is not supported."
            )
        if annotation_type in seen_annotations:
            raise BuildError(f"Cannot specify more than one {annotation_type} annotation.")
        parser(annotation, collection, emission)
        seen_annotations.add(annotation_type)

    if emission.noise_ref and not emission.twirl_register_type:
        raise BuildError(f"Cannot get a builder for {annotations}. Inject noise requires twirling.")

    if collection.dressing is DressingMode.LEFT:
        return LeftBoxTemplateBuilder(collection), LeftBoxSamplexBuilder(collection, emission)
    return RightBoxTemplateBuilder(collection), RightBoxSamplexBuilder(collection, emission)


def basis_transform_parser(
    basis_transform: BasisTransform,
    collection: CollectionSpec,
    emission: EmissionSpec,
):
    """Parse a basis transform annotation by mutating emission and collection specs.

    Args:
        basis_transform: The basis transform annotation to parse.
        collection: The collection spec to modify.
        emission: The emission spec to modify.

    Raises:
        BuildError: If `dressing` is already specified on one of the specs and is incompatible
            with the basis transform mode.
        BuildError: If `synth` is already specified on the `collection` and not equal to the
            synth corresponding to `basis_transform.decomposition`.
    """
    emission.basis_register_type = VirtualType.U2
    emission.basis_ref = basis_transform.ref

    synth = get_synth(basis_transform.decomposition)
    if (current_synth := collection.synth) is not None:
        if synth != current_synth:
            raise BuildError(
                "Cannot use different synthesizers on different annotations on the same box."
            )
    else:
        collection.synth = synth

    dressing = (
        DressingMode.LEFT
        if (mode := basis_transform.mode) is BasisTransformMode.MEASURE
        else DressingMode.RIGHT
    )
    if (current_dressing := collection.dressing) is not None:
        if dressing != current_dressing:
            raise BuildError(
                f"Cannot use {mode} basis transform with another annotation that uses "
                f"{current_dressing}."
            )
    else:
        collection.dressing = dressing
        emission.dressing = dressing


def inject_noise_parser(
    inject_noise: InjectNoise, collection: CollectionSpec, emission: EmissionSpec
):
    """Parse an inject noise annotation by mutating emission and collection specs.

    Args:
        inject_noise: The inject noise annotation to parse.
        collection: The collection spec to modify.
        emission: The emission spec to modify.
    """
    emission.noise_ref = inject_noise.ref
    emission.noise_modifier_ref = inject_noise.modifier_ref


def twirl_parser(twirl: Twirl, collection: CollectionSpec, emission: EmissionSpec):
    """Parse a twirl annotation by mutating emission and collection specs.

    Args:
        twirl: The twirl annotation to parse.
        collection: The collection spec to modify.
        emission: The emission spec to modify.

    Raises:
        BuildError: If `twirl.group` is unsupported.
        BuildError: If `dressing` is already specified on one of the specs and not equal
            to `twirl.dressing`.
        BuildError: If `synth` is already specified on the `collection` and not equal to the
            synth corresponding to `twirl.decomposition`.
    """
    if twirl.group is not VirtualType.PAULI:
        raise BuildError(f"Group '{twirl.group}' is not supported.")
    emission.twirl_register_type = VirtualType.PAULI

    synth = get_synth(twirl.decomposition)
    if (current_synth := collection.synth) is not None:
        if synth != current_synth:
            raise BuildError(
                "Cannot use different synthesizers on different annotations on the same box."
            )
    else:
        collection.synth = synth

    dressing = twirl.dressing
    if (current_dressing := collection.dressing) is not None:
        if dressing != current_dressing:
            raise BuildError(
                "Cannot use different dressings on different annotations on the same box."
            )
    else:
        collection.dressing = dressing
        emission.dressing = dressing


SUPPORTED_ANNOTATIONS: dict[
    Annotation, Callable[[type[Annotation], CollectionSpec, EmissionSpec], None]
] = {BasisTransform: basis_transform_parser, Twirl: twirl_parser, InjectNoise: inject_noise_parser}
