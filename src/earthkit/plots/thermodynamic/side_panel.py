# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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
Side panels of thermodynamic diagrams.

A side panel is a strip of axes alongside the right edge of a diagram, sharing
its vertical pressure scale, for quantities other than temperature: e.g. the
dewpoint depression, the wind or the relative humidity.

On a skew-T or emagram the isobars are horizontal, so a pressure level is at
the same height in the panel as everywhere in the diagram. On a tephigram the
isobars are curved, and a pressure level is placed at the height where its
isobar meets the right edge of the diagram, so that the isobars continue as
horizontal lines into the panel.
"""

import numpy as np
from matplotlib.ticker import FixedFormatter, FixedLocator, MaxNLocator, NullLocator

from earthkit.plots.thermodynamic import profiles
from earthkit.plots.thermodynamic.ticks import DEFAULT_PRESSURE_TICKS, _format_number

#: Default colour of the lines and bands of a side panel.
PANEL_COLOR = "#0060ff"


class SidePanel:
    """
    A strip of axes alongside the right edge of a thermodynamic diagram.

    Values are plotted against pressure: the x axis of the panel is in the
    units of the data and its y axis follows the pressure of the diagram.
    Create it with :meth:`ThermoDiagram.side_panel`.

    Parameters
    ----------
    diagram : ThermoDiagram
        The diagram the panel belongs to.
    width : float
        Width of the panel as a fraction of the width of the diagram.
    pad : float
        Gap between the diagram and the panel as a fraction of the width of the diagram.
    xlim : tuple of float, optional
        Limits of the x axis of the panel. By default they fit the data.
    xlabel : str, optional
        Label of the x axis.
    isobars : bool
        Continue the isobars of the diagram's background lines into the panel.
    pressure_labels : bool
        Label the pressure levels on the right edge of the panel.
    xaxis : bool
        Show the x axis (ticks, labels and vertical grid lines). Set it to
        ``False`` for panels without a horizontal scale, e.g. only wind barbs.
    """

    def __init__(
        self,
        diagram,
        width=0.25,
        pad=0.05,
        xlim=None,
        xlabel=None,
        isobars=True,
        pressure_labels=True,
        xaxis=True,
    ):
        self.diagram = diagram
        self.isobars = isobars
        self.pressure_labels = pressure_labels
        # Positioned in the axes coordinates of the diagram, so the panel
        # follows its box when the equal aspect ratio is applied.
        self.ax = diagram.ax.inset_axes([1.0 + pad, 0.0, width, 1.0])
        self._isobar_artists = []
        if xlim is not None:
            self.ax.set_xlim(*xlim)
        if xlabel is not None:
            self.ax.set_xlabel(xlabel)
        self.ax.tick_params(which="both", length=0)
        # The panel is narrow: a few round values, with vertical grid lines;
        # the isobars are the horizontal ones.
        self.ax.grid(False, axis="y")
        if xaxis:
            self.ax.xaxis.set_major_locator(MaxNLocator(nbins=3, steps=[1, 2, 2.5, 5, 10]))
            self.ax.grid(True, axis="x", color="#cccccc", linewidth=0.6, linestyle="--")
        else:
            self.ax.xaxis.set_major_locator(NullLocator())
            self.ax.grid(False, axis="x")
        self.ax.yaxis.tick_right()
        self.ax.yaxis.set_label_position("right")
        self._setup()

    # ------------------------------------------------------------------
    # Pressure scale
    # ------------------------------------------------------------------

    def pressure_to_y(self, p):
        """
        Vertical (diagram) coordinate of the pressure ``p`` (hPa) in the panel.

        It is where the isobar ``p`` meets the right edge of the diagram.
        """
        x1 = self.diagram.extent[1]
        return np.asarray(self.diagram.geometry.isobar_y(np.asarray(p, dtype=float), x1), dtype=float)

    def _setup(self):
        """Set the vertical scale, ticks and isobars from the extent of the diagram."""
        ax = self.ax
        _, _, y0, y1 = self.diagram.extent
        ax.set_ylim(y0, y1)
        ax.set_autoscaley_on(False)

        if self.pressure_labels:
            values = np.asarray(DEFAULT_PRESSURE_TICKS, dtype=float)
            y = self.pressure_to_y(values)
            inside = np.isfinite(y) & (y >= y0 - 1e-9) & (y <= y1 + 1e-9)
            ax.yaxis.set_major_locator(FixedLocator(y[inside]))
            ax.yaxis.set_major_formatter(FixedFormatter([_format_number(v) for v in values[inside]]))
        else:
            ax.yaxis.set_major_locator(NullLocator())
        ax.yaxis.set_minor_locator(NullLocator())

        for artist in self._isobar_artists:
            artist.remove()
        self._isobar_artists = []
        grid = self.diagram.thermo_grid
        if self.isobars and grid is not None and grid.families["isobars"].enabled:
            family = grid.families["isobars"]
            values = np.asarray(family.values, dtype=float)
            y = self.pressure_to_y(values)
            y = y[np.isfinite(y) & (y > y0) & (y < y1)]
            style = {"zorder": grid.zorder, **family.style}
            self._isobar_artists = [ax.axhline(v, **style) for v in y]

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def line(self, data, p=None, p_units="hPa", **kwargs):
        """
        Plot a profile.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            The profile, e.g. the dewpoint depression. The values are plotted
            as they are, in their own units.
        p : xarray.DataArray or array-like, optional
            Pressure of the profile, required when ``data`` is a plain array.
            Taken from the pressure coordinate of xarray objects.
        p_units : str, optional
            Units of ``p`` when it is a plain array. Default ``"hPa"``.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.plot`.

        Returns
        -------
        matplotlib.lines.Line2D
        """
        values, p_hpa = profiles.extract(data, p=p, kind="raw", p_units=p_units)
        style = {"color": PANEL_COLOR, "linewidth": 2, "zorder": 3, **kwargs}
        (line,) = self.ax.plot(values, self.pressure_to_y(p_hpa), **style)
        return line

    def envelope(self, lower, upper, p=None, p_units="hPa", alpha=0.4, **kwargs):
        """
        Shade the band between two profiles, e.g. the spread of an ensemble.

        Parameters
        ----------
        lower, upper : xarray.DataArray or array-like
            The profiles bounding the band, on the same pressure levels.
        p : xarray.DataArray or array-like, optional
            Pressure of the profiles, required when they are plain arrays.
        p_units : str, optional
            Units of ``p`` when it is a plain array. Default ``"hPa"``.
        alpha : float, optional
            Opacity of the band. Default 0.4.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.fill_betweenx`.

        Returns
        -------
        matplotlib.collections.PolyCollection
        """
        lo, p_lo = profiles.extract(lower, p=p, kind="raw", p_units=p_units)
        hi, p_hi = profiles.extract(upper, p=p, kind="raw", p_units=p_units)
        if p_lo.shape != p_hi.shape or not np.allclose(p_lo, p_hi):
            raise ValueError("lower and upper must be on the same pressure levels")
        style = {"color": PANEL_COLOR, "alpha": alpha, "linewidth": 0, "zorder": 1.2, **kwargs}
        return self.ax.fill_betweenx(self.pressure_to_y(p_lo), lo, hi, **style)

    def wind(
        self,
        u=None,
        v=None,
        p=None,
        speed=None,
        direction=None,
        p_units="hPa",
        units="m/s",
        knots=True,
        x=None,
        every=1,
        **kwargs,
    ):
        """
        Plot a column of wind barbs in the panel.

        Parameters
        ----------
        u, v : xarray.DataArray or array-like, optional
            Wind components.
        p : xarray.DataArray or array-like, optional
            Pressure of the profile, required for plain arrays.
        speed, direction : xarray.DataArray or array-like, optional
            Wind speed and meteorological direction (degrees, the direction the
            wind blows from), used instead of ``u`` and ``v``.
        p_units : str, optional
            Units of ``p`` when it is a plain array. Default ``"hPa"``.
        units : {"m/s", "knots"}, optional
            Units of the wind. Default ``"m/s"``.
        knots : bool, optional
            Draw the barbs in knots (half barb 5 kt, full barb 10 kt, flag 50 kt).
            Default ``True``.
        x : float, optional
            Position of the column on the x axis of the panel. Default: its centre.
        every : int, optional
            Plot every n-th level.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.barbs`.

        Returns
        -------
        matplotlib.quiver.Barbs
        """
        u, v, p_hpa = profiles.wind_components(
            u=u, v=v, p=p, speed=speed, direction=direction, p_units=p_units, units=units, knots=knots
        )
        sel = slice(None, None, max(1, int(every)))
        u, v, p_hpa = u[sel], v[sel], p_hpa[sel]

        if x is None:
            x = 0.5 * sum(self.ax.get_xlim())
            # The barbs do not change the x limits: keep the column in the
            # centre of limits set by the other data
            self.ax.set_autoscalex_on(False)
        y = self.pressure_to_y(p_hpa)
        _, _, y0, y1 = self.diagram.extent
        ok = np.isfinite(y) & np.isfinite(u) & np.isfinite(v) & (y >= y0) & (y <= y1)
        style = {"length": 6, "linewidth": 0.8, "color": "#333333", "zorder": 3, "clip_on": False, **kwargs}
        return self.ax.barbs(np.full(ok.sum(), float(x)), y[ok], u[ok], v[ok], **style)
