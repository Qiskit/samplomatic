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

"""VirtualRegister"""

import abc
from typing import TypeVar

import numpy as np

from ..annotations import VirtualType
from ..exceptions import VirtualGateError
from ..utils.serialization import array_to_json

T = TypeVar("T")


class VirtualRegisterMeta(abc.ABCMeta):
    """Metaclass for :class:`~.VirtualRegister`."""

    _TYPE_MAP: dict[VirtualType, "VirtualRegisterMeta"] = {}

    def __new__(mcs, name, bases, namespace):
        new_cls = super().__new__(mcs, name, bases, namespace)
        if new_cls.TYPE is not NotImplemented:
            if not isinstance(new_cls.TYPE, VirtualType):
                raise ValueError("VirtualRegister.TYPE must be a VirtualType.")
            if new_cls.TYPE in mcs._TYPE_MAP:
                raise ValueError(
                    f"TYPE '{new_cls.TYPE.value} has already been registered by "
                    f"{mcs._TYPE_MAP[new_cls.TYPE]}'"
                )
            mcs._TYPE_MAP[new_cls.TYPE] = new_cls

        return new_cls


class VirtualRegister(metaclass=VirtualRegisterMeta):
    """A data register containing a 2D array of virtual gates.

    Each virtual gate itself has a shape equal to :attr:`~.GATE_SHAPE`, so the number of dimensions
    of the array owned by a virtual register is actually 2 plus one for each member of gate shape.
    The first two axes of the array are respectively reserved to represent the number of subsystems
    and the number of samples.
    For example, a virtual register representing 2-qubit unitaries might have an array of shape
    ``(5, 6, 4, 4)`` to store a 5x6 array of 4x4 complex unitary matrices.

    Args:
        virtual_gates: The virtual gates in this register.

    Raises:
        VirtualGateError: If ``virtual_gates``' shape is not understood.
    """

    TYPE: VirtualType = NotImplemented
    """The group name in 1-1 correspondence with this virtual gate type."""

    GATE_SHAPE: tuple[int, ...] = NotImplemented
    """The array shape of any single virtual gate."""

    SUBSYSTEM_SIZE: int = NotImplemented
    """The number of qubits each virtual gate acts on."""

    DTYPE: np.dtype = NotImplemented
    """The data type of gate array elements."""

    CONVERTABLE_TYPES: frozenset[VirtualType] = frozenset()
    """Valid arguments for :func:`convert_to`."""

    __slots__ = ("_array",)

    def __init__(self, virtual_gates: np.ndarray):
        self._array: np.ndarray = np.asarray(virtual_gates, dtype=self.DTYPE)

        if (ndim := self._array.ndim) != 2 + len(self.GATE_SHAPE):
            raise VirtualGateError(
                f"Expected ``virtual_gates`` to have 2 leading axes followed by one axis for each "
                f"element of the gate shape {self.GATE_SHAPE}, but found a {ndim}D array."
            )

        if self._array.shape[2:] != self.GATE_SHAPE:
            raise VirtualGateError(
                f"Expected the shape of ``virtual_gates`` to end with {self.GATE_SHAPE} "
                "to account for the shape of each virtual gate element, but found total shape "
                f"{self._array.shape}."
            )

    def to_json_dict(self) -> dict[str, str]:
        array_data = array_to_json(self._array)
        return {"type": self.TYPE, "array": array_data}

    @staticmethod
    def select(register_type: VirtualType) -> type["VirtualRegister"]:
        r"""Select a :class:`~.VirtualRegister` subclass based on a :class:`~.VirtualType` enum.

        ..note::
            Not all :class:`~.VirtualRegister`\s need to define a :attr:`TYPE`, though they will
            need to if they want to participate in many types of :class:`~.Node` actions.
            Conversely, not every :class:`~.VirtualType` must correspond to a
            :class:`~.VirtualRegister`, most notably intermediate abstractions like
            :class:`~.GroupRegister. It is promised, however, that each :class:`~.VirtualType`
            can correspond to at most one :class:`~.VirtualRegister` type.

        Args:
            register_type: The identifier of the type to select.

        Returns:
            The unique subclass associated with the ``register_type``, if any.
        """
        try:
            return VirtualRegister._TYPE_MAP[register_type]
        except KeyError as exc:
            raise ValueError(f"Virtual type '{register_type}' has not been registered.") from exc

    @classmethod
    def empty(cls: type[T], num_subsystems: int, num_samples: int) -> T:
        """Instantiate a new register.

        The array element values are not initialized to any value, so it is expected that the user
        of this constructor overwrites them all.
        """
        return cls(np.empty((num_subsystems, num_samples) + cls.GATE_SHAPE, dtype=cls.DTYPE))

    @classmethod
    @abc.abstractmethod
    def identity(cls: type[T], num_subsystems: int, num_samples: int) -> T:
        """Instantiate a new register of identity virtual gates."""

    @property
    def shape(self) -> tuple[int, int]:
        """The shape of this register, excluding the trailing shape due to gate shape."""
        return self.virtual_gates.shape[:2]

    @property
    def size(self) -> int:
        """The total number of virtual gates in this register."""
        return self.num_samples * self.num_subsystems

    @property
    def num_subsystems(self) -> int:
        """The number of subsystems in this register."""
        return self.virtual_gates.shape[0]

    @property
    def num_samples(self) -> int:
        """The number of samples in this register."""
        return self.virtual_gates.shape[1]

    @property
    def virtual_gates(self) -> np.ndarray:
        """The virtual gates of the virtual gates in this register."""
        return self._array

    def copy(self) -> "VirtualRegister":
        """Generate a copy of this virtual register."""
        return type(self)(self._array.copy())

    def convert_to(self, register_type: VirtualType) -> "VirtualRegister":
        """Convert this register type to some other type, if possible.

        Args:
            register_type: The type of register to convert to.

        Returns:
            A new register of the specified output type, or this instance if its type is
            ``register_type``.

        Raises:
            VirtualGateError: If this type cannot be converted to the specified type.
        """
        if self.TYPE is register_type:
            return self
        raise VirtualGateError(f"Cannot convert {self} to a '{register_type}'.")

    def __getitem__(self, sl):
        if isinstance(sl, tuple) and len(sl) != 1:
            raise VirtualGateError("Virtual registers can only be sliced along their first axis.")
        arr = self._array[sl]
        if arr.ndim != 2 + len(self.GATE_SHAPE):
            raise VirtualGateError("Slicing to singletons is not supported.")
        return type(self)(arr)

    def __repr__(self):
        return f"{type(self).__name__}(<{self.num_subsystems}, {self.num_samples}>)"

    def __setitem__(self, sl, value):
        self._array[sl] = value.virtual_gates if isinstance(value, VirtualRegister) else value

    def __eq__(self, other: "VirtualRegister"):
        return isinstance(other, type(self)) and np.array_equal(self._array, other._array)
