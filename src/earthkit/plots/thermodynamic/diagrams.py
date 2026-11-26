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

"""Thermodynamic diagram subplots: :class:`Tephigram`, :class:`SkewT` and :class:`Emagram`."""

import numpy as np

from earthkit.plots.components.subplots import Subplot
from earthkit.plots.thermodynamic import profiles
from earthkit.plots.thermodynamic.axes import ThermoAxes
from earthkit.plots.thermodynamic.grid import ThermoGrid
from earthkit.plots.thermodynamic.ticks import apply_ticks
from earthkit.plots.thermodynamic.transforms import T_C2K, EmagramGeometry, SkewTGeometry, TephigramGeometry

#: Default colour of the temperature and dewpoint profiles.
TEMPERATURE_COLOR = "#e41a1c"

#: Conversion factor from m/s to knots.
KNOTS_PER_MS = 3600.0 / 1852.0


class ThermoDiagram(Subplot):
    """
    Base class of thermodynamic diagrams.

    .. warning::
        This is an experimental new feature. We welcome feedback and bug reports
        on GitHub issues: https://github.com/ecmwf/earthkit-plots/issues

    Data are plotted in temperature (°C) and pressure (hPa): the plotting
    methods map them onto the diagram's coordinate system, which is defined by
    the subclasses (:class:`Tephigram`, :class:`SkewT`, :class:`Emagram`).

    Parameters
    ----------
    temperature_range : tuple of float, optional
        ``(minimum, maximum)`` temperature (°C) along the bottom edge.
    pressure_range : tuple of float, optional
        ``(bottom, top)`` pressure (hPa).
    grid : bool, dict or ThermoGrid, optional
        The background lines. ``True`` (default) draws the default lines,
        ``False`` draws none, and a dict is passed to :class:`ThermoGrid`.
    **kwargs
        Passed to :class:`~earthkit.plots.components.subplots.Subplot`.
    """

    #: Default ``(minimum, maximum)`` temperature (°C).
    default_temperature_range = (-40.0, 50.0)
    #: Default ``(bottom, top)`` pressure (hPa).
    default_pressure_range = (1050.0, 100.0)

    def __init__(self, *args, temperature_range=None, pressure_range=None, grid=True, **kwargs):
        # Profiles in different units (e.g. T in K, Td in °C) are converted to
        # the diagram's coordinates rather than routed onto twin axes.
        kwargs.setdefault("auto_twin_axes", False)
        ax = kwargs.get("ax")
        if ax is not None and not isinstance(ax, ThermoAxes):
            raise TypeError(
                f"{type(self).__name__} requires a ThermoAxes; got {type(ax).__name__}. "
                "Omit ax= to let the diagram create its own axes."
            )
        super().__init__(*args, **kwargs)
        self.temperature_range = tuple(
            float(v) for v in (temperature_range if temperature_range is not None else self.default_temperature_range)
        )
        self.pressure_range = tuple(
            float(v) for v in (pressure_range if pressure_range is not None else self.default_pressure_range)
        )
        if self.pressure_range[0] <= self.pressure_range[1]:
            raise ValueError(f"pressure_range must be (bottom, top) with bottom > top, got {self.pressure_range}")
        if self.temperature_range[0] >= self.temperature_range[1]:
            raise ValueError(f"temperature_range must be (minimum, maximum), got {self.temperature_range}")
        # The geometry is fixed for the lifetime of the axes (artists hold its
        # transform), so it is set up from the initial ranges.
        self.geometry = ax.geometry if ax is not None else self._make_geometry()
        self.thermo_grid = self._parse_grid(grid)
        self._grid_artists = []
        if ax is not None:
            self._setup_axes()

    def _make_geometry(self):
        raise NotImplementedError

    @staticmethod
    def _parse_grid(grid):
        if grid is True:
            return ThermoGrid()
        if grid is False or grid is None:
            return None
        if isinstance(grid, ThermoGrid):
            return grid
        return ThermoGrid(**grid)

    @property
    def ax(self):
        """The underlying :class:`~earthkit.plots.thermodynamic.axes.ThermoAxes`."""
        if self._ax is None:
            subspec = self.figure.gridspec[self.row, self.column]
            self._ax = self.figure.fig.add_subplot(
                subspec, axes_class=ThermoAxes, geometry=self.geometry, **self._ax_kwargs
            )
            self._setup_axes()
        return self._ax

    @property
    def extent(self):
        """The diagram box ``(x0, x1, y0, y1)`` in diagram coordinates."""
        return self.geometry.extent(self.temperature_range, self.pressure_range)

    def _setup_axes(self):
        ax = self._ax
        x0, x1, y0, y1 = self.extent
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        apply_ticks(ax, self.extent)
        ax.set_xlabel("Temperature (°C)")
        ax.set_ylabel("Pressure (hPa)")
        self._draw_grid()

    def _draw_grid(self):
        for artist in self._grid_artists:
            artist.remove()
        self._grid_artists = []
        if self.thermo_grid is not None:
            self._grid_artists = self.thermo_grid.draw(self._ax, self.extent)

    def set_extent(self, temperature_range=None, pressure_range=None):
        """
        Set the temperature and pressure ranges of the diagram.

        Parameters
        ----------
        temperature_range : tuple of float, optional
            ``(minimum, maximum)`` temperature (°C) along the bottom edge.
        pressure_range : tuple of float, optional
            ``(bottom, top)`` pressure (hPa).
        """
        if temperature_range is not None:
            self.temperature_range = tuple(float(v) for v in temperature_range)
        if pressure_range is not None:
            self.pressure_range = tuple(float(v) for v in pressure_range)
        if self._ax is not None:
            self._setup_axes()
        return self

    def grid(self, grid=True, **kwargs):
        """
        Set the background lines of the diagram.

        Parameters
        ----------
        grid : bool or ThermoGrid
            ``False`` removes the background lines.
        **kwargs
            Passed to :class:`ThermoGrid` (e.g. ``mixing_ratios=False``).
        """
        self.thermo_grid = self._parse_grid(kwargs if (grid is True and kwargs) else grid)
        if self._ax is not None:
            self._draw_grid()
        return self

    # Alias matching the name used by Subplot for maps
    gridlines = grid

    def _plot_kwargs(self, source):
        return {}

    # ------------------------------------------------------------------
    # Profiles
    # ------------------------------------------------------------------

    def _profile_line(self, data, p, kind, units, p_units, defaults, kwargs):
        style = {**defaults, **kwargs}
        if profiles._is_xarray(data) and p is None and units is None:
            # Keep the xarray metadata (for titles and labels) by going
            # through the standard plotting pipeline.
            name = profiles.find_pressure_coord(data)
            if data.ndim == 1:
                return self.line(data, y=name, x_units="celsius", y_units="hPa", **style)
        values, p_hpa = profiles.extract(data, p=p, kind=kind, units=units, p_units=p_units)
        return self.line(x=values, y=p_hpa, **style)

    def temperature(self, data, p=None, units=None, p_units="hPa", **kwargs):
        """
        Plot a temperature profile.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            Temperature profile. For xarray objects the units are read from the
            ``units`` attribute and the pressure from the pressure coordinate.
        p : xarray.DataArray or array-like, optional
            Pressure of the profile, required when ``data`` is a plain array.
        units : str, optional
            Units of ``data`` when it is a plain array (default °C) or has no
            ``units`` attribute, e.g. ``"K"``.
        p_units : str, optional
            Units of ``p`` when it is a plain array. Default ``"hPa"``.
        **kwargs
            Passed to :meth:`line` (e.g. ``color``, ``linewidth``, ``label``).
        """
        defaults = {"color": TEMPERATURE_COLOR, "linewidth": 2, "label": "Temperature", "zorder": 3}
        return self._profile_line(data, p, "temperature", units, p_units, defaults, kwargs)

    def dewpoint(
        self,
        data=None,
        p=None,
        units=None,
        p_units="hPa",
        specific_humidity=None,
        relative_humidity=None,
        temperature=None,
        **kwargs,
    ):
        """
        Plot a dewpoint profile.

        The dewpoint is either given directly, or computed with earthkit-meteo
        from ``specific_humidity``, or from ``relative_humidity`` and ``temperature``.

        Parameters
        ----------
        data : xarray.DataArray or array-like, optional
            Dewpoint profile.
        p : xarray.DataArray or array-like, optional
            Pressure of the profile, required for plain arrays.
        units : str, optional
            Units of ``data`` or ``temperature`` when they are plain arrays
            (default °C) or have no ``units`` attribute.
        p_units : str, optional
            Units of ``p`` when it is a plain array. Default ``"hPa"``.
        specific_humidity : xarray.DataArray or array-like, optional
            Specific humidity profile (kg/kg).
        relative_humidity : xarray.DataArray or array-like, optional
            Relative humidity profile (%), used together with ``temperature``.
        temperature : xarray.DataArray or array-like, optional
            Temperature profile, used together with ``relative_humidity``.
        **kwargs
            Passed to :meth:`line`.
        """
        defaults = {
            "color": TEMPERATURE_COLOR,
            "linewidth": 2,
            "linestyle": "--",
            "label": "Dewpoint",
            "zorder": 3,
        }
        if data is not None:
            return self._profile_line(data, p, "temperature", units, p_units, defaults, kwargs)

        if specific_humidity is not None:
            q, p_hpa = profiles.extract(specific_humidity, p=p, kind="raw", p_units=p_units)
            td = profiles.dewpoint_from_specific_humidity(q, p_hpa)
        elif relative_humidity is not None and temperature is not None:
            r, p_hpa = profiles.extract(relative_humidity, p=p, kind="relative_humidity", p_units=p_units)
            t, p_t = profiles.extract(temperature, p=p, kind="temperature", units=units, p_units=p_units)
            if not np.array_equal(p_hpa, p_t):
                raise ValueError("relative_humidity and temperature must be on the same pressure levels")
            td = profiles.dewpoint_from_relative_humidity(t, r)
        else:
            raise ValueError("Provide the dewpoint, specific_humidity, or relative_humidity and temperature")
        return self.line(x=td, y=p_hpa, **{**defaults, **kwargs})

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
        position=0.95,
        every=1,
        **kwargs,
    ):
        """
        Plot a column of wind barbs alongside the diagram.

        The barbs are drawn at a fixed horizontal position, at the height where
        each isobar crosses it.

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
        position : float, optional
            Horizontal position of the column as a fraction of the diagram width.
        every : int, optional
            Plot every n-th level.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.barbs`.
        """
        if u is not None and v is not None:
            u, p_hpa = profiles.extract(u, p=p, kind="raw", p_units=p_units)
            v, _ = profiles.extract(v, p=p, kind="raw", p_units=p_units)
        elif speed is not None and direction is not None:
            from earthkit.meteo.wind import array as wind

            speed, p_hpa = profiles.extract(speed, p=p, kind="raw", p_units=p_units)
            direction, _ = profiles.extract(direction, p=p, kind="raw", p_units=p_units)
            u, v = wind.polar_to_xy(speed, direction)
        else:
            raise ValueError("Provide u and v, or speed and direction")

        if units not in ("m/s", "knots"):
            raise ValueError(f"units must be 'm/s' or 'knots', got {units!r}")
        if knots and units == "m/s":
            u, v = u * KNOTS_PER_MS, v * KNOTS_PER_MS
        elif not knots and units == "knots":
            u, v = u / KNOTS_PER_MS, v / KNOTS_PER_MS

        sel = slice(None, None, max(1, int(every)))
        u, v, p_hpa = u[sel], v[sel], p_hpa[sel]

        x0, x1, y0, y1 = self.extent
        x = x0 + float(position) * (x1 - x0)
        y = np.asarray(self.geometry.isobar_y(p_hpa, x), dtype=float)
        ok = np.isfinite(y) & np.isfinite(u) & np.isfinite(v) & (y >= y0) & (y <= y1)
        style = {"length": 6, "linewidth": 0.8, "color": "#1a6b1a", "zorder": 3, "clip_on": False, **kwargs}
        return self.ax.barbs(np.full(ok.sum(), x), y[ok], u[ok], v[ok], transform=self.ax.transData, **style)


