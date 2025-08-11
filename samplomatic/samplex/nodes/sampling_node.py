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

"""SamplingNode"""

import abc

from numpy.random import Generator

from ...aliases import RegisterName
from ...virtual_registers import VirtualRegister
from ..interfaces import SamplexInput
from .node import Node


class SamplingNode(abc.ABC, Node):
    """A node that produces samples."""

    @abc.abstractmethod
    def sample(
        self,
        registers: dict[RegisterName, VirtualRegister],
        rng: Generator,
        inputs: SamplexInput,
        **kwargs,
    ):
        """Sample this node.

        Args:
            registers: Where to sample into.
            rng: A randomness generator.
            kwargs: Optional keyword arguments to be used at sample time.
        """

    def get_style(self):
        style = super().get_style()
        style.marker = "star"
        style.color = "red"
        style.size = 30
        return style
