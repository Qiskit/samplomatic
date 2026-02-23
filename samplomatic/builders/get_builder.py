# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""get_builders"""

from collections.abc import Callable, Sequence

from qiskit.circuit import Annotation, Qubit
from qiskit.converters import circuit_to_dag

from ..aliases import DAGOpNode
from ..annotations import (
    GATE_DEPENDENT_TWIRLING_GROUPS,
    TWIRLING_GROUPS,
    ChangeBasis,
    DressingMode,
    InjectLocalClifford,
    InjectNoise,
    Twirl,
)
from ..exceptions import BuildError
from ..partition import QubitPartition
from ..synths import get_synth
from ..virtual_registers import VirtualType
from .box_builder import LeftBoxBuilder, RightBoxBuilder
from .builder import Builder
from .passthrough_builder import PassthroughBuilder
from .specs import CollectionSpec, EmissionSpec


def _classify_gate_dependent_twirl(body, emission: EmissionSpec) -> None:
    """Classify qubits in a gate-dependent twirl box into entangling and fallback qubits.

    Inspects the box body DAG for 2Q gates and splits qubits accordingly.
    Mutates ``emission`` in place to set ``gate_dependent_twirl_qubits``, ``fallback_qubits``,
    and ``twirl_gate``. If no 2Q gates are found, downgrades
    ``twirl_register_type`` to PAULI.

    Raises:
        BuildError: If the same qubit pair has duplicate 2Q gates.
        BuildError: If 2Q gates on partially overlapping qubits are found.
        BuildError: If multiple distinct 2Q gate types are used.
    """
    dag = circuit_to_dag(body)
    seen_pairs = QubitPartition(2, [])
    gate_names: set[str] = set()

    for node in dag.topological_op_nodes():
        if node.is_standard_gate() and node.op.num_qubits == 2:
            pair = tuple(node.qargs)
            if pair in seen_pairs:
                raise BuildError(
                    f"Cannot use gate-dependent twirling with duplicate 2Q gates on qubits {pair}."
                )
            # QubitPartition.add rejects partial overlaps automatically
            seen_pairs.add(pair)
            gate_names.add(node.op.name)

    if not gate_names:
        emission.twirl_register_type = VirtualType.PAULI
        return

    if len(gate_names) > 1:
        raise BuildError(
            f"Cannot use gate-dependent twirling with multiple 2Q gate types: {gate_names}."
        )

    (gate,) = gate_names
    emission.twirl_gate = gate

    # C1 qubits: flatten pairs preserving operand order
    gate_dependent_qubit_list = []
    for pair in seen_pairs:
        for q in pair:
            if q not in {qq for tup in gate_dependent_qubit_list for qq in tup}:
                gate_dependent_qubit_list.append((q,))
    emission.gate_dependent_twirl_qubits = QubitPartition(1, gate_dependent_qubit_list)

    # Pauli qubits: remainder
    all_qubits = {q for subsys in emission.qubits for q in subsys}
    fallback_only = all_qubits - emission.gate_dependent_twirl_qubits.all_elements
    emission.fallback_twirl_qubits = QubitPartition(1, [(q,) for q in fallback_only])


def get_builder(instr: DAGOpNode | None, qubits: Sequence[Qubit]) -> Builder:
    """Get the builders of a box.

    Args:
        instr: The box instruction.
        qubits: The qubits of the circuit containing the instruction.

    Raises:
        BuildError: If any of the annotations are unsupported.
        BuildError: If there are duplicates of any supported annotations.
        BuildError: If there is an inject noise annotation without a twirling annotation.

    Returns:
        A tuple containing a template and samplex builder.
    """
    if instr is None or not (annotations := instr.op.annotations):
        return PassthroughBuilder()

    qubit_permutation = dict(zip(instr.qargs, instr.op.body.qubits))
    qubits = QubitPartition.from_elements(
        qubit_permutation[q] for q in qubits if q in qubit_permutation
    )
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

    if emission.twirl_register_type in GATE_DEPENDENT_TWIRLING_GROUPS:
        _classify_gate_dependent_twirl(instr.op.body, emission)

    if collection.dressing is DressingMode.LEFT:
        return LeftBoxBuilder(collection, emission)
    return RightBoxBuilder(collection, emission)