class Tephigram(ThermoDiagram):
    """
    A tephigram: temperature against entropy (logarithm of potential temperature).

    Isotherms and dry adiabats are straight lines at right angles; isobars are
    gently curved.

    Parameters
    ----------
    temperature_range : tuple of float, optional
        ``(minimum, maximum)`` temperature (°C) along the bottom isobar. Default ``(-60, 60)``.
    pressure_range : tuple of float, optional
        ``(bottom, top)`` pressure (hPa). Default ``(1050, 50)``.
    a : float, optional
        Scale (K) of the entropy coordinate: isobars are horizontal where the
        temperature equals ``a``. By default it is the logarithmic mean of
        ``temperature_range`` (in K), which makes the bottom isobar level at
        both ends so the isobars arch gently across the diagram. See
        :class:`~earthkit.plots.thermodynamic.transforms.TephigramGeometry`.
    theta_ref : float, optional
        Reference potential temperature (K) of the entropy coordinate.
    **kwargs
        Passed to :class:`ThermoDiagram`.
    """

    default_temperature_range = (-60.0, 60.0)
    default_pressure_range = (1050.0, 50.0)

    def __init__(self, *args, a=None, theta_ref=None, **kwargs):
        self._geometry_kwargs = {k: v for k, v in {"a": a, "theta_ref": theta_ref}.items() if v is not None}
        super().__init__(*args, **kwargs)

    def _make_geometry(self):
        kwargs = dict(self._geometry_kwargs)
        if "a" not in kwargs:
            # Along an isobar y is proportional to a ln(T) - T, so the ends of the
            # bottom isobar are level when a is the logarithmic mean temperature.
            t_min, t_max = (t + T_C2K for t in self.temperature_range)
            kwargs["a"] = (t_max - t_min) / np.log(t_max / t_min)
        return TephigramGeometry(**kwargs)


