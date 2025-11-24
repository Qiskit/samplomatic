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

"""Common utils for Samplex nodes"""

import numpy as np

from ...exceptions import SamplexError
from ...virtual_registers import U2Register


def get_fractional_gate_register(op_name: str, parameter_values: np.ndarray) -> U2Register:
    """Return a register representing the operation.

    Currently supports only ``rx`` and ``rz`` gates.
    Each value in ``parameter_values`` serves as an argument for a single qubit.

    Args:
        op_name: The name of the operation.
        parameter_values: The parameter of each operation, given as array.

    Returns:
        A :class:`~.U2Register` representing the operation.

    Raises:
        ``SamplexError`` if ``op_name`` not in ``rx`` or ``ry``.
    """
    result = np.empty((len(parameter_values), 1, 2, 2), dtype=U2Register.DTYPE)

    if op_name == "rx":
        result[:, 0, 0, 0] = np.cos(0.5 * parameter_values)
        result[:, 0, 0, 1] = -1j * np.sin(0.5 * parameter_values)
        result[:, 0, 1, 0] = result[:, 0, 0, 1]
        result[:, 0, 1, 1] = result[:, 0, 0, 0]
    elif op_name == "rz":
        result[:, 0, 0, 0] = np.exp(-0.5j * parameter_values)
        result[:, 0, 0, 1] = 0
        result[:, 0, 1, 0] = 0
        result[:, 0, 1, 1] = np.exp(0.5j * parameter_values)
    else:
        raise SamplexError(f"Unknown operation {op_name}")

    return U2Register(result)
