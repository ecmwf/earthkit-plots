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

import functools
import warnings

import matplotlib.dates as mdates
import numpy as np

from earthkit.plots.components.extractors import (
    _apply_coordinate_unit_conversion,
    extract_plottables_1D,
    extract_plottables_2D,
    extract_plottables_vector_2D,
)
from earthkit.plots.components.layers import Layer
from earthkit.plots.metadata.formatters import (
    LayerFormatter,
    SourceFormatter,
    SubplotFormatter,
)
from earthkit.plots.resample import _AUTO, Bilinear
from earthkit.plots.schemas import schema
from earthkit.plots.sources import get_source
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.styles import _STYLE_KWARGS, auto, get_style_class
from earthkit.plots.utils import string_utils

DEFAULT_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]
ZERO_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]

TARGET_DENSITY = 40

LAYER_ZORDERS = {
    "contourf": 1,
    "pcolormesh": 1,
    "scatter": 2,
    "contour": 3,
    "quiver": 3,
    "barbs": 3,
    "streamplot": 3,
}


def _darken_color(color, factor=0.25):
    from matplotlib.colors import to_hex, to_rgb

    rgb = to_rgb(color)
    return to_hex(tuple(c * factor for c in rgb))


def plot_1D(method_name=None):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(
            self,
            *args,
            x=None,
            y=None,
            z=None,
            style=None,
            every=None,
            colorby=None,
            dashby=None,
            markerby=None,
            sizeby=None,
            colors=None,
            dashes=None,
            markers=None,
            sizes=None,
            label=None,
            **kwargs,
        ):
            from itertools import product

            import numpy as np
            import pandas as pd
            import xarray as xr

            # Inject subplot-level fixed units if not already specified by the caller.
            if "x_units" not in kwargs and self._fixed_x_units is not None:
                kwargs["x_units"] = self._fixed_x_units
            if (
                "y_units" not in kwargs
                and "units" not in kwargs
                and self._fixed_y_units is not None
            ):
                kwargs["y_units"] = self._fixed_y_units

            # Accept underscore aliases (color_by → colorby, etc.)
            if colorby is None:
                colorby = kwargs.pop("color_by", None)
            if dashby is None:
                dashby = kwargs.pop("dash_by", None)
            if markerby is None:
                markerby = kwargs.pop("marker_by", None)
            if sizeby is None:
                sizeby = kwargs.pop("size_by", None)

            # Collect active *by dimensions: param_key → coordinate name
            by_dims = {
                k: v
                for k, v in [
                    ("colorby", colorby),
                    ("dashby", dashby),
                    ("markerby", markerby),
                    ("sizeby", sizeby),
                ]
                if v is not None
            }

            if not by_dims:
                # Default single-call path — no grouping requested
                return extract_plottables_1D(
                    self,
                    method_name or method.__name__,
                    args=args,
                    x=x,
                    y=y,
                    z=z,
                    style=style,
                    every=every,
                    label=label,
                    **kwargs,
                )

            # Require xarray DataArray when any *by is set
            data = args[0] if args else None
            if not isinstance(data, xr.DataArray):
                raise TypeError(
                    "colorby/dashby/markerby/sizeby require a single xarray "
                    "DataArray as the first positional argument."
                )
            rest_args = args[1:]

            # ------------------------------------------------------------------
            # Helpers
            # ------------------------------------------------------------------

            def _unique_vals(da, dim):
                """Unique values along *dim*, preserving numpy dtype for .sel()."""
                vals = da[dim].values
                seen = {}
                for v in vals.flat:
                    key = v.tobytes() if hasattr(v, "tobytes") else v
                    if key not in seen:
                        seen[key] = v
                return list(seen.values())

            def _to_python(val):
                """Convert numpy scalar to a Python-native value for formatting."""
                if isinstance(val, np.datetime64):
                    return pd.Timestamp(val)
                if hasattr(val, "item"):
                    return val.item()
                return val

            def _scalar_str(val):
                """Default human-readable string for a single value."""
                py_val = _to_python(val)
                if hasattr(py_val, "isoformat"):
                    return str(py_val)[:10]
                return str(py_val)

            def _make_label(combo):
                """Build legend label for a combination of *by values."""
                # Map coordinate name → python value, deduplicating repeated coords
                coord_vals = {}
                for dim_key, val in zip(dim_keys, combo):
                    coord = by_dims[dim_key]
                    if coord not in coord_vals:
                        coord_vals[coord] = _to_python(val)
                if label is not None:
                    return label.format(**coord_vals)
                # Default: join unique values with " / "
                return " / ".join(_scalar_str(v) for v in coord_vals.values())

            # ------------------------------------------------------------------
            # Build visual mappings for each *by dimension
            # list  → positional assignment (index order matches unique values)
            # dict  → explicit mapping (coord value string → visual value)
            # None  → use defaults
            # ------------------------------------------------------------------

            _DEFAULT_DASHES = ["solid", "dashed", "dotted", "dashdot"]
            _DEFAULT_MARKERS = ["o", "s", "^", "D", "v", "p", "X", "*"]

            from matplotlib import rcParams

            # Call _unique_vals ONCE per dimension so id() keys are stable
            # throughout the entire function.
            dim_keys = list(by_dims.keys())
            dim_unique = {dk: _unique_vals(data, by_dims[dk]) for dk in dim_keys}

            def _build_map(unique, user_values, default_fn):
                """Return {id(val): visual_value} for a *by dimension."""
                n = len(unique)
                if user_values is None:
                    vis_vals = [default_fn(i) for i in range(n)]
                elif isinstance(user_values, dict):
                    vis_vals = [
                        user_values.get(str(_to_python(v)), default_fn(i))
                        for i, v in enumerate(unique)
                    ]
                else:
                    cycle = list(user_values)
                    vis_vals = [cycle[i % len(cycle)] for i in range(n)]
                return {id(v): vis for v, vis in zip(unique, vis_vals)}

            prop_cycle_colors = [p["color"] for p in rcParams["axes.prop_cycle"]]

            color_map = (
                _build_map(
                    dim_unique["colorby"],
                    colors,
                    lambda i: prop_cycle_colors[i % len(prop_cycle_colors)],
                )
                if colorby is not None
                else {}
            )
            dash_map = (
                _build_map(
                    dim_unique["dashby"],
                    dashes,
                    lambda i: _DEFAULT_DASHES[i % len(_DEFAULT_DASHES)],
                )
                if dashby is not None
                else {}
            )
            marker_map = (
                _build_map(
                    dim_unique["markerby"],
                    markers,
                    lambda i: _DEFAULT_MARKERS[i % len(_DEFAULT_MARKERS)],
                )
                if markerby is not None
                else {}
            )
            size_map = (
                _build_map(
                    dim_unique["sizeby"],
                    sizes,
                    lambda i: float(
                        np.linspace(0.8, 2.0, max(len(dim_unique["sizeby"]), 1))[i]
                    ),
                )
                if sizeby is not None
                else {}
            )

            # ------------------------------------------------------------------
            # Iterate over the cartesian product of all *by dimensions
            # ------------------------------------------------------------------

            combos = list(product(*[dim_unique[dk] for dk in dim_keys]))

            seen_label_keys = set()
            mappables = []

            for combo in combos:
                sel = {}
                call_kwargs = dict(kwargs)

                for dim_key, val in zip(dim_keys, combo):
                    coord = by_dims[dim_key]
                    sel[coord] = val
                    if dim_key == "colorby":
                        call_kwargs["color"] = color_map[id(val)]
                    elif dim_key == "dashby":
                        call_kwargs["linestyle"] = dash_map[id(val)]
                    elif dim_key == "markerby":
                        call_kwargs["marker"] = marker_map[id(val)]
                    elif dim_key == "sizeby":
                        call_kwargs["linewidth"] = size_map[id(val)]

                slice_da = data.sel(sel)

                # One legend entry per unique combination of *by coord values;
                # suppress duplicates (e.g. same coord used in colorby + dashby).
                label_key = tuple(
                    id(combo[i])
                    for i, dk in enumerate(dim_keys)
                    # deduplicate by coord name — only first occurrence counts
                    if by_dims[dk] not in [by_dims[dim_keys[j]] for j in range(i)]
                )
                if label_key not in seen_label_keys:
                    call_kwargs["label"] = _make_label(combo)
                    seen_label_keys.add(label_key)
                else:
                    call_kwargs["label"] = "_nolegend_"

                mappables.append(
                    extract_plottables_1D(
                        self,
                        method_name or method.__name__,
                        args=(slice_da, *rest_args),
                        x=x,
                        y=y,
                        z=z,
                        style=style,
                        every=every,
                        **call_kwargs,
                    )
                )

            return mappables

        return wrapper

    return decorator


