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
Axis ticks of thermodynamic diagrams.

Temperature ticks are placed where the isotherms cross the bottom edge of the
diagram and pressure ticks where the isobars cross its left edge. On a skew-T
or tephigram these positions are not evenly spaced in diagram coordinates.
"""

import numpy as np
from matplotlib.ticker import FixedFormatter, FixedLocator

#: Pressure levels (hPa) labelled by default.
DEFAULT_PRESSURE_TICKS = (1000, 900, 800, 700, 600, 500, 400, 300, 200, 100, 70, 50, 30, 20, 10, 5, 2, 1)


def _format_number(value):
    return f"{value:g}"


def temperature_ticks(geometry, extent, interval=10.0, values=None):
    """
    Positions (diagram x) and labels of the temperature ticks on the bottom edge.

    Parameters
    ----------
    geometry : DiagramGeometry
        The geometry of the diagram.
    extent : tuple of float
        The diagram box ``(x0, x1, y0, y1)``.
    interval : float
        Spacing (°C) of the ticks when ``values`` is not given.
    values : list of float, optional
        Explicit tick temperatures (°C).
    """
    x0, x1, y0, _ = extent
    if values is None:
        # The temperatures along the bottom edge
        t_left, _ = geometry.inverse(x0, y0)
        t_right, _ = geometry.inverse(x1, y0)
        t_lo, t_hi = sorted((float(t_left), float(t_right)))
        values = np.arange(np.ceil(t_lo / interval) * interval, t_hi + 1e-9, interval)
    values = np.asarray(values, dtype=float)
    positions = geometry.isotherm_x(values, y0)
    inside = (positions >= x0 - 1e-9) & (positions <= x1 + 1e-9)
    return positions[inside], [_format_number(v) for v in values[inside]]


def pressure_ticks(geometry, extent, values=DEFAULT_PRESSURE_TICKS):
    """
    Positions (diagram y) and labels of the pressure ticks on the left edge.

    Parameters
    ----------
    geometry : DiagramGeometry
        The geometry of the diagram.
    extent : tuple of float
        The diagram box ``(x0, x1, y0, y1)``.
    values : list of float
        Candidate tick pressures (hPa). Only those inside the diagram are kept.
    """
    x0, _, y0, y1 = extent
    values = np.asarray(values, dtype=float)
    positions = np.asarray(geometry.isobar_y(values, x0), dtype=float)
    inside = np.isfinite(positions) & (positions >= min(y0, y1) - 1e-9) & (positions <= max(y0, y1) + 1e-9)
    return positions[inside], [_format_number(v) for v in values[inside]]


def apply_ticks(ax, extent, temperature_interval=10.0, temperature_values=None, pressure_values=None):
    """Set the temperature and pressure ticks of a :class:`ThermoAxes`."""
    geometry = ax.geometry
    xpos, xlabels = temperature_ticks(geometry, extent, interval=temperature_interval, values=temperature_values)
    ax.xaxis.set_major_locator(FixedLocator(xpos))
    ax.xaxis.set_major_formatter(FixedFormatter(xlabels))

    kwargs = {} if pressure_values is None else {"values": pressure_values}
    ypos, ylabels = pressure_ticks(geometry, extent, **kwargs)
    ax.yaxis.set_major_locator(FixedLocator(ypos))
    ax.yaxis.set_major_formatter(FixedFormatter(ylabels))

    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.yaxis.set_minor_locator(FixedLocator([]))
