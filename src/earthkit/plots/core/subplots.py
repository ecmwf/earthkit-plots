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


def _darken_color(color, factor=0.25):
    """
    Darken a color by multiplying RGB values by factor.

    Parameters
    ----------
    color : color
        Any matplotlib color specification
    factor : float
        Multiplication factor (0 = black, 1 = original color)
        Default 0.25 = very dark version

    Returns
    -------
    str
        Hex color string
    """
    from matplotlib.colors import to_rgb, to_hex
    rgb = to_rgb(color)
    darkened = tuple(c * factor for c in rgb)
    return to_hex(darkened)


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

        # Multi-axis support for unit-based y-axis management
        # Each entry maps units (str) to (axis, side, offset) tuple
        # side is 'left' for primary axis, 'right' for secondary axes
        # offset is the spine offset for right-side axes (in axes fraction)
        self._yaxes = {}  # {units: (ax, side, offset)}
        self._right_axis_count = 0  # Track number of right-side axes for offset calculation

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

                # Determine which y-axis to use based on units
                # Priority: explicit yunits > explicit units (if y is primary) > actual data units from dimension_set
                if yunits is not None:
                    y_axis_units = yunits
                elif units is not None and primary_axis == 'y':
                    y_axis_units = units
                else:
                    # Extract actual units from the dimension_set (from the data itself)
                    y_axis_units = dimension_set.y.units

                target_ax = self._get_or_create_yaxis(y_axis_units)

                # Call matplotlib method on the appropriate axis
                mpl_method = getattr(target_ax, method_name or method.__name__)
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

    def plot_2d(method_name=None, extract_domain=False, default_reproject_to_target=True):
        """Decorator for 2D plotting methods (contour, pcolormesh)."""
        # Sentinel value to distinguish "not provided" from "explicitly None"
        _LABEL_AUTO = object()
        _REPROJECT_AUTO = object()

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
                reproject_to_target=_REPROJECT_AUTO,
                **kwargs,
            ):
                # Convert sentinels to actual values
                label_for_extraction = None if label is _LABEL_AUTO else label
                reproject_value = default_reproject_to_target if reproject_to_target is _REPROJECT_AUTO else reproject_to_target

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
                    reproject_to_target=reproject_value,
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

    def _get_or_create_yaxis(self, units):
        """
        Get or create a y-axis for the given units.

        This method implements automatic multi-axis support based on unit matching.
        If data has no units (None), it's added to the primary axis. If units match
        an existing axis, that axis is reused. Otherwise, a new axis is created.

        Parameters
        ----------
        units : str or None
            The units for the y-axis. None means unitless data (uses primary axis).

        Returns
        -------
        matplotlib.axes.Axes
            The axis to plot on.

        Notes
        -----
        - First axis is always on the left (primary axis)
        - Subsequent axes are created on the right side using twinx()
        - Multiple right-side axes are spaced 60 points apart to avoid overlap
        - Unit comparison uses metadata.units.are_equal()
        """
        from earthkit.plots.metadata import units as metadata_units

        # Handle unitless data - always use primary axis
        if units is None:
            if None not in self._yaxes:
                # First time: register primary axis
                self._yaxes[None] = (self.ax, 'left', 0)
            return self._yaxes[None][0]

        # Check if we already have an axis for these units (or equivalent units)
        for existing_units, axis_info in self._yaxes.items():
            existing_ax, side, offset = axis_info
            if existing_units is not None and metadata_units.are_equal(units, existing_units):
                return existing_ax

        # Need to create a new axis
        if len(self._yaxes) == 0:
            # First axis - use primary axis on the left
            new_ax = self.ax
            side = 'left'
            offset = 0
        else:
            # Create twin axis on the right
            new_ax = self.ax.twinx()
            side = 'right'

            # Calculate offset for this axis (60 points per additional right axis)
            # This spacing accommodates tick labels and axis labels
            offset = self._right_axis_count * 60

            # Move the spine outward
            new_ax.spines['right'].set_position(('outward', offset))

            # Increment right axis counter
            self._right_axis_count += 1

        # Register this axis with its units
        self._yaxes[units] = (new_ax, side, offset)

        return new_ax

    def ylabel(self, label=None, **kwargs):
        """
        Add y-axis labels to the plot.

        When multiple y-axes exist (due to different units), this method sets
        labels on each axis using the appropriate metadata from the layers
        associated with that axis.

        Parameters
        ----------
        label : str, optional
            Label template string. Can include format placeholders like
            {variable_name} and {units}. Default is "{variable_name} ({units})".
        **kwargs
            Additional keyword arguments passed to ax.set_ylabel().
        """
        label_template = "{variable_name} ({units})" if label is None else label

        # If no multi-axis setup, use simple approach
        if len(self._yaxes) <= 1:
            formatted_label = self.format_string(label_template, axis="y")
            return self.ax.set_ylabel(formatted_label, **kwargs)

        # Multi-axis case: set label on each y-axis using its layers' metadata
        from earthkit.plots.metadata import units as metadata_units

        # Group layers by their y-axis units
        layers_by_units = {}
        for layer in self.layers:
            # Get y-axis units for this layer from the actual data (dimension_set)
            # This is more reliable than axis_units which only has explicitly passed units
            layer_yunits = layer.dimension_set.y.units

            # Find which axis this layer belongs to
            target_units = None
            for registered_units in self._yaxes.keys():
                if layer_yunits is None and registered_units is None:
                    target_units = None
                    break
                elif layer_yunits is not None and registered_units is not None:
                    if metadata_units.are_equal(layer_yunits, registered_units):
                        target_units = registered_units
                        break

            if target_units not in layers_by_units:
                layers_by_units[target_units] = []
            layers_by_units[target_units].append(layer)

        # Set label on each axis using its layers
        results = []
        for units_key, layers_group in layers_by_units.items():
            if units_key in self._yaxes:
                target_ax, side, offset = self._yaxes[units_key]

                # Create a temporary subplot-like object with just these layers for formatting
                # Use SubplotFormatter with filtered layers
                if len(layers_group) > 0:
                    formatted_label = LayerFormatter(layers_group[0], axis="y").format(label_template)
                    result = target_ax.set_ylabel(formatted_label, **kwargs)
                    results.append(result)

        return results if len(results) > 1 else results[0] if results else None

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
            When quantiles=None (pre-computed), this specifies which dimension contains the quantile values.
        quantiles : list of float, "auto", or None, optional
            - If "auto" (default): compute quantiles [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]
            - If list of float: compute these specific quantiles (values between 0 and 1)
            - If None: don't compute quantiles - treat 'dim' as containing pre-computed quantile values.
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

        # Import needed functions early to avoid shadowing issues
        from earthkit.plots.core.extractors import _infer_plot_type_from_subplot, _ensure_style_from_kwargs
        from earthkit.plots.sources import get_dimension_set
        from earthkit.plots.sources.core import PlotType

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

        # PATHWAY DECISION: Pre-computed quantiles OR compute quantiles
        if quantiles is None:
            # ============================================================
            # PRE-COMPUTED QUANTILES PATHWAY
            # ============================================================
            # User is signaling: "dim" contains pre-computed quantile values

            if dim is None:
                raise ValueError(
                    "When quantiles=None (pre-computed quantiles), you must specify "
                    "which dimension contains the quantile values using the 'dim' parameter"
                )

            if dim not in data.dims:
                raise ValueError(
                    f"Quantile dimension '{dim}' not found in data. "
                    f"Available dimensions: {list(data.dims)}"
                )

            # Treat 'dim' as the quantile dimension
            quantile_dim = dim
            quantile_data = data

            # Try to extract quantile values from coordinate
            if dim in data.coords:
                quantile_coord = data.coords[dim].values
                # Check if they look like normalized quantiles (between 0 and 1)
                if all(0 <= q <= 1 for q in quantile_coord):
                    quantiles = sorted(quantile_coord.tolist())
                else:
                    # Not normalized quantiles - could be percentiles (0-100), indices, etc.
                    # Still use them for pairing logic
                    quantiles = sorted(quantile_coord.tolist())
            else:
                # No coordinate - use dimension indices as quantile values
                quantiles = list(range(data.sizes[dim]))

            # Apply unit conversion if needed (on the pre-computed data)
            if target_yunits is not None or target_units is not None:
                y_target_units = target_yunits or target_units

                if len(quantile_data.dims) >= 2:
                    # Get plot type from subplot
                    plot_type_enum = _infer_plot_type_from_subplot(self, is_1d=True)

                    # Create a 1D slice to extract units metadata
                    data_slice = quantile_data.isel({quantile_dim: 0})

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

                        # Set target units
                        temp_dimension_set.y.set_target_units(y_target_units)

                        # Get converted values
                        converted_values_1d = temp_dimension_set.y.values

                        # Check if conversion actually happened
                        if converted_values_1d is not original_values and not np.array_equal(converted_values_1d, original_values):
                            # Compute scale factor and offset
                            if len(original_values) > 1:
                                scale_factor = (converted_values_1d[1] - converted_values_1d[0]) / (original_values[1] - original_values[0])
                                offset = converted_values_1d[0] - scale_factor * original_values[0]
                            else:
                                scale_factor = 1.0
                                offset = converted_values_1d[0] - original_values[0]

                            # Apply conversion to full data, preserving metadata
                            converted_values = quantile_data.values * scale_factor + offset
                            quantile_data = xr.DataArray(
                                converted_values,
                                dims=quantile_data.dims,
                                coords=quantile_data.coords,
                                attrs=quantile_data.attrs
                            )

        else:
            # ============================================================
            # COMPUTE QUANTILES PATHWAY (existing behavior)
            # ============================================================

            # Set default quantiles
            if quantiles == "auto":
                quantiles = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]

            # Validate quantiles
            quantiles = sorted(quantiles)
            if not all(0 <= q <= 1 for q in quantiles):
                raise ValueError("All quantiles must be between 0 and 1")

            # Determine the dimension to compute quantiles over
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

            # Preserve metadata before computing quantiles (Option C)
            attrs_to_preserve = data.attrs.copy()
            coord_attrs = {coord: data.coords[coord].attrs.copy()
                          for coord in data.coords if coord in data.coords}

            # Compute quantiles along the specified dimension
            quantile_data = data.quantile(quantiles, dim=dim)
            quantile_dim = 'quantile'  # xarray always names it 'quantile'

            # Restore attributes
            quantile_data.attrs.update(attrs_to_preserve)
            for coord, attrs in coord_attrs.items():
                if coord in quantile_data.coords:
                    quantile_data.coords[coord].attrs.update(attrs)

        # ============================================================
        # COMMON CODE FOR BOTH PATHWAYS
        # ============================================================

        # After processing, we should have quantile_data with quantile_dim and remaining dimension(s)
        remaining_dims = [d for d in quantile_data.dims if d != quantile_dim]

        if len(remaining_dims) == 0:
            raise ValueError(
                f"After processing quantiles, no dimensions remain for x-axis. "
                f"Data dimensions: {list(quantile_data.dims)}"
            )
        elif len(remaining_dims) > 1:
            raise ValueError(
                f"After processing quantiles, multiple dimensions remain: {remaining_dims}. "
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
            'quantiles': quantiles,
            'target_xunits': target_xunits,
            'target_yunits': target_yunits,
            'target_units': target_units,
            'representative_data': representative_data,
            'style': style,
        }

    def multiboxplot(
        self,
        data,
        x="auto",
        dim=None,
        quantiles="auto",
        style=None,
        label=None,
        color=None,
        units=None,
        xunits=None,
        yunits=None,
        boxprops=None,
        whiskerprops=None,
        medianprops=None,
        capprops=None,
        showcaps=False,
        **kwargs
    ):
        """
        Plot a multiboxplot (letter-value plot) from multi-dimensional quantile data.

        A multiboxplot visualizes quantiles as stacked boxes with varying widths, where
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
            If None, uses the left-most dimension. When quantiles=None (pre-computed quantiles),
            this specifies which dimension contains the quantile values.
        quantiles : list of float, "auto", or None, optional
            - If "auto" (default): compute quantiles [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]
            - If list of float: compute these specific quantiles (values between 0 and 1),
              paired symmetrically (e.g., 0.1-0.9, 0.25-0.75)
            - If None: don't compute quantiles - treat the dimension specified by 'dim' as
              containing pre-computed quantile values. This allows plotting data where quantiles
              have already been calculated.
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
        boxprops : dict, optional
            Dictionary of properties for the box rectangles. Can include:
            - 'edgecolor': Color of box outlines (default: 'black')
            - 'linewidth': Width of box outlines (default: 1.0)
            - 'linestyle': Style of box outlines (default: 'solid')
            - Any other matplotlib Rectangle properties
        whiskerprops : dict, optional
            Dictionary of properties for the whisker/range lines (vertical lines from min to max).
            Can include:
            - 'color': Whisker line color (default: inherits from boxprops['edgecolor'])
            - 'linewidth': Whisker line width (default: inherits from boxprops['linewidth'])
            - 'linestyle': Whisker line style (default: 'solid')
            - Any other matplotlib Line2D properties
        medianprops : dict, optional
            Dictionary of properties for the median line. Can include:
            - 'color': Median line color (default: darkened version of main color parameter)
            - 'linewidth': Median line width (default: 1.5)
            - 'linestyle': Median line style (default: 'solid')
            - 'alpha': Median line transparency (default: 1.0)
            - Any other matplotlib Line2D properties
        capprops : dict, optional
            Dictionary of properties for the cap lines (horizontal lines at whisker ends).
            Can include:
            - 'color': Cap line color (default: inherits from whiskerprops['color'])
            - 'linewidth': Cap line width (default: inherits from whiskerprops['linewidth'])
            - 'linestyle': Cap line style (default: 'solid')
            - 'capwidth': Width of cap as fraction of box width (default: 1.0)
            - Any other matplotlib Line2D properties
        showcaps : bool, optional
            Whether to show horizontal cap lines at the ends of whiskers (default: False).
        **kwargs
            Additional keyword arguments passed to the underlying matplotlib functions.

        Returns
        -------
        list of matplotlib artists
            List of matplotlib artists (Lines and Rectangles) for each quantile band.

        Examples
        --------
        >>> # Ensemble forecast visualization with automatic colors
        >>> chart = Chart()
        >>> chart.multiboxplot(ensemble_data, dim='number')
        >>> chart.xlabel()
        >>> chart.ylabel()
        >>> chart.show()

        >>> # Custom color
        >>> chart.multiboxplot(data, dim='member', color='steelblue')

        >>> # Multiple multiboxplots with automatic color cycling
        >>> chart.multiboxplot(data1, dim='member', label='Forecast 1')
        >>> chart.multiboxplot(data2, dim='member', label='Forecast 2')  # Different color

        >>> # Custom box styling with boxprops
        >>> chart.multiboxplot(data, dim='member', color='steelblue',
        ...                     boxprops={'edgecolor': 'navy', 'linewidth': 1.0})

        >>> # Custom whiskers (different from box edges)
        >>> chart.multiboxplot(data, dim='member', color='steelblue',
        ...                     whiskerprops={'color': 'gray', 'linewidth': 0.8, 'linestyle': '--'})

        >>> # Custom median line
        >>> chart.multiboxplot(data, dim='member', color='steelblue',
        ...                     medianprops={'color': 'red', 'linewidth': 2.0})

        >>> # With caps
        >>> chart.multiboxplot(data, dim='member', showcaps=True,
        ...                     capprops={'capwidth': 0.8})

        >>> # Fully customized
        >>> chart.multiboxplot(data, dim='member', color='#4287f5',
        ...                     boxprops={'edgecolor': 'black', 'linewidth': 0.8},
        ...                     whiskerprops={'color': 'gray', 'linewidth': 0.5},
        ...                     medianprops={'color': 'darkred', 'linewidth': 2.5'},
        ...                     showcaps=True, capprops={'capwidth': 1.0})

        >>> # Pre-computed quantiles (skip quantile computation)
        >>> quantile_data = ensemble_data.quantile([0.1, 0.5, 0.9], dim='member')
        >>> chart.multiboxplot(quantile_data, dim='quantile', quantiles=None)
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
        quantiles = result['quantiles']
        target_xunits = result['target_xunits']
        target_yunits = result['target_yunits']
        target_units = result['target_units']
        representative_data = result['representative_data']
        style = result['style']

        # Multiboxplot style: letter-value plot with varying box widths
        # Inner quantiles get wider boxes to show distribution shape
        from matplotlib.patches import Rectangle
        from matplotlib.colors import to_rgb, to_hex
        import numpy as np

        mappables = []

        # Resolve boxprops with defaults
        boxprops = boxprops or {}
        box_edgecolor = boxprops.get('edgecolor', 'black')
        box_linewidth = boxprops.get('linewidth', 1.0)
        box_linestyle = boxprops.get('linestyle', 'solid')

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

        # Resolve whiskerprops (inherits from boxprops)
        whiskerprops = whiskerprops or {}
        whisker_color = whiskerprops.get('color', box_edgecolor)
        whisker_linewidth = whiskerprops.get('linewidth', box_linewidth)
        whisker_linestyle = whiskerprops.get('linestyle', 'solid')

        # Resolve medianprops (color from darkened main color unless explicitly provided)
        medianprops = medianprops or {}
        if 'color' not in medianprops:
            median_color = _darken_color(plot_color, 0.25)
        else:
            median_color = medianprops['color']
        median_linewidth = medianprops.get('linewidth', 1.5)
        median_linestyle = medianprops.get('linestyle', 'solid')
        median_alpha = medianprops.get('alpha', 1.0)

        # Resolve capprops (inherits from whiskerprops)
        if showcaps:
            capprops = capprops or {}
            cap_color = capprops.get('color', whisker_color)
            cap_linewidth = capprops.get('linewidth', whisker_linewidth)
            cap_linestyle = capprops.get('linestyle', 'solid')
            cap_width_factor = capprops.get('capwidth', 1.0)

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
                    # Outermost box (min-max): draw as a whisker line
                    # Use zorder=1 to ensure it appears behind the boxes
                    if np.issubdtype(x_values.dtype, np.datetime64):
                        from matplotlib.dates import date2num
                        x_pos_numeric = date2num(x_pos)
                        # Draw vertical line from min to max
                        line = self.ax.plot(
                            [x_pos_numeric, x_pos_numeric],
                            [y_lower, y_upper],
                            color=whisker_color,
                            linewidth=whisker_linewidth,
                            linestyle=whisker_linestyle,
                            alpha=1.0,
                            zorder=1,
                        )
                    else:
                        # Draw vertical line from min to max
                        line = self.ax.plot(
                            [x_pos, x_pos],
                            [y_lower, y_upper],
                            color=whisker_color,
                            linewidth=whisker_linewidth,
                            linestyle=whisker_linestyle,
                            alpha=1.0,
                            zorder=1,
                        )

                    if x_idx == 0:
                        mappables.extend(line)

                    # Draw caps if showcaps is True
                    if showcaps:
                        cap_half_width = base_width * cap_width_factor / 2
                        if np.issubdtype(x_values.dtype, np.datetime64):
                            x_pos_numeric = date2num(x_pos)
                            # Draw cap at lower end
                            self.ax.plot(
                                [x_pos_numeric - cap_half_width, x_pos_numeric + cap_half_width],
                                [y_lower, y_lower],
                                color=cap_color,
                                linewidth=cap_linewidth,
                                linestyle=cap_linestyle,
                                alpha=1.0,
                                zorder=1,
                            )
                            # Draw cap at upper end
                            self.ax.plot(
                                [x_pos_numeric - cap_half_width, x_pos_numeric + cap_half_width],
                                [y_upper, y_upper],
                                color=cap_color,
                                linewidth=cap_linewidth,
                                linestyle=cap_linestyle,
                                alpha=1.0,
                                zorder=1,
                            )
                        else:
                            # Draw cap at lower end
                            self.ax.plot(
                                [x_pos - cap_half_width, x_pos + cap_half_width],
                                [y_lower, y_lower],
                                color=cap_color,
                                linewidth=cap_linewidth,
                                linestyle=cap_linestyle,
                                alpha=1.0,
                                zorder=1,
                            )
                            # Draw cap at upper end
                            self.ax.plot(
                                [x_pos - cap_half_width, x_pos + cap_half_width],
                                [y_upper, y_upper],
                                color=cap_color,
                                linewidth=cap_linewidth,
                                linestyle=cap_linestyle,
                                alpha=1.0,
                                zorder=1,
                            )
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
                            edgecolor=box_edgecolor,
                            alpha=1.0,
                            linewidth=box_linewidth,
                            linestyle=box_linestyle,
                            zorder=2,
                        )
                    else:
                        rect = Rectangle(
                            (x_pos - box_width/2, y_lower),
                            box_width,
                            box_height,
                            facecolor=box_color,
                            edgecolor=box_edgecolor,
                            alpha=1.0,
                            linewidth=box_linewidth,
                            linestyle=box_linestyle,
                            zorder=2,
                        )
                    self.ax.add_patch(rect)

                    # Only add the first rectangle to mappables for layer tracking
                    if x_idx == 0 and pair_idx == 1:
                        mappables.append(rect)

            # Draw median line at this x position if it exists
            if median_idx is not None:
                y_median = q_values[median_idx, x_idx]
                # Make median line slightly narrower than the widest box to avoid poking out
                median_width = base_width * 0.95
                if np.issubdtype(x_values.dtype, np.datetime64):
                    from matplotlib.dates import date2num
                    x_pos_numeric = date2num(x_pos)
                    median_line = self.ax.plot(
                        [x_pos_numeric - median_width/2, x_pos_numeric + median_width/2],
                        [y_median, y_median],
                        color=median_color,
                        linewidth=median_linewidth,
                        linestyle=median_linestyle,
                        alpha=median_alpha,
                        zorder=10,
                    )
                else:
                    median_line = self.ax.plot(
                        [x_pos - median_width/2, x_pos + median_width/2],
                        [y_median, y_median],
                        color=median_color,
                        linewidth=median_linewidth,
                        linestyle=median_linestyle,
                        alpha=median_alpha,
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

        # Mark this layer as a multiboxplot for legend generation
        layer._layer_type = 'multiboxplot'
        layer._multiboxplot_quantiles = quantiles
        layer._multiboxplot_color = plot_color  # Use plot_color (actual color used) not base_color
        layer._multiboxplot_styling = {
            'whisker_color': whisker_color,
            'whisker_linewidth': whisker_linewidth,
            'box_edgecolor': box_edgecolor,
            'box_linewidth': box_linewidth,
            'median_color': median_color,
            'median_linewidth': median_linewidth,
        }

        # Handle label
        if label is not None:
            formatted_label = layer.format_string(label)
            # Set label on the first (outermost) band
            if mappables:
                mappables[0].set_label(formatted_label)

        self.layers.append(layer)

        # Store quantiles and color for potential legend creation
        self._last_multiboxplot_quantiles = quantiles
        self._last_multiboxplot_color = base_color

        return mappables

    def envelopes(
        self,
        data,
        x="auto",
        dim=None,
        quantiles="auto",
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
            If None, uses the left-most dimension. When quantiles=None (pre-computed quantiles),
            this specifies which dimension contains the quantile values.
        quantiles : list of float, "auto", or None, optional
            - If "auto" (default): compute quantiles [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]
            - If list of float: compute these specific quantiles (values between 0 and 1),
              paired symmetrically (e.g., 0.1-0.9, 0.25-0.75)
            - If None: don't compute quantiles - treat the dimension specified by 'dim' as
              containing pre-computed quantile values. This allows plotting data where quantiles
              have already been calculated.
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

        >>> # Pre-computed quantiles (skip quantile computation)
        >>> quantile_data = ensemble_data.quantile([0.1, 0.5, 0.9], dim='member')
        >>> chart.envelopes(quantile_data, dim='quantile', quantiles=None)
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
        quantiles = result['quantiles']
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
    def multiboxplot_legend(
        self,
        location='right',
        fontsize=8,
        color=None,
        boxprops=None,
        whiskerprops=None,
        medianprops=None,
        **kwargs
    ):
        """
        Create a visual legend for the last multiboxplot showing quantile structure.

        This creates a miniature demonstration plot showing the quantile structure with
        labeled percentiles. The legend is placed outside the plot area, similar to a colorbar.
        The legend is always displayed in vertical orientation (0.75 x 0.75 inches) regardless
        of where it's positioned.

        Parameters
        ----------
        location : str, optional
            Location for the legend outside the plot area.
            Options: 'right', 'left', 'top', 'bottom'. Default is 'right'.
        fontsize : int, optional
            Font size for labels. Default is 8.
        color : str or tuple, optional
            Base color for the legend. If None, uses the color from the multiboxplot.
        boxprops : dict, optional
            Properties for box edges (edgecolor, linewidth, linestyle).
            If None, uses styling from the multiboxplot.
        whiskerprops : dict, optional
            Properties for whisker lines (color, linewidth, linestyle).
            If None, uses styling from the multiboxplot.
        medianprops : dict, optional
            Properties for median line (color, linewidth, linestyle).
            If None, uses styling from the multiboxplot.
        **kwargs
            Additional keyword arguments:
            - size: Size of legend in inches (default: 0.75, creating a 0.75x0.75 square)
            - pad: Padding between plot and legend in inches (default: 0.1)

        Returns
        -------
        matplotlib.axes.Axes
            The axes containing the legend.

        Examples
        --------
        >>> subplot.multiboxplot(ensemble_data, dim='member', color='steelblue')
        >>> subplot.multiboxplot_legend()  # Uses 'steelblue' from the plot

        >>> # Override with custom styling
        >>> subplot.multiboxplot_legend(
        ...     color='orange',
        ...     boxprops={'edgecolor': 'red', 'linewidth': 1.5},
        ...     medianprops={'color': 'darkred', 'linewidth': 2.0}
        ... )
        """
        # Check if we have quantiles from a previous multiboxplot call
        # If not stored yet, look for multiboxplot layers
        if not hasattr(self, '_last_multiboxplot_quantiles'):
            multiboxplot_layers = [
                layer for layer in self.layers
                if hasattr(layer, '_layer_type') and layer._layer_type == 'multiboxplot'
            ]

            if not multiboxplot_layers:
                raise ValueError(
                    "No multiboxplot has been created yet. "
                    "Call multiboxplot() before creating a legend."
                )

            # Use the most recent multiboxplot layer
            layer = multiboxplot_layers[-1]
            self._last_multiboxplot_quantiles = layer._multiboxplot_quantiles
            self._last_multiboxplot_color = layer._multiboxplot_color
            self._last_multiboxplot_styling = getattr(layer, '_multiboxplot_styling', {})

        quantiles = self._last_multiboxplot_quantiles
        stored_color = self._last_multiboxplot_color
        stored_styling = getattr(self, '_last_multiboxplot_styling', {})

        # Ensure quantiles are floats
        quantiles = [float(q) for q in quantiles]

        # Use provided color or fall back to stored color
        base_color = color if color is not None else stored_color

        # Convert base_color to RGB for use in gradient and median calculations
        import matplotlib.colors as mcolors
        if isinstance(base_color, str):
            base_color_rgb = mcolors.to_rgb(base_color)
        else:
            base_color_rgb = base_color

        # Resolve styling parameters - use provided values or fall back to stored styling
        # Whisker properties
        whiskerprops = whiskerprops or {}
        whisker_color = whiskerprops.get('color', stored_styling.get('whisker_color', (0.3, 0.3, 0.3)))
        whisker_linewidth = whiskerprops.get('linewidth', stored_styling.get('whisker_linewidth', 0.8))

        # Box properties
        boxprops = boxprops or {}
        box_edgecolor = boxprops.get('edgecolor', stored_styling.get('box_edgecolor', base_color))
        box_linewidth = boxprops.get('linewidth', stored_styling.get('box_linewidth', 0.5))

        # Median properties
        medianprops = medianprops or {}
        median_color = medianprops.get('color', stored_styling.get('median_color', tuple(c * 0.6 for c in base_color_rgb)))
        median_linewidth = medianprops.get('linewidth', stored_styling.get('median_linewidth', 1.5))

        # Validate location
        valid_locations = ['right', 'left', 'top', 'bottom']
        if location not in valid_locations:
            raise ValueError(
                f"Invalid location '{location}'. "
                f"Valid options: {valid_locations}"
            )

        # Create legend axes using axes_divider (like colorbar does)
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        divider = make_axes_locatable(self.ax)

        # Get pad parameter
        pad = kwargs.pop('pad', 0.1)

        # Always create a 0.75x0.75 inch square legend with vertical orientation
        # The legend is always vertical regardless of where it's positioned
        size = kwargs.pop('size', 0.75)  # inches

        # Create the axes at the specified location
        legend_ax = divider.append_axes(location, size=size, pad=pad)

        # Set fixed aspect ratio and size
        # The legend box will always be 0.75 x 0.75 inches
        legend_ax.set_aspect('equal', adjustable='box')

        # Import for drawing
        import matplotlib.patches as mpatches

        # Use the base_color_rgb we already calculated above
        rgb = base_color_rgb

        # Draw the multiboxplot structure
        n_quantiles = len(quantiles)
        pairs = []
        for i in range(n_quantiles // 2):
            pairs.append((i, n_quantiles - 1 - i))

        if n_quantiles % 2 == 1:
            median_idx = n_quantiles // 2
        else:
            median_idx = None

        # Always draw in vertical orientation (regardless of location)
        x_center = 0.25  # Shift left to make room for labels on the right
        base_width = 0.15  # 50% narrower than before (was 0.3)

        for pair_idx, (lower_idx, upper_idx) in enumerate(pairs):
            width_factor = (pair_idx + 1) / len(pairs)
            box_width = base_width * width_factor

            q_lower = quantiles[lower_idx]
            q_upper = quantiles[upper_idx]
            y_lower = q_lower
            y_upper = q_upper
            box_height = y_upper - y_lower

            if pair_idx == 0:
                # Outermost: whisker line (use actual styling from multiboxplot)
                legend_ax.plot(
                    [x_center, x_center],
                    [y_lower, y_upper],
                    color=whisker_color,
                    linewidth=whisker_linewidth,
                    zorder=1,
                )
            else:
                # Inner boxes - match the actual multiboxplot gradient
                # Replicate the lightness calculation from multiboxplot
                normalized_idx = (pair_idx - 1) / max(1, len(pairs) - 2)
                lightness_factor = 0.4 * (1.0 - normalized_idx)
                color = tuple(c * (1 - lightness_factor) + lightness_factor for c in rgb)

                legend_ax.add_patch(
                    mpatches.Rectangle(
                        (x_center - box_width/2, y_lower),
                        box_width,
                        box_height,
                        facecolor=color,
                        edgecolor=box_edgecolor,
                        linewidth=box_linewidth,
                        zorder=2,
                    )
                )

        # Draw median line if it exists
        if median_idx is not None:
            q_median = quantiles[median_idx]
            median_width = base_width * 0.95
            legend_ax.plot(
                [x_center - median_width/2, x_center + median_width/2],
                [q_median, q_median],
                color=median_color,
                linewidth=median_linewidth,
                zorder=10,
            )

        # Add labels for quantiles - always on the right of the box
        for i, q in enumerate(quantiles):
            # Format label
            if q == 0:
                label_text = 'min'
            elif q == 1:
                label_text = 'max'
            elif q == 0.5:
                label_text = 'median'
            else:
                percentile = int(q * 100)
                label_text = f'{percentile}%'

            # Position label to the right of the box
            legend_ax.text(
                0.4, q, label_text,
                ha='left', va='center',
                fontsize=fontsize - 1,
            )

        # Configure legend axes
        legend_ax.set_xlim(0, 1)
        legend_ax.set_ylim(-0.05, 1.05)
        legend_ax.set_xticks([])
        legend_ax.set_yticks([])
        for spine in legend_ax.spines.values():
            spine.set_visible(False)

        return legend_ax

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

    @plot_2d(extract_domain=True, default_reproject_to_target=False)
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
        reproject_to_target : bool, optional
            Whether to reproject data to the map's CRS before plotting. Default is False for pcolormesh.
            When False, data is plotted in its native CRS using matplotlib's transform parameter.
            When True, data is reprojected to match the map's CRS, which can be useful for certain projections
            but may be slower and lose some precision.
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

        Note: For multiboxplot layers, use the multiboxplot_legend() method to create
        a specialized visual legend showing the quantile structure.

        Parameters
        ----------
        location : str, optional
            The location for the colorbar(s).
            Valid options: 'right', 'left', 'top', 'bottom'. Default is 'right'.
        label : str, optional
            Label for the colorbar(s). Default is "auto" which generates a label from
            layer metadata. Can contain format placeholders (e.g., "{units}",
            "{long_name}", etc.) which will be replaced with layer metadata values.
            Use None for no label.
        **kwargs
            Additional keyword arguments passed to each colorbar/legend creation.

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

        legends = []

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