def plot_2D(method_name=None, extract_domain=False, default_resample=_AUTO):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(
            self,
            *args,
            x=None,
            y=None,
            z=None,
            style=None,
            every=None,
            auto_style=False,
            resample=_AUTO,
            **kwargs,
        ):
            if resample is _AUTO:
                # "auto": resolved later in extract_plottables_2D once the
                # source gridspec is known (Regrid for HEALPix/reduced_gg,
                # Bilinear for everything else).
                if default_resample is False:
                    resample = False  # method explicitly opts out of resampling
                # else: keep _AUTO — the pipeline will resolve it
            elif resample is True:
                resample = Bilinear()
            elif isinstance(resample, list):
                from earthkit.plots.resample import Chain

                resample = Chain(resample)
            return extract_plottables_2D(
                subplot=self,
                method_name=method_name or method.__name__,
                args=args,
                x=x,
                y=y,
                z=z,
                style=style,
                every=every,
                auto_style=auto_style,
                extract_domain=extract_domain,
                resample=resample,
                **kwargs,
            )

        return wrapper

    return decorator


def plot_vector(method_name=None, extract_domain=False):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(
            self,
            *args,
            x=None,
            y=None,
            u=None,
            v=None,
            colors=False,
            style=None,
            units=None,
            auto_style=False,
            source_units=None,
            resample=Bilinear(40),
            **kwargs,
        ):
            return extract_plottables_vector_2D(
                subplot=self,
                method_name=method_name or method.__name__,
                args=args,
                x=x,
                y=y,
                u=u,
                v=v,
                style=style,
                units=units,
                auto_style=auto_style,
                source_units=source_units,
                extract_domain=extract_domain,
                resample=resample,
                colors=colors,
                **kwargs,
            )

        return wrapper

    return decorator


