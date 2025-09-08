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

"""InjectNoiseNode"""

import numpy as np
from qiskit.quantum_info import PauliLindbladMap, QubitSparsePauliList

from ...aliases import NumSubsystems, RegisterName, StrRef
from ...annotations import VirtualType
from ...virtual_registers import PauliRegister, Z2Register
from .sampling_node import SamplingNode


class InjectNoiseNode(SamplingNode):
    """A node that produces samples for injecting noise.

    The node constructs a :class:`qiskit.quantum_info.PauliLindbladMap` from its model as the
    distribution to draw samples from. Its rates can be specified at sample time. The rates can be
    modified with inputs:

    * ``global_scale``, a float that is applied to scale all of the rates;
    * ``noise_scales``, a namespace containing modifier references to floats. If ``modifier_ref``
      is in the namespace, all of the rates are mulitiplied by the corresponding float. Takes
      precendence over ``global_scale``;
    * ``local_scales``, a namespace containing modifier references to arrays of floats. If
      ``modifier_ref`` is in the namespace, the rates are scaled individually. The array is
      expected to have the same number of terms as ``model``.

    Args:
        register_name: The name of the register to store the samples.
        sign_register_name: The name of the register to store the signs.
        noise_ref: Unique identifier of the noise map to draw samples from.
        model: The noise model for this noise map.
        modifier_ref: Unique identifier for modifiers applied to the noise map before sampling.
    """

    def __init__(
        self,
        register_name: RegisterName,
        sign_register_name: RegisterName,
        noise_ref: StrRef,
        model: QubitSparsePauliList,
        modifier_ref: StrRef = "",
    ):
        self._register_name = register_name
        self._sign_register_name = sign_register_name
        self._noise_ref = noise_ref
        self._model = model
        self._modifier_ref = modifier_ref

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "5",
            "register_name": self._register_name,
            "sign_register_name": self._sign_register_name,
            "noise_ref": self._noise_ref,
            "modifier_ref": self._modifier_ref,
            "num_subsystems": str(self._num_subsystems),
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "InjectNoiseNode":
        return cls(
            data["register_name"],
            data["sign_register_name"],
            data["noise_ref"],
            int(data["num_subsystems"]),
            data["modifier_ref"],
        )

    @property
    def outgoing_register_type(self) -> VirtualType:
        return VirtualType.PAULI

    def instantiates(self) -> dict[RegisterName, tuple[NumSubsystems, VirtualType]]:
        return {
            self._register_name: (self._model.num_qubits, VirtualType.PAULI),
            self._sign_register_name: (1, VirtualType.Z2),
        }

    def sample(self, registers, rng, inputs, num_randomizations):
        rates = inputs.get(self._noise_ref)
        if self._modifier_ref:
            scale = inputs.get("noise_scales." + self._modifier_ref) or inputs.get(
                "noise_scales.all", 1.0
            )
            local_scale = inputs.get(
                "local_scales." + self._modifier_ref, np.ones(self._model.num_terms)
            )
            rates = rates * scale * local_scale
        noise_map = PauliLindbladMap.from_sparse_list(
            [
                (paulis, qubit_idxs, rate)
                for (paulis, qubit_idxs), rate in zip(self._model.to_sparse_list(), rates)
            ],
            self._model.num_qubits,
        )
        signs, samples = noise_map.signed_sample(num_randomizations, rng.bit_generator.random_raw())
        registers[self._register_name] = PauliRegister(samples.to_dense_array().transpose())
        registers[self._sign_register_name] = Z2Register(signs.reshape(1, -1))

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Register Name", repr(self._register_name))
            .append_data("Subsystems", repr(self._num_subsystems))
            .append_data("Noise Reference", repr(self._noise_ref))
            .append_data("Modifier Reference", repr(self._modifier_ref))
        )
