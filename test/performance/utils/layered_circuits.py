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

"""Layered circuits."""

from itertools import product

from qiskit.circuit import ParameterVector, QuantumCircuit
from qiskit.quantum_info import PauliLindbladMap

from samplomatic.annotations import InjectNoise, Twirl

ENTANGLERS = {"cz", "cx", "ecr"}
"""The supported entanglers."""


def make_layered_circuit(
    num_qubits: int,
    num_boxes: int,
    entangler: str = "cx",
    inject_noise: bool = False,
    unique_modifiers: bool = False,
) -> QuantumCircuit:
    """Generate a layered quantum circuit.

    This function generates a circuit that contains ``num_boxes`` boxes. Every box contains five
    rounds of one-qubit gates (RZ-SX-RZ-SX-RZ with pametric RZs) followed by one round of
    entangling gates. In boxes in even positions, the entangling gates acts on qubits
    ``(2 * i, 2 * i + 1)``, for every ``i`` in ``range(0, num_qubits // 2)``, while in boxes in odd
    positions they act on qubits ``(2 * i + 1, 2 * i + 2)``.

    One additional box is added with a twirled measurement of all qubits.

    Args:
        num_qubits: The number of qubits in the returned circuit.
        num_boxes: The number of boxes in the returned circuit.
        entangler: The entangler gate used in the circuit.
        inject_noise: Whether to add an inject noise annotation. If ``True``, the boxes in
            even positions are assigned the reference (and modifier reference) ``"even"`` and those
            in odd positions are assigned the reference ``"odd"``.
        unique_modifiers: Whether to add a unique modifier to each annotation.
    """
    circuit = QuantumCircuit(num_qubits)

    if entangler not in ENTANGLERS:
        raise ValueError(f"``entangler`` must be one of {ENTANGLERS}.")
    entangle_fn = getattr(circuit, entangler)

    num_2q_gates_per_layer = num_qubits // 2

    entangled_pairs_even = [
        (2 * qubit_idx, 2 * qubit_idx + 1) for qubit_idx in range(num_2q_gates_per_layer)
    ]
    control_qubits_even = [qubit for (qubit, _) in entangled_pairs_even]
    target_qubits_even = [qubit for (_, qubit) in entangled_pairs_even]
    all_qubits_even = [qubit for pair in entangled_pairs_even for qubit in pair]

    entangled_pairs_odd = [
        (2 * qubit_idx + 1, 2 * qubit_idx + 2)
        for qubit_idx in range(num_2q_gates_per_layer)
        if 2 * qubit_idx + 2 < num_qubits
    ]
    control_qubits_odd = [qubit for (qubit, _) in entangled_pairs_odd]
    target_qubits_odd = [qubit for (_, qubit) in entangled_pairs_odd]
    all_qubits_odd = [qubit for pair in entangled_pairs_odd for qubit in pair]

    def annotations(box_idx, parity):
        ret = [Twirl()]
        if inject_noise:
            modifier = f"{parity}_{box_idx}" if unique_modifiers else parity
            ret.append(InjectNoise(parity, modifier))
        return ret

    for counter in range(num_boxes // 2):
        params0 = ParameterVector(f"v0_{2 * counter}", len(all_qubits_even))
        params1 = ParameterVector(f"v1_{2 * counter}", len(all_qubits_even))
        params2 = ParameterVector(f"v2_{2 * counter}", len(all_qubits_even))
        with circuit.box(annotations(counter, "even")):
            circuit.noop(range(circuit.num_qubits))
            for qubit_idx, qubit in enumerate(all_qubits_even):
                circuit.rz(params0[qubit_idx], qubit)
                circuit.sx(qubit)
                circuit.rz(params1[qubit_idx], qubit)
                circuit.sx(qubit)
                circuit.rz(params2[qubit_idx], qubit)
            entangle_fn(control_qubits_even, target_qubits_even)

        params0 = ParameterVector(f"v0_{2 * counter + 1}", len(all_qubits_odd))
        params1 = ParameterVector(f"v1_{2 * counter + 1}", len(all_qubits_odd))
        params2 = ParameterVector(f"v2_{2 * counter + 1}", len(all_qubits_odd))
        with circuit.box(annotations(counter, "odd")):
            circuit.noop(range(circuit.num_qubits))
            for qubit_idx, qubit in enumerate(all_qubits_odd):
                circuit.rz(params0[qubit_idx], qubit)
                circuit.sx(qubit)
                circuit.rz(params1[qubit_idx], qubit)
                circuit.sx(qubit)
                circuit.rz(params2[qubit_idx], qubit)
            entangle_fn(control_qubits_odd, target_qubits_odd)

    if num_boxes % 2 == 1:
        params0 = ParameterVector(f"v0_{2 * counter + 2}", len(all_qubits_even))
        params1 = ParameterVector(f"v1_{2 * counter + 2}", len(all_qubits_even))
        params2 = ParameterVector(f"v2_{2 * counter + 2}", len(all_qubits_even))
        with circuit.box(annotations(num_boxes - 1, "even")):
            circuit.noop(range(circuit.num_qubits))
            for qubit_idx, qubit in enumerate(all_qubits_even):
                circuit.rz(params0[qubit_idx], qubit)
                circuit.sx(qubit)
                circuit.rz(params1[qubit_idx], qubit)
                circuit.sx(qubit)
                circuit.rz(params2[qubit_idx], qubit)
            entangle_fn(control_qubits_even, target_qubits_even)

    with circuit.box([Twirl(dressing="left")]):
        circuit.measure_all()

    return circuit


def make_noise_maps(
    num_qubits: int, avg_noise_rate: float = 0.0005
) -> tuple[PauliLindbladMap, PauliLindbladMap]:
    """Generate a pair of noise maps.

    The first corresponds to the even layers of :meth:`~.make_layered_circuit` while the
    second corresponds to the odd layers.

    Args:
        num_qubits: The number of qubits.
        avg_noise_rate: The average noise rate of the map.
    """
    pairs_even = [(idx, idx + 1) for idx in range(0, num_qubits - 1, 2)]
    pairs_odd = [(idx, idx + 1) for idx in range(1, num_qubits - 1, 2)]

    single_paulis = [
        ("".join(p), (idx,), avg_noise_rate) for p, idx in product("XYZ", range(num_qubits))
    ]
    even_layer_paulis = [
        ("".join(p + q), pair, avg_noise_rate) for p, q, pair in product("XYZ", "XYZ", pairs_even)
    ]
    odd_layer_paulis = [
        ("".join(p + q), pair, avg_noise_rate) for p, q, pair in product("XYZ", "XYZ", pairs_odd)
    ]
    return PauliLindbladMap.from_sparse_list(
        single_paulis + even_layer_paulis, num_qubits
    ), PauliLindbladMap.from_sparse_list(single_paulis + odd_layer_paulis, num_qubits)