class Subplot:
    """
    A single plot within a Figure.

    A Subplot is a container for one or more Layers, each of which is a plot of
    a single data source.

    Parameters
    ----------
    row : int, optional
        The row index of the subplot in the Figure.
    column : int, optional
        The column index of the subplot in the Figure.
    figure : Figure, optional
        The Figure to which the subplot belongs.
    **kwargs
        Additional keyword arguments to pass to the :class:`matplotlib.axes.Axes` constructor.
    """

    def __init__(self, row=0, column=0, figure=None, size=None, **kwargs):
        self._figure = figure

        if figure is not None and size is not None:
            warnings.warn("Subplot size is ignored when a Figure is provided.")
            self._size = None
        else:
            self._size = size

        self._ax = None
        self._ax_kwargs = kwargs

        self.layers = []

        self.row = row
        self.column = column

        self.domain = None
        self._crs = None

        self._fixed_x_units = None
        self._fixed_y_units = None

    def fix_x_units(self, units):
        """
        Set a permanent unit for the x-axis.

        All subsequent plot calls on this subplot will convert x-axis data to
        *units* without needing ``x_units=`` on every call.

        Parameters
        ----------
        units : str
            Target units string (e.g. ``"celsius"``).
        """
        self._fixed_x_units = units

    def fix_y_units(self, units):
        """
        Set a permanent unit for the y-axis.

        All subsequent plot calls on this subplot will convert y-axis data to
        *units* without needing ``units=`` on every call.

        Parameters
        ----------
        units : str
            Target units string (e.g. ``"celsius"``).
        """
        self._fixed_y_units = units

    @property
    def crs(self):
        """The Coordinate Reference System of the subplot."""
        return None

    def attribution(self, attribution, location="lower center", **kwargs):
        """
        Add an attribution to the figure.

        Parameters
        ----------
        attribution : str
            The attribution text to add to the figure.
        location : str, optional
            The location of the attribution text. Accepts the same values as
            matplotlib legend locations: 'upper left', 'upper right',
            'lower left', 'lower right', 'upper center', 'lower center',
            'center left', 'center right', 'center'. Default is 'lower center'.
        **kwargs
            Additional keyword arguments passed to ``matplotlib.figure.Figure.text``.
        """
        self.figure.attribution(attribution, location=location, **kwargs)

    def add_logo(self, logo):
        """
        Add a logo to the figure.

        Parameters
        ----------
        logo : str
            Either the name of a built-in logo, or a path to the logo image file to add to the figure.
        """
        self.figure.add_logo(logo)

    def xticks(
        self,
        frequency=None,
        minor_frequency=None,
        format=None,
        minor_format=None,
        period=False,
        labels="major",
        **kwargs,
    ):
        """
        Set x-axis tick locations and formatting.

        Parameters
        ----------
        frequency : str, optional
            Major tick frequency (e.g., "Y", "M6", "D7", "H").
            Default is None (auto).
        minor_frequency : str, optional
            Minor tick frequency. If None, uses frequency.
            Default is None.
        format : str, optional
            Format string for major tick labels.
            Default is None (auto).
        minor_format : str, optional
            Format string for minor tick labels. If None and format is specified, uses format.
            Default is None.
        period : bool, optional
            If True, centers labels between ticks for better visual balance.
            Default is False.
        labels : str, optional
            Which tick labels to show: "major", "minor", "both", or None.
            Default is "major".
        **kwargs
            Additional keyword arguments to pass to the tick locators.
        """
        from .ticks import set_xticks

        set_xticks(
            self.ax,
            frequency=frequency,
            minor_frequency=minor_frequency,
            format=format,
            minor_format=minor_format,
            period=period,
            labels=labels,
            **kwargs,
        )

    def yticks(
        self,
        frequency=None,
        minor_frequency=None,
        format=None,
        minor_format=None,
        labels="major",
        **kwargs,
    ):
        """
        Set y-axis tick locations and formatting.

        Parameters
        ----------
        frequency : str, optional
            Major tick frequency (e.g., "Y", "M6", "D7", "H").
            Default is None (auto).
        minor_frequency : str, optional
            Minor tick frequency. If None, uses frequency.
            Default is None.
        format : str, optional
            Format string for major tick labels.
            Default is None (auto).
        minor_format : str, optional
            Format string for minor tick labels. If None and format is specified, uses format.
            Default is None.
        labels : str, optional
            Which tick labels to show: "major", "minor", "both", or None.
            Default is "major".
        **kwargs
            Additional keyword arguments to pass to the tick locators.
        """
        from .ticks import set_yticks

        set_yticks(
            self.ax,
            frequency=frequency,
            minor_frequency=minor_frequency,
            format=format,
            minor_format=minor_format,
            labels=labels,
            **kwargs,
        )

    def set_major_xticks(
        self,
        frequency=None,
        format=None,
        highlight=None,
        highlight_color="red",
        **kwargs,
    ):
        """
        Set the major xticks of the subplot.

        Parameters
        ----------
        frequency : str, optional
            The frequency of the xticks.
        format : str, optional
            The format of the xticks. See :class:`matplotlib.dates.ConciseDateFormatter` for more details.
        highlight : dict, optional
            A dictionary of highlight conditions. See :class:`matplotlib.dates.ConciseDateFormatter` for more details.
        highlight_color : str, optional
            The color of the highlighted xticks.
        **kwargs : dict, optional
            Additional keyword arguments to pass to :class:`matplotlib.dates.DayLocator`, :class:`matplotlib.dates.MonthLocator`, :class:`matplotlib.dates.YearLocator`, or :class:`matplotlib.dates.HourLocator`.
        """
        formats = DEFAULT_FORMATS
        if frequency is None:
            locator = mdates.AutoDateLocator(maxticks=30)
        else:
            if frequency.startswith("D"):
                interval = frequency.lstrip("D") or 1
                if interval is not None:
                    interval = int(interval)
                locator = mdates.DayLocator(interval=interval, **kwargs)
            elif frequency.startswith("M"):
                interval = int(frequency.lstrip("M") or "1")
                locator = mdates.MonthLocator(interval=interval, bymonthday=15)
            elif frequency.startswith("Y"):
                locator = mdates.YearLocator()
            elif frequency.startswith("H"):
                interval = int(frequency.lstrip("H") or "1")
                locator = mdates.HourLocator(interval=interval)

        if format:
            formats = [format] * 6

        formatter = mdates.ConciseDateFormatter(
            locator, formats=formats, zero_formats=ZERO_FORMATS, show_offset=False
        )
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)

        if highlight is not None:
            dates = [mdates.num2date(i) for i in self.ax.get_xticks()]
            for i, date in enumerate(dates):
                highlight_this = False
                for key, value in highlight.items():
                    attr = getattr(date, key)
                    attr = attr if not callable(attr) else attr()
                    if isinstance(value, list):
                        if attr in value:
                            highlight_this = True
                    else:
                        if attr == value:
                            highlight_this = True
                if highlight_this:
                    self.ax.get_xticklabels()[i].set_color(highlight_color)

    def set_minor_xticks(
        self,
        frequency=None,
        format=None,
        **kwargs,
    ):
        """
        Set the minor xticks of the subplot.

        Parameters
        ----------
        frequency : str, optional
            The frequency of the xticks.
        format : str, optional
            The format of the xticks. See :class:`matplotlib.dates.ConciseDateFormatter` for more details.
        **kwargs : dict, optional
            Additional keyword arguments to pass to :class:`matplotlib.dates.DayLocator`, :class:`matplotlib.dates.MonthLocator`, :class:`matplotlib.dates.YearLocator`, or :class:`matplotlib.dates.HourLocator`.
        """
        formats = DEFAULT_FORMATS
        if frequency is None:
            locator = mdates.AutoDateLocator(maxticks=30)
        else:
            if frequency.startswith("D"):
                interval = frequency.lstrip("D") or 1
                if interval is not None:
                    interval = int(interval)
                locator = mdates.DayLocator(interval=interval, **kwargs)
            elif frequency.startswith("M"):
                interval = int(frequency.lstrip("M") or "1")
                locator = mdates.MonthLocator(interval=interval, bymonthday=15)
            elif frequency.startswith("Y"):
                locator = mdates.YearLocator()
            elif frequency.startswith("H"):
                interval = int(frequency.lstrip("H") or "1")
                locator = mdates.HourLocator(interval=interval)

        if format:
            formats = [format] * 6

        formatter = mdates.ConciseDateFormatter(
            locator, formats=formats, zero_formats=ZERO_FORMATS, show_offset=False
        )
        self.ax.xaxis.set_minor_locator(locator)
        self.ax.xaxis.set_minor_formatter(formatter)

    def _configure_style(self, method_name, style, source, units, auto_style, kwargs):
        """
        Configures style based on method name, style, source, and units.

        If a style is provided along with additional style kwargs, the kwargs will
        override the corresponding attributes without modifying the original style.
        """
        # Handle style="auto" as an alternative to auto_style=True
        if style == "auto":
            auto_style = True
            style = None

        # Handle cmap as an alias for colors
        if "cmap" in kwargs and "colors" in kwargs:
            raise ValueError(
                "Cannot specify both 'cmap' and 'colors'. They are aliases for the same parameter."
            )
        if "cmap" in kwargs:
            kwargs["colors"] = kwargs.pop("cmap")

        # Extract style-specific keyword arguments
        style_kwargs = {k: kwargs.pop(k) for k in _STYLE_KWARGS if k in kwargs}

        # If a style is provided and we have style kwargs to override
        if style and style_kwargs:
            # Create a copy with overrides without modifying the original
            return style.with_overrides(**style_kwargs)

        # If a style is provided without overrides, return it as-is
        if style:
            return style

        # Create a new style
        style_class = get_style_class(method_name)
        if not auto_style:
            style = style_class(**{**style_kwargs, "units": units})
        else:
            style = auto.guess_style(source, units=units or source.units)
            # Apply any style kwargs as overrides to the auto-detected style
            if style_kwargs and style is not None:
                style = style.with_overrides(**style_kwargs)
        return style

    @property
    def figure(self):
        """The :class:`earthkit.plots.components.figures.Figure` object."""
        from earthkit.plots.components.figures import Figure

        if self._figure is None:
            self._figure = Figure(1, 1, size=self._size)
            self._figure.subplots = [self]
        return self._figure

    @property
    def fig(self):
        """The underlying :class:`matplotlib.figure.Figure` object."""
        return self.figure.fig

    @property
    def ax(self):
        """The underlying :class:`matplotlib.axes.Axes` object."""
        if self._ax is None:
            subspec = self.figure.gridspec[self.row, self.column]
            self._ax = self.figure.fig.add_subplot(subspec, **self._ax_kwargs)
        return self._ax

    def ylabel(self, label=None, **kwargs):
        """
        Add a y-axis label to the plot.
        """
        if label is None:
            # Check if units metadata exists
            units = self.layers[0].sources[0].y.units
            if units is not None:
                label = "{variable_name} ({units})"
            else:
                label = "{variable_name}"
        label = self.format_string(label, axis="y")
        return self.ax.set_ylabel(label, **kwargs)

    def xlabel(self, label=None, **kwargs):
        """
        Add an x-axis label to the plot.
        """
        if label is None:
            # Check if units metadata exists
            units = self.layers[0].sources[0].x.units
            if units is not None:
                label = "{variable_name} ({units})"
            else:
                label = "{variable_name}"
        label = self.format_string(label, axis="x")
        return self.ax.set_xlabel(label, **kwargs)

    @property
    def _default_title_template(self):
        """The default title template for the Subplot."""
        templates = [layer._default_title_template for layer in self.layers]
        if len(set(templates)) == 1:
            template = templates[0]
        else:
            title_parts = []
            for i, template in enumerate(templates):
                import string

                keys = [k for _, k, _, _ in string.Formatter().parse(template)]
                for key in set(keys):
                    template = template.replace("{" + key, "{" + key + f"!{i}")
                title_parts.append(template)
            template = string_utils.list_to_human(title_parts)
        return template

    @property
    def distinct_legend_layers(self):
        """Layers on this subplot which have a unique `Style`."""
        unique_layers = []
        for layer in self.layers:
            for legend_layer in unique_layers:
                if legend_layer.style == layer.style:
                    break
            else:
                unique_layers.append(layer)
        return unique_layers

    def _plot_kwargs(self, *args, **kwargs):
        return kwargs

    def coastlines(self, *args, **kwargs):
        """
        Plot coastlines on the Subplot.

        NOTE: This method is not implemented on Subplots, but may be available
        on subclasses such as :class:`earthkit.plots.components.maps.Map`.
        """
        raise NotImplementedError

    def gridlines(self, *args, **kwargs):
        """
        Plot gridlines on the Subplot.

        NOTE: This method is not implemented on Subplots, but may be available
        on subclasses such as :class:`earthkit.plots.components.maps.Map`.
        """
        raise NotImplementedError

    @plot_1D()
    def quantiles(self, *args, **kwargs):
        pass

    def multiboxplot(
        self,
        data,
        x="auto",
        dim=None,
        quantiles="auto",
        color=None,
        units=None,
        x_units=None,
        y_units=None,
        label=None,
        boxprops=None,
        whiskerprops=None,
        medianprops=None,
        capprops=None,
        showcaps=False,
        **kwargs,
    ):
        """
        Plot a multiboxplot (letter-value plot) from multi-dimensional data.

        Visualises quantiles as stacked boxes with varying widths — innermost
        quantile pair is widest and darkest; the outermost pair (min/max) is
        rendered as a whisker line.  Useful for ensemble spread, uncertainty
        bands, or any distribution that varies along a second axis.

        Parameters
        ----------
        data : xarray.DataArray
            The data to plot.  Must have at least two dimensions after
            squeezing: one for the quantile/ensemble dimension and one for
            the x-axis.
        x : str, optional
            Dimension name to use as x-axis.  Default ``"auto"`` uses the
            remaining dimension after the quantile dimension is removed.
        dim : str, optional
            Dimension along which to compute quantiles (e.g. ``'number'``
            for ensemble members).  If ``None``, the left-most dimension is
            used.  When *quantiles* is ``None`` (pre-computed), this names
            the dimension that already holds quantile values.
        quantiles : list of float, "auto", or None, optional
            * ``"auto"`` (default) – compute ``[0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]``.
            * list of float – compute the specified quantiles (0–1).
            * ``None`` – treat *dim* as pre-computed quantile values.
        color : str or tuple, optional
            Fill colour for the innermost (darkest) box.  Defaults to the
            next colour in matplotlib's colour cycle.
        units : str, optional
            Target units for y-axis values.
        x_units : str, optional
            Target units for x-axis values.
        y_units : str, optional
            Target units for y-axis values (overrides *units*).
        label : str, optional
            Legend label.  Supports metadata format placeholders such as
            ``"{variable_name}"``.
        boxprops : dict, optional
            Properties for box rectangles (``edgecolor``, ``linewidth``,
            ``linestyle``).
        whiskerprops : dict, optional
            Properties for the min/max whisker line (``color``, ``linewidth``,
            ``linestyle``).
        medianprops : dict, optional
            Properties for the median line (``color``, ``linewidth``,
            ``linestyle``, ``alpha``).
        capprops : dict, optional
            Properties for whisker cap lines.  Only drawn when
            ``showcaps=True``.  Extra key ``capwidth`` (default ``1.0``)
            controls width as a fraction of the box width.
        showcaps : bool, optional
            Whether to draw horizontal cap lines at whisker ends.
            Default ``False``.
        **kwargs
            Extra keyword arguments are ignored (for forward-compat).

        Returns
        -------
        list
            List of matplotlib artists drawn for this layer.
        """
        import xarray as xr
        from matplotlib.colors import to_rgb
        from matplotlib.patches import Rectangle

        # ------------------------------------------------------------------ #
        # 1. Normalise input                                                  #
        # ------------------------------------------------------------------ #
        if isinstance(data, xr.Dataset):
            data_vars = [v for v in data.data_vars if data[v].ndim > 0]
            if len(data_vars) != 1:
                raise ValueError(
                    "Dataset must have exactly one non-scalar variable; "
                    f"got {data_vars}"
                )
            data = data[data_vars[0]]

        data = data.squeeze()

        # ------------------------------------------------------------------ #
        # 2. Resolve target units (y_units > units)                           #
        # ------------------------------------------------------------------ #
        if self._fixed_y_units is not None and units is None and y_units is None:
            units = self._fixed_y_units
        if self._fixed_x_units is not None and x_units is None:
            x_units = self._fixed_x_units
        target_yunits = y_units or units

        # ------------------------------------------------------------------ #
        # 3. Compute / validate quantiles                                     #
        # ------------------------------------------------------------------ #
        if quantiles is None:
            # Pre-computed: dim must name the quantile dimension
            if dim is None:
                raise ValueError(
                    "When quantiles=None (pre-computed), 'dim' must name the "
                    "dimension that holds the quantile values."
                )
            if dim not in data.dims:
                raise ValueError(
                    f"Dimension '{dim}' not found; available: {list(data.dims)}"
                )
            quantile_data = data
            quantile_dim = dim
            if dim in data.coords:
                q_list = sorted(data.coords[dim].values.tolist())
            else:
                q_list = list(range(data.sizes[dim]))
        else:
            if quantiles == "auto":
                quantiles = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]
            quantiles = sorted(quantiles)
            if not all(0.0 <= q <= 1.0 for q in quantiles):
                raise ValueError("All quantiles must be between 0 and 1.")
            if len(data.dims) < 2:
                raise ValueError(
                    "Data must have at least 2 dimensions for multiboxplot "
                    f"(got {list(data.dims)})."
                )
            if dim is None:
                dim = data.dims[0]
            elif dim not in data.dims:
                raise ValueError(
                    f"Dimension '{dim}' not found; available: {list(data.dims)}"
                )
            # Unit-convert the raw data before computing quantiles so the
            # box positions are in the target units.
            if target_yunits is not None:
                data_slice = data.isel({dim: 0})
                src_original = get_source(
                    data_slice,
                    context=PlotContext.CARTESIAN_1D,
                )
                src_converted = get_source(
                    data_slice,
                    context=PlotContext.CARTESIAN_1D,
                    units=target_yunits,
                )
                original = src_original.y.values
                converted = src_converted.y.values
                if not np.array_equal(original, converted) and len(original) > 1:
                    scale = (converted[1] - converted[0]) / (original[1] - original[0])
                    offset = converted[0] - scale * original[0]
                    attrs = data.attrs.copy()
                    coord_attrs = {c: data.coords[c].attrs.copy() for c in data.coords}
                    data = xr.DataArray(
                        data.values * scale + offset,
                        dims=data.dims,
                        coords=data.coords,
                        attrs=attrs,
                    )
                    for c, a in coord_attrs.items():
                        if c in data.coords:
                            data.coords[c].attrs.update(a)

            attrs_backup = data.attrs.copy()
            coord_attrs_backup = {c: data.coords[c].attrs.copy() for c in data.coords}
            quantile_data = data.quantile(quantiles, dim=dim)
            quantile_dim = "quantile"
            q_list = quantiles
            quantile_data.attrs.update(attrs_backup)
            for c, a in coord_attrs_backup.items():
                if c in quantile_data.coords:
                    quantile_data.coords[c].attrs.update(a)

        # ------------------------------------------------------------------ #
        # 4. Determine x dimension and values                                 #
        # ------------------------------------------------------------------ #
        remaining = [d for d in quantile_data.dims if d != quantile_dim]
        if len(remaining) != 1:
            raise ValueError(
                f"After quantile processing, expected 1 remaining dim, got {remaining}."
            )
        x_dim = remaining[0]
        x_values = quantile_data[x_dim].values
        q_values = quantile_data.values  # shape: (n_quantiles, n_x)

        # ------------------------------------------------------------------ #
        # 5. Pair quantiles symmetrically                                     #
        # ------------------------------------------------------------------ #
        n_q = len(q_list)
        pairs = [(i, n_q - 1 - i) for i in range(n_q // 2)]
        median_idx = n_q // 2 if n_q % 2 == 1 else None

        # ------------------------------------------------------------------ #
        # 6. Resolve styling                                                  #
        # ------------------------------------------------------------------ #
        boxprops = boxprops or {}
        box_edgecolor = boxprops.get("edgecolor", "black")
        box_linewidth = boxprops.get("linewidth", 1.0)
        box_linestyle = boxprops.get("linestyle", "solid")

        if color is None:
            color = self.ax._get_lines.get_next_color()
        plot_color = color

        whiskerprops = whiskerprops or {}
        whisker_color = whiskerprops.get("color", box_edgecolor)
        whisker_linewidth = whiskerprops.get("linewidth", box_linewidth)
        whisker_linestyle = whiskerprops.get("linestyle", "solid")

        medianprops = medianprops or {}
        median_color = medianprops.get("color", _darken_color(plot_color, 0.25))
        median_linewidth = medianprops.get("linewidth", 1.5)
        median_linestyle = medianprops.get("linestyle", "solid")
        median_alpha = medianprops.get("alpha", 1.0)

        if showcaps:
            capprops = capprops or {}
            cap_color = capprops.get("color", whisker_color)
            cap_linewidth = capprops.get("linewidth", whisker_linewidth)
            cap_linestyle = capprops.get("linestyle", "solid")
            cap_width_factor = capprops.get("capwidth", 1.0)

        # ------------------------------------------------------------------ #
        # 7. Compute box widths from x spacing                               #
        # ------------------------------------------------------------------ #
        is_datetime = np.issubdtype(x_values.dtype, np.datetime64)
        if len(x_values) > 1:
            if is_datetime:
                from matplotlib.dates import date2num

                x_num = date2num(x_values)
                x_spacing = float(np.min(np.diff(x_num)))
            else:
                x_spacing = float(np.min(np.diff(x_values.astype(float))))
        else:
            x_spacing = 1.0
        base_width = 0.6 * x_spacing

        # ------------------------------------------------------------------ #
        # 8. Draw boxes                                                       #
        # ------------------------------------------------------------------ #
        mappables = []

        # Register the x-axis as a date axis before drawing any patches or
        # lines with numeric (date2num) coordinates.  Without this, matplotlib
        # never installs the date converter and the x-axis shows raw floats.
        if is_datetime:
            self.ax.plot([], [], visible=False)
            self.ax.xaxis.update_units(x_values)

        def _x_pos_num(x_val):
            if is_datetime:
                from matplotlib.dates import date2num

                return date2num(x_val)
            return float(x_val)

        for x_idx, x_val in enumerate(x_values):
            xp = _x_pos_num(x_val)

            for pair_idx, (lo_i, hi_i) in enumerate(pairs):
                width_factor = (pair_idx + 1) / len(pairs)
                box_width = base_width * width_factor
                y_lo = float(q_values[lo_i, x_idx])
                y_hi = float(q_values[hi_i, x_idx])

                if pair_idx == 0:
                    # Outermost pair → whisker line
                    line = self.ax.plot(
                        [xp, xp],
                        [y_lo, y_hi],
                        color=whisker_color,
                        linewidth=whisker_linewidth,
                        linestyle=whisker_linestyle,
                        zorder=3,
                    )
                    if x_idx == 0:
                        mappables.extend(line)

                    if showcaps:
                        hw = base_width * cap_width_factor / 2
                        for y_cap in (y_lo, y_hi):
                            self.ax.plot(
                                [xp - hw, xp + hw],
                                [y_cap, y_cap],
                                color=cap_color,
                                linewidth=cap_linewidth,
                                linestyle=cap_linestyle,
                                zorder=3,
                            )
                else:
                    # Inner pair → box
                    norm_i = (pair_idx - 1) / max(1, len(pairs) - 2)
                    lightness = 0.4 * (1.0 - norm_i)
                    rgb = to_rgb(plot_color)
                    box_color = tuple(c * (1 - lightness) + lightness for c in rgb)

                    rect = Rectangle(
                        (xp - box_width / 2, y_lo),
                        box_width,
                        y_hi - y_lo,
                        facecolor=box_color,
                        edgecolor=box_edgecolor,
                        linewidth=box_linewidth,
                        linestyle=box_linestyle,
                        zorder=4,
                    )
                    self.ax.add_patch(rect)
                    if x_idx == 0 and pair_idx == 1:
                        mappables.append(rect)

            # Median line
            if median_idx is not None:
                y_med = float(q_values[median_idx, x_idx])
                mw = base_width * 0.95
                med_line = self.ax.plot(
                    [xp - mw / 2, xp + mw / 2],
                    [y_med, y_med],
                    color=median_color,
                    linewidth=median_linewidth,
                    linestyle=median_linestyle,
                    alpha=median_alpha,
                    zorder=5,
                )
                if x_idx == 0:
                    mappables.extend(med_line)

        # ------------------------------------------------------------------ #
        # 9. Axis limits                                                       #
        # ------------------------------------------------------------------ #
        if is_datetime:
            from matplotlib.dates import date2num

            x_num = date2num(x_values)
            self.ax.set_xlim(x_num[0] - base_width, x_num[-1] + base_width)
        else:
            xf = x_values.astype(float)
            self.ax.set_xlim(float(xf[0]) - base_width, float(xf[-1]) + base_width)
        self.ax.autoscale_view(scalex=False, scaley=True)

        # ------------------------------------------------------------------ #
        # 10. Create Layer using the current Source machinery                 #
        # ------------------------------------------------------------------ #
        median_or_mid = median_idx if median_idx is not None else n_q // 2
        rep_data = quantile_data.isel({quantile_dim: median_or_mid})
        source = get_source(rep_data, context=PlotContext.CARTESIAN_1D)

        axis_units = {}
        if target_yunits is not None:
            axis_units["y"] = target_yunits
        if x_units is not None:
            axis_units["x"] = x_units

        layer = Layer(
            source,
            mappables,
            self,
            style=None,
            primary_axis="y",
            axis_units=axis_units,
        )

        if label is not None:
            from earthkit.plots.metadata.formatters import LayerFormatter

            formatted_label = LayerFormatter(layer).format(label)
            if mappables:
                mappables[0].set_label(formatted_label)

        # Store metadata on the layer so multiboxplot_legend() can read it.
        layer._layer_type = "multiboxplot"
        layer._multiboxplot_quantiles = q_list
        layer._multiboxplot_color = plot_color
        layer._multiboxplot_styling = {
            "whisker_color": whisker_color,
            "whisker_linewidth": whisker_linewidth,
            "box_edgecolor": box_edgecolor,
            "box_linewidth": box_linewidth,
            "median_color": median_color,
            "median_linewidth": median_linewidth,
        }

        self.layers.append(layer)
        return mappables

    def multiboxplot_legend(
        self,
        location="right",
        fontsize=8,
        color=None,
        boxprops=None,
        whiskerprops=None,
        medianprops=None,
        **kwargs,
    ):
        """
        Add a visual legend for the most recent multiboxplot.

        Creates a miniature replica of the quantile box structure with labelled
        percentiles, placed outside the plot area using
        :func:`mpl_toolkits.axes_grid1.make_axes_locatable` (the same
        mechanism as a colorbar).  The legend is always rendered as a small
        square regardless of which side it is placed on.

        Call this **after** :meth:`multiboxplot`.

        Parameters
        ----------
        location : str, optional
            Side of the axes on which to place the legend.
            One of ``'right'`` (default), ``'left'``, ``'top'``, ``'bottom'``.
        fontsize : int, optional
            Font size for the quantile labels.  Default ``8``.
        color : str or tuple, optional
            Override the fill colour.  Defaults to the colour used by the
            most recent :meth:`multiboxplot` call.
        boxprops : dict, optional
            Override box-edge properties (``edgecolor``, ``linewidth``).
        whiskerprops : dict, optional
            Override whisker-line properties (``color``, ``linewidth``).
        medianprops : dict, optional
            Override median-line properties (``color``, ``linewidth``).
        size : float, optional
            Width/height of the legend square in inches.  Default ``0.75``.
        pad : float, optional
            Gap between the main axes and the legend in inches.  Default ``0.1``.

        Returns
        -------
        matplotlib.axes.Axes
            The axes containing the legend.

        Raises
        ------
        ValueError
            If no :meth:`multiboxplot` has been drawn yet, or *location* is
            invalid.
        """
        from matplotlib.colors import to_rgb
        from matplotlib.patches import Rectangle
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        # ------------------------------------------------------------------ #
        # 1. Retrieve metadata from the most recent multiboxplot layer        #
        # ------------------------------------------------------------------ #
        mbp_layers = [
            layer
            for layer in self.layers
            if getattr(layer, "_layer_type", None) == "multiboxplot"
        ]
        if not mbp_layers:
            raise ValueError(
                "No multiboxplot has been drawn yet. "
                "Call multiboxplot() before multiboxplot_legend()."
            )
        last = mbp_layers[-1]
        quantiles = [float(q) for q in last._multiboxplot_quantiles]
        stored_color = last._multiboxplot_color
        stored_styling = last._multiboxplot_styling

        # ------------------------------------------------------------------ #
        # 2. Resolve colours / styling                                        #
        # ------------------------------------------------------------------ #
        base_color = color if color is not None else stored_color
        rgb = to_rgb(base_color)

        whiskerprops = whiskerprops or {}
        whisker_color = whiskerprops.get(
            "color", stored_styling.get("whisker_color", (0.3, 0.3, 0.3))
        )
        whisker_linewidth = whiskerprops.get(
            "linewidth", stored_styling.get("whisker_linewidth", 0.8)
        )

        boxprops = boxprops or {}
        box_edgecolor = boxprops.get(
            "edgecolor", stored_styling.get("box_edgecolor", base_color)
        )
        box_linewidth = boxprops.get(
            "linewidth", stored_styling.get("box_linewidth", 0.5)
        )

        medianprops = medianprops or {}
        median_color = medianprops.get(
            "color",
            stored_styling.get("median_color", tuple(c * 0.6 for c in rgb)),
        )
        median_linewidth = medianprops.get(
            "linewidth", stored_styling.get("median_linewidth", 1.5)
        )

        # ------------------------------------------------------------------ #
        # 3. Validate location and create legend axes                         #
        # ------------------------------------------------------------------ #
        valid_locations = ("right", "left", "top", "bottom")
        if location not in valid_locations:
            raise ValueError(
                f"Invalid location {location!r}. " f"Choose from: {valid_locations}"
            )

        size = kwargs.pop("size", 0.75)
        pad = kwargs.pop("pad", 0.1)

        divider = make_axes_locatable(self.ax)
        legend_ax = divider.append_axes(location, size=size, pad=pad)
        legend_ax.set_aspect("equal", adjustable="box")

        # ------------------------------------------------------------------ #
        # 4. Draw the miniature box structure                                 #
        # ------------------------------------------------------------------ #
        n_q = len(quantiles)
        pairs = [(i, n_q - 1 - i) for i in range(n_q // 2)]
        median_idx = n_q // 2 if n_q % 2 == 1 else None

        x_center = 0.25
        base_width = 0.15

        for pair_idx, (lo_i, hi_i) in enumerate(pairs):
            width_factor = (pair_idx + 1) / len(pairs)
            box_width = base_width * width_factor
            y_lo, y_hi = quantiles[lo_i], quantiles[hi_i]

            if pair_idx == 0:
                legend_ax.plot(
                    [x_center, x_center],
                    [y_lo, y_hi],
                    color=whisker_color,
                    linewidth=whisker_linewidth,
                    zorder=1,
                )
            else:
                norm_i = (pair_idx - 1) / max(1, len(pairs) - 2)
                lightness = 0.4 * (1.0 - norm_i)
                box_color = tuple(c * (1 - lightness) + lightness for c in rgb)
                legend_ax.add_patch(
                    Rectangle(
                        (x_center - box_width / 2, y_lo),
                        box_width,
                        y_hi - y_lo,
                        facecolor=box_color,
                        edgecolor=box_edgecolor,
                        linewidth=box_linewidth,
                        zorder=2,
                    )
                )

        if median_idx is not None:
            mw = base_width * 0.95
            legend_ax.plot(
                [x_center - mw / 2, x_center + mw / 2],
                [quantiles[median_idx], quantiles[median_idx]],
                color=median_color,
                linewidth=median_linewidth,
                zorder=10,
            )

        # ------------------------------------------------------------------ #
        # 5. Add quantile labels                                              #
        # ------------------------------------------------------------------ #
        for q in quantiles:
            if q == 0:
                label_text = "min"
            elif q == 1:
                label_text = "max"
            elif q == 0.5:
                label_text = "median"
            else:
                label_text = f"{int(round(q * 100))}%"
            legend_ax.text(
                0.4,
                q,
                label_text,
                ha="left",
                va="center",
                fontsize=fontsize - 1,
            )

        # ------------------------------------------------------------------ #
        # 6. Clean up axes                                                    #
        # ------------------------------------------------------------------ #
        legend_ax.set_xlim(0, 1)
        legend_ax.set_ylim(-0.05, 1.05)
        legend_ax.set_xticks([])
        legend_ax.set_yticks([])
        for spine in legend_ax.spines.values():
            spine.set_visible(False)

        return legend_ax

    @plot_1D()
    def line(self, *args, **kwargs):
        """
        Plot a line on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x and y must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the line. If None, a Style is automatically
            generated based on the data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.plot`.
        """

    @schema.envelope.apply()
    def envelope(self, data_1, data_2=0, alpha=0.4, units=None, **kwargs):
        """
        Plot an envelope on the Subplot.

        Parameters
        ----------
        data_1 : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot the envelope.
        data_2 : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot the envelope.
        alpha : float, optional
            The alpha value of the envelope.
        units : str, optional
            Units for the data values.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.fill_between`.
        """
        x = kwargs.pop("x", None)
        drawstyle = kwargs.pop("drawstyle", None)
        if units is None and self._fixed_y_units is not None:
            units = self._fixed_y_units
        source_1 = get_source(
            data_1, x=x, context=PlotContext.CARTESIAN_1D, units=units
        )
        x_values, y1_values = _apply_coordinate_unit_conversion(source_1)

        # ax.fill_between cannot handle datetime x-values (unlike ax.plot
        # which runs unit conversion automatically).  Force conversion here.
        import datetime

        import matplotlib.dates as mdates

        x_arr = np.asarray(x_values)
        if np.issubdtype(x_arr.dtype, np.datetime64):
            py_dates = x_arr.astype("datetime64[ms]").astype("O")
        elif (
            x_arr.dtype == object
            and len(x_arr) > 0
            and isinstance(
                x_arr.flat[0], (datetime.datetime, datetime.date, np.datetime64)
            )
        ):
            py_dates = x_arr
        else:
            py_dates = None

        if py_dates is not None:
            # Register as a date axis so tick formatters work correctly.
            self.ax.plot([], [], visible=False)
            self.ax.xaxis.update_units(py_dates)
            x_values = mdates.date2num(py_dates)

        if isinstance(data_2, (int, float)):
            y2_values = np.full_like(y1_values, fill_value=data_2, dtype=float)
        else:
            source_2 = get_source(
                data_2, x=x, context=PlotContext.CARTESIAN_1D, units=units
            )
            _, y2_values = _apply_coordinate_unit_conversion(source_2)

        if drawstyle == "spline":
            from earthkit.plots.styles import spline_interpolate

            x_smooth, y1_smooth, y2_smooth = spline_interpolate(
                np.asarray(x_values), y1_values, y2_values
            )
            mappable = self.ax.fill_between(
                x=x_smooth, y1=y1_smooth, y2=y2_smooth, alpha=alpha, **kwargs
            )
        else:
            mappable = self.ax.fill_between(
                x=x_values, y1=y1_values, y2=y2_values, alpha=alpha, **kwargs
            )
        axis_units = {"y": units} if units is not None else {}
        self.layers.append(
            Layer(
                source_1,
                mappable,
                self,
                style=None,
                primary_axis="y",
                axis_units=axis_units,
            )
        )
        return mappable

    def fill_between(self, y1, y2=0, x=None, alpha=0.2, units=None, **kwargs):
        """
        Fill the area between two curves.

        Parameters
        ----------
        y1 : xarray.DataArray or array-like
            The lower (or upper) bound of the filled region.
        y2 : xarray.DataArray, array-like, or scalar, optional
            The upper (or lower) bound.  Defaults to ``0``, which shades
            from *y1* down to zero.
        x : str or array-like, optional
            The x-axis coordinate name or values.  If not provided, earthkit-plots
            will attempt to infer it automatically from *y1*.
        alpha : float, optional
            Opacity of the filled region.  Default is ``0.2``.
        units : str, optional
            Target units for value conversion (e.g. ``"celsius"``).
        **kwargs
            Additional keyword arguments forwarded to
            :func:`matplotlib.pyplot.fill_between` (e.g. ``color``,
            ``zorder``, ``label``).

        Examples
        --------
        Shade between two pre-computed bounds:

        >>> ts.fill_between(mean - std, mean + std, units="celsius")

        With an explicit x coordinate:

        >>> ts.fill_between(p10, p90, x="valid_time", color="#1f78b4")

        Shade from a curve down to zero:

        >>> ts.fill_between(values)
        """
        self.envelope(y1, y2, x=x, units=units, alpha=alpha, **kwargs)

    def text(self, x, y=None, s="", **kwargs):
        """
        Add text to the Subplot at position (*x*, *y*).

        Can be called in two ways:

        - ``text(x, y, s)`` — explicit coordinates and string.
        - ``text(data, s=...)`` — pass an xarray DataArray; *x* and *y* are
          extracted from the data's coordinates and values respectively.

        Parameters
        ----------
        x : float, datetime-like, or xarray.DataArray
            The x position in data coordinates, or a DataArray from which
            both *x* and *y* are extracted.
        y : float, optional
            The y position in data coordinates. Required when *x* is not a
            DataArray.
        s : str, optional
            The text string.
        **kwargs
            Additional keyword arguments passed to
            :func:`matplotlib.axes.Axes.text`.
        """
        import xarray as xr

        if isinstance(x, xr.DataArray):
            source = get_source(x, context=PlotContext.CARTESIAN_1D)
            x_val, y_val = _apply_coordinate_unit_conversion(source)
            # x_val/y_val are arrays; take the first (and typically only) element
            x_val = x_val.flat[0]
            y_val = y_val.flat[0]
            if y is not None:
                # called as text(da, "hello") — y holds the string
                s = y
            s = SourceFormatter(source).format(s)
            self.ax.text(x_val, y_val, s, **kwargs)
        else:
            s = self.format_string(s)
            self.ax.text(x, y, s, **kwargs)

    def annotate(self, s, xy, xytext=None, **kwargs):
        """
        Add an annotation to the Subplot.

        Can be called in two ways:

        - ``annotate(s, (x, y))`` — explicit coordinates.
        - ``annotate(s, data)`` — pass an xarray DataArray; *xy* is extracted
          from the data's coordinates and values respectively.

        Parameters
        ----------
        s : str
            The annotation text. Supports format strings (e.g. ``"{time:%Y}"``).
        xy : tuple or xarray.DataArray
            The point to annotate. Either an ``(x, y)`` tuple in data
            coordinates, or a DataArray from which both are extracted.
        xytext : tuple, optional
            The position of the text. If not given, the text is placed at *xy*.
            Can be an offset in points when used with
            ``textcoords="offset points"``.
        **kwargs
            Additional keyword arguments passed to
            :func:`matplotlib.axes.Axes.annotate`.
        """
        import xarray as xr

        if isinstance(xy, xr.DataArray):
            source = get_source(xy, context=PlotContext.CARTESIAN_1D)
            x_val, y_val = _apply_coordinate_unit_conversion(source)
            x_val = x_val.flat[0]
            y_val = y_val.flat[0]
            s = SourceFormatter(source).format(s)
            xy = (x_val, y_val)
        else:
            s = self.format_string(s)

        if xytext is not None:
            self.ax.annotate(s, xy=xy, xytext=xytext, **kwargs)
        else:
            self.ax.annotate(s, xy=xy, **kwargs)

    def labels(self, data=None, label=None, x=None, y=None, **kwargs):
        """
        Plot labels on the Subplot.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot the labels.
        label : str, optional
            The label to plot.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.annotate`.
        """
        source = get_source(data=data, x=x, y=y)
        labels = SourceFormatter(source).format(label)
        for label, x, y in zip(labels, source.x.values, source.y.values):
            self.ax.annotate(label, (x, y), **kwargs)

    def plot(self, data, style=None, units=None, **kwargs):
        """
        Plot a line on the Subplot.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot the data.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the data.
        units : str, optional
            The units to use for the data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.plot`.
        """
        warnings.warn("`plot` is deprecated. Use `quickplot` instead.")
        if not kwargs.pop("auto_style", True):
            warnings.warn("`auto_style` cannot be switched off for `plot`.")
        source = get_source(data)
        if style is None:
            auto_style = auto.guess_style(source, units=units, **kwargs)
            if auto_style is not None:
                method = getattr(self, auto_style._preferred_method)
            else:
                method = getattr(self, "grid_cells", self.pcolormesh)
        else:
            method = getattr(self, style._preferred_method)
        return method(data, style=style, units=units, auto_style=True, **kwargs)

    def quickplot(self, data, style="auto", units=None, **kwargs):
        """
        Generate a convenient plot from the given data with optional grouping.

        Parameters
        ----------
        *args : list
            The data to be plotted. Can be a single xarray or earthkit data object,
            or separate x, y, z, u, v arguments.
        methods : string or list, optional
            The plot method(s) to apply.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the data.
        units : string or list, optional
            Units to convert the data to.
        **kwargs : dict
            Additional arguments for the plot method(s).
        """
        import earthkit.data
        import xarray as xr
        from earthkit.data.core import Base

        if not kwargs.pop("auto_style", True):
            warnings.warn("`auto_style` cannot be switched off for `quickplot`.")
        if not isinstance(data, (Base, xr.DataArray, xr.Dataset)):
            data = earthkit.data.from_object(data)
        source = get_source(data)
        if style == "auto":
            resolved_style = auto.guess_style(source, units=units, **kwargs)
            if resolved_style is not None:
                method = getattr(self, resolved_style._preferred_method)
            else:
                method = getattr(self, "grid_cells", self.pcolormesh)
            use_auto_style = True
        elif style is None:
            resolved_style = None
            method = getattr(self, "grid_cells", self.pcolormesh)
            use_auto_style = False
        else:
            if isinstance(style, str):
                from earthkit.plots.styles import auto as _auto

                resolved_style = _auto.load_style(style)
            else:
                resolved_style = style
            method = getattr(self, resolved_style._preferred_method)
            use_auto_style = False
        zorder = LAYER_ZORDERS.get(method.__name__, 10)
        kwargs.setdefault("zorder", zorder)
        return method(
            data, style=resolved_style, units=units, auto_style=use_auto_style, **kwargs
        )

    def hsv_composite(self, *args):
        """
        Plot an HSV composite on the Subplot.

        Parameters
        ----------
        *args : xarray.DataArray or earthkit.data.core.Base
            The data sources for the H, S, and V channels. If a single argument
            is provided, it is assumed to be a tuple of (H, S, V).
        """
        import xarray as xr

        if len(args) == 1:
            red, green, blue = args[0]
        else:
            red, green, blue = args

        red_source = get_source(red)
        green_source = get_source(green)
        blue_source = get_source(blue)

        if red_source.z is None or green_source.z is None or blue_source.z is None:
            raise ValueError("RGB plots require z values for all three channels")

        x_values = red_source.x.values
        y_values = red_source.y.values

        red = (red_source.z.values - red_source.z.values.min()) / (
            red_source.z.values.max() - red_source.z.values.min()
        )
        green = (green_source.z.values - green_source.z.values.min()) / (
            green_source.z.values.max() - green_source.z.values.min()
        )
        blue = (blue_source.z.values - blue_source.z.values.min()) / (
            blue_source.z.values.max() - blue_source.z.values.min()
        )

        rgb = np.stack((red, green, blue), axis=-1)

        if x_values.ndim == 2:
            x_values = x_values[0, :]  # Extract unique x-coordinates
        if y_values.ndim == 2:
            y_values = y_values[:, 0]  # Extract unique y-coordinates

        # Turn RGB into an xarray
        rgb = xr.DataArray(
            rgb,
            coords={
                "y": y_values,
                "x": x_values,
                "rgb": ["red", "green", "blue"],
            },  # Ensure 1D  # Ensure 1D
            dims=["y", "x", "rgb"],
        )

        result = self.pcolormesh(c=rgb, x=x_values, y=y_values, no_style=True)

        self.layers[-1].sources = [red_source, green_source, blue_source]
        self.layers[-1].style = None

        return result

    def rgb_composite(self, *args):
        """
        Plot an RGB composite on the Subplot.

        Parameters
        ----------
        *args : xarray.DataArray or earthkit.data.core.Base
            The data sources for the R, G, and B channels. If a single argument
            is provided, it is assumed to be a tuple of (R, G, B).
        """
        import xarray as xr

        if len(args) == 1:
            red, green, blue = args[0]
        else:
            red, green, blue = args

        red_source = get_source(red)
        green_source = get_source(green)
        blue_source = get_source(blue)

        if red_source.z is None or green_source.z is None or blue_source.z is None:
            raise ValueError("RGB plots require z values for all three channels")

        x_values = red_source.x.values
        y_values = red_source.y.values

        red = (red_source.z.values - red_source.z.values.min()) / (
            red_source.z.values.max() - red_source.z.values.min()
        )
        green = (green_source.z.values - green_source.z.values.min()) / (
            green_source.z.values.max() - green_source.z.values.min()
        )
        blue = (blue_source.z.values - blue_source.z.values.min()) / (
            blue_source.z.values.max() - blue_source.z.values.min()
        )

        rgb = np.stack((red, green, blue), axis=-1)

        if x_values.ndim == 2:
            x_values = x_values[0, :]  # Extract unique x-coordinates
        if y_values.ndim == 2:
            y_values = y_values[:, 0]  # Extract unique y-coordinates

        # Turn RGB into an xarray
        rgb = xr.DataArray(
            rgb,
            coords={
                "y": y_values,
                "x": x_values,
                "rgb": ["red", "green", "blue"],
            },  # Ensure 1D  # Ensure 1D
            dims=["y", "x", "rgb"],
        )

        result = self.pcolormesh(rgb, x=x_values, y=y_values, no_style=True)

        self.layers[-1].sources = [red_source, green_source, blue_source]
        self.layers[-1].style = None

        return result

    @plot_1D()
    def bar(self, *args, **kwargs):
        """
        Plot a bar chart on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x and y must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the bar chart. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.

        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.bar`.
        """

    @schema.scatter.apply()
    @plot_1D()
    def scatter(self, *args, **kwargs):
        """
        Plot a scatter plot on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x and y must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the scatter plot. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.scatter`.
        """

    @plot_1D()
    def stripes(self, *args, **kwargs):
        """
        Plot a climate stripes visualisation on the Subplot.

        Draws one vertical bar per data point, colored according to the data
        value mapped through the given (or auto-detected) style.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            The data to plot.
        x : str or array-like, optional
            The x (time) coordinate. If *data* is a DataArray this is inferred
            automatically.
        y : str or array-like, optional
            The values used to color the stripes. Defaults to the primary
            data variable.
        style : earthkit.plots.styles.Style or str, optional
            Style object or named style string. If ``None`` an auto-style is
            chosen from the data metadata.
        units : str, optional
            Convert the data to these units before coloring.
        ymin : float, optional
            Bottom of the stripes in axes-fraction coordinates (default ``0``).
        ymax : float, optional
            Top of the stripes in axes-fraction coordinates (default ``1``).
        **kwargs
            Additional keyword arguments forwarded to
            :class:`matplotlib.collections.BrokenBarHCollection`.
        """

    @plot_2D(extract_domain=True, default_resample=False)
    def pcolormesh(self, *args, **kwargs):
        """
        Plot a pcolormesh on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, and z must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the pcolormesh. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        resample : earthkit.plots.resample.Resample, bool, or dict, optional
            Controls resampling of data before plotting. Pass a
            :class:`~earthkit.plots.resample.Unstructured` (or subclass) instance to
            interpolate unstructured data onto a regular grid, a dict of keyword
            arguments to construct one, or ``True`` for defaults. Default is ``False``
            for pcolormesh.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.pcolormesh`.
        """

    @schema.contour.apply()
    @plot_2D(extract_domain=True)
    def contour(self, *args, **kwargs):
        """
        Plot a contour plot on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, and z must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the contour plot. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        resample : earthkit.plots.resample.Resample, bool, or False, optional
            Controls resampling before plotting. Pass a
            :class:`~earthkit.plots.resample.Bilinear` or :class:`~earthkit.plots.resample.NearestNeighbour` instance (or ``True`` for
            defaults) to reproject onto a regular target grid, or ``False`` to
            disable. Default is ``Bilinear()`` (1000 × 1000 pixels).
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.contour`.
        """

    @schema.contourf.apply()
    @plot_2D(extract_domain=True)
    def contourf(self, *args, **kwargs):
        """
        Plot a filled contour plot on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, and z must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the filled contour plot. If None, a Style is
            automatically generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        resample : earthkit.plots.resample.Resample, bool, or False, optional
            Controls resampling before plotting. Pass a
            :class:`~earthkit.plots.resample.Bilinear` or :class:`~earthkit.plots.resample.NearestNeighbour` instance (or ``True`` for
            defaults) to reproject onto a regular target grid, or ``False`` to
            disable. Default is ``Bilinear()`` (1000 × 1000 pixels). Pass an
            :class:`~earthkit.plots.resample.Unstructured` instance to interpolate
            unstructured data onto a structured grid instead.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.contourf`.
        """

    @plot_2D()
    def tripcolor(self, *args, **kwargs):
        """
        Plot a tripcolor plot on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, and z must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the tripcolor plot. If None, a Style is
            automatically generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.tripcolor`.
        """

    @plot_2D()
    def tricontour(self, *args, **kwargs):
        """
        Plot a tricontour plot on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, and z must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the tricontour plot. If None, a Style is
            automatically generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.tricontour`.
        """

    @plot_2D()
    def tricontourf(self, *args, **kwargs):
        """
        Plot a filled tricontour plot on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, and z must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the filled tricontour plot. If None, a Style is
            automatically generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.tricontourf`.
        """

    @schema.quiver.apply()
    @plot_vector()
    def quiver(self, *args, **kwargs):
        """
        Plot arrows on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, u, and v must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        u : str, list, numpy.ndarray, or xarray.DataArray, optional
            The u values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        v : str, list, numpy.ndarray, or xarray.DataArray, optional
            The v values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the quiver plot. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.quiver`.
        """

    @plot_vector()
    def streamplot(self, *args, **kwargs):
        """
        Plot streamlines on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, u, and v must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        u : str, list, numpy.ndarray, or xarray.DataArray, optional
            The u values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        v : str, list, numpy.ndarray, or xarray.DataArray, optional
            The v values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the stream plot. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.streamplot`.
        """

    @schema.barbs.apply()
    @plot_vector()
    def barbs(self, *args, **kwargs):
        """
        Plot wind barbs on the Subplot.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, u, and v must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        u : str, list, numpy.ndarray, or xarray.DataArray, optional
            The u values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        v : str, list, numpy.ndarray, or xarray.DataArray, optional
            The v values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If None, data must be provided.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the wind barbs. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.barbs`.
        """

    def block(self, *args, **kwargs):
        """
        Plot a pcolormesh on the Subplot.

        Deprecated: Use :meth:`pcolormesh` instead.

        Parameters
        ----------
        *args : xarray.DataArray or earthkit.data.core.Base
            The data source for which to plot the block.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :meth:`pcolormesh`.
        """
        import warnings

        warnings.warn(
            "block is deprecated and will be removed in a future release. "
            "Please use pcolormesh instead."
        )
        return self.pcolormesh(*args, **kwargs)

    def spaghetti(
        self,
        data_list,
        *args,
        levels=None,
        color="#0673e0",
        label=None,
        highlight=None,
        highlight_kwargs=None,
        highlight_label=None,
        **kwargs,
    ):
        """
        Plot spaghetti contours for ensemble data with optional highlighting.

        This method plots contour lines for each member in an ensemble dataset,
        with the ability to highlight specific members based on metadata criteria.

        Parameters
        ----------
        data_list : earthkit.data.core.Base, xarray.DataArray, or list
            The ensemble data to plot. Can be an earthkit data object, xarray DataArray,
            or a list of data objects that can be iterated over.
        *args
            Positional arguments passed to the contour method.
        levels : float or list of float, optional
            Contour level(s) to plot. Accepts a single value or a list of values.
            If provided, overrides any ``levels`` in kwargs.
        color : str or list, default "#0673e0"
            Color for normal ensemble members.
        label : str, optional
            Legend label for the ensemble members. If provided (along with
            ``highlight_label`` if highlighting is used), a legend entry is
            automatically added. Pass an empty string to suppress the entry.
        highlight : dict, optional
            Dictionary with metadata criteria to select members for highlighting.
            For example, {'dataType': 'cf'} to highlight control forecast.
        highlight_kwargs : dict, optional
            Dictionary with keyword arguments to pass to the contour method for
            highlighted members.
        highlight_label : str, optional
            Legend label for the highlighted members. Only used when ``highlight``
            is also set. Defaults to ``"Control"`` if ``label`` is set and
            ``highlight`` is set but ``highlight_label`` is not provided.
        **kwargs
            Additional keyword arguments passed to matplotlib.pyplot.contour.
            Common parameters include:
            - linewidths : float or list - line widths for contours
            - labels : bool - whether to show contour labels
            - alpha : float - transparency level
        """
        import earthkit.data

        # Convert to earthkit data if needed, keeping reference to original for sel operations
        original_data = data_list
        if not isinstance(data_list, earthkit.data.core.Base):
            data_list = earthkit.data.from_object(data_list)

        # Set up contour parameters
        if levels is not None:
            kwargs["levels"] = levels if isinstance(levels, (list, tuple)) else [levels]
        if color is not None:
            kwargs["colors"] = [color]
        kwargs.setdefault("labels", False)
        kwargs.setdefault("linewidths", 0.25)

        # Plot all ensemble members, nulling out their styles so the
        # figure-level colorbar legend machinery ignores them.
        # Store the label and line properties on the first member's layer so
        # the unified proxy-artist legend can pick it up.
        first_member_layer = None
        for data in data_list:
            self.contour(data, *args, **kwargs)
            self.layers[-1].style = None
            self.layers[-1].proxy_label = None
            if first_member_layer is None:
                first_member_layer = self.layers[-1]

        if label is not None and first_member_layer is not None:
            first_member_layer.proxy_label = label
            first_member_layer._proxy_color = color
            first_member_layer._proxy_linewidth = kwargs.get("linewidths", 0.25)

        # Plot highlighted members if specified
        highlight_color = "red"
        if highlight is not None:
            # Use original data for sel operations to preserve xarray functionality
            if hasattr(original_data, "sel"):
                highlighted_data = original_data.sel(**highlight)
            else:
                highlighted_data = data_list.sel(**highlight)

            if highlighted_data is not None and bool(highlighted_data):
                # Create highlight-specific kwargs
                highlight_kwargs = highlight_kwargs or dict()
                highlight_color = highlight_kwargs.pop("color", highlight_color)
                highlight_kwargs.setdefault("colors", highlight_color)
                highlight_kwargs.setdefault("linewidths", 1.5)
                highlight_kwargs = {**kwargs, **highlight_kwargs}

                self.contour(highlighted_data, *args, **highlight_kwargs)
                self.layers[-1].style = None
                _hl_label = (
                    highlight_label if highlight_label is not None else "Control"
                )
                if label is not None:
                    self.layers[-1].proxy_label = _hl_label
                    self.layers[-1]._proxy_color = highlight_color
                    self.layers[-1]._proxy_linewidth = highlight_kwargs.get(
                        "linewidths", 1.5
                    )
                else:
                    self.layers[-1].proxy_label = None

    def legend(self, label=None, *args, **kwargs):
        """
        Add a legend to the Subplot.

        Parameters
        ----------
        style : Style, optional
            The Style to use for the legend. If None (default), a legend is
            created for each Layer with a unique Style. If a single Style is
            provided, a single legend is created based on that Style.
        location : str or tuple, optional
            The location of the legend(s). Must be a valid matplotlib location
            (see :func:`matplotlib.pyplot.legend`).
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.legend`.
        """
        import matplotlib.lines as mlines

        proxy_handles = []
        for layer in self.layers:
            proxy_label = getattr(layer, "proxy_label", None)
            if proxy_label is not None:
                color = getattr(layer, "_proxy_color", None)
                lw = getattr(layer, "_proxy_linewidth", 1.0)
                if color is None:
                    try:
                        color = layer.mappable.collections[0].get_edgecolor()[0]
                    except (AttributeError, IndexError):
                        color = "black"
                proxy_handles.append(
                    mlines.Line2D([], [], color=color, linewidth=lw, label=proxy_label)
                )

        if proxy_handles:
            self.ax.legend(handles=proxy_handles, *args, **kwargs)
        else:
            self.ax.legend(*args, **kwargs)

    @schema.title.apply()
    def title(self, label=None, unique=True, wrap=True, capitalize=True, **kwargs):
        """
        Add a title to the plot.

        Parameters
        ----------
        label : str, optional
            The title text. If None, a default template is used. The template
            can contain metadata keys in curly braces, e.g. "{variable_name}".
        unique : bool, optional
            Whether to use unique metadata values from each Layer. If False,
            metadata values from all Layers are combined.
        wrap : bool, optional
            Whether to wrap the title text. Default is True.
        capitalize : bool, optional
            Whether to capitalize the first letter of the title. Default is True.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.title`.
        """
        if label is None:
            label = self._default_title_template
        label = self.format_string(label, unique)
        if "fontsize" not in kwargs:
            if self.figure.rows * self.figure.columns >= 10:
                scale_factor = 0.8
            elif self.figure.rows * self.figure.columns >= 4:
                scale_factor = 0.9
            else:
                scale_factor = 1.0
            kwargs["fontsize"] = schema.reference_fontsize * scale_factor
        if capitalize and label:
            label = label[0].upper() + label[1:]
        return self.ax.set_title(label, wrap=wrap, **kwargs)

    def set_title(self, label=None, **kwargs):
        """
        Set the title of the subplot.

        Alias for :meth:`title` that matches the matplotlib ``set_title``
        convention. Accepts the same arguments.

        Parameters
        ----------
        label : str, optional
            The title text. Can contain metadata keys in curly braces,
            e.g. ``"{variable_name}"``.
        **kwargs
            Additional keyword arguments forwarded to :meth:`title`.
        """
        return self.title(label, **kwargs)

    def suptitle(self, *args, **kwargs):
        """
        Add a top-level title to the chart.

        Parameters
        ----------
        label : str, optional
            The text to use in the title. This text can include format keys
            surrounded by `{}` curly brackets, which will extract metadata from
            your plotted data layers.
        unique : bool, optional
            If True, format keys which are uniform across subplots/layers will
            produce a single result. For example, if all data layers have the
            same `variable_name`, only one variable name will appear in the
            title.
            If False, each format key will evaluate to a list of values found
            across subplots/layers.
        grouped : bool, optional
            If True, a single title will be generated to represent all data
            layers, with each format key evaluating to a list where layers
            differ - e.g. `"{variable} at {time}"` might be evaluated to
            `"temperature and wind at 2023-01-01 00:00".
            If False, the title will be duplicated by the number of subplots/
            layers - e.g. `"{variable} at {time}"` might be evaluated to
            `"temperature at 2023-01-01 00:00 and wind at 2023-01-01 00:00".
        kwargs : dict, optional
            Keyword argument to :func:`matplotlib.pyplot.suptitle`.
        """
        return self.figure.title(*args, **kwargs)

    def format_string(self, string, unique=True, grouped=True, axis=None):
        """
        Format a string with metadata from the Subplot.

        Parameters
        ----------
        string : str
            The string to format. This can contain metadata keys in curly
            braces, e.g. "{variable_name}".
        unique : bool, optional
            Whether to use unique metadata values from each Layer. If False,
            metadata values from all Layers are combined.
        grouped : bool, optional
            Whether to group metadata values from all Layers into a single
            string. If False, metadata values from each Layer are listed
            separately.
        axis : str, optional
            The axis to format. If None, the format string will use the
            general metadata of the subplot.
        """
        if not grouped:
            return string_utils.list_to_human(
                [
                    LayerFormatter(layer, axis=axis).format(string)
                    for layer in self.layers
                ]
            )
        else:
            return SubplotFormatter(self, unique=unique, axis=axis).format(string)

    def show(self):
        """Display the plot."""
        return self.figure.show()

    def save(self, *args, **kwargs):
        """Save the plot to a file."""
        return self.figure.save(*args, **kwargs)

    def _repr_mimebundle_(self, **kwargs):
        """Called by Jupyter to render the figure inline."""
        return self.figure._repr_mimebundle_(**kwargs)

    def _repr_html_(self):
        """Fallback for environments that use _repr_html_ instead."""
        return self.figure._repr_html_()
