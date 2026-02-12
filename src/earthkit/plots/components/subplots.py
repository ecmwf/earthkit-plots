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
    extract_plottables_1D,
    extract_plottables_2D,
    extract_plottables_envelope,
    extract_plottables_vector_2D,
)
from earthkit.plots.components.layers import Layer
from earthkit.plots.metadata.formatters import (
    LayerFormatter,
    SourceFormatter,
    SubplotFormatter,
)
from earthkit.plots.resample import Regrid
from earthkit.plots.schemas import schema
from earthkit.plots.sources import get_source
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
            **kwargs,
        ):
            return extract_plottables_1D(
                self,
                method_name or method.__name__,
                args=args,
                x=x,
                y=y,
                z=z,
                style=style,
                every=every,
                **kwargs,
            )

        return wrapper

    return decorator


def plot_2D(method_name=None, extract_domain=False):
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
            **kwargs,
        ):
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
            resample=Regrid(40),
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

    @property
    def crs(self):
        """The Coordinate Reference System of the subplot."""
        return None

    def add_attribution(self, attribution):
        """
        Add an attribution to the figure.

        Parameters
        ----------
        attribution : str
            The attribution text to add to the figure.
        """
        self.figure.add_attribution(attribution)

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

    def _extract_plottables_envelope(
        self,
        data=None,
        x=None,
        y=None,
        z=None,
        every=None,
        source_units=None,
        extract_domain=False,
        **kwargs,
    ):
        return extract_plottables_envelope(
            self,
            data=data,
            x=x,
            y=y,
            z=z,
            every=every,
            source_units=source_units,
            extract_domain=extract_domain,
            **kwargs,
        )

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
            units = self.layers[0].sources[0].y.metadata("units")
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
            units = self.layers[0].sources[0].x.metadata("units")
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
                keys = [k for _, k, _, _ in SubplotFormatter().parse(template)]
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
    def envelope(self, data_1, data_2=0, alpha=0.4, **kwargs):
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
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.fill_between`.
        """
        x1, y1, _ = self._extract_plottables_envelope(y=data_1, **kwargs)
        x2, y2, _ = self._extract_plottables_envelope(y=data_2, **kwargs)
        kwargs.pop("x")
        mappable = self.ax.fill_between(x=x1, y1=y1, y2=y2, alpha=alpha, **kwargs)
        self.layers.append(Layer(get_source(data=data_1), mappable, self, style=None))
        return mappable

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
                method = self.grid_cells
        else:
            method = getattr(self, style._preferred_method)
        return method(data, style=style, units=units, auto_style=True, **kwargs)

    def quickplot(self, data, style=None, units=None, **kwargs):
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
        from earthkit.data.core import Base

        if not kwargs.pop("auto_style", True):
            warnings.warn("`auto_style` cannot be switched off for `quickplot`.")
        if not isinstance(data, Base):
            data = earthkit.data.from_object(data)
        source = get_source(data)
        if style is None:
            auto_style = auto.guess_style(source, units=units, **kwargs)
            if auto_style is not None:
                method = getattr(self, auto_style._preferred_method)
            else:
                method = self.grid_cells
        else:
            method = getattr(self, style._preferred_method)
        zorder = LAYER_ZORDERS.get(method.__name__, 10)
        kwargs.setdefault("zorder", zorder)
        return method(data, style=style, units=units, auto_style=True, **kwargs)

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

    @plot_2D(extract_domain=True)
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
        interpolate: earthkit.plots.resample.Interpolate, dict, optional
            A :class:`plots.resample.Interpolate` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Interpolate` class.
            If not provided and the data is unstructured, an `Interpolate` class is created
            by detecting the resolution of the data.
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
        interpolate: earthkit.plots.resample.Interpolate, dict, optional
            A :class:`plots.resample.Interpolate` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Interpolate` class.
            If not provided and the data is unstructured, an `Interpolate` class is created
            by detecting the resolution of the data.
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

        Deprecated: Use :meth:`pcolormesh` or :meth:`grid_cells` instead.

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
            "Please use grid_cells instead."
        )
        return self.pcolormesh(*args, **kwargs)

    grid_cells = pcolormesh

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
        if capitalize:
            label = label[0].upper() + label[1:]
        return self.ax.set_title(label, wrap=wrap, **kwargs)

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
