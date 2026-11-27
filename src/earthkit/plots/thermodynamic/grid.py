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
Background lines of thermodynamic diagrams.

The line families are generated in data coordinates (T [°C], p [hPa]) using the
thermodynamic functions of earthkit-meteo, over the range of temperatures and
pressures visible in the diagram, and are clipped by the axes.

============================  ==============================================
Family                        Line
============================  ==============================================
``isotherms``                 T = const
``isobars``                   p = const
``dry_adiabats``              θ = const (labelled in °C)
``saturated_adiabats``        θw = const, pseudoadiabats (labelled in °C)
``mixing_ratios``             saturation mixing ratio = const (g/kg)
============================  ==============================================
"""

import copy
import dataclasses as dc
from typing import Any

import numpy as np

from earthkit.plots.thermodynamic.transforms import P_REF, T_C2K, thermo_backend

#: Number of points sampled along the background lines.
N_SAMPLES = 160


@dc.dataclass
class LineFamily:
    """
    Settings of one family of background lines.

    Parameters
    ----------
    enabled : bool
        Whether the family is drawn.
    values : list of float, optional
        The values of the lines. Takes precedence over ``interval``.
    interval : float, optional
        Spacing of the lines when ``values`` is not given.
    style : dict
        Keyword arguments for :meth:`matplotlib.axes.Axes.plot`.
    labels : bool
        Whether the lines are labelled.
    label_style : dict
        Keyword arguments for :meth:`matplotlib.axes.Axes.text`.
    label_frequency : int
        Label every n-th line.
    top_pressure : float, optional
        Pressure (hPa) where the lines end (e.g. mixing-ratio lines are
        usually drawn only in the lower troposphere).
    """

    enabled: bool = True
    values: Any = None
    interval: float | None = None
    style: dict = dc.field(default_factory=dict)
    labels: bool = True
    label_style: dict = dc.field(default_factory=dict)
    label_frequency: int = 1
    top_pressure: float | None = None

    def update(self, settings):
        """Return a copy updated from a ``bool``, a dict of settings or a :class:`LineFamily`."""
        new = copy.deepcopy(self)
        if isinstance(settings, LineFamily):
            return copy.deepcopy(settings)
        if isinstance(settings, bool):
            new.enabled = settings
            return new
        for key, value in dict(settings).items():
            if key in ("style", "label_style"):
                getattr(new, key).update(value)
            elif hasattr(new, key):
                setattr(new, key, value)
            else:
                # anything else is a matplotlib line property, e.g. color="red"
                new.style[key] = value
        return new


_LABEL_DEFAULTS = {"fontsize": 7, "ha": "center", "va": "center"}


def default_families():
    """The default settings of the background line families."""
    red = "#d62728"
    green = "#2ca02c"
    purple = "#8c64b4"
    return {
        "isobars": LineFamily(
            values=list(range(1050, 99, -50)) + [70, 50, 30, 20, 10],
            style={"color": "#888888", "linewidth": 0.6},
            labels=False,
        ),
        "isotherms": LineFamily(
            interval=10.0,
            style={"color": red, "linewidth": 0.6, "alpha": 0.8},
            labels=False,
        ),
        "dry_adiabats": LineFamily(
            interval=10.0,
            style={"color": red, "linewidth": 0.6, "alpha": 0.8},
            label_style={**_LABEL_DEFAULTS, "color": red},
        ),
        "saturated_adiabats": LineFamily(
            interval=5.0,
            style={"color": green, "linewidth": 0.6, "linestyle": (0, (4, 3)), "alpha": 0.9},
            label_style={**_LABEL_DEFAULTS, "color": green},
        ),
        "mixing_ratios": LineFamily(
            values=[0.4, 1, 2, 4, 7, 10, 16, 24, 32],
            style={"color": purple, "linewidth": 0.6, "linestyle": (0, (2, 2))},
            label_style={**_LABEL_DEFAULTS, "color": purple},
            top_pressure=400.0,
        ),
    }


class ThermoGrid:
    """
    The background lines of a thermodynamic diagram.

    Each family can be configured with ``True``/``False``, a dict of
    :class:`LineFamily` settings (any other key is used as a matplotlib line
    property) or a :class:`LineFamily`.

    Parameters
    ----------
    isobars, isotherms, dry_adiabats, saturated_adiabats, mixing_ratios
        Settings of the line families.
    layer : {"background", "foreground"}
        Whether the lines are drawn below or above the data.

    Examples
    --------
    >>> ThermoGrid(mixing_ratios=False, dry_adiabats={"color": "grey", "label_frequency": 2})
    """

    FAMILIES = ("isobars", "isotherms", "dry_adiabats", "saturated_adiabats", "mixing_ratios")

    def __init__(
        self,
        isobars=True,
        isotherms=True,
        dry_adiabats=True,
        saturated_adiabats=True,
        mixing_ratios=True,
        layer="background",
    ):
        if layer not in ("background", "foreground"):
            raise ValueError(f"layer must be 'background' or 'foreground', got {layer!r}")
        defaults = default_families()
        settings = {
            "isobars": isobars,
            "isotherms": isotherms,
            "dry_adiabats": dry_adiabats,
            "saturated_adiabats": saturated_adiabats,
            "mixing_ratios": mixing_ratios,
        }
        self.families = {name: defaults[name].update(settings[name]) for name in self.FAMILIES}
        self.layer = layer

    @property
    def zorder(self):
        return 0.5 if self.layer == "background" else 2.5

    def draw(self, ax, extent):
        """
        Draw the background lines on a :class:`ThermoAxes`.

        Returns
        -------
        list of matplotlib.artist.Artist
            The artists created, so that they can be removed when the extent changes.
        """
        ranges = visible_ranges(ax.geometry, extent)
        artists = []
        for name in self.FAMILIES:
            family = self.families[name]
            if not family.enabled:
                continue
            lines = LINE_GENERATORS[name](family, ranges)
            artists += _draw_family(ax, extent, family, lines, self.zorder)
        return artists


# ---------------------------------------------------------------------------
# Visible ranges
# ---------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class VisibleRanges:
    """Ranges of the thermodynamic quantities visible in a diagram."""

    t: tuple  # °C
    p: tuple  # hPa, (max, min)
    theta: tuple  # °C
    theta_w: tuple  # °C


def visible_ranges(geometry, extent, n=200):
    """Compute the ranges of T, p, θ and θw over the boundary of the diagram box."""
    thermo = thermo_backend()
    x0, x1, y0, y1 = extent
    s = np.linspace(0.0, 1.0, n)
    xs = np.concatenate([x0 + (x1 - x0) * s, np.full(n, x1), x1 - (x1 - x0) * s, np.full(n, x0)])
    ys = np.concatenate([np.full(n, y0), y0 + (y1 - y0) * s, np.full(n, y1), y1 - (y1 - y0) * s])
    t, p = geometry.inverse(xs, ys)
    ok = np.isfinite(t) & np.isfinite(p) & (p > 0)
    t, p = t[ok], p[ok]

    theta = thermo.potential_temperature(t + T_C2K, p * 100.0) - T_C2K
    with np.errstate(all="ignore"):
        ept = thermo.saturation_ept(t + T_C2K, p * 100.0)
        theta_w = thermo.temperature_on_moist_adiabat(ept, P_REF * 100.0) - T_C2K

    return VisibleRanges(
        t=(float(np.min(t)), float(np.max(t))),
        p=(float(np.max(p)), float(np.min(p))),
        theta=(float(np.min(theta)), float(np.max(theta))),
        theta_w=(float(np.nanmin(theta_w)), float(np.nanmax(theta_w))),
    )


def _family_values(family, lo, hi):
    if family.values is not None:
        return [float(v) for v in family.values]
    interval = family.interval
    return list(np.arange(np.floor(lo / interval) * interval, hi + 0.5 * interval, interval))


def _pressure_samples(ranges, top=None):
    p_max, p_min = ranges.p
    if top is not None:
        p_min = max(p_min, top)
    return np.geomspace(p_max, p_min, N_SAMPLES)


# ---------------------------------------------------------------------------
# Line generators: each returns a list of (value, t [°C], p [hPa]) ordered from
# the bottom of the diagram (high pressure) upwards.
# ---------------------------------------------------------------------------


def _isobars(family, ranges):
    t = np.linspace(ranges.t[0], ranges.t[1], N_SAMPLES)
    p_max, p_min = ranges.p
    return [(v, t, np.full_like(t, v)) for v in _family_values(family, p_min, p_max) if p_min <= v <= p_max]


def _isotherms(family, ranges):
    p = _pressure_samples(ranges, family.top_pressure)
    return [(v, np.full_like(p, v), p) for v in _family_values(family, *ranges.t)]


def _dry_adiabats(family, ranges):
    thermo = thermo_backend()
    p = _pressure_samples(ranges, family.top_pressure)
    lines = []
    for v in _family_values(family, *ranges.theta):
        t = thermo.temperature_from_potential_temperature(v + T_C2K, p * 100.0) - T_C2K
        lines.append((v, t, p))
    return lines


def _saturated_adiabats(family, ranges):
    thermo = thermo_backend()
    p = _pressure_samples(ranges, family.top_pressure)
    values = _family_values(family, *ranges.theta_w)
    if not values:
        return []
    # The pseudoadiabat through (theta_w, 1000 hPa) at saturation
    ept = thermo.saturation_ept(np.asarray(values) + T_C2K, P_REF * 100.0)
    ept_2d, p_2d = np.meshgrid(ept, p * 100.0, indexing="ij")
    with np.errstate(all="ignore"):
        t = thermo.temperature_on_moist_adiabat(ept_2d.ravel(), p_2d.ravel()).reshape(ept_2d.shape) - T_C2K
    return [(v, t[i], p) for i, v in enumerate(values)]


def _mixing_ratios(family, ranges):
    thermo = thermo_backend()
    p = _pressure_samples(ranges, family.top_pressure)
    lines = []
    for v in _family_values(family, 0.1, 40.0):
        t = thermo.dewpoint_from_mixing_ratio(v / 1000.0, p * 100.0) - T_C2K
        lines.append((v, t, p))
    return lines


#: Ranges covering every diagram, used for single lines that must not depend
#: on the extent of the diagram.
FULL_RANGES = VisibleRanges(t=(-160.0, 70.0), p=(1100.0, 1.0), theta=(-100.0, 500.0), theta_w=(-60.0, 50.0))


def single_line(family, value, top_pressure=None):
    """
    Compute one background line over the full range of the diagrams.

    Parameters
    ----------
    family : str
        One of :attr:`ThermoGrid.FAMILIES`.
    value : float
        The value of the line: pressure (hPa) for ``"isobars"``, temperature
        (°C) for ``"isotherms"``, potential temperature (°C) for
        ``"dry_adiabats"``, wet-bulb potential temperature (°C) for
        ``"saturated_adiabats"`` and saturation mixing ratio (g/kg) for
        ``"mixing_ratios"``.
    top_pressure : float, optional
        Pressure (hPa) where the line ends.

    Returns
    -------
    t, p : numpy.ndarray
        Temperature (°C) and pressure (hPa) along the line, from the bottom up.
    """
    if family not in LINE_GENERATORS:
        raise ValueError(f"Unknown line family {family!r}; expected one of {list(LINE_GENERATORS)}")
    lines = LINE_GENERATORS[family](LineFamily(values=[float(value)], top_pressure=top_pressure), FULL_RANGES)
    if not lines:
        raise ValueError(f"{family} value {value} is outside the range of the diagrams")
    _, t, p = lines[0]
    ok = np.isfinite(t) & np.isfinite(p)
    return t[ok], p[ok]


LINE_GENERATORS = {
    "isobars": _isobars,
    "isotherms": _isotherms,
    "dry_adiabats": _dry_adiabats,
    "saturated_adiabats": _saturated_adiabats,
    "mixing_ratios": _mixing_ratios,
}


# ---------------------------------------------------------------------------
# Drawing and labelling
# ---------------------------------------------------------------------------


def _draw_family(ax, extent, family, lines, zorder):
    artists = []
    style = {"zorder": zorder, **family.style}
    for i, (value, t, p) in enumerate(lines):
        ok = np.isfinite(t) & np.isfinite(p)
        if ok.sum() < 2:
            continue
        artists += ax.plot(t[ok], p[ok], **style)
        if family.labels and i % max(1, family.label_frequency) == 0:
            label = _label_line(ax, extent, value, t[ok], p[ok], family.label_style, zorder)
            if label is not None:
                artists.append(label)
    return artists


def _inside(x, y, extent, margin=0.0):
    x0, x1, y0, y1 = extent
    return (x >= x0 + margin) & (x <= x1 - margin) & (y >= y0 + margin) & (y <= y1 - margin)


def _label_line(ax, extent, value, t, p, label_style, zorder):
    """Label a line just inside the point where it leaves the diagram, or at its end."""
    x, y = ax.geometry.forward(t, p)
    inside = _inside(x, y, extent)
    if not inside.any():
        return None
    last = np.flatnonzero(inside)[-1]
    first = np.flatnonzero(inside[: last + 1] == False)  # noqa: E712
    start = first[-1] + 1 if len(first) else 0
    xs, ys = x[start : last + 1], y[start : last + 1]
    if len(xs) < 2:
        return None

    # Step back along the line from where it leaves the box
    x0, x1, y0, y1 = extent
    pad = 0.03 * max(abs(x1 - x0), abs(y1 - y0))
    seg = np.hypot(np.diff(xs), np.diff(ys))
    dist = np.concatenate([[0.0], np.cumsum(seg)])
    target = max(dist[-1] - pad, 0.0)
    xl = float(np.interp(target, dist, xs))
    yl = float(np.interp(target, dist, ys))

    k = int(np.clip(np.searchsorted(dist, target), 1, len(xs) - 1))
    angle = np.degrees(np.arctan2(ys[k] - ys[k - 1], xs[k] - xs[k - 1]))
    if angle > 90:
        angle -= 180
    elif angle <= -90:
        angle += 180

    style = {
        "rotation": angle,
        "rotation_mode": "anchor",
        "transform_rotates_text": True,
        "clip_on": True,
        "zorder": zorder + 0.1,
        **label_style,
    }
    return ax.text(xl, yl, f"{value:g}", transform=ax.transData, **style)
