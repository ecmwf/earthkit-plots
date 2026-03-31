# Copyright 2024-, European Centre for Medium Range Weather Forecasts.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
_AxisRegistry: maps display-unit strings to matplotlib Axes for a single Subplot.

Auto-creates twinx() axes the first time a new unit string is encountered
when _auto_twin_axes is enabled on the parent Subplot.  Uses are_equal()
for alias-insensitive unit comparison so e.g. "celsius" and "Celsius"
resolve to the same axis.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.axes

    from earthkit.plots.components.subplots import Subplot


class _AxisRegistry:
    """
    Maps canonical display-unit strings to matplotlib Axes for one Subplot.

    The primary axes is claimed on the first :meth:`resolve` call.  Each
    subsequent call with a *different* canonical unit creates a ``twinx()``
    and registers it.  User-assigned names are stored as aliases so that
    both ``subplot.axis("celsius")`` and ``subplot.axis("temperature")``
    can find the same axis.
    """

    def __init__(self, subplot: Subplot) -> None:
        self._subplot = subplot
        # Insertion-ordered: canonical_units_str → mpl_axes
        self._units_to_ax: dict[str, matplotlib.axes.Axes] = {}
        # User-assigned name → canonical_units_str
        self._name_to_canonical: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _canonical(self, units: str) -> str:
        """
        Return the canonical key already stored for *units*, or *units* itself.

        Iterates over already-registered keys and returns the first one for
        which ``are_equal(units, registered)`` is True.  This makes the
        lookup insensitive to capitalisation and pint-registered aliases
        (e.g. "K" and "kelvin" will match).
        """
        from earthkit.plots.metadata.units import are_equal

        units_str = str(units)
        for registered in self._units_to_ax:
            try:
                if are_equal(units_str, registered):
                    return registered
            except Exception:
                # are_equal can raise for unrecognised unit strings (e.g.
                # "fraction").  Fall through to string comparison.
                if units_str == registered:
                    return registered
        return units_str

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def resolve(self, display_units: str) -> matplotlib.axes.Axes:
        """
        Return the Axes for *display_units*, creating it if necessary.

        The first call claims the primary ``Subplot.ax``.  Each subsequent
        call with a *different* canonical unit appends a new ``twinx()``.
        """
        key = self._canonical(display_units)

        if key in self._units_to_ax:
            return self._units_to_ax[key]

        if not self._units_to_ax:
            # First unit seen → owns the primary axes.
            ax = self._subplot.ax
        else:
            ax = self._subplot.ax.twinx()

        self._units_to_ax[key] = ax
        return ax

    def get(self, key: str) -> matplotlib.axes.Axes | None:
        """
        Look up an axis by canonical units string or user-assigned name.

        Returns ``None`` when the key is not found.
        """
        # Try name alias first, then canonical unit lookup.
        canonical = self._name_to_canonical.get(key)
        if canonical is not None:
            return self._units_to_ax.get(canonical)
        return self._units_to_ax.get(self._canonical(key))

    def register_name(self, name: str, mpl_ax: matplotlib.axes.Axes) -> None:
        """
        Associate a user-chosen *name* with the axis that owns *mpl_ax*.

        Raises ``KeyError`` if *mpl_ax* is not yet in the registry.
        """
        for canonical, ax in self._units_to_ax.items():
            if ax is mpl_ax:
                self._name_to_canonical[name] = canonical
                return
        raise KeyError(
            f"Axes {mpl_ax!r} is not registered.  "
            "Call resolve() before register_name()."
        )

    def items(self) -> Iterator[tuple[str, matplotlib.axes.Axes]]:
        """Iterate over (canonical_units, mpl_ax) pairs in insertion order."""
        return iter(self._units_to_ax.items())

    def __len__(self) -> int:
        return len(self._units_to_ax)
