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

import numpy as np
from qiskit.circuit import Annotation, Qubit
from qiskit.converters import circuit_to_dag

from samplomatic.constants import SUPPORTED_2Q_FRACTIONAL_GATES

from ..aliases import DAGOpNode
from ..annotations import (
    GATE_DEPENDENT_TWIRLING_GROUPS,
    ChangeBasis,
    DressingMode,
    GroupMode,
    InjectLocalClifford,
    InjectNoise,
    Tag,
    Twirl,
)
from ..exceptions import BuildError
from ..partition import QubitPartition
from ..synths import get_synth
from .box_builder import LeftBoxBuilder, RightBoxBuilder
from .builder import Builder
from .passthrough_builder import PassthroughBuilder
from .specs import CollectionSpec, EmissionSpec


def _local_pauli_twirls(dag) -> tuple[dict[str, QubitPartition], set[Qubit]]:
    seen_qubits = set()
    other_qubits = set()
    gate_pairs: dict[str, QubitPartition] = {}

    for node in dag.topological_op_nodes():
        if node.is_standard_gate() and node.op.num_qubits == 2:
            pair = tuple(node.qargs)
            if node.op.name in SUPPORTED_2Q_FRACTIONAL_GATES and not (
                not node.op.is_parameterized() and np.allclose(np.abs(node.op.params), np.pi / 2)
            ):
                if seen_qubits.intersection(pair):
                    raise BuildError(
                        f"Cannot use `{GroupMode.LOCAL_PAULI}` twirling on a box with multiple "
                        f"two-qubit gates from `{SUPPORTED_2Q_FRACTIONAL_GATES}` on one of qubits "
                        f"{pair}."
                    )
                gate_pairs.setdefault(node.op.name, QubitPartition(2, [])).add(pair)
                seen_qubits.update(pair)
            else:
                other_qubits.update(pair)

    if seen_qubits.intersection(other_qubits):
        raise BuildError(
            f"Cannot use `{GroupMode.LOCAL_PAULI}` twirling on a box where gates from "
            f"`{SUPPORTED_2Q_FRACTIONAL_GATES}` have overlapping support with other "
            "entanglers."
        )

    return gate_pairs, seen_qubits


def _local_c1_twirls(dag) -> tuple[dict[str, QubitPartition], set[Qubit]]:
    seen_qubits = set()
    gate_pairs: dict[str, QubitPartition] = {}

    for node in dag.topological_op_nodes():
        if node.is_standard_gate() and node.op.num_qubits == 2:
            pair = tuple(node.qargs)
            if seen_qubits.intersection(pair):
                raise BuildError(
                    f"Cannot use `{GroupMode.LOCAL_C1}` twirling with multiple two-qubit gates on "
                    f"one of qubits {pair}."
                )
            seen_qubits.update(pair)
            gate_pairs.setdefault(node.op.name, QubitPartition(2, [])).add(pair)

    return gate_pairs, seen_qubits


def _classify_gate_dependent_twirl(body, emission: EmissionSpec) -> None:
    """Classify qubits in a gate-dependent twirl box into entangling and fallback qubits.

    Inspects the box body DAG for two-qubit gates and splits qubits accordingly.
    Mutates ``emission`` in place to set ``gate_dependent_twirls``, ``fallback_twirl_qubits``,
    and ``twirl_gate``. If no two-qubit gates are found, sets ``twirl_type`` to PAULI.

    Raises:
        BuildError: If the same qubit pair has duplicate gate-dependent two-qubits gates.
        BuildError: If gate-dependent two-qubits gates on partially overlapping qubits are found.
    """
    dag = circuit_to_dag(body)
    local_twirls = (
        _local_pauli_twirls if emission.twirl_type is GroupMode.LOCAL_PAULI else _local_c1_twirls
    )
    gate_pairs, seen_qubits = local_twirls(dag)

    if not gate_pairs:
        emission.twirl_type = GroupMode.PAULI
        return

    gate_dependent_twirls = {}
    for gate, pairs in gate_pairs.items():
        # Gate-dependent qubits: flatten pairs preserving operand order
        gate_dependent_qubit_list = []
        for pair in pairs:
            for q in pair:
                gate_dependent_qubit_list.append((q,))
        gate_dependent_twirls[gate] = QubitPartition(1, gate_dependent_qubit_list)

    emission.gate_dependent_twirls = gate_dependent_twirls

    # Pauli qubits: remainder
    all_qubits = {q for subsys in emission.qubits for q in subsys}
    fallback_only = all_qubits - seen_qubits
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

    if emission.noise_ref and not emission.twirl_type:
        raise BuildError(f"Cannot get a builder for {annotations}. Inject noise requires twirling.")

    if emission.twirl_type in GATE_DEPENDENT_TWIRLING_GROUPS:
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

    emission.trace_refs["inject_noise"] = inject_noise.ref


def twirl_parser(twirl: Twirl, collection: CollectionSpec, emission: EmissionSpec):
    """Parse a twirl annotation by mutating emission and collection specs.

    Args:
        twirl: The twirl annotation to parse.
        collection: The collection spec to modify.
        emission: The emission spec to modify.

    Raises:
        BuildError: If `dressing` is already specified on one of the specs and not equal
            to `twirl.dressing`.
        BuildError: If `synth` is already specified on the `collection` and not equal to the
            synth corresponding to `twirl.decomposition`.
    """
    emission.twirl_type = twirl.group

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


def tag_parser(tag: Tag, collection: CollectionSpec, emission: EmissionSpec):
    """Parse a trace box annotation by mutating emission spec.

    Args:
        tag: The trace box annotation to parse.
        collection: The collection spec to modify.
        emission: The emission spec to modify.
    """
    emission.trace_refs["tag"] = tag.ref


SUPPORTED_ANNOTATIONS: dict[
    Annotation, Callable[[type[Annotation], CollectionSpec, EmissionSpec], None]
] = {
    ChangeBasis: change_basis_parser,
    Twirl: twirl_parser,
    InjectLocalClifford: inject_local_clifford_parser,
    InjectNoise: inject_noise_parser,
    Tag: tag_parser,
}
