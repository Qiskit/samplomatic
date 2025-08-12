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

"""CollectionNode"""

import abc

from numpy.random import Generator

from ...aliases import RegisterName
from ...virtual_registers import VirtualRegister
from ..interfaces import SamplexOutput
from .node import Node


class CollectionNode(abc.ABC, Node):
    """A node that collects register state for return."""

    @abc.abstractmethod
    def collect(
        self, registers: dict[RegisterName, VirtualRegister], outputs: SamplexOutput, rng: Generator
    ):
        """Collect.

        Args:
            registers: Registers to collect from.
            outputs: Where to output.
            rng: A randomness generator.
        """

    def get_style(self):
        style = super().get_style()
        style.marker = "bowtie"
        style.color = "blue"
        style.size = 30
        return style
