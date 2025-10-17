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

from __future__ import annotations

import numpy as np

from samplomatic.aliases import (
    InterfaceName,
    NumSubsystems,
    ParamIndex,
    RegisterName,
    SubsystemIndex,
)
from samplomatic.annotations import VirtualType
from samplomatic.distributions import HaarU2, UniformPauli
from samplomatic.samplex.nodes import CollectionNode, EvaluationNode, Node, SamplingNode
from samplomatic.virtual_registers import PauliRegister, U2Register


class DummyNode(Node):
    """Dummy child for testing.

    .. note::
       * If both ``writes_to`` and ``parameter_idxs`` are defined, then the parameters from these
         indices are written to the write-indices of the write registers (as many as possible).

       * If both ``reads_from`` and ``outputs_to`` are defined, then we write the very first
         numerical entry of the first reads_from entry to all of the output arrays.
    """

    def __init__(
        self,
        *,
        reads_from: dict[RegisterName, tuple[set[SubsystemIndex], VirtualType]] | None = None,
        writes_to: dict[RegisterName, tuple[set[SubsystemIndex], VirtualType]] | None = None,
        instantiates: dict[RegisterName, tuple[NumSubsystems, VirtualType]] | None = None,
        removes: set[RegisterName] | None = None,
        parameter_idxs: list[ParamIndex] | None = None,
        outputs_to: set[InterfaceName] | None = None,
    ):
        self._reads_from = reads_from or {}
        self._writes_to = writes_to or {}
        self._instantiates = instantiates or {}
        self._removes = removes or set()
        self._parameter_idxs = parameter_idxs or []
        self._outputs_to = outputs_to or set()

    @property
    def parameter_idxs(self):
        return self._parameter_idxs

    def outputs_to(self):
        return self._outputs_to

    def reads_from(self):
        return self._reads_from

    def writes_to(self):
        return self._writes_to

    def instantiates(self):
        return self._instantiates

    def removes(self):
        return self._removes

    def _update(self, registers, rng, size=1):
        for register_name, (num_subsystems, register_type) in self.instantiates().items():
            if register_type is U2Register:
                register = HaarU2(num_subsystems).sample(size, rng)
            elif register_type is PauliRegister:
                register = UniformPauli(num_subsystems).sample(size, rng)
            else:
                register = register_type.empty(num_subsystems, size)
            registers[register_name] = register

        for register_name in self.removes():
            registers.pop(register_name)


class DummyCollectionNode(CollectionNode, DummyNode):
    """Dummy child collection node for testing."""

    def collect(self, registers, outputs, rng):
        self._update(registers, rng)

        # add some silly mutation rules so that we can test outputs
        for output_name in self.outputs_to():
            if isinstance(output := outputs[output_name], np.ndarray) and self.reads_from():
                first_register_name, (subsys_idxs, _) = next(iter(self.reads_from().items()))
                register = registers[first_register_name][sorted(subsys_idxs)]
                output[:] = register.virtual_gates.ravel()[0]


class DummySamplingNode(SamplingNode, DummyNode):
    """Dummy child sampling node for testing."""

    def sample(self, registers, rng, inputs, num_randomizations):
        self._update(registers, rng, num_randomizations)


class DummyEvaluationNode(EvaluationNode, DummyNode):
    """Dummy child evaluation node for testing."""

    def evaluate(self, registers, parameter_values, *_):
        self._update(registers, np.random.default_rng())

        # add some silly mutation rules so that we can test parameter values
        for register_name, (subsys_idxs, register_type) in self.writes_to().items():
            if register_type is PauliRegister and (reg := registers[register_name]).num_samples:
                num_write = min(len(subsys_idxs), self.num_parameters)
                pos = sorted(subsys_idxs)[:num_write]
                reg[pos, 0] = parameter_values.astype(int)[:num_write]
