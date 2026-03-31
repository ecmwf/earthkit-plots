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
AxisView: a thin handle on one matplotlib Axes within a multi-axis Subplot.

Returned by :meth:`Subplot.axis`, it exposes the per-axis decoration surface
(ylabel, ylim, format_y_ticks, fix_y_units) and always returns the *parent
Subplot* so method-chaining is not broken at the call site.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.axes

    from earthkit.plots.components.subplots import Subplot


class AxisView:
    """
    Handle on one matplotlib Axes that belongs to a :class:`Subplot`.

    All mutating methods return the **parent Subplot** so the method-chaining
    idiom is preserved after a ``subplot.axis(key)`` call::

        ts.axis("celsius").ylabel("Temperature (°C)")
        ts.axis("mm").ylabel("Precipitation (mm)").ylim(0, 50)
        ts.show()

    Parameters
    ----------
    mpl_ax:
        The underlying matplotlib Axes this view wraps.
    subplot:
        The parent Subplot that owns *mpl_ax*.
    """

    def __init__(
        self,
        mpl_ax: matplotlib.axes.Axes,
        subplot: Subplot,
    ) -> None:
        self._ax = mpl_ax
        self._subplot = subplot

    # ------------------------------------------------------------------
    # Per-axis decoration
    # ------------------------------------------------------------------

    def ylabel(self, label: str | None = None, **kwargs) -> Subplot:
        """
        Set the y-axis label on this axis.

        When *label* is ``None`` the label is auto-generated from the
        metadata of the layers rendered onto this axis, using the same
        ``"{variable_name} ({units})"`` template as :meth:`Subplot.ylabel`.

        Parameters
        ----------
        label:
            Label text.  Supports the same ``{variable_name}``,
            ``{units}``, etc. placeholders as other format strings.
        **kwargs
            Forwarded to :meth:`matplotlib.axes.Axes.set_ylabel`.

        Returns
        -------
        Subplot
        """
        if label is None:
            label = self._auto_label()
        self._ax.set_ylabel(label, **kwargs)
        return self._subplot

    def ylim(
        self,
        bottom: float | None = None,
        top: float | None = None,
        **kwargs,
    ) -> Subplot:
        """
        Set y-axis limits on this axis.

        Parameters
        ----------
        bottom, top:
            Lower and upper y-axis bounds.
        **kwargs
            Forwarded to :meth:`matplotlib.axes.Axes.set_ylim`.

        Returns
        -------
        Subplot
        """
        self._ax.set_ylim(bottom, top, **kwargs)
        return self._subplot

    def format_y_ticks(self, format_spec: str) -> Subplot:
        """
        Apply a tick formatter to the y-axis of this axis.

        Supports the same format specifiers as :meth:`Subplot.format_y_ticks`:
        ``%Lt``, ``%Ln``, or any standard Python format spec.

        Parameters
        ----------
        format_spec:
            Format specifier string.

        Returns
        -------
        Subplot
        """
        from matplotlib.ticker import FuncFormatter

        from earthkit.plots.components.subplots import _build_tick_formatter

        formatter = _build_tick_formatter(format_spec)
        self._ax.yaxis.set_major_formatter(FuncFormatter(formatter))
        return self._subplot

    def fix_y_units(self, units: str) -> Subplot:
        """
        Pre-register *units* on this axis so the auto-routing logic always
        directs data with these units here, without waiting for a plot call.

        Useful when you want to declare the axis layout before plotting::

            ts.axis("celsius").fix_y_units("celsius")

        Parameters
        ----------
        units:
            The display unit string to associate with this axis.

        Returns
        -------
        Subplot
        """
        registry = self._subplot._get_axis_registry()
        canonical = registry._canonical(units)
        # Only register if not already present — avoids overwriting a
        # different axis that was already claimed for these units.
        if canonical not in registry._units_to_ax:
            registry._units_to_ax[canonical] = self._ax
        return self._subplot

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auto_label(self) -> str:
        """
        Build a y-axis label from the layers rendered onto this axis.

        Falls back to an empty string when no layers have been plotted yet.
        """
        from earthkit.plots.metadata.formatters import LayerFormatter

        ax_layers = [
            layer
            for layer in self._subplot.layers
            if getattr(layer, "render_ax", None) is self._ax
        ]
        if not ax_layers:
            return ""

        src = ax_layers[0].sources[0]
        template = (
            "{variable_name} ({units})"
            if src.y.units is not None
            else "{variable_name}"
        )
        return LayerFormatter(ax_layers[0], axis="y").format(template)
