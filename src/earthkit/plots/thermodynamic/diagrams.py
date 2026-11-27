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
from earthkit.plots.thermodynamic import grid, parcel, profiles
from earthkit.plots.thermodynamic.axes import ThermoAxes
from earthkit.plots.thermodynamic.grid import ThermoGrid
from earthkit.plots.thermodynamic.ticks import apply_ticks
from earthkit.plots.thermodynamic.transforms import T_C2K, EmagramGeometry, SkewTGeometry, TephigramGeometry

#: Default colour of the temperature and dewpoint profiles.
TEMPERATURE_COLOR = "#e41a1c"

#: Default colour of parcel paths.
PARCEL_COLOR = "#333333"

#: Default colour of single highlighted background lines.
HIGHLIGHT_COLOR = "#333333"

#: Default colour of wind barbs.
WIND_COLOR = "#1a6b1a"

#: Conversion factor from m/s to knots.
KNOTS_PER_MS = profiles.KNOTS_PER_MS


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
        self._side_panels = []
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
        # The side panels follow the extent and the isobars of the diagram
        for panel in self._side_panels:
            panel._setup()

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

    def _profile_line(self, data, p, kind, units, p_units, defaults, kwargs, column=None):
        style = {**defaults, **kwargs}
        if profiles.is_pandas(data):
            # Keep the whole frame (e.g. the constant latitude and longitude
            # columns of a station) for titles and labels by going through the
            # standard plotting pipeline, with the profile indexed by pressure.
            frame, column, p_name = profiles.pandas_profile(
                data, column=column, p=p, kind=kind, units=units, p_units=p_units
            )
            return self.line(frame, x=column, y=p_name, x_units="celsius", y_units="hPa", **style)
        if profiles._is_xarray(data) and p is None and units is None:
            # Keep the xarray metadata (for titles and labels) by going
            # through the standard plotting pipeline.
            name = profiles.find_pressure_coord(data)
            if data.ndim == 1:
                return self.line(data, y=name, x_units="celsius", y_units="hPa", **style)
        values, p_hpa = profiles.extract(data, p=p, kind=kind, units=units, p_units=p_units)
        return self.line(x=values, y=p_hpa, **style)

    def temperature(self, data, p=None, units=None, p_units="hPa", column=None, **kwargs):
        """
        Plot a temperature profile.

        Parameters
        ----------
        data : xarray.DataArray, pandas.DataFrame, pandas.Series or array-like
            Temperature profile. For xarray objects the units are read from the
            ``units`` attribute and the pressure from the pressure coordinate.
        p : str, xarray.DataArray or array-like, optional
            Pressure of the profile, required when ``data`` is a plain array.
            For pandas objects it may be the name of a column, and defaults to
            the index when it is named.
        units : str, optional
            Units of ``data`` when it is a plain array (default °C) or has no
            ``units`` attribute, e.g. ``"K"``.
        p_units : str, optional
            Units of ``p`` when it is a plain array or has no units attribute.
            Default ``"hPa"``.
        column : str, optional
            For a pandas DataFrame, the column holding the temperature. Levels
            with missing values are dropped, and the other columns provide
            metadata for titles: e.g. constant ``latitude`` and ``longitude``
            columns give ``{latitude}`` and ``{longitude}``.
        **kwargs
            Passed to :meth:`line` (e.g. ``color``, ``linewidth``, ``label``).

        Examples
        --------
        >>> tephi.temperature(df, column="airTemperature", p="pressure", units="K", p_units="Pa")
        >>> tephi.title("Station at {latitude:%Lt}, {longitude:%Ln}")
        """
        defaults = {"color": TEMPERATURE_COLOR, "linewidth": 2, "label": "Temperature", "zorder": 3}
        return self._profile_line(data, p, "temperature", units, p_units, defaults, kwargs, column=column)

    def dewpoint(
        self,
        data=None,
        p=None,
        units=None,
        p_units="hPa",
        specific_humidity=None,
        relative_humidity=None,
        temperature=None,
        column=None,
        **kwargs,
    ):
        """
        Plot a dewpoint profile.

        The dewpoint is either given directly, or computed with earthkit-meteo
        from ``specific_humidity``, or from ``relative_humidity`` and ``temperature``.

        Parameters
        ----------
        data : xarray.DataArray, pandas.DataFrame, pandas.Series or array-like, optional
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
        column : str, optional
            For a pandas DataFrame, the column holding the dewpoint, see
            :meth:`temperature`.
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
            return self._profile_line(data, p, "temperature", units, p_units, defaults, kwargs, column=column)

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

    def envelope(self, lower, upper, p=None, units=None, p_units="hPa", alpha=0.4, column=None, **kwargs):
        """
        Shade the band between two temperature (or dewpoint) profiles.

        Typically used for the spread of an ensemble, e.g. its minimum and
        maximum or two of its quantiles at each pressure level.

        Parameters
        ----------
        lower, upper : xarray.DataArray or array-like
            The profiles bounding the band, on the same pressure levels. For
            xarray objects the units are read from the ``units`` attribute and
            the pressure from the pressure coordinate.
        p : xarray.DataArray or array-like, optional
            Pressure of the profiles, required when they are plain arrays.
        units : str, optional
            Units of the profiles when they are plain arrays (default °C) or have
            no ``units`` attribute, e.g. ``"K"``.
        p_units : str, optional
            Units of ``p`` when it is a plain array. Default ``"hPa"``.
        alpha : float, optional
            Opacity of the band. Default 0.4.
        column : str, optional
            For pandas DataFrames, the column holding the profiles.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.fill_betweenx`, e.g. ``color``
            and ``label``.

        Returns
        -------
        matplotlib.collections.PolyCollection

        Examples
        --------
        >>> q = t_ens.quantile([0.25, 0.75], dim="member", keep_attrs=True)
        >>> tephi.envelope(q.sel(quantile=0.25), q.sel(quantile=0.75), color="red")
        """
        lo, p_lo = profiles.extract(lower, p=p, kind="temperature", units=units, p_units=p_units, column=column)
        hi, p_hi = profiles.extract(upper, p=p, kind="temperature", units=units, p_units=p_units, column=column)
        if p_lo.shape != p_hi.shape or not np.allclose(p_lo, p_hi):
            raise ValueError("lower and upper must be on the same pressure levels")
        style = {"color": TEMPERATURE_COLOR, "alpha": alpha, "linewidth": 0, "zorder": 1.2, **kwargs}
        return self.ax.fill_betweenx(p_lo, lo, hi, **style)

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
        panel=False,
        **kwargs,
    ):
        """
        Plot a column of wind barbs on the diagram or in a side panel.

        On the diagram the barbs are drawn at a fixed horizontal position, at
        the height where each isobar crosses it.

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
            Not used when the barbs are drawn in a panel.
        every : int, optional
            Plot every n-th level.
        panel : bool or SidePanel, optional
            Where to draw the barbs. ``False`` (default) draws them on the
            diagram; ``True`` in a new narrow :meth:`side_panel` without an x
            axis; a :class:`SidePanel` (from :meth:`side_panel`) in that panel,
            e.g. alongside the dewpoint depression.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.barbs`.

        Examples
        --------
        >>> tephi.wind(u, v, p=p)  # on the diagram
        >>> tephi.wind(u, v, p=p, panel=True)  # in a side panel
        """
        if panel is not False and panel is not None:
            if panel is True:
                panel = self.side_panel(width=0.14, pad=0.02, xaxis=False)
            kwargs.setdefault("color", WIND_COLOR)
            return panel.wind(
                u=u,
                v=v,
                p=p,
                speed=speed,
                direction=direction,
                p_units=p_units,
                units=units,
                knots=knots,
                every=every,
                **kwargs,
            )
        u, v, p_hpa = profiles.wind_components(
            u=u, v=v, p=p, speed=speed, direction=direction, p_units=p_units, units=units, knots=knots
        )
        sel = slice(None, None, max(1, int(every)))
        u, v, p_hpa = u[sel], v[sel], p_hpa[sel]

        x0, x1, y0, y1 = self.extent
        x = x0 + float(position) * (x1 - x0)
        y = np.asarray(self.geometry.isobar_y(p_hpa, x), dtype=float)
        ok = np.isfinite(y) & np.isfinite(u) & np.isfinite(v) & (y >= y0) & (y <= y1)
        style = {"length": 6, "linewidth": 0.8, "color": WIND_COLOR, "zorder": 3, "clip_on": False, **kwargs}
        return self.ax.barbs(np.full(ok.sum(), x), y[ok], u[ok], v[ok], transform=self.ax.transData, **style)

    def side_panel(self, width=0.25, pad=0.05, xlim=None, xlabel=None, isobars=True, pressure_labels=True, xaxis=True):
        """
        Add a panel alongside the right edge of the diagram.

        The panel shares the pressure scale of the diagram and plots other
        quantities against pressure, e.g. the dewpoint depression or the wind.
        Each pressure level is at the height where its isobar meets the right
        edge of the diagram, so the isobars continue horizontally into the panel.

        Parameters
        ----------
        width : float, optional
            Width of the panel as a fraction of the width of the diagram. Default 0.25.
        pad : float, optional
            Gap between the diagram and the panel as a fraction of the width of
            the diagram. Default 0.05, which leaves room for the tick labels.
        xlim : tuple of float, optional
            Limits of the x axis of the panel. By default they fit the data.
        xlabel : str, optional
            Label of the x axis of the panel.
        isobars : bool, optional
            Continue the isobars of the background lines into the panel. Default ``True``.
        pressure_labels : bool, optional
            Label the pressure levels on the right edge of the panel. Default ``True``.
        xaxis : bool, optional
            Show the x axis of the panel. Set it to ``False`` for a panel of wind
            barbs only (see also ``wind(..., panel=True)``). Default ``True``.

        Returns
        -------
        SidePanel
            The panel, with :meth:`~SidePanel.line`, :meth:`~SidePanel.envelope`
            and :meth:`~SidePanel.wind` methods. Its matplotlib axes is ``panel.ax``.

        Examples
        --------
        >>> panel = tephi.side_panel(xlim=(0, 20), xlabel="T - Td (K)")
        >>> panel.line(t - td)
        >>> panel.wind(u, v)
        """
        from earthkit.plots.thermodynamic.side_panel import SidePanel

        panel = SidePanel(
            self,
            width=width,
            pad=pad,
            xlim=xlim,
            xlabel=xlabel,
            isobars=isobars,
            pressure_labels=pressure_labels,
            xaxis=xaxis,
        )
        self._side_panels.append(panel)
        return panel

    # ------------------------------------------------------------------
    # Parcel ascent
    # ------------------------------------------------------------------

    def parcel(self, path, virtual=True, **kwargs):
        """
        Plot the path of a lifted parcel.

        Parameters
        ----------
        path : earthkit.meteo.thermo.array.cape_cin.ParcelPath
            The parcel ascent of a single profile, computed with earthkit-meteo:
            ``extras["parcel_path"]`` from
            :func:`earthkit.meteo.thermo.surface_cape_cin`,
            :func:`~earthkit.meteo.thermo.mixed_layer_cape_cin` or
            :func:`~earthkit.meteo.thermo.most_unstable_cape_cin` called with
            ``extra_outputs=["parcel_path"]``.
        virtual : bool, optional
            Plot the virtual temperature of the parcel (default), which is what
            CAPE and CIN are computed from and what bounds the areas shaded by
            :meth:`cape_cin`. If ``False`` the temperature is plotted.
        **kwargs
            Passed to :meth:`line`.

        Examples
        --------
        >>> from earthkit.meteo import thermo
        >>> cape, cin, extras = thermo.surface_cape_cin(
        ...     p, t, q, zh, p_sfc, t_sfc, q_sfc, zh_sfc, extra_outputs=["parcel_path"]
        ... )
        >>> tephi.cape_cin(extras["parcel_path"])
        >>> tephi.parcel(extras["parcel_path"])
        """
        prof = parcel.ParcelProfiles.from_path(path)
        defaults = {"color": PARCEL_COLOR, "linestyle": "--", "linewidth": 2.5, "label": "Parcel", "zorder": 3}
        return self.line(x=prof.tv if virtual else prof.t, y=prof.p, **{**defaults, **kwargs})

    def cape_cin(self, path, positive_color="red", negative_color="blue", alpha=0.6, **kwargs):
        """
        Shade the positive (CAPE) and negative (CIN) buoyancy areas of a lifted parcel.

        The areas lie between the virtual temperature of the parcel and that of
        the environment, from the start of the ascent up to the equilibrium
        level. The parcel is warmer than its environment in the positive areas
        and colder in the negative ones. Nothing is shaded when the parcel has no
        level of free convection.

        Parameters
        ----------
        path : earthkit.meteo.thermo.array.cape_cin.ParcelPath
            The parcel ascent of a single profile, see :meth:`parcel`.
        positive_color : str, optional
            Colour of the positive areas. Default ``"red"``.
        negative_color : str, optional
            Colour of the negative areas. Default ``"blue"``.
        alpha : float, optional
            Opacity of the areas. Default 0.6.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.fill_betweenx` for both areas.

        Returns
        -------
        tuple of matplotlib.collections.PolyCollection or None
            The positive and negative areas (``None`` when nothing is shaded).
        """
        prof = parcel.ParcelProfiles.from_path(path)
        top = parcel.shading_top(path)
        if top is None or len(prof.p) < 2:
            return None, None
        in_layer = prof.p >= top
        style = {"alpha": alpha, "linewidth": 0, "zorder": 1, **kwargs}
        areas = []
        for color, mask in (
            (positive_color, prof.tv > prof.tv_env),
            (negative_color, prof.tv < prof.tv_env),
        ):
            areas.append(
                self.ax.fill_betweenx(
                    prof.p, prof.tv_env, prof.tv, where=mask & in_layer, interpolate=True, color=color, **style
                )
            )
        return tuple(areas)

    # ------------------------------------------------------------------
    # Annotations
    # ------------------------------------------------------------------

    def info_box(self, content, loc="upper right", fontsize=8, **kwargs):
        """
        Add a box of text, e.g. a summary of a parcel computation.

        Parameters
        ----------
        content : dict, list of str or str
            The text. A dict is written as ``label: value`` lines with the labels
            right-aligned on the colons; the values are written with ``str`` so
            format numbers before passing them. A list is written one item per line.
        loc : str, optional
            Location of the box, as for :meth:`legend`, e.g. ``"upper right"``.
        fontsize : float, optional
            Font size of the text. The font is monospaced so that the lines align.
        **kwargs
            Passed to :class:`matplotlib.offsetbox.AnchoredText`.

        Returns
        -------
        matplotlib.offsetbox.AnchoredText

        Examples
        --------
        >>> tephi.info_box({"CAPE": f"{cape:.0f} J/kg", "CIN": f"{cin:.0f} J/kg"})
        """
        from matplotlib.offsetbox import AnchoredText

        if isinstance(content, dict):
            width = max((len(str(k)) for k in content), default=0)
            text = "\n".join(f"{str(k):>{width}}: {v}" for k, v in content.items())
        elif isinstance(content, str):
            text = content
        else:
            text = "\n".join(str(line) for line in content)

        prop = {"family": "monospace", "size": fontsize, **kwargs.pop("prop", {})}
        box = AnchoredText(text, loc=loc, prop=prop, **kwargs)
        box.patch.set_boxstyle("square,pad=0.3")
        box.patch.set_edgecolor("#333333")
        box.set_zorder(5)
        self.ax.add_artist(box)
        return box

    # ------------------------------------------------------------------
    # Single background lines
    # ------------------------------------------------------------------

    def _background_line(self, family, value, top_pressure, kwargs):
        t, p = grid.single_line(family, value, top_pressure=top_pressure)
        style = {"color": HIGHLIGHT_COLOR, "linewidth": 1.5, "zorder": 1.5, **kwargs}
        (line,) = self.ax.plot(t, p, **style)
        return line

    def isotherm(self, t, **kwargs):
        """
        Draw (e.g. highlight) the isotherm of temperature ``t`` (°C).

        Parameters
        ----------
        t : float
            Temperature (°C).
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.plot`.

        Examples
        --------
        >>> tephi.isotherm(0, color="red")
        """
        return self._background_line("isotherms", t, None, kwargs)

    def isobar(self, p, **kwargs):
        """
        Draw the isobar of pressure ``p`` (hPa).

        **kwargs are passed to :meth:`matplotlib.axes.Axes.plot`.
        """
        return self._background_line("isobars", p, None, kwargs)

    def dry_adiabat(self, theta, **kwargs):
        """
        Draw the dry adiabat of potential temperature ``theta`` (°C).

        **kwargs are passed to :meth:`matplotlib.axes.Axes.plot`.
        """
        return self._background_line("dry_adiabats", theta, None, kwargs)

    def saturated_adiabat(self, theta_w, **kwargs):
        """
        Draw the saturated (pseudo) adiabat of wet-bulb potential temperature ``theta_w`` (°C).

        **kwargs are passed to :meth:`matplotlib.axes.Axes.plot`.
        """
        return self._background_line("saturated_adiabats", theta_w, None, kwargs)

    def mixing_ratio_line(self, w, top_pressure=None, **kwargs):
        """
        Draw the saturation mixing-ratio line of ``w`` (g/kg).

        Parameters
        ----------
        w : float
            Saturation mixing ratio (g/kg).
        top_pressure : float, optional
            Pressure (hPa) where the line ends. By default it reaches the top of the diagram.
        **kwargs
            Passed to :meth:`matplotlib.axes.Axes.plot`.
        """
        return self._background_line("mixing_ratios", w, top_pressure, kwargs)


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
