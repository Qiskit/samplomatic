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

import io
import json

import numpy as np
import pybase64

from ..annotations import VirtualType as VirtualType
from ..exceptions import DeserializationError
from .group_register import GroupRegister
from .pauli_register import PauliRegister
from .u2_register import U2Register
from .virtual_register import VirtualRegister
from .z2_register import Z2Register


def virtual_register_from_json(data: str) -> VirtualRegister:
    data = json.loads(data)
    register_type = VirtualType(data["type"])
    with io.BytesIO(pybase64.b64decode(data["array"])) as buf:
        array = np.load(buf)
    if register_type == VirtualType.U2:
        return U2Register(array)
    elif register_type == VirtualType.Z2:
        return Z2Register(array)
    elif register_type == VirtualType.PAULI:
        return PauliRegister(array)
    else:
        raise DeserializationError(f"Invalid register type: {register_type}")
