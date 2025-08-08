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

"""EvaluationNode"""

import abc

import numpy as np

from ...aliases import RegisterName
from ...virtual_registers import VirtualRegister
from .node import Node


class EvaluationNode(abc.ABC, Node):
    """A node that evaluates on an existing register state."""

    @abc.abstractmethod
    def evaluate(
        self, registers: dict[RegisterName, VirtualRegister], parameter_values: np.ndarray
    ):
        """Evaluate this node.

        Args:
            registers: At least those registers needed by this node to read from or write to.
            parameter_values: Parameter values to use during evaluation.

        Raises:
            SamplexRuntimeError: If the number of parameter values received does not equal the
                number required by this node.
        """
