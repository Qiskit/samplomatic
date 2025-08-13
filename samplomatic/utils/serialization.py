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

"""Serialization utils"""

import json

import numpy as np
import pybase64

from samplomatic.exceptions import DeserializationError


def array_to_json(array: np.ndarray) -> str:
    """Convert an array to a json format.

    Args:
        array: The array to convert.

    Returns:
        The json string.

    Raises:
        ValueError: If the type of the array is unsupported."""
    if array.dtype == np.dtype(np.complex128):
        dtype = "c128"
        data = pybase64.b64encode_as_string(array.astype("<c16").tobytes())
    elif array.dtype == np.dtype(np.int64):
        dtype = "i64"
        data = pybase64.b64encode_as_string(array.astype("<i8").tobytes())
    elif array.dtype == np.dtype(np.uint32):
        dtype = "u32"
        data = pybase64.b64encode_as_string(array.astype("<u8").tobytes())
    else:
        raise ValueError(f"Unexpected NumPy dtype {array.dtype}.")

    return json.dumps({"data": data, "shape": array.shape, "dtype": dtype})


def array_from_json(data: str) -> np.ndarray:
    """Convert a json string to a numpy array.

    Args:
        data: The json string.

    Returns:
        A numpy array.

    Raises:
        DeserializationError: If the type of the array is unsupported.
    """
    data = json.loads(data)
    dtype = data["dtype"]
    shape = tuple(data["shape"])
    raw = pybase64.b64decode(data["data"])

    if dtype == "c128":
        return np.frombuffer(raw, dtype="<c16").reshape(shape)
    elif dtype == "i64":
        return np.frombuffer(raw, dtype="<i8").reshape(shape)
    elif dtype == "u32":
        return np.frombuffer(raw, dtype="<u8").reshape(shape)

    raise DeserializationError(f"Unexpected NumPy dtype {dtype}.")
