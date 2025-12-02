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

from earthkit.plots.core.extractors import (
    extract_plottables_1d,
    extract_plottables_2d,
)
from earthkit.plots.core.layers import Layer
from earthkit.plots.metadata.formatters import (
    LayerFormatter,
    DimensionSetFormatter,
    SubplotFormatter,
)
from earthkit.plots.resample import Regrid
from earthkit.plots.schemas import schema
from earthkit.plots.utils import string_utils

DEFAULT_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]
ZERO_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]

TARGET_DENSITY = 40

LAYER_ZORDERS = {
    "contourf": 1,
    "pcolormesh": 1,
    "imshow": 1,
    "scatter": 2,
    "contour": 3,
    "quiver": 3,
    "barbs": 3,
    "streamplot": 3,
}


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

    def plot_1d(method_name=None):
        """Decorator for 1D plotting methods (line, scatter)."""
        # Sentinel value to distinguish "not provided" from "explicitly None"
        _LABEL_AUTO = object()

        def decorator(method):
            @functools.wraps(method)
            def wrapper(
                self,
                *args,
                x="auto",
                y="auto",
                z=None,
                style=None,
                every=None,
                label=_LABEL_AUTO,
                **kwargs,
            ):
                # Convert sentinel to None for extract_plottables_1d
                label_for_extraction = None if label is _LABEL_AUTO else label

                # Get processed data and kwargs from extract_plottables_1d
                x_values, y_values, z_values, plot_kwargs = extract_plottables_1d(
                    self,
                    method_name or method.__name__,
                    args=args,
                    x=x,
                    y=y,
                    z=z,
                    style=style,
                    every=every,
                    label=label_for_extraction,
                    **kwargs,
                )

                # Extract metadata (keys starting with _) for layer creation
                dimension_set = plot_kwargs.pop('_dimension_set')
                plot_style = plot_kwargs.pop('_style')
                primary_axis = plot_kwargs.pop('_primary_axis')
                units = plot_kwargs.pop('_units')
                xunits = plot_kwargs.pop('_xunits')
                yunits = plot_kwargs.pop('_yunits')
                plot_kwargs.pop('_label')  # Discard, we use our own label handling

                # Call matplotlib method directly
                mpl_method = getattr(self.ax, method_name or method.__name__)
                if z_values is not None:
                    # For scatter with color
                    mappable = mpl_method(x_values, y_values, c=z_values, **plot_kwargs)
                else:
                    mappable = mpl_method(x_values, y_values, **plot_kwargs)

                # Create and store layer
                from earthkit.plots.core.layers import Layer
                axis_units = {}
                if xunits is not None:
                    axis_units["x"] = xunits
                if yunits is not None:
                    axis_units["y"] = yunits
                if units is not None and primary_axis not in axis_units:
                    axis_units[primary_axis] = units

                layer = Layer(
                    dimension_set=dimension_set,
                    mappable=mappable,
                    subplot=self,
                    style=plot_style,
                    axis_units=axis_units,
                )

                # Handle label for legend
                # Distinguish between:
                # - label not provided (_LABEL_AUTO) → use default "{variable_name}"
                # - label=None explicitly → don't show in legend (set to special marker)
                # - label="something" → use that label
                if label is _LABEL_AUTO:
                    # Default: use variable name
                    label_to_use = "{variable_name}"
                elif label is None:
                    # Explicitly None: mark as excluded from legend
                    label_to_use = "_no_legend_"
                else:
                    # User-provided label
                    label_to_use = label

                # Store the label from plot time for later use by legend()
                layer._plot_label = label_to_use

                # Set label on mappable (unless excluded)
                if label_to_use != "_no_legend_":
                    formatted_label = layer.format_string(label_to_use)
                    if isinstance(mappable, list):
                        for m in mappable:
                            m.set_label(formatted_label)
                    else:
                        mappable.set_label(formatted_label)

                self.layers.append(layer)

                return mappable

            return wrapper

        return decorator

    def plot_2d(method_name=None, extract_domain=False):
        """Decorator for 2D plotting methods (contour, pcolormesh)."""
        # Sentinel value to distinguish "not provided" from "explicitly None"
        _LABEL_AUTO = object()

        def decorator(method):
            @functools.wraps(method)
            def wrapper(
                self,
                *args,
                x="auto",
                y="auto",
                z="auto",
                regrid="auto",
                style=None,
                every=None,
                auto_style=False,
                label=_LABEL_AUTO,
                reproject_to_target=True,
                **kwargs,
            ):
                # Convert sentinel to None for extract_plottables_2d
                label_for_extraction = None if label is _LABEL_AUTO else label
                # Get processed data and kwargs from extract_plottables_2d
                x_values, y_values, z_values, plot_kwargs = extract_plottables_2d(
                    self,
                    method_name or method.__name__,
                    args=args,
                    x=x,
                    y=y,
                    z=z,
                    style=style,
                    every=every,
                    auto_style=auto_style,
                    extract_domain=extract_domain,
                    regrid=regrid,
                    label=label_for_extraction,
                    reproject_to_target=reproject_to_target,
                    **kwargs,
                )

                # Extract metadata (keys starting with _) for layer creation
                dimension_set = plot_kwargs.pop('_dimension_set')
                plot_style = plot_kwargs.pop('_style')
                primary_axis = plot_kwargs.pop('_primary_axis')
                units = plot_kwargs.pop('_units')
                xunits = plot_kwargs.pop('_xunits')
                yunits = plot_kwargs.pop('_yunits')
                is_specialized = plot_kwargs.pop('_is_specialized')
                actual_method_name = plot_kwargs.pop('_method_name')
                no_style = plot_kwargs.pop('_no_style')
                plot_label = plot_kwargs.pop('_label')

                import time
                import logging
                logger = logging.getLogger(__name__)

                # Handle specialized grids (healpix, octahedral)
                if is_specialized and not regrid:
                    from earthkit.plots.core.extractors import _handle_specialized_grids_dimension_set
                    t_render_start = time.time()
                    mappable = _handle_specialized_grids_dimension_set(
                        self, dimension_set, z_values, plot_style, actual_method_name, plot_kwargs
                    )
                    t_render = (time.time() - t_render_start) * 1000
                    logger.info(f"[TIMING] specialized grid rendering: {t_render:.2f}ms")
                else:
                    # Handle interpolation if requested
                    if not no_style and 'interpolate' in plot_kwargs:
                        from earthkit.plots.core.extractors import plot_with_interpolation
                        t_render_start = time.time()
                        mappable = plot_with_interpolation(
                            self,
                            plot_style,
                            actual_method_name,
                            x_values,
                            y_values,
                            z_values,
                            getattr(self, 'crs', None),
                            plot_kwargs,
                        )
                        t_render = (time.time() - t_render_start) * 1000
                        logger.info(f"[TIMING] interpolation + rendering: {t_render:.2f}ms")
                    else:
                        import cartopy.crs as ccrs

                        # Call matplotlib method directly
                        mpl_method = getattr(self.ax, method_name or method.__name__)

                        # Extract contour-specific parameters
                        show_labels = plot_kwargs.pop('labels', False)

                        # Timing: Start matplotlib rendering
                        t_render_start = time.time()

                        # For scatter, handle z_values specially
                        if actual_method_name == 'scatter':
                            if z_values is not None:
                                # Colored scatter - pass z as 'c' parameter
                                mappable = mpl_method(x_values, y_values, c=z_values, **plot_kwargs)
                            else:
                                # Uncolored scatter - no color parameter
                                mappable = mpl_method(x_values, y_values, **plot_kwargs)
                        else:
                            mappable = mpl_method(x_values, y_values, z_values, **plot_kwargs)

                        # Timing: Log matplotlib rendering time
                        t_render = (time.time() - t_render_start) * 1000
                        logger.info(f"[TIMING] matplotlib.{actual_method_name}() rendering: {t_render:.2f}ms")

                        # Add contour labels if requested (only for contour, not contourf)
                        if show_labels and actual_method_name in ['contour', 'tricontour']:
                            self.ax.clabel(mappable, inline=True, fontsize=10)
                # Create and store layer
                from earthkit.plots.core.layers import Layer
                axis_units = {}
                if xunits is not None:
                    axis_units["x"] = xunits
                if yunits is not None:
                    axis_units["y"] = yunits
                if units is not None and primary_axis not in axis_units:
                    axis_units[primary_axis] = units

                layer = Layer(
                    dimension_set=dimension_set,
                    mappable=mappable,
                    subplot=self,
                    style=plot_style,
                    axis_units=axis_units,
                )

                # Handle label for legend
                # Distinguish between:
                # - label not provided (_LABEL_AUTO) → use default "{variable_name} ({units})"
                # - label=None explicitly → don't show in legend (set to special marker)
                # - label="something" → use that label
                if label is _LABEL_AUTO:
                    # Default: use variable name with units
                    label_to_use = "{variable_name} ({units})"
                elif label is None:
                    # Explicitly None: mark as excluded from legend
                    label_to_use = "_no_legend_"
                else:
                    # User-provided label
                    label_to_use = label

                # Store the label from plot time for later use by legend()
                layer._plot_label = label_to_use

                self.layers.append(layer)

                return mappable

            return wrapper

        return decorator

    def plot_1d_or_2d(method_name=None):
        """
        Decorator for plotting methods that can handle both 1D and 2D data (e.g., scatter).

        Tries 2D extraction first (to get x, y, z). If that fails with MissingDimensionError,
        falls back to 1D extraction (to get x, y without z).

        This allows scatter to work with:
        - 2D/spatial data: data(points) with lat(points), lon(points) → x=lon, y=lat, z=values
        - 1D/time series: data(time) → x=time, y=values, z=None
        """
        # Sentinel value to distinguish "not provided" from "explicitly None"
        _LABEL_AUTO = object()

        def decorator(method):
            @functools.wraps(method)
            def wrapper(
                self,
                *args,
                x="auto",
                y="auto",
                z="auto",
                regrid="auto",
                style=None,
                every=None,
                auto_style=False,
                label=_LABEL_AUTO,
                **kwargs,
            ):
                from earthkit.plots.sources.extractors.exceptions import MissingDimensionError, IncompatibleDimensionsError

                # Try 2D extraction first (for spatial scatter, even with z=None for grid_points)
                # This handles geographic data with lat/lon coordinates
                use_1d = False

                # Convert sentinel to None for extraction functions
                label_for_extraction = None if label is _LABEL_AUTO else label

                try:
                    x_values, y_values, z_values, plot_kwargs = extract_plottables_2d(
                        self,
                        method_name or method.__name__,
                        args=args,
                        x=x,
                        y=y,
                        z=z,
                        style=style,
                        every=every,
                        auto_style=auto_style,
                        extract_domain=True,  # Always extract domain for scatter
                        regrid=regrid,
                        label=label_for_extraction,
                        **kwargs,
                    )

                    # Extract metadata for layer creation
                    dimension_set = plot_kwargs.pop('_dimension_set')
                    plot_style = plot_kwargs.pop('_style')
                    primary_axis = plot_kwargs.pop('_primary_axis')
                    units = plot_kwargs.pop('_units')
                    xunits = plot_kwargs.pop('_xunits')
                    yunits = plot_kwargs.pop('_yunits')
                    # Pop 2D-specific keys that won't be used
                    plot_kwargs.pop('_is_specialized', None)
                    plot_kwargs.pop('_method_name', None)
                    plot_kwargs.pop('_no_style', None)
                    # Discard _label - we use the label parameter from the decorator
                    plot_kwargs.pop('_label', None)

                except (MissingDimensionError, IncompatibleDimensionsError):
                    # Fall back to 1D extraction (for time series scatter)
                    use_1d = True

                if use_1d:
                    # Fall back to 1D extraction (for time series scatter)
                    x_values, y_values, z_values, plot_kwargs = extract_plottables_1d(
                        self,
                        method_name or method.__name__,
                        args=args,
                        x=x,
                        y=y,
                        z=z,
                        style=style,
                        every=every,
                        auto_style=auto_style,
                        label=label_for_extraction,
                        **kwargs,
                    )

                    # Extract metadata for layer creation
                    dimension_set = plot_kwargs.pop('_dimension_set')
                    plot_style = plot_kwargs.pop('_style')
                    primary_axis = plot_kwargs.pop('_primary_axis')
                    units = plot_kwargs.pop('_units')
                    xunits = plot_kwargs.pop('_xunits')
                    yunits = plot_kwargs.pop('_yunits')
                    # Discard _label - we use the label parameter from the decorator
                    plot_kwargs.pop('_label', None)

                # Call matplotlib scatter method
                mpl_method = getattr(self.ax, method_name or method.__name__)
                if z_values is not None:
                    # Colored scatter
                    mappable = mpl_method(x_values, y_values, c=z_values, **plot_kwargs)
                else:
                    # Uncolored scatter
                    mappable = mpl_method(x_values, y_values, **plot_kwargs)

                # Create and store layer
                from earthkit.plots.core.layers import Layer
                axis_units = {}
                if xunits is not None:
                    axis_units["x"] = xunits
                if yunits is not None:
                    axis_units["y"] = yunits
                if units is not None and primary_axis not in axis_units:
                    axis_units[primary_axis] = units

                # Create layer
                layer = Layer(
                    dimension_set=dimension_set,
                    mappable=mappable,
                    subplot=self,
                    style=plot_style,
                    axis_units=axis_units,
                )

                # Handle label for legend
                # Distinguish between:
                # - label not provided (_LABEL_AUTO) → use default based on context
                # - label=None explicitly → don't show in legend (set to special marker)
                # - label="something" → use that label
                if label is _LABEL_AUTO:
                    # Default: set based on plot context
                    if dimension_set.z is None:
                        # 1D scatter: use variable name
                        label_to_use = "{variable_name}"
                    else:
                        # 2D scatter: use variable name and units
                        label_to_use = "{variable_name} ({units})"
                elif label is None:
                    # Explicitly None: mark as excluded from legend
                    label_to_use = "_no_legend_"
                else:
                    # User-provided label
                    label_to_use = label

                # Store the label from plot time for later use by legend()
                layer._plot_label = label_to_use

                # Set label on mappable (unless excluded)
                if label_to_use != "_no_legend_":
                    formatted_label = layer.format_string(label_to_use)
                    if isinstance(mappable, list):
                        for m in mappable:
                            m.set_label(formatted_label)
                    else:
                        mappable.set_label(formatted_label)

                self.layers.append(layer)
                return mappable

            return wrapper

        return decorator

    def plot_vector(method_name=None):
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
                u_source = None
                v_source = None

                if not args:
                    u_source = get_source(u, x=x, y=y, units=source_units)
                    v_source = get_source(v, x=x, y=y, units=source_units)
                elif len(args) == 1:
                    u_source, v_source = get_vector_sources(
                        args[0], x=x, y=y, u=u, v=v, units=source_units
                    )
                elif len(args) == 2:
                    u_source = get_source(args[0], x=x, y=y, units=source_units)
                    v_source = get_source(args[1], x=x, y=y, units=source_units)

                assert (
                    u_source is not None and v_source is not None
                ), "Could not determine vector components from input arguments"

                kwargs = {**self._plot_kwargs(u_source), **kwargs}

                multi_source = MultiSource([u_source, v_source])

                style = self._configure_style(
                    method_name or method.__name__,
                    style,
                    multi_source,
                    units,
                    auto_style,
                    {**kwargs, "colors": colors},
                )
                m = getattr(style, method_name or method.__name__)

                x_values = u_source.x_values
                y_values = u_source.y_values
                u_values = style.convert_units(u_source.z_values, u_source.units)
                v_values = style.convert_units(v_source.z_values, v_source.units)

                resample = style.resample or resample

                if self.domain is not None:
                    x_values, y_values, _, [u_values, v_values] = self.domain.extract(
                        x_values,
                        y_values,
                        extra_values=[u_values, v_values],
                        source_crs=u_source.crs,
                    )

                if resample is not None:
                    kwargs.pop("regrid_shape", None)
                    if resample.__class__.__name__ == "Regrid":
                        kwargs.pop("transform")
                    args = resample.apply(
                        x_values,
                        y_values,
                        u_values,
                        v_values,
                        source_crs=u_source.crs,
                        target_crs=self.crs,
                        extents=self.ax.get_extent(),
                    )
                else:
                    args = [x_values, y_values, u_values, v_values]

                if colors:
                    args.append((args[2] ** 2 + args[3] ** 2) ** 0.5)

                mappable = m(self.ax, *args, **kwargs)
                self.layers.append(Layer([u_source, v_source], mappable, self, style))
                if isinstance(u_source._x, str):
                    self.ax.set_xlabel(u_source._x)
                if isinstance(u_source._y, str):
                    self.ax.set_ylabel(u_source._y)
                return mappable

            return wrapper

        return decorator

    @property
    def figure(self):
        """The :class:`earthkit.plots.components.figures.Figure` object."""
        from earthkit.plots.core.figures import Figure

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
        # if label is None:
        #     metadata = self.layers[0].sources[0].y_metadata
        #     if metadata is not None and "units" in metadata:
        #         label = "{variable_name} ({units})"
        #     else:
        #         label = "{variable_name}"
        label = "{variable_name} ({units})" if label is None else label
        label = self.format_string(label, axis="y")
        return self.ax.set_ylabel(label, **kwargs)

    def xlabel(self, label=None, **kwargs):
        """
        Add an x-axis label to the plot.
        """
        # if label is None:
        #     metadata = self.layers[0].sources[0].x_metadata
        #     if metadata is not None and "units" in metadata:
        #         label = "{variable_name} ({units})"
        #     else:
        #         label = "{variable_name}"
        label = "{variable_name} ({units})" if label is None else label
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
        on subclasses such as :class:`earthkit.plots.core.maps.Map`.
        """
        raise NotImplementedError

    def gridlines(self, *args, **kwargs):
        """
        Plot gridlines on the Subplot.

        NOTE: This method is not implemented on Subplots, but may be available
        on subclasses such as :class:`earthkit.plots.core.maps.Map`.
        """
        raise NotImplementedError

    def _compute_quantiles(
        self,
        data,
        x="auto",
        dim=None,
        quantiles=None,
        style=None,
        units=None,
        xunits=None,
        yunits=None,
    ):
        """
        Compute quantiles along a specified dimension with unit conversion.

        This is a private helper method that handles data validation, unit conversion,
        and quantile computation. It returns all necessary data for visualization
        methods like boxenplot() and envelopes().

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to process. Will be automatically squeezed.
        x : str, optional
            The dimension to use for the x-axis. Default is "auto".
        dim : str, optional
            The dimension along which to compute quantiles. If None, uses left-most dimension.
        quantiles : list of float, optional
            Quantile values to compute. Default is [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1].
        style : earthkit.plots.styles.Style, optional
            The Style to use for colors and units.
        units : str, optional
            Target units for the data values (y-axis).
        xunits : str, optional
            Target units for the x-axis values.
        yunits : str, optional
            Target units for the y-axis values. Takes precedence over `units`.

        Returns
        -------
        dict
            Dictionary containing:
            - quantile_data: xarray.DataArray with computed quantiles
            - x_values: array of x-axis values
            - x_dim: name of x dimension
            - q_values: 2D array of quantile values (n_quantiles, n_x_points)
            - base_color: color extracted from style
            - pairs: list of (lower_idx, upper_idx) tuples for quantile pairs
            - median_idx: index of median quantile (None if even number of quantiles)
            - n_quantiles: number of quantiles
            - target_xunits: target units for x-axis
            - target_yunits: target units for y-axis
            - target_units: general target units
            - representative_data: 1D data for dimension set creation
            - style: processed style object
        """
        import xarray as xr
        xr.set_options(keep_attrs=True)

        # Import needed functions early to avoid shadowing issues
        from earthkit.plots.core.extractors import _infer_plot_type_from_subplot, _ensure_style_from_kwargs
        from earthkit.plots.sources import get_dimension_set
        from earthkit.plots.sources.core import PlotType

        # Default quantiles
        if quantiles is None:
            quantiles = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]

        # Validate quantiles
        quantiles = sorted(quantiles)
        if not all(0 <= q <= 1 for q in quantiles):
            raise ValueError("All quantiles must be between 0 and 1")

        # Ensure we have a DataArray
        if isinstance(data, xr.Dataset):
            # Get the first data variable
            data_vars = [v for v in data.data_vars if data[v].ndim > 0]
            if len(data_vars) == 0:
                raise ValueError("Dataset has no multi-dimensional data variables")
            if len(data_vars) > 1:
                raise ValueError(
                    f"Dataset has multiple data variables: {data_vars}. "
                    f"Please select one explicitly (e.g., ds['variable_name'])"
                )
            data = data[data_vars[0]]

        # Auto-squeeze dimensions of size 1
        data = data.squeeze()

        # Configure units based on style if provided
        style, _ = _ensure_style_from_kwargs(style, {})

        # Set target units on the data dimension (y-axis for quantile plots)
        # Priority: explicit parameter > style units > no conversion
        target_units = units
        target_xunits = xunits
        target_yunits = yunits

        if style is not None:
            if target_units is None and hasattr(style, '_units'):
                target_units = style._units

        # Determine the dimension to compute quantiles over first
        # We need this to know which dimension to slice for unit conversion
        if dim is None:
            # Use the left-most (first) dimension
            if len(data.dims) < 2:
                raise ValueError(
                    f"Data must have at least 2 dimensions for quantile plotting. "
                    f"Got {len(data.dims)} dimension(s): {list(data.dims)}. "
                    f"After squeezing, need one dimension for quantiles and one for x-axis."
                )
            dim = data.dims[0]
        elif dim not in data.dims:
            raise ValueError(
                f"Dimension '{dim}' not found in data. Available dimensions: {list(data.dims)}"
            )

        # For quantile plots, the y-axis contains the data values
        # Apply unit conversion to the raw data before computing quantiles
        if target_yunits is not None or target_units is not None:
            y_target_units = target_yunits or target_units

            # Use earthkit's unit conversion if available
            # For 2D data, we need to create a 1D slice to get the dimension for conversion
            if len(data.dims) >= 2:
                # Get plot type from subplot
                plot_type_enum = _infer_plot_type_from_subplot(self, is_1d=True)

                # Create a 1D slice to extract units metadata
                # Slice along the quantile dimension (dim), keeping the x-axis dimension
                data_slice = data.isel({dim: 0})

                temp_dimension_set = get_dimension_set(
                    data_slice,
                    plot_type=plot_type_enum,
                    x="auto",
                    y="auto",
                    z=None,
                )

                # Check if we have a y dimension with unit conversion capability
                if hasattr(temp_dimension_set, 'y') and temp_dimension_set.y is not None:
                    # Get original values before conversion
                    original_values = temp_dimension_set.y._values

                    # Set target units - this will trigger conversion when we access .values
                    temp_dimension_set.y.set_target_units(y_target_units)

                    # Get converted values - the .values property handles conversion automatically
                    converted_values_1d = temp_dimension_set.y.values

                    # Check if conversion actually happened
                    if converted_values_1d is not original_values and not np.array_equal(converted_values_1d, original_values):
                        # Conversion happened, compute scale factor and offset from the 1D conversion
                        # Use linear regression to find scale and offset: converted = original * scale + offset
                        # For temperature conversions like K to C, this captures the relationship
                        if len(original_values) > 1:
                            # Use two points to compute scale and offset
                            scale_factor = (converted_values_1d[1] - converted_values_1d[0]) / (original_values[1] - original_values[0])
                            offset = converted_values_1d[0] - scale_factor * original_values[0]
                        else:
                            # Single value - assume additive offset only
                            scale_factor = 1.0
                            offset = converted_values_1d[0] - original_values[0]

                        # Apply the same conversion to the full 2D data
                        converted_values = data.values * scale_factor + offset
                        data = xr.DataArray(
                            converted_values,
                            dims=data.dims,
                            coords=data.coords,
                            attrs=data.attrs
                        )

        # Compute quantiles along the specified dimension
        quantile_data = data.quantile(quantiles, dim=dim)

        # After quantile computation, we should have a 'quantile' dimension
        # and the remaining dimension(s) for plotting
        remaining_dims = [d for d in quantile_data.dims if d != 'quantile']

        if len(remaining_dims) == 0:
            raise ValueError(
                f"After computing quantiles and squeezing, no dimensions remain for x-axis. "
                f"Original dimensions: {list(data.dims)}"
            )
        elif len(remaining_dims) > 1:
            raise ValueError(
                f"After computing quantiles, multiple dimensions remain: {remaining_dims}. "
                f"Please squeeze or select data to have only one remaining dimension."
            )

        # Get x values
        x_dim = remaining_dims[0]
        if x == "auto":
            x_values = quantile_data[x_dim].values
        else:
            # User specified x coordinate
            if x in quantile_data.coords:
                x_values = quantile_data[x].values
            else:
                raise ValueError(f"Coordinate '{x}' not found in data")

        # Get the quantile values as a 2D array: (n_quantiles, n_x_points)
        q_values = quantile_data.values

        # Configure style for colors
        if style is None:
            # Use a default blue color scheme
            base_color = 'steelblue'
        else:
            # Try to get color from style
            if hasattr(style, '_colors') and style._colors:
                if isinstance(style._colors, str):
                    base_color = style._colors
                elif hasattr(style._colors, '__iter__'):
                    base_color = style._colors[0] if len(style._colors) > 0 else 'steelblue'
                else:
                    base_color = 'steelblue'
            else:
                base_color = 'steelblue'

        # Plot quantile bands symmetrically
        # Pair quantiles from outside to inside: (0, 1), (0.1, 0.9), (0.25, 0.75), etc.
        n_quantiles = len(quantiles)

        # Find pairs and the median
        pairs = []
        median_idx = None

        for i in range(n_quantiles // 2):
            pairs.append((i, n_quantiles - 1 - i))

        # Check if there's a median (odd number of quantiles)
        if n_quantiles % 2 == 1:
            median_idx = n_quantiles // 2

        # Create representative data for dimension set creation
        median_or_first_idx = median_idx if median_idx is not None else n_quantiles // 2
        representative_data = quantile_data.isel(quantile=median_or_first_idx)

        return {
            'quantile_data': quantile_data,
            'x_values': x_values,
            'x_dim': x_dim,
            'q_values': q_values,
            'base_color': base_color,
            'pairs': pairs,
            'median_idx': median_idx,
            'n_quantiles': n_quantiles,
            'target_xunits': target_xunits,
            'target_yunits': target_yunits,
            'target_units': target_units,
            'representative_data': representative_data,
            'style': style,
        }

    def boxenplot(
        self,
        data,
        x="auto",
        dim=None,
        quantiles=None,
        style=None,
        label=None,
        color=None,
        units=None,
        xunits=None,
        yunits=None,
        **kwargs
    ):
        """
        Plot a boxenplot (letter-value plot) from multi-dimensional quantile data.

        A boxenplot visualizes quantiles as stacked boxes with varying widths, where
        inner quantiles have wider boxes to show the distribution shape. The outermost
        quantile pair (min-max) is shown as a line. Boxes use solid colors with a gradient
        from light (outer) to dark (inner) shades. This is useful for ensemble forecasts,
        uncertainty visualization, or distribution analysis.

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to plot. Will be automatically squeezed to remove size-1 dimensions.
        x : str, optional
            The dimension to use for the x-axis. Default is "auto" (uses the remaining
            dimension after quantile computation).
        dim : str, optional
            The dimension along which to compute quantiles (e.g., 'number' for ensemble members).
            If None, uses the left-most dimension.
        quantiles : list of float, optional
            Quantile values to compute, as fractions between 0 and 1.
            Default is [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1].
            Quantiles are paired symmetrically (e.g., 0.1-0.9, 0.25-0.75).
        style : earthkit.plots.styles.Style, optional
            The Style to use for colors. If None, uses default styling.
        label : str, optional
            Label for the legend. Can contain format placeholders like "{variable_name}".
        color : str or tuple, optional
            Color for the darkest (innermost) box. If None, uses matplotlib's color cycle
            to automatically assign colors. This allows multiple boxenplots on the same axes
            to have different colors. Can be any valid matplotlib color specification.
        units : str, optional
            Target units for the data values (y-axis). If specified, data will be
            automatically converted from source units to target units.
        xunits : str, optional
            Target units for the x-axis values.
        yunits : str, optional
            Target units for the y-axis values. Takes precedence over `units`.
        **kwargs
            Additional keyword arguments. Supports `boxprops` for styling the boxes.
            boxprops : dict, optional
                Dictionary of properties for the box rectangles. Can include:
                - 'edgecolor': Color of box outlines (default: 'black')
                - 'linewidth': Width of box outlines (default: 0.5)
                - 'linestyle': Style of box outlines (default: 'solid')

        Returns
        -------
        list of matplotlib artists
            List of matplotlib artists (Lines and Rectangles) for each quantile band.

        Examples
        --------
        >>> # Ensemble forecast visualization with automatic colors
        >>> chart = Chart()
        >>> chart.boxenplot(ensemble_data, dim='number')
        >>> chart.xlabel()
        >>> chart.ylabel()
        >>> chart.show()

        >>> # Custom color
        >>> chart.boxenplot(data, dim='member', color='steelblue')

        >>> # Multiple boxenplots with automatic color cycling
        >>> chart.boxenplot(data1, dim='member', label='Forecast 1')
        >>> chart.boxenplot(data2, dim='member', label='Forecast 2')  # Different color

        >>> # Custom box styling with boxprops
        >>> chart.boxenplot(data, dim='member', color='steelblue',
        ...                 boxprops={'edgecolor': 'navy', 'linewidth': 1.0})
        """
        # Compute quantiles
        result = self._compute_quantiles(
            data, x=x, dim=dim, quantiles=quantiles, style=style,
            units=units, xunits=xunits, yunits=yunits
        )

        # Extract results
        quantile_data = result['quantile_data']
        x_values = result['x_values']
        x_dim = result['x_dim']
        q_values = result['q_values']
        base_color = result['base_color']
        pairs = result['pairs']
        median_idx = result['median_idx']
        n_quantiles = result['n_quantiles']
        target_xunits = result['target_xunits']
        target_yunits = result['target_yunits']
        target_units = result['target_units']
        representative_data = result['representative_data']
        style = result['style']

        # Boxenplot style: letter-value plot with varying box widths
        # Inner quantiles get wider boxes to show distribution shape
        from matplotlib.patches import Rectangle
        from matplotlib.colors import to_rgb, to_hex
        import numpy as np

        mappables = []

        # Extract boxprops from kwargs
        boxprops = kwargs.pop('boxprops', {})

        # Set default box styling
        edge_color = boxprops.get('edgecolor', 'black')
        edge_linewidth = boxprops.get('linewidth', 0.5)
        edge_linestyle = boxprops.get('linestyle', 'solid')

        # Determine the base color
        # If color is explicitly provided, use it. Otherwise use matplotlib's color cycle
        if color is not None:
            plot_color = color
        elif style is not None and hasattr(style, '_colors') and style._colors:
            # Use color from style if available
            if isinstance(style._colors, str):
                plot_color = style._colors
            elif hasattr(style._colors, '__iter__'):
                plot_color = style._colors[0] if len(style._colors) > 0 else None
            else:
                plot_color = None
        else:
            plot_color = None

        # If no color specified, get next color from matplotlib's cycle
        if plot_color is None:
            # Get the next color from the axis's color cycle
            plot_color = self.ax._get_lines.get_next_color()

        # Calculate the spacing between x positions
        if len(x_values) > 1:
            # Use the minimum spacing between consecutive x values
            if np.issubdtype(x_values.dtype, np.datetime64):
                # Convert to numeric for spacing calculation
                from matplotlib.dates import date2num
                x_numeric = date2num(x_values)
                x_spacing = np.min(np.diff(x_numeric))
            else:
                x_spacing = np.min(np.diff(x_values))
        else:
            x_spacing = 1.0

        # Base box width (as fraction of x_spacing)
        base_width = 0.6 * x_spacing

        # For each x position, draw boxes for each quantile pair
        for x_idx, x_val in enumerate(x_values):
            # Use x_val directly (matplotlib handles datetime conversion)
            x_pos = x_val

            # Draw boxes for each quantile pair (from outside to inside)
            for pair_idx, (lower_idx, upper_idx) in enumerate(pairs):
                # Width decreases as we go inward (reverse of typical letter-value plot)
                # Outermost band (min-max) is narrowest, innermost is widest
                width_factor = (pair_idx + 1) / len(pairs)
                box_width = base_width * width_factor

                # Get the y-values for this quantile pair at this x position
                y_lower = q_values[lower_idx, x_idx]
                y_upper = q_values[upper_idx, x_idx]
                box_height = y_upper - y_lower

                # Calculate color: widest box (innermost, largest pair_idx) is darkest
                # narrowest box (outermost, smallest pair_idx) is lightest
                if pair_idx == 0:
                    # Outermost box (min-max): draw as a line instead
                    # Use the same color as box edges for consistency
                    # Use zorder=1 to ensure it appears behind the boxes
                    if np.issubdtype(x_values.dtype, np.datetime64):
                        from matplotlib.dates import date2num
                        x_pos_numeric = date2num(x_pos)
                        # Draw vertical line from min to max
                        line = self.ax.plot(
                            [x_pos_numeric, x_pos_numeric],
                            [y_lower, y_upper],
                            color=edge_color,
                            linewidth=edge_linewidth,
                            linestyle=edge_linestyle,
                            alpha=1.0,
                            zorder=1,
                        )
                    else:
                        # Draw vertical line from min to max
                        line = self.ax.plot(
                            [x_pos, x_pos],
                            [y_lower, y_upper],
                            color=edge_color,
                            linewidth=edge_linewidth,
                            linestyle=edge_linestyle,
                            alpha=1.0,
                            zorder=1,
                        )

                    if x_idx == 0:
                        mappables.extend(line)
                else:
                    # For other boxes, create lighter shades
                    # pair_idx goes from 1 to len(pairs)-1
                    # Create gradient from light (outer) to dark (inner)
                    # Normalize pair_idx (excluding the first pair which is a line)
                    normalized_idx = (pair_idx - 1) / max(1, len(pairs) - 2)

                    # Convert base color to RGB
                    rgb = to_rgb(plot_color)

                    # Create lighter shade by blending with white
                    # Outer boxes are lighter (more white), inner boxes are darker (less white)
                    # lightness_factor: 0.0 = full color (darkest), 1.0 = white (lightest)
                    lightness_factor = 0.4 * (1.0 - normalized_idx)  # 0.7 = max lightness for outermost

                    # Blend with white
                    box_color = tuple(c * (1 - lightness_factor) + lightness_factor for c in rgb)

                    # Create a rectangle for this box
                    # For datetime, we need to use date2num for the position
                    # Use zorder=2 to ensure boxes appear above the range line
                    if np.issubdtype(x_values.dtype, np.datetime64):
                        from matplotlib.dates import date2num
                        x_pos_numeric = date2num(x_pos)
                        rect = Rectangle(
                            (x_pos_numeric - box_width/2, y_lower),
                            box_width,
                            box_height,
                            facecolor=box_color,
                            edgecolor=edge_color,
                            alpha=1.0,
                            linewidth=edge_linewidth,
                            linestyle=edge_linestyle,
                            zorder=2,
                        )
                    else:
                        rect = Rectangle(
                            (x_pos - box_width/2, y_lower),
                            box_width,
                            box_height,
                            facecolor=box_color,
                            edgecolor=edge_color,
                            alpha=1.0,
                            linewidth=edge_linewidth,
                            linestyle=edge_linestyle,
                            zorder=2,
                        )
                    self.ax.add_patch(rect)

                    # Only add the first rectangle to mappables for layer tracking
                    if x_idx == 0 and pair_idx == 1:
                        mappables.append(rect)

            # Draw median line at this x position if it exists
            if median_idx is not None:
                y_median = q_values[median_idx, x_idx]
                if np.issubdtype(x_values.dtype, np.datetime64):
                    from matplotlib.dates import date2num
                    x_pos_numeric = date2num(x_pos)
                    median_line = self.ax.plot(
                        [x_pos_numeric - base_width/2, x_pos_numeric + base_width/2],
                        [y_median, y_median],
                        color='white',
                        linewidth=1.5,
                        alpha=0.9,
                        zorder=10,
                    )
                else:
                    median_line = self.ax.plot(
                        [x_pos - base_width/2, x_pos + base_width/2],
                        [y_median, y_median],
                        color='white',
                        linewidth=1.5,
                        alpha=0.9,
                        zorder=10,
                    )
                if x_idx == 0:
                    mappables.extend(median_line)

        # Update axis limits to include all boxes
        # For datetime axes, explicitly set the x-limits
        if np.issubdtype(x_values.dtype, np.datetime64):
            from matplotlib.dates import date2num
            x_numeric = date2num(x_values)
            margin = base_width
            self.ax.set_xlim(x_numeric[0] - margin, x_numeric[-1] + margin)
        else:
            margin = base_width
            self.ax.set_xlim(x_values[0] - margin, x_values[-1] + margin)

        # Let matplotlib autoscale the y-axis
        self.ax.autoscale_view(scalex=False, scaley=True)

        # Create a layer for this plot
        from earthkit.plots.sources import get_dimension_set
        from earthkit.plots.sources.core import PlotType

        dimension_set = get_dimension_set(
            representative_data,
            plot_type=PlotType.CARTESIAN_1D,
            x=x_dim if x == "auto" else x,
            y="auto",
            z=None,
        )

        # Set target units on the dimension set if specified
        if target_yunits is not None or target_units is not None:
            y_target_units = target_yunits or target_units
            if hasattr(dimension_set, 'y') and dimension_set.y is not None:
                dimension_set.y.set_target_units(y_target_units)

        if target_xunits is not None:
            if hasattr(dimension_set, 'x') and dimension_set.x is not None:
                dimension_set.x.set_target_units(target_xunits)

        # Track axis units for proper label formatting
        axis_units = {}
        if target_xunits is not None:
            axis_units["x"] = target_xunits
        if target_yunits is not None or target_units is not None:
            axis_units["y"] = target_yunits or target_units

        layer = Layer(
            dimension_set=dimension_set,
            mappable=mappables,
            subplot=self,
            style=style,
            axis_units=axis_units,
        )

        # Handle label
        if label is not None:
            formatted_label = layer.format_string(label)
            # Set label on the first (outermost) band
            if mappables:
                mappables[0].set_label(formatted_label)

        self.layers.append(layer)

        return mappables

    def envelopes(
        self,
        data,
        x="auto",
        dim=None,
        quantiles=None,
        style=None,
        label=None,
        alpha=0.3,
        units=None,
        xunits=None,
        yunits=None,
        **kwargs
    ):
        """
        Plot quantile envelopes (fan chart) from multi-dimensional data.

        Envelopes visualize quantiles as simple filled regions between quantile pairs
        with uniform transparency, creating a fan chart effect. This is useful for
        ensemble forecasts, uncertainty visualization, or distribution analysis.

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to plot. Will be automatically squeezed to remove size-1 dimensions.
        x : str, optional
            The dimension to use for the x-axis. Default is "auto" (uses the remaining
            dimension after quantile computation).
        dim : str, optional
            The dimension along which to compute quantiles (e.g., 'number' for ensemble members).
            If None, uses the left-most dimension.
        quantiles : list of float, optional
            Quantile values to compute, as fractions between 0 and 1.
            Default is [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1].
            Quantiles are paired symmetrically (e.g., 0.1-0.9, 0.25-0.75).
        style : earthkit.plots.styles.Style, optional
            The Style to use for colors. If None, uses default styling.
        label : str, optional
            Label for the legend. Can contain format placeholders like "{variable_name}".
        alpha : float, optional
            Transparency level for the filled quantile bands. Default is 0.3.
        units : str, optional
            Target units for the data values (y-axis). If specified, data will be
            automatically converted from source units to target units.
        xunits : str, optional
            Target units for the x-axis values.
        yunits : str, optional
            Target units for the y-axis values. Takes precedence over `units`.
        **kwargs
            Additional keyword arguments passed to matplotlib's fill_between.

        Returns
        -------
        list of matplotlib artists
            List of matplotlib artists (PolyCollections and Lines) for each quantile band.

        Examples
        --------
        >>> # Ensemble forecast visualization with envelopes
        >>> chart = Chart()
        >>> chart.envelopes(ensemble_data, dim='number')
        >>> chart.xlabel()
        >>> chart.ylabel()
        >>> chart.show()

        >>> # Custom quantiles and transparency
        >>> chart.envelopes(data, dim='member', quantiles=[0, 0.25, 0.5, 0.75, 1], alpha=0.5)
        """
        # Compute quantiles
        result = self._compute_quantiles(
            data, x=x, dim=dim, quantiles=quantiles, style=style,
            units=units, xunits=xunits, yunits=yunits
        )

        # Extract results
        quantile_data = result['quantile_data']
        x_values = result['x_values']
        x_dim = result['x_dim']
        q_values = result['q_values']
        base_color = result['base_color']
        pairs = result['pairs']
        median_idx = result['median_idx']
        n_quantiles = result['n_quantiles']
        target_xunits = result['target_xunits']
        target_yunits = result['target_yunits']
        target_units = result['target_units']
        representative_data = result['representative_data']
        style = result['style']

        # Envelope style: simple filled regions between quantile pairs
        mappables = []
        for i, (lower_idx, upper_idx) in enumerate(pairs):
            # Constant alpha for envelope style
            band_alpha = alpha

            fill = self.ax.fill_between(
                x_values,
                q_values[lower_idx, :],
                q_values[upper_idx, :],
                alpha=band_alpha,
                color=base_color,
                edgecolor='none',
                **kwargs
            )
            mappables.append(fill)

        # Plot median line
        if median_idx is not None:
            line = self.ax.plot(
                x_values,
                q_values[median_idx, :],
                color=base_color,
                linewidth=2,
                alpha=0.9,
            )
            mappables.extend(line)

        # Create a layer for this plot
        from earthkit.plots.sources import get_dimension_set
        from earthkit.plots.sources.core import PlotType

        dimension_set = get_dimension_set(
            representative_data,
            plot_type=PlotType.CARTESIAN_1D,
            x=x_dim if x == "auto" else x,
            y="auto",
            z=None,
        )

        # Set target units on the dimension set if specified
        if target_yunits is not None or target_units is not None:
            y_target_units = target_yunits or target_units
            if hasattr(dimension_set, 'y') and dimension_set.y is not None:
                dimension_set.y.set_target_units(y_target_units)

        if target_xunits is not None:
            if hasattr(dimension_set, 'x') and dimension_set.x is not None:
                dimension_set.x.set_target_units(target_xunits)

        # Track axis units for proper label formatting
        axis_units = {}
        if target_xunits is not None:
            axis_units["x"] = target_xunits
        if target_yunits is not None or target_units is not None:
            axis_units["y"] = target_yunits or target_units

        layer = Layer(
            dimension_set=dimension_set,
            mappable=mappables,
            subplot=self,
            style=style,
            axis_units=axis_units,
        )

        # Handle label
        if label is not None:
            formatted_label = layer.format_string(label)
            # Set label on the first (outermost) band
            if mappables:
                mappables[0].set_label(formatted_label)

        self.layers.append(layer)

        return mappables

    @plot_1d("plot")
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
        labels = DimensionSetFormatter(source).format(label)
        for label, x, y in zip(labels, source.x_values, source.y_values):
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

    def quickplot(self, data, style="auto", units=None, **kwargs):
        """
        Generate a convenient plot from the given data using automatic style detection.

        This method automatically determines the appropriate plotting method and style
        based on the data's metadata (paramId, shortName, standard_name, etc.).

        Parameters
        ----------
        data : xarray.DataArray, earthkit.data object, or array-like
            The data to be plotted. Can be a single data object or field.
        style : str, Style, or list of str, optional
            The style(s) to use for plotting. Default is "auto" which automatically
            matches styles based on data metadata. Can be:
            - "auto" (default): Automatic style detection
            - A style name string (e.g., "MEAN_SEA_LEVEL_PRESSURE_IN_HPA")
            - A Style object
            - A list of style names for multi-layer plotting
        units : str, optional
            Units to convert the data to.
        **kwargs : dict
            Additional arguments passed to the underlying plot method.

        Returns
        -------
        The result of the plotting method (typically a matplotlib artist or Layer).

        Examples
        --------
        >>> chart = ek.plots.Map()
        >>> chart.quickplot(data)  # Auto-detects style and method

        >>> # Use a specific style
        >>> chart.quickplot(data, style="RIVER_DISCHARGE_EUROPE_IN_M3_S-1")

        >>> # Multi-layer plotting
        >>> chart.quickplot(data, style=["PRESSURE_CONTOUR", "WIND_BARBS"])

        Notes
        -----
        The `auto_style` parameter is always True for quickplot and cannot be disabled.
        """
        from earthkit.plots import styles as ekp_styles
        from earthkit.plots.styles import Style

        # Ensure auto_style is always True for quickplot
        if not kwargs.pop("auto_style", True):
            warnings.warn("`auto_style` cannot be switched off for `quickplot`.")

        # Handle multiple styles (list of style names)
        if isinstance(style, list):
            # Multi-layer plotting: apply each style in sequence
            results = []
            for style_item in style:
                result = self.quickplot(data, style=style_item, units=units, **kwargs)
                results.append(result)
            return results

        # Resolve style to a Style object (handles "auto", style names, or Style objects)
        from earthkit.plots.sources import get_dimension_set

        # Get dimension set to pass for auto-matching
        dimension_set = get_dimension_set(data)

        # Resolve the style
        from earthkit.plots.styles.utils import resolve_style
        resolved_style = resolve_style(style, data=dimension_set, auto_style=(style == "auto"))

        # Handle CompositeStyle - plot each component style in sequence
        from earthkit.plots.styles import CompositeStyle
        if isinstance(resolved_style, CompositeStyle):
            results = []
            for component_style in resolved_style.styles:
                # Plot this component with its own plot_type
                if component_style.plot_type:
                    method_name = component_style.plot_type
                else:
                    method_name = "grid_cells"

                try:
                    method = getattr(self, method_name)
                except AttributeError:
                    warnings.warn(
                        f"Plot method '{method_name}' not found. Falling back to 'grid_cells'."
                    )
                    method = self.grid_cells

                # Set default zorder based on method
                zorder = LAYER_ZORDERS.get(method_name, 10)
                component_kwargs = kwargs.copy()
                component_kwargs.setdefault("zorder", zorder)

                # Call the plotting method with this component style
                result = method(data, style=component_style, units=units, **component_kwargs)
                results.append(result)
            return results

        # Single style - determine which plotting method to use
        if resolved_style is not None and hasattr(resolved_style, 'plot_type') and resolved_style.plot_type:
            # Use the plot_type from the style
            method_name = resolved_style.plot_type
        else:
            # Fallback to grid_cells if no style or plot_type
            method_name = "grid_cells"

        # Get the method from self
        try:
            method = getattr(self, method_name)
        except AttributeError:
            warnings.warn(
                f"Plot method '{method_name}' not found. Falling back to 'grid_cells'."
            )
            method = self.grid_cells

        # Set default zorder based on method
        zorder = LAYER_ZORDERS.get(method_name, 10)
        kwargs.setdefault("zorder", zorder)

        # Call the plotting method with the resolved style
        return method(data, style=resolved_style, units=units, **kwargs)

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

    @plot_1d()
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
    @plot_1d_or_2d()
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
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to use for coloring the scatter points. If None, points
            will not be colored. If data is provided, this is assumed to be the
            name of a variable in the data.
        style : earthkit.plots.styles.Style, optional
            The Style to use for the scatter plot. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.scatter`.
        """

    @plot_2d(extract_domain=True)
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

    @plot_2d(extract_domain=True)
    def imshow(self, *args, **kwargs):
        """
        Plot an image on the Subplot.

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
            The Style to use for the image. If None, a Style is automatically
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
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.imshow`.
        """

    @schema.contour.apply()
    @plot_2d(extract_domain=True)
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
        labels : bool, optional
            If True, add labels to the contour lines showing their values. Default is False.
            This parameter can also be included in Style definitions.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.contour`.
        """

    @schema.contourf.apply()
    @plot_2d(extract_domain=True)
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

    @plot_2d()
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

    @plot_2d()
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

    @plot_2d()
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

    def grid_cells(
        self,
        *args,
        x="auto",
        y="auto",
        z="auto",
        style=None,
        every=None,
        auto_style=False,
        label=None,  # Default to None, will be converted to auto-generated label
        **kwargs,
    ):
        """
        Plot data using grid-specific cell visualization or standard pcolormesh.

        This method automatically detects specialized grid types (HEALPix, octahedral)
        and delegates to their grid-specific plotting methods. For regular grids,
        it falls back to standard pcolormesh.

        Parameters
        ----------
        data : list, numpy.ndarray, xarray.DataArray, or earthkit.data.core.Base, optional
            The data to plot. If None, x, y, and z must be provided.
        x : str, list, numpy.ndarray, or xarray.DataArray, optional
            The x values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If "auto" (default), coordinates are
            inferred from data.
        y : str, list, numpy.ndarray, or xarray.DataArray, optional
            The y values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If "auto" (default), coordinates are
            inferred from data.
        z : str, list, numpy.ndarray, or xarray.DataArray, optional
            The z values to plot. If data is provided, this is assumed to be the
            name of a coordinate in the data. If "auto" (default), values are
            inferred from data.
        style : earthkit.plots.styles.Style, optional
            The Style to use for plotting. If None, a Style is automatically
            generated based on the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to
            understand the units of your input data.
        every : int, optional
            Sampling interval for data reduction.
        auto_style : bool, default=False
            Whether to automatically guess the appropriate style.
        label : str, optional
            The label to use for the legend. If None (default), an automatic label
            will be generated.
        **kwargs
            Additional keyword arguments to pass to the underlying plotting method.
            Note: 'regrid' parameter is not supported and will raise an error.

        Returns
        -------
        mappable
            The matplotlib mappable object (artist) created by the plot.

        Raises
        ------
        ValueError
            If the 'regrid' parameter is passed. Use pcolormesh() or contourf()
            for regridding support.

        Examples
        --------
        >>> # Automatically plot HEALPix data with grid cells
        >>> chart.grid_cells(healpix_data)

        >>> # Plot octahedral grid data
        >>> chart.grid_cells(octahedral_data, style=style)

        >>> # Falls back to pcolormesh for regular grids
        >>> chart.grid_cells(regular_data)
        """
        # Sentinel value to distinguish "not provided" from "explicitly None"
        _LABEL_AUTO = object()

        # If label was not provided (is None), use sentinel
        # This allows us to distinguish between label=None (explicitly passed)
        # and label not provided at all
        label_sentinel = _LABEL_AUTO if label is None else label

        # Check for regrid parameter and raise error
        if 'regrid' in kwargs:
            raise ValueError(
                "The 'regrid' parameter is not compatible with grid_cells(). "
                "The grid_cells method is designed to show the exact grid cells "
                "in your data without any regridding. If you need regridding, "
                "please use pcolormesh() or contourf() instead."
            )

        # Convert sentinel to None for extract_plottables_2d
        label_for_extraction = None if label_sentinel is _LABEL_AUTO else label_sentinel

        # Get processed data and kwargs from extract_plottables_2d
        x_values, y_values, z_values, plot_kwargs = extract_plottables_2d(
            self,
            "grid_cells",  # Use grid_cells to trigger special handling
            args=args,
            x=x,
            y=y,
            z=z,
            style=style,
            every=every,
            auto_style=auto_style,
            extract_domain=False,  # Don't extract domain for grid cells
            regrid=False,  # Never regrid for grid_cells
            label=label_for_extraction,
            **kwargs,
        )

        # Extract metadata (keys starting with _) for layer creation
        dimension_set = plot_kwargs.pop('_dimension_set')
        plot_style = plot_kwargs.pop('_style')
        primary_axis = plot_kwargs.pop('_primary_axis')
        units = plot_kwargs.pop('_units')
        xunits = plot_kwargs.pop('_xunits')
        yunits = plot_kwargs.pop('_yunits')
        is_specialized = plot_kwargs.pop('_is_specialized')
        actual_method_name = plot_kwargs.pop('_method_name')
        no_style = plot_kwargs.pop('_no_style')
        plot_label = plot_kwargs.pop('_label')
        grid_cells_callable = plot_kwargs.pop('_grid_cells_callable', None)

        # Try to use specialized grid_cells method if available
        mappable = None
        if grid_cells_callable is not None:
            # Delegate to the GridIdentifier's grid_cells method
            mappable = grid_cells_callable(
                self, dimension_set, z_values, plot_style, actual_method_name, plot_kwargs
            )

        # Fall back to standard pcolormesh if no specialized grid was handled
        if mappable is None:
            # Handle interpolation if requested
            if not no_style and 'interpolate' in plot_kwargs:
                from earthkit.plots.core.extractors import plot_with_interpolation
                mappable = plot_with_interpolation(
                    self,
                    plot_style,
                    "pcolormesh",
                    x_values,
                    y_values,
                    z_values,
                    getattr(self, 'crs', None),
                    plot_kwargs,
                )
            else:
                # Call matplotlib pcolormesh directly
                mappable = self.ax.pcolormesh(x_values, y_values, z_values, **plot_kwargs)

        # Create and store layer
        from earthkit.plots.core.layers import Layer
        axis_units = {}
        if xunits is not None:
            axis_units["x"] = xunits
        if yunits is not None:
            axis_units["y"] = yunits
        if units is not None and primary_axis not in axis_units:
            axis_units[primary_axis] = units

        layer = Layer(
            dimension_set=dimension_set,
            mappable=mappable,
            subplot=self,
            style=plot_style,
            axis_units=axis_units,
        )

        # Handle label for legend
        # Distinguish between:
        # - label not provided (_LABEL_AUTO) → use default "{variable_name} ({units})"
        # - label=None explicitly → don't show in legend (set to special marker)
        # - label="something" → use that label
        if label_sentinel is _LABEL_AUTO:
            # Default: use variable name with units
            label_to_use = "{variable_name} ({units})"
        elif label_sentinel is None:
            # Explicitly None: mark as excluded from legend
            label_to_use = "_no_legend_"
        else:
            # User-provided label
            label_to_use = label_sentinel

        # Store the label from plot time for later use by legend()
        layer._plot_label = label_to_use

        self.layers.append(layer)

        return mappable

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

    def grid_points(self, *args, regrid=False, z=None, **kwargs):
        """
        Plot grid points using scatter without regridding.

        This method is designed to visualize the original data grid points
        without any interpolation or regridding. It's useful for inspecting
        the native resolution and structure of your data.

        By default, regrid is set to False to preserve the original grid.
        You can override this by explicitly passing regrid=True.

        Parameters
        ----------
        *args
            Positional arguments passed to scatter.
        regrid : bool or Regrid, optional
            Whether to regrid the data. Default is False (no regridding).
            Can be set to True or a Regrid instance to enable regridding.
        **kwargs
            Additional keyword arguments passed to scatter.

        Returns
        -------
        matplotlib.collections.PathCollection
            The PathCollection object representing the plotted points.

        See Also
        --------
        scatter : The underlying plotting method.
        grid_cells : Plot grid cells using pcolormesh.
        """
        default_kwargs = {
            "color": "red",
            "marker": ".",
            "s": 10,
            "edgecolors": "none",
            "label": "{grid} grid points",
        }
        return self.scatter(*args, z=z, regrid=regrid, **{**default_kwargs, **kwargs})

    def legend(self, location='right', label="auto", **kwargs):
        """
        Add legends/colorbars to the Subplot for all unique styles.

        Creates one colorbar for each unique style used in the subplot's layers.
        Layers are grouped by their style's legend key, so layers with visually
        identical styles (same colors, levels, etc.) share a colorbar.

        Parameters
        ----------
        location : str, optional
            The location for the colorbar(s). Valid options are 'right', 'left',
            'top', 'bottom'. Default is 'right'.
        label : str, optional
            Label for the colorbar(s). Default is "auto" which generates a label from
            layer metadata. Can contain format placeholders (e.g., "{units}",
            "{long_name}", etc.) which will be replaced with layer metadata values.
            Use None for no label.
        **kwargs
            Additional keyword arguments passed to each colorbar creation.

        Returns
        -------
        list of matplotlib.colorbar.Colorbar
            List of created colorbars, one for each unique style.

        Examples
        --------
        >>> chart = Chart()
        >>> chart.contourf(temp_data, style=temp_style)
        >>> chart.contourf(precip_data, style=precip_style)
        >>> chart.legend()  # Creates two colorbars with auto-generated labels
        >>> chart.legend(label="{units}")  # Use only units as label
        >>> chart.legend(label="Custom Label")  # Use a fixed label
        >>> chart.legend(label=None)  # No label
        """
        from collections import defaultdict

        # Group layers by their style's legend key
        style_groups = defaultdict(list)

        for layer in self.layers:
            # Skip layers explicitly excluded from legend (label=None at plot time)
            if hasattr(layer, '_plot_label') and layer._plot_label == "_no_legend_":
                continue

            if layer.style is not None:
                legend_key = layer.style.get_legend_key()
                style_groups[legend_key].append(layer)

        # Create a colorbar for each unique style
        colorbars = []
        for legend_key, layers in style_groups.items():
            # Use the first layer as representative
            layer = layers[0]

            # Determine which label to use:
            # - If label provided at legend-time (not "auto"), use it (overrides plot-time label)
            # - Otherwise, use plot-time label if available
            # - Otherwise, use "auto"
            effective_label = label
            if label == "auto" and hasattr(layer, '_plot_label'):
                effective_label = layer._plot_label

            # Create colorbar for this style
            cbar = layer.legend(location=location, label=effective_label, **kwargs)
            colorbars.append(cbar)

        return colorbars

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
