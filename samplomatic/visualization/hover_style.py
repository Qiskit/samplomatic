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

"""Hover Styles for Graphs"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeVar

from ..aliases import Self

T = TypeVar("T", bound="HoverStyle")


class Datum:
    """A datum within :class:`~.HoverStyle` data."""

    __slots__ = ("name", "bullet")

    DEFAULT_BULLET: str = " ▸ "
    NAME_LIMIT: int = 50

    def __init__(self, name: str, bullet: str | None = None):
        self.name = name
        self.bullet = bullet or self.DEFAULT_BULLET

    @property
    def html(self) -> str:
        """HTML to render for this datum."""
        name = str(self.name)
        if len(name) > self.NAME_LIMIT:
            name = name[: self.NAME_LIMIT] + "..."
        return f"{self.bullet}<b>{name}</b>"


class ItemDatum(Datum):
    """A datum with a value."""

    __slots__ = ("value",)

    def __init__(self, name: str, value: Any, bullet: str | None = None):
        super().__init__(name, bullet)
        self.value = value

    @property
    def html(self) -> str:
        return f"{super().html}: {self.value}"


class ListDatum(Datum):
    """A list-valued datum."""

    __slots__ = ("values", "multiline", "max_display")

    DELIMITERS: tuple[str, str] = "[", "]"

    def __init__(
        self,
        name: str,
        values: list,
        bullet: str | None = None,
        multiline: int = 3,
        max_display: int = 10,
    ):
        super().__init__(name, bullet)
        self.multiline = multiline
        if len(values) > max_display:
            values = values[:max_display]
            values.append("...")
        self.values = values

    @property
    def html(self) -> str:
        if len(self.values) >= self.multiline:
            lines = [super().html]
            lines.extend("&nbsp;" * 5 + f"• {value}" for value in self.values)
            return "\n</br>".join(lines)
        else:
            value_text = ", ".join(map(str, self.values))
            return f"{super().html}: {self.DELIMITERS[0]}{value_text}{self.DELIMITERS[1]}"


class DictDatum(ListDatum):
    """A dictionary-valued datum."""

    DELIMITERS: tuple[str, str] = "{", "}"

    def __init__(
        self,
        name: str,
        values: dict,
        bullet: str | None = None,
        multiline: int = 3,
        max_display: int = 10,
    ):
        values = [f"{key}: {value}" for key, value in values.items()]
        super().__init__(name, values, bullet=bullet, multiline=multiline, max_display=max_display)


class Divider(Datum):
    """A datum that is just a divider"""

    def __init__(self):
        super().__init__(name="", bullet="────────────────────────────")


@dataclass
class HoverStyle:
    """Summarizes the style of a graph element when plotted."""

    title: str | None = None
    """The title of the node."""

    description: str | None = None
    """The desription of the node."""

    html_override: str | None = None
    """Raw html to display.

    When accessing :attr:`html`, setting this attribute overrides anything in
    ``title``, ``description``, and ``data``.
    """

    data: list[Datum] = field(default_factory=list)
    """A list of data to display below the title and description."""

    def get_style(self) -> Self:
        """Return self, which is helpful for testing visualization."""
        return self

    @classmethod
    def from_object(cls: type[T], obj: object) -> T:
        """Return a :class:`~HoverStyle` from any object.

        This is taken as the output of the object's ``get_style()`` method, if it exists.
        """
        if hasattr(obj, "get_style") and isinstance(style := obj.get_style(), cls):
            return style
        return cls(title=None if obj is None else repr(obj))

    def append_data(self, key: str, value: Any, bullet: str | None = None) -> Self:
        """Append data to this node.

        Args:
            key: The name of the datum.
            value: The value of the datum.
            bullet: The bullet to prepend the datum with.

        Returns:
            This instance, for chaining.
        """
        self.data.append(ItemDatum(key, value, bullet=bullet))
        return self

    def append_list_data(
        self,
        key: str,
        values: list,
        multiline: int = 3,
        max_display: int = 10,
        bullet: str | None = None,
    ) -> Self:
        """Append list-valued data to this node.

        Args:
            key: The name of the datum.
            values: The values of the datum.
            multiline: The list length at which to start displaying one entry per line.
            max_display: The maximum number of values to display before added ellipses.
            bullet: The bullet to prepend the datum with.

        Returns:
            This instance, for chaining.
        """
        self.data.append(
            ListDatum(key, values, multiline=multiline, bullet=bullet, max_display=max_display)
        )
        return self

    def append_dict_data(
        self,
        key: str,
        values: dict,
        multiline: int = 3,
        max_display: int = 10,
        bullet: str | None = None,
    ):
        """Append list-valued data to this node.

        Args:
            key: The name of the datum.
            values: The key-value pairs of the datum.
            multiline: The dictionary length at which to start displaying one entry per line.
            max_display: The maximum number of values to display before added ellipses.
            bullet: The bullet to prepend the datum with.

        Returns:
            This instance, for chaining.
        """
        self.data.append(
            DictDatum(key, values, multiline=multiline, max_display=max_display, bullet=bullet)
        )
        return self

    def append_divider(self) -> Self:
        """Add a divider between data items."""
        self.data.append(Divider())
        return self

    @property
    def html(self) -> str | None:
        """HTML to display on hover."""
        if self.html_override is None:
            html = []
            if self.title:
                html.append(f"<b>{self.title}</b>")
            if self.description:
                html.append(str(self.description))
            html.extend(datum.html for datum in self.data)
            return "<br>\n".join(html) if html else None
        return self.html_override


@dataclass
class NodeStyle(HoverStyle):
    """Style of a node."""

    marker: str = "circle"
    """The shape of the marker to draw."""

    color: str = "limegreen"
    """The color of the node."""

    size: int = 20
    """The size of the node."""


@dataclass
class EdgeStyle(HoverStyle):
    """Style of an edge."""
