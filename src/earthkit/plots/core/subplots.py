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

import warnings

import matplotlib.dates as mdates
import numpy as np

from earthkit.plots.core.decorators import plot_2D, plot_3D, plot_vector
from earthkit.plots.core.layers import Layer
from earthkit.plots.metadata.formatters import (
    LayerFormatter,
    SourceFormatter,
    SubplotFormatter,
)
from earthkit.plots.schemas import schema
from earthkit.plots.sources import get_source
from earthkit.plots.sources.numpy import NumpySource
from earthkit.plots.styles import auto
from earthkit.plots.utils import string_utils

DEFAULT_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]
ZERO_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]

TARGET_DENSITY = 40


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
        Additional keyword arguments to pass to the matplotlib Axes constructor.
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
        return None

    def _cleanup(self, *args, **kwargs):
        """
        Space for any cleanup that needs to be done after a plot is made.
        """
        pass

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

    def set_major_xticks(
        self,
        frequency=None,
        format=None,
        highlight=None,
        highlight_color="red",
        **kwargs,
    ):
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
                interval = int(frequency.lstrip("Y") or "1")
                locator = mdates.YearLocator(interval, month=6, day=1)
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
        import matplotlib.ticker as ticker

        # Set major ticks
        if frequency is None:
            locator = mdates.AutoDateLocator(maxticks=30)
        else:
            if frequency.startswith("D"):
                interval = int(frequency.lstrip("D") or "1")
                locator = mdates.DayLocator(interval=interval, **kwargs)
            elif frequency.startswith("M"):
                interval = int(frequency.lstrip("M") or "1")
                locator = mdates.MonthLocator(interval=interval, bymonthday=1)
            elif frequency.startswith("Y"):
                interval = int(frequency.lstrip("Y") or "1")
                locator = mdates.YearLocator(interval, month=1, day=1)
            elif frequency.startswith("H"):
                interval = int(frequency.lstrip("H") or "1")
                locator = mdates.HourLocator(interval=interval)
            else:
                # Fallback to auto locator
                locator = mdates.AutoDateLocator(maxticks=30)

        # Set major tick format
        if format:
            major_formats = [format] * 6
        else:
            major_formats = DEFAULT_FORMATS

        # Handle period behavior (centered labels)
        if period:
            # Hide major labels by setting null formatter
            self.ax.xaxis.set_major_locator(locator)
            self.ax.xaxis.set_major_formatter(ticker.NullFormatter())

            # Create minor locator for centered labels based on frequency
            if frequency and frequency.startswith("D"):
                # For days, place minor ticks at noon (12:00)
                interval = int(frequency.lstrip("D") or "1")
                minor_locator = mdates.HourLocator(byhour=12, interval=1)
            elif frequency and frequency.startswith("M"):
                # For months, place minor ticks on the 16th (middle of month)
                interval = int(frequency.lstrip("M") or "1")
                minor_locator = mdates.MonthLocator(interval=interval, bymonthday=16)
            elif frequency and frequency.startswith("Y"):
                # For years, place minor ticks in the middle of the year (July 1st)
                interval = int(frequency.lstrip("Y") or "1")
                minor_locator = mdates.MonthLocator(interval=1, bymonth=7, bymonthday=1)
            elif frequency and frequency.startswith("H"):
                # For hours, place minor ticks at 30 minutes past the hour
                interval = int(frequency.lstrip("H") or "1")
                minor_locator = mdates.MinuteLocator(interval=interval, byminute=30)
            else:
                # For other frequencies, use the same locator but with adjusted parameters
                # This will create minor ticks that are offset from major ticks
                minor_locator = locator
            if interval != 1:
                raise ValueError("Period mode is not supported for non-whole intervals")

            # Set the minor locator and formatter
            minor_formatter = mdates.ConciseDateFormatter(
                minor_locator,
                formats=major_formats,
                zero_formats=ZERO_FORMATS,
                show_offset=False,
            )
            self.ax.xaxis.set_minor_locator(minor_locator)
            self.ax.xaxis.set_minor_formatter(minor_formatter)

            # Override labels argument to "minor" when period=True
            labels = "minor"
        else:
            # Regular behavior - labels on major ticks
            # Only set major formatter if we want to show major labels
            if labels in ["major", "both"]:
                formatter = mdates.ConciseDateFormatter(
                    locator,
                    formats=major_formats,
                    zero_formats=ZERO_FORMATS,
                    show_offset=False,
                )
                self.ax.xaxis.set_major_locator(locator)
                self.ax.xaxis.set_major_formatter(formatter)
            else:
                # Hide major labels by setting null formatter
                self.ax.xaxis.set_major_locator(locator)
                self.ax.xaxis.set_major_formatter(ticker.NullFormatter())

        # Set minor ticks if specified
        if minor_frequency is not None:
            if minor_frequency.startswith("D"):
                interval = int(minor_frequency.lstrip("D") or "1")
                minor_locator = mdates.DayLocator(interval=interval, **kwargs)
            elif minor_frequency.startswith("M"):
                interval = int(minor_frequency.lstrip("M") or "1")
                minor_locator = mdates.MonthLocator(interval=interval, bymonthday=15)
            elif minor_frequency.startswith("Y"):
                interval = int(minor_frequency.lstrip("Y") or "1")
                minor_locator = mdates.YearLocator(interval, month=6, day=1)
            elif minor_frequency.startswith("H"):
                interval = int(minor_frequency.lstrip("H") or "1")
                minor_locator = mdates.HourLocator(interval=interval)
            else:
                # Fallback to auto locator
                minor_locator = mdates.AutoDateLocator(maxticks=30)

            # Set minor tick format - use format if minor_format is None
            if minor_format is not None:
                minor_formats = [minor_format] * 6
            elif format is not None:
                minor_formats = [format] * 6
            else:
                minor_formats = major_formats

            # Only set minor ticks if not in period mode (to avoid conflicts)
            if not period:
                # Only set minor formatter if we want to show minor labels
                if labels in ["minor", "both"]:
                    minor_formatter = mdates.ConciseDateFormatter(
                        minor_locator,
                        formats=minor_formats,
                        zero_formats=ZERO_FORMATS,
                        show_offset=False,
                    )
                    self.ax.xaxis.set_minor_locator(minor_locator)
                    self.ax.xaxis.set_minor_formatter(minor_formatter)
                else:
                    # Hide minor labels by setting null formatter
                    self.ax.xaxis.set_minor_locator(minor_locator)
                    self.ax.xaxis.set_minor_formatter(ticker.NullFormatter())

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
        import matplotlib.ticker as ticker

        # For y-axis, we'll use numeric tickers since y-axis is typically numeric
        if frequency is not None:
            # Parse frequency specification
            if frequency.startswith("auto"):
                major_locator = ticker.AutoLocator()
            elif frequency.startswith("log"):
                major_locator = ticker.LogLocator()
            elif frequency.startswith("maxN"):
                max_ticks = int(frequency.lstrip("maxN") or "10")
                major_locator = ticker.MaxNLocator(nbins=max_ticks)
            else:
                # Default to auto locator
                major_locator = ticker.AutoLocator()
        else:
            major_locator = ticker.AutoLocator()

        # Set major ticks
        self.ax.yaxis.set_major_locator(major_locator)

        # Only set major tick format if we want to show major labels
        if labels in ["major", "both"] and format:
            self.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter(format))
        elif labels not in ["major", "both"]:
            # Hide major labels by setting null formatter
            self.ax.yaxis.set_major_formatter(ticker.NullFormatter())

        # Set minor ticks if specified
        if minor_frequency is not None:
            if minor_frequency.startswith("auto"):
                minor_locator = ticker.AutoMinorLocator()
            elif minor_frequency.startswith("log"):
                minor_locator = ticker.LogLocator(subs=np.arange(2, 10))
            else:
                # Default to auto minor locator
                minor_locator = ticker.AutoMinorLocator()

            self.ax.yaxis.set_minor_locator(minor_locator)

            # Only set minor tick format if we want to show minor labels
            if labels in ["minor", "both"]:
                # Set minor tick format - use format if minor_format is None
                if minor_format is not None:
                    minor_format_str = minor_format
                elif format is not None:
                    minor_format_str = format
                else:
                    minor_format_str = None

                if minor_format_str:
                    self.ax.yaxis.set_minor_formatter(
                        ticker.FormatStrFormatter(minor_format_str)
                    )
            else:
                # Hide minor labels by setting null formatter
                self.ax.yaxis.set_minor_formatter(ticker.NullFormatter())

    @property
    def figure(self):
        from earthkit.plots.core.figures import Figure

        if self._figure is None:
            self._figure = Figure(1, 1, size=self._size)
            self._figure.subplots = [self]
        return self._figure

    @property
    def fig(self):
        """The underlying matplotlib Figure object."""
        return self.figure.fig

    @property
    def ax(self):
        """The underlying matplotlib Axes object."""
        if self._ax is None:
            subspec = self.figure.gridspec[self.row, self.column]
            self._ax = self.figure.fig.add_subplot(subspec, **self._ax_kwargs)
        return self._ax

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
        raise NotImplementedError

    def gridlines(self, *args, **kwargs):
        raise NotImplementedError

    @plot_2D()
    def quantiles(self, *args, **kwargs):
        pass

    @schema.line.apply()
    @plot_2D()
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
            Additional keyword arguments to pass to `matplotlib.pyplot.plot`.
        """

    @schema.envelope.apply()
    def envelope(self, data_1, data_2=0, alpha=0.4, **kwargs):
        from earthkit.plots.core.extractors import extract_plottables_envelope

        x1, y1, _ = extract_plottables_envelope(self, y=data_1, **kwargs)
        x2, y2, _ = extract_plottables_envelope(self, y=data_2, **kwargs)
        kwargs.pop("x")
        mappable = self.ax.fill_between(x=x1, y1=y1, y2=y2, alpha=alpha, **kwargs)
        self.layers.append(Layer(get_source(data=data_1), mappable, self, style=None))
        return mappable

    def labels(self, data=None, label=None, x=None, y=None, **kwargs):
        source = get_source(data=data, x=x, y=y)
        labels = SourceFormatter(source).format(label)
        for label, x, y in zip(labels, source.x_values, source.y_values):
            self.ax.annotate(label, (x, y), **kwargs)

    def plot(self, data, style=None, units=None, **kwargs):
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
        if not kwargs.pop("auto_style", True):
            warnings.warn("`auto_style` cannot be switched off for `quickplot`.")
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

    def hsv_composite(self, *args):
        import xarray as xr

        if len(args) == 1:
            red, green, blue = args[0]
        else:
            red, green, blue = args

        red_source = get_source(red)
        green_source = get_source(green)
        blue_source = get_source(blue)

        x_values = red_source.x_values
        y_values = red_source.y_values

        red = (red_source.z_values - red_source.z_values.min()) / (
            red_source.z_values.max() - red_source.z_values.min()
        )
        green = (green_source.z_values - green_source.z_values.min()) / (
            green_source.z_values.max() - green_source.z_values.min()
        )
        blue = (blue_source.z_values - blue_source.z_values.min()) / (
            blue_source.z_values.max() - blue_source.z_values.min()
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

    def rgb_composite(self, *args, **kwargs):
        import xarray as xr

        if len(args) == 1:
            red, green, blue = args[0]
        else:
            red, green, blue = args

        red_source = get_source(red)
        green_source = get_source(green)
        blue_source = get_source(blue)

        x_values = red_source.x_values
        y_values = red_source.y_values

        red = (red_source.z_values - red_source.z_values.min()) / (
            red_source.z_values.max() - red_source.z_values.min()
        )
        green = (green_source.z_values - green_source.z_values.min()) / (
            green_source.z_values.max() - green_source.z_values.min()
        )
        blue = (blue_source.z_values - blue_source.z_values.min()) / (
            blue_source.z_values.max() - blue_source.z_values.min()
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

        result = self.pcolormesh(c=rgb, x=x_values, y=y_values, no_style=True, **kwargs)

        self.layers[-1].sources = [red_source, green_source, blue_source]

        return result

    @plot_2D()
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

        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.bar`.
        """

    @plot_2D()
    def stripes(self, *args, cmap="RdBu_r", center=0, **kwargs):
        """
        Plot climate stripes on the Subplot.

        Climate stripes are horizontal bars where each bar represents a time period
        and the color represents the value, creating a visually striking representation
        of long-term trends. Each stripe is centered on its x-value, making it
        compatible with other plot types.

        Parameters
        ----------
        *args : tuple
            Data arguments (data, x, y, values).
        cmap : str, optional
            Colormap to use for the stripes. Default is 'RdBu_r'.
        center : float, optional
            Value to center the colormap on. Default is 0.
        **kwargs : dict
            Additional keyword arguments to pass to the stripes method.

        Returns
        -------
        matplotlib.cm.ScalarMappable
            The mappable object for creating colorbars.
        """
        return self.style.stripes(self.ax, *args, cmap=cmap, center=center, **kwargs)

    @schema.scatter.apply()
    @plot_2D()
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.scatter`.
        """

    @plot_3D(extract_domain=True)
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
        interpolate: earthkit.plots.resample.Interpolate, dict, optional
            A :class:`plots.resample.Interpolate` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Interpolate` class.
            If not provided and the data is unstructured, an `Interpolate` class is created
            by detecting the resolution of the data.
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.pcolormesh`.
        """

    @schema.contour.apply()
    @plot_3D(extract_domain=True)
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.contour`.
        """

    @schema.contourf.apply()
    @plot_3D(extract_domain=True)
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
        interpolate: earthkit.plots.resample.Interpolate, dict, optional
            A :class:`plots.resample.Interpolate` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Interpolate` class.
            If not provided and the data is unstructured, an `Interpolate` class is created
            by detecting the resolution of the data.
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.contourf`.
        """

    @plot_3D()
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.tripcolor`.
        """

    @plot_3D()
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.tricontour`.
        """

    @plot_3D()
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.tricontourf`.
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.quiver`.
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.barbs`.
        """

    def block(self, *args, **kwargs):
        import warnings

        warnings.warn(
            "block is deprecated and will be removed in a future release. "
            "Please use grid_cells instead."
        )
        return self.pcolormesh(*args, **kwargs)

    grid_cells = pcolormesh

    @schema.legend.apply()
    def legend(self, style=None, location=None, **kwargs):
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
            (see https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html).
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.legend`.
        """
        legends = []
        if style is not None:
            dummy = [[1, 2], [3, 4]]
            mappable = self.contourf(x=dummy, y=dummy, z=dummy, style=style)
            layer = Layer(NumpySource(), mappable, self, style)
            legend = layer.style.legend(layer, label=kwargs.pop("label", ""), **kwargs)
            legends.append(legend)
        else:
            for i, layer in enumerate(self.distinct_legend_layers):
                if isinstance(location, (list, tuple)):
                    loc = location[i]
                else:
                    loc = location
                if layer.style is not None:
                    legend = layer.style.legend(layer, location=loc, **kwargs)
                legends.append(legend)
        return legends

    def ylabel(self, label=None, **kwargs):
        """
        Add a y-axis label to the plot.
        """
        if label is None:
            metadata = self.layers[0].sources[0].y_metadata
            if metadata is not None and "units" in metadata:
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
            metadata = self.layers[0].sources[0].x_metadata
            if metadata is not None and "units" in metadata:
                label = "{variable_name} ({units})"
            else:
                label = "{variable_name}"
        label = self.format_string(label, axis="x")
        return self.ax.set_xlabel(label, **kwargs)

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
            Additional keyword arguments to pass to `matplotlib.pyplot.title`.
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
            Keyword argument to matplotlib.pyplot.suptitle (see
            https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.suptitle.html#matplotlib-pyplot-suptitle
            ).
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


def thin_array(array, every=2):
    """
    Reduce the size of an array by taking every `every`th element.

    Parameters
    ----------
    array : numpy.ndarray
        The array to thin.
    every : int, optional
        The number of elements to skip.
    """
    if len(array.shape) == 1:
        return array[::every]
    else:
        return array[::every, ::every]
