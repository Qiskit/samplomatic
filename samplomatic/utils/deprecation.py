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

"""Deprecation Tools"""

from collections.abc import Callable
from typing import Any

from qiskit.utils.deprecation import deprecate_arg as _deprecate_arg


def deprecate_arg(
    name: str,
    *,
    since: str,
    additional_msg: str | None = None,
    deprecation_description: str | None = None,
    pending: bool = False,
    new_alias: str | None = None,
    predicate: Callable[[Any], bool] | None = None,
    removal_timeline: str = "no earlier than 1 month after the release date",
) -> Callable:
    """Return a decorator to indicate an argument has been deprecated in some way.

    This decorator may be used multiple times on the same function, once per deprecated argument.
    It should be placed beneath other decorators like ``@staticmethod`` and property decorators.

    .. note::

        This is currently implemented as a thin wrapper around :func:`qiskit.utils.deprecation`
        where we hard-code the package name to samplomatic and lower the default removal timeline.

    Args:
        name: The name of the deprecated argument.
        since: The version the deprecation started at. If the deprecation is pending, set
            the version to when that started; but later, when switching from pending to
            deprecated, update ``since`` to the new version.
        deprecation_description: What is being deprecated? E.g. "Setting my_func()'s ``my_arg``
            argument to ``None``." If not set, will default to "{func_name}'s argument ``{name}``".
        additional_msg: Put here any additional information, such as what to use instead
            (if ```new_alias``` is not set). For example, "Instead, use the argument `new_arg`,
            which is similar but does not impact the circuit's setup."
        pending: Set to ``True`` if the deprecation is still pending.
        new_alias: If the arg has simply been renamed, set this to the new name. The decorator will
            dynamically update the ``kwargs`` so that when the user sets the old arg, it will be
            passed in as the ``new_alias`` arg.
        predicate: Only log the runtime warning if the predicate returns True. This is useful to
            deprecate certain values or types for an argument, e.g.
            ``lambda my_arg: isinstance(my_arg, dict)``. Regardless of if a predicate is set, the
            runtime warning will only log when the user specifies the argument.
        removal_timeline: How soon can this deprecation be removed? Expects a value
            like "no sooner than 6 months after the latest release" or "in release 9.99".

    Returns:
        The decorated callable.
    """
    return _deprecate_arg(
        name,
        since=since,
        additional_msg=additional_msg,
        deprecation_description=deprecation_description,
        pending=pending,
        new_alias=new_alias,
        predicate=predicate,
        package_name="samplomatic",
        removal_timeline=removal_timeline,
    )
