# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""unbox"""

from qiskit.circuit import QuantumCircuit


def unbox(circuit: QuantumCircuit) -> QuantumCircuit:
    """Return a circuit with all box operations inlined.

    Args:
        circuit: The circuit to inline box operations from.

    Returns:
        A new circuit with no boxes.
    """
    from qiskit.transpiler import PassManager

    from samplomatic.transpiler.passes import InlineBoxes

    return PassManager([InlineBoxes()]).run(circuit)