def change_basis_parser(
    change_basis: ChangeBasis,
    collection: CollectionSpec,
    emission: EmissionSpec,
):
    """Parse a basis change annotation by mutating emission and collection specs.

    Args:
        change_basis: The basis change annotation to parse.
        collection: The collection spec to modify.
        emission: The emission spec to modify.

    Raises:
        BuildError: If ``emission.basis_ref`` is already specified.
        BuildError: If ``dressing`` is already specified on one of the specs and is not equal to
            ``change_basis.dressing``.
        BuildError: If ``synth`` is already specified on the ``collection`` and not equal to the
            synth corresponding to ``change_basis.decomposition``.
    """
    if emission.basis_ref:
        raise BuildError("Cannot specify multiple frame changing annotations on the same box.")

    emission.basis_change = f"pauli_{change_basis.mode.name.lower()}"
    emission.basis_ref = f"basis_changes.{change_basis.ref}"

    synth = get_synth(change_basis.decomposition)
    if (current_synth := collection.synth) is not None:
        if synth != current_synth:
            raise BuildError(
                "Cannot use different synthesizers on different annotations on the same box."
            )
    else:
        collection.synth = synth

    dressing = change_basis.dressing
    if (current_dressing := collection.dressing) is not None:
        if dressing != current_dressing:
            raise BuildError(
                f"Cannot use a `{dressing}` basis change with another annotation that uses "
                f"{current_dressing}."
            )
    else:
        collection.dressing = dressing
        emission.dressing = dressing


def inject_local_clifford_parser(
    local_clifford: InjectLocalClifford,
    collection: CollectionSpec,
    emission: EmissionSpec,
):
    """Parse an inject local Clifford annotation by mutating emission and collection specs.

    Args:
        local_clifford: The annotation to parse.
        collection: The collection spec to modify.
        emission: The emission spec to modify.

    Raises:
        BuildError: If ``emission.basis_ref`` is already specified.
        BuildError: If ``dressing`` is already specified on one of the specs and is incompatible
            with the annotation's dressing.
        BuildError: If ``synth`` is already specified on the ``collection`` and not equal to the
            synth corresponding to ``local_clifford.decomposition``.
    """
    if emission.basis_ref:
        raise BuildError("Cannot specify multiple frame changing annotations on the same box.")

    emission.basis_change = "local_clifford"
    emission.basis_ref = f"local_cliffords.{local_clifford.ref}"

    synth = get_synth(local_clifford.decomposition)
    if (current_synth := collection.synth) is not None:
        if synth != current_synth:
            raise BuildError(
                "Cannot use different synthesizers on different annotations on the same box."
            )
    else:
        collection.synth = synth

    dressing = local_clifford.dressing
    if (current_dressing := collection.dressing) is not None:
        if dressing != current_dressing:
            raise BuildError(
                f"Cannot use {dressing} on when injecting local Clifford with another annotation "
                f"that uses {current_dressing}."
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

    Raises:
        BuildError: If `emission.noise_ref` is not ``None``.
    """
    if emission.noise_ref is not None:
        raise BuildError(
            f"Cannot inject noise with reference '{inject_noise.ref}' on a dressed box "
            f"with noise reference '{emission.noise_ref}' already present."
        )
    emission.noise_ref = inject_noise.ref
    emission.noise_modifier_ref = inject_noise.modifier_ref
    emission.noise_site = inject_noise.site


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
    if twirl.group not in TWIRLING_GROUPS:
        raise BuildError(f"Group '{twirl.group}' is not supported.")
    emission.twirl_register_type = twirl.group

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
] = {
    ChangeBasis: change_basis_parser,
    Twirl: twirl_parser,
    InjectLocalClifford: inject_local_clifford_parser,
    InjectNoise: inject_noise_parser,
}