class SkewT(ThermoDiagram):
    """
    A skew-T log-p diagram.

    Isobars are horizontal and the isotherms are skewed by ``skew`` degrees.

    Parameters
    ----------
    temperature_range : tuple of float, optional
        ``(minimum, maximum)`` temperature (°C) along the bottom isobar. Default ``(-40, 50)``.
    pressure_range : tuple of float, optional
        ``(bottom, top)`` pressure (hPa). Default ``(1050, 100)``.
    skew : float, optional
        Angle (degrees) of the isotherms from the horizontal. Default 45.
    **kwargs
        Passed to :class:`ThermoDiagram`.
    """

    default_temperature_range = (-40.0, 50.0)
    default_pressure_range = (1050.0, 100.0)

    def __init__(self, *args, skew=45.0, **kwargs):
        self._skew = skew
        super().__init__(*args, **kwargs)

    def _make_geometry(self):
        return SkewTGeometry(skew=self._skew)


class Emagram(ThermoDiagram):
    """
    An emagram: temperature against the logarithm of pressure.

    Isotherms are vertical and isobars horizontal.

    Parameters
    ----------
    temperature_range : tuple of float, optional
        ``(minimum, maximum)`` temperature (°C). Default ``(-80, 40)``.
    pressure_range : tuple of float, optional
        ``(bottom, top)`` pressure (hPa). Default ``(1050, 100)``.
    **kwargs
        Passed to :class:`ThermoDiagram`.
    """

    default_temperature_range = (-80.0, 40.0)
    default_pressure_range = (1050.0, 100.0)

    def _make_geometry(self):
        return EmagramGeometry()
