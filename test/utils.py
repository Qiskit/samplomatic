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

from qiskit.circuit import QuantumCircuit

from samplomatic.aliases import CircuitInstruction, Qubit, QubitIndex


def remove_boxes(
    circuit: QuantumCircuit,
    qubit_map: dict[Qubit, QubitIndex] | None = None,
    output: QuantumCircuit | None = None,
) -> QuantumCircuit:
    """A utility function that removes boxes from a circuit.

    Args:
        circuit: A quantum circuit.
        qubit_map: A map from qubit to indices, or ``None`` to create it.
        output: The returned circuit into which to place instructions, or ``None`` to create it.

    Returns:
        A circuit that contains the same operations as the given ``circuit``, but no boxes.
    """
    qubit_map = (
        {qubit: idx for idx, qubit in enumerate(circuit.qubits)} if qubit_map is None else qubit_map
    )
    output = QuantumCircuit(*circuit.cregs, *circuit.qregs) if output is None else output
    for instr in circuit:
        if instr.operation.name != "box":
            qargs = [qubit_map[qubit] for qubit in instr.qubits]
            output.append(CircuitInstruction(instr.operation, qargs, instr.clbits))
        else:
            box_map = {box_qubit: qubit_map[box_qubit] for box_qubit in instr.qubits}
            remove_boxes(instr.operation.body, box_map, output)

    return output
