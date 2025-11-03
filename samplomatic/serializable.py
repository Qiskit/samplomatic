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

"""Serializable"""

import abc
import inspect

TYPE_REGISTRY: set["Serializable"] = set()
"""Registry of types that should be serializable, a map from type to type id."""


class Serializable(abc.ABCMeta):
    """Metaclass to record which classes ought to be serializable.

    This is a convenience class to help accidental lack of serialization of classes that ought to be
    serializable. Tests can cross-examine the registry.
    """

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        if cls.__name__ != "Serializable" and not inspect.isabstract(cls):
            TYPE_REGISTRY.add(cls)
        return cls
