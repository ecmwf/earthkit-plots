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
Coordinate systems of thermodynamic diagrams.

Every diagram maps the *data coordinates* (temperature in °C, pressure in hPa)
onto a 2-D *diagram coordinate* system (x, y), which is what the underlying
matplotlib axes uses as its native data coordinates. The mapping is described
by a :class:`DiagramGeometry` (pure numpy, independently testable) and wrapped
for matplotlib by :class:`ThermoTransform`.

=========  =========================================  ======================
Diagram    Diagram coordinates                        Straight lines
=========  =========================================  ======================
Emagram    x = T, y = -s ln(p / p_ref)                isotherms, isobars
Skew-T     x = T + c y, y = -s ln(p / p_ref)          isotherms, isobars
Tephigram  x = (T + Y) / √2, y = (Y - T) / √2,        isotherms, dry adiabats
           Y = a ln(θ / θ_ref)
=========  =========================================  ======================
"""

import numpy as np
from matplotlib.transforms import Transform

#: Celsius-to-Kelvin offset.
T_C2K = 273.15

#: Reference pressure (hPa) of the logarithmic pressure coordinate.
P_REF = 1000.0


def thermo_backend():
    """Return the ``earthkit.meteo.thermo.array`` module.

    Raises
    ------
    ImportError
        If earthkit-meteo is not installed.
    """
    try:
        from earthkit.meteo.thermo import array as thermo
    except ImportError as e:  # pragma: no cover - depends on the environment
        raise ImportError(
            "Thermodynamic diagrams require earthkit-meteo. Install it with: pip install 'earthkit-plots[thermo]'"
        ) from e
    return thermo


def potential_temperature(t, p):
    """Potential temperature (K) from temperature (°C) and pressure (hPa)."""
    thermo = thermo_backend()
    return thermo.potential_temperature(np.asarray(t, dtype=float) + T_C2K, np.asarray(p, dtype=float) * 100.0)


def pressure_on_dry_adiabat(t, theta):
    """Pressure (hPa) where the dry adiabat ``theta`` (K) has temperature ``t`` (°C)."""
    thermo = thermo_backend()
    return (
        thermo.pressure_on_dry_adiabat(np.asarray(t, dtype=float) + T_C2K, np.asarray(theta, dtype=float), 1e5) / 100.0
    )


class DiagramGeometry:
    """
    Mapping between data coordinates (T [°C], p [hPa]) and diagram coordinates (x, y).

    Subclasses implement :meth:`forward` and :meth:`inverse` and, for tick
    placement, the edge-intersection helpers :meth:`isotherm_x` and
    :meth:`isobar_y`.
    """

    #: Short name of the diagram.
    name = None

    #: Whether the axes must use an equal aspect ratio so that the angles
    #: between the background lines are preserved (e.g. 45° isotherms).
    equal_aspect = True

    def forward(self, t, p):
        """Transform (T [°C], p [hPa]) to diagram coordinates (x, y)."""
        raise NotImplementedError

    def inverse(self, x, y):
        """Transform diagram coordinates (x, y) to (T [°C], p [hPa])."""
        raise NotImplementedError

    def isotherm_x(self, t, y):
        """The x coordinate where the isotherm ``t`` (°C) crosses the horizontal line ``y``."""
        raise NotImplementedError

    def isobar_y(self, p, x):
        """The y coordinate where the isobar ``p`` (hPa) crosses the vertical line ``x``."""
        raise NotImplementedError

    def extent(self, temperature_range, pressure_range):
        """
        Diagram-coordinate box ``(x0, x1, y0, y1)`` of a diagram.

        Parameters
        ----------
        temperature_range : tuple of float
            ``(minimum, maximum)`` temperature (°C) along the bottom isobar.
        pressure_range : tuple of float
            ``(bottom, top)`` pressure (hPa).
        """
        raise NotImplementedError


class LogPressureGeometry(DiagramGeometry):
    """
    Geometry of diagrams with a logarithmic pressure axis (emagram, skew-T).

    ``y = -scale * ln(p / P_REF)`` and ``x = T + skew_factor * y``.

    Parameters
    ----------
    skew_factor : float
        Horizontal shift of the isotherms per unit of ``y``. 0 gives vertical
        isotherms (emagram), 1 gives isotherms at 45° when the aspect is equal.
    scale : float
        Scale of the logarithmic pressure coordinate. With an equal aspect it
        sets the height of the diagram relative to its width in °C.
    """

    def __init__(self, skew_factor=0.0, scale=40.0):
        self.skew_factor = float(skew_factor)
        self.scale = float(scale)

    def _y(self, p):
        return -self.scale * np.log(np.asarray(p, dtype=float) / P_REF)

    def _p(self, y):
        return P_REF * np.exp(-np.asarray(y, dtype=float) / self.scale)

    def forward(self, t, p):
        y = self._y(p)
        return np.asarray(t, dtype=float) + self.skew_factor * y, y

    def inverse(self, x, y):
        y = np.asarray(y, dtype=float)
        return np.asarray(x, dtype=float) - self.skew_factor * y, self._p(y)

    def isotherm_x(self, t, y):
        return np.asarray(t, dtype=float) + self.skew_factor * np.asarray(y, dtype=float)

    def isobar_y(self, p, x):
        return np.broadcast_to(self._y(p), np.broadcast_shapes(np.shape(p), np.shape(x))).copy()

    def extent(self, temperature_range, pressure_range):
        t_min, t_max = temperature_range
        p_bottom, p_top = pressure_range
        y0, y1 = float(self._y(p_bottom)), float(self._y(p_top))
        return (
            float(self.isotherm_x(t_min, y0)),
            float(self.isotherm_x(t_max, y0)),
            y0,
            y1,
        )


class EmagramGeometry(LogPressureGeometry):
    """Emagram: temperature against the logarithm of pressure."""

    name = "emagram"
    equal_aspect = False

    def __init__(self, scale=40.0):
        super().__init__(skew_factor=0.0, scale=scale)


class SkewTGeometry(LogPressureGeometry):
    """
    Skew-T log-p diagram.

    Parameters
    ----------
    skew : float
        Angle (degrees) of the isotherms measured from the horizontal.
    scale : float
        Scale of the logarithmic pressure coordinate.
    """

    name = "skewt"

    def __init__(self, skew=45.0, scale=40.0):
        if not 0 < skew < 90:
            raise ValueError(f"skew must be between 0 and 90 degrees, got {skew}")
        self.skew = float(skew)
        super().__init__(skew_factor=1.0 / np.tan(np.radians(skew)), scale=scale)


class TephigramGeometry(DiagramGeometry):
    """
    Tephigram: temperature against entropy (the logarithm of potential temperature).

    With ``X = T`` and ``Y = a ln(θ / θ_ref)`` the diagram coordinates are the
    (X, Y) plane rotated by 45°, so that isotherms run from bottom-left to
    top-right and dry adiabats from bottom-right to top-left, at right angles.

    Parameters
    ----------
    a : float
        Scale (K) of the entropy coordinate. Along an isobar ``dY/dX = a / T``,
        so isobars are horizontal where ``T = a``. The default makes isobars
        horizontal near 0 °C.
    theta_ref : float
        Potential temperature (K) where ``Y = 0``.
    """

    name = "tephigram"

    #: Sampling of an isobar used to find where it crosses a vertical line.
    _ISOBAR_T = np.linspace(-200.0, 150.0, 3501)

    def __init__(self, a=T_C2K, theta_ref=T_C2K):
        self.a = float(a)
        self.theta_ref = float(theta_ref)

    def _xy(self, X, Y):
        return (X + Y) / np.sqrt(2.0), (Y - X) / np.sqrt(2.0)

    def forward(self, t, p):
        t = np.asarray(t, dtype=float)
        theta = potential_temperature(t, p)
        Y = self.a * np.log(theta / self.theta_ref)
        return self._xy(t, Y)

    def inverse(self, x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        t = (x - y) / np.sqrt(2.0)
        Y = (x + y) / np.sqrt(2.0)
        theta = self.theta_ref * np.exp(Y / self.a)
        return t, pressure_on_dry_adiabat(t, theta)

    def isotherm_x(self, t, y):
        # On an isotherm X = T is constant, i.e. x - y = sqrt(2) * T
        return np.sqrt(2.0) * np.asarray(t, dtype=float) + np.asarray(y, dtype=float)

    def isobar_y(self, p, x):
        p, x = np.broadcast_arrays(np.asarray(p, dtype=float), np.asarray(x, dtype=float))
        out = np.empty(p.shape)
        for idx in np.ndindex(p.shape):
            # x increases monotonically with T along an isobar
            xs, ys = self.forward(self._ISOBAR_T, p[idx])
            out[idx] = np.interp(x[idx], xs, ys, left=np.nan, right=np.nan)
        return out

    def extent(self, temperature_range, pressure_range):
        t_min, t_max = temperature_range
        p_bottom, p_top = pressure_range
        (x0, x1), (ya, yb) = self.forward(np.array([t_min, t_max], dtype=float), p_bottom)
        # The bottom isobar arches upwards, so the bottom edge goes through
        # its lower end to keep the whole of it inside the diagram.
        y0 = min(ya, yb)
        # The top edge goes through the top isobar at the centre of the diagram.
        y1 = float(self.isobar_y(p_top, 0.5 * (x0 + x1)))
        return float(x0), float(x1), float(y0), y1


class ThermoTransform(Transform):
    """
    Matplotlib transform from data coordinates (T [°C], p [hPa]) to diagram coordinates.

    Combined with an axes' ``transData`` it maps (T, p) onto the display.
    Segments between consecutive points are drawn as straight lines in diagram
    coordinates, which is the convention for soundings; the background lines
    are densely sampled so they follow their true shapes.
    """

    input_dims = 2
    output_dims = 2
    is_separable = False
    has_inverse = True

    def __init__(self, geometry):
        super().__init__()
        self.geometry = geometry

    def transform_non_affine(self, values):
        values = np.asarray(values, dtype=float)
        x, y = self.geometry.forward(values[:, 0], values[:, 1])
        return np.column_stack([x, y])

    def inverted(self):
        return InvertedThermoTransform(self.geometry)


class InvertedThermoTransform(Transform):
    """Matplotlib transform from diagram coordinates to (T [°C], p [hPa])."""

    input_dims = 2
    output_dims = 2
    is_separable = False
    has_inverse = True

    def __init__(self, geometry):
        super().__init__()
        self.geometry = geometry

    def transform_non_affine(self, values):
        values = np.asarray(values, dtype=float)
        t, p = self.geometry.inverse(values[:, 0], values[:, 1])
        return np.column_stack([t, p])

    def inverted(self):
        return ThermoTransform(self.geometry)
