# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""TraceInfo"""

from dataclasses import dataclass, field


@dataclass
class TraceInfo:
    """Debug trace information attached to nodes when building with ``debug=True``.

    This carries annotation-derived metadata (e.g. tag refs, inject-noise refs) from box
    origins through to their corresponding samplex nodes, analogous to source-location debug
    info in compilers.

    Each key in :attr:`trace_refs` is an annotation type (e.g. ``"tag"``, ``"inject_noise"``),
    and each value is the set of ref strings from all boxes that contributed to the node (for
    example, more than one when propagation nodes from multiple boxes are merged).
    """

    trace_refs: dict[str, set[str]] = field(default_factory=dict)
    """A map from trace origin types, to sets of origin references."""

    @staticmethod
    def from_emission_trace_refs(trace_refs: dict[str, str]) -> "TraceInfo | None":
        """Create a :class:`TraceInfo` from an :class:`~.EmissionSpec` ``trace_refs`` dict.

        Returns ``None`` if all values are empty strings (no trace info present).

        Args:
            trace_refs: A mapping from annotation type names to ref strings, as found on
                :attr:`~.EmissionSpec.trace_refs`.

        Returns:
            A new :class:`TraceInfo`, or ``None`` if no non-empty refs are present.
        """
        filtered = {origin_type: {origin} for origin_type, origin in trace_refs.items() if origin}
        return TraceInfo(trace_refs=filtered) if filtered else None

    def style_data(self) -> dict[str, list[str]]:
        """Return trace refs formatted for display in node styles.

        Returns:
            A dict mapping origin types to sorted lists of origin refs.
        """
        return {k: sorted(v) for k, v in self.trace_refs.items()}

    def copy(self) -> "TraceInfo":
        """Return a deep copy of this instance."""
        return TraceInfo(
            {origin_type: set(origin) for origin_type, origin in self.trace_refs.items()}
        )

    def merge(self, other: "TraceInfo"):
        """Mutate this instance by merging in another :class:`TraceInfo` instance.

        Args:
            other: The :class:`TraceInfo` to merge in.
        """
        for key, values in other.trace_refs.items():
            self.trace_refs.setdefault(key, set()).update(values)
