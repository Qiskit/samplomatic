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

"""validate_literals"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import get_args


def validate_literals(*arg_names: str) -> Callable:
    """Return a decorator to validate function arguments against literal type annotations.

    .. plot::

        from typing import Literal
        from samplomatic.utils import validate_literals

        @validate_literals("color", "shape")
        def draw(color: Literal["red", "green"], shape: Literal["circle", "square"]):
            ...

    Args:
        *arg_names: The arguments to validate the values of against their :class:`Literal` type
            annotations.

    Returns:
        A decorator that wraps a function in a validation routine.
    """

    def decorator(fn):
        signature = inspect.signature(fn)
        annotations = fn.__annotations__

        # build a map from arguments to allowed values
        arg_valid_values = {}
        for arg_name in arg_names:
            if arg_name not in signature.parameters:
                raise ValueError(f"Function '{fn.__name__}' has no argument named '{arg_name}'.")
            annotation = annotations.get(arg_name)
            if annotation is None:
                raise TypeError(f"Argument '{arg_name}' has no type annotation.")
            values = get_args(annotation)
            if not values:
                raise TypeError(f"Annotation for '{arg_name}' is not a Literal[...] type.")
            arg_valid_values[arg_name] = set(values)

        @wraps(fn)
        def decorated(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()

            for name, valid_values in arg_valid_values.items():
                value = bound.arguments.get(name)
                if value not in valid_values:
                    raise ValueError(
                        f"Invalid value for argument '{name}': {value!r}. "
                        f"Allowed values are: {valid_values}."
                    )

            return fn(*args, **kwargs)

        return decorated

    return decorator
