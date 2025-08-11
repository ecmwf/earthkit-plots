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

"""
Plot decorators for the Subplot class.

This module provides decorators that standardize the plotting interface for different
types of plots (2D, 3D, vector, box) by handling common data extraction and
processing patterns.
"""

import matplotlib.dates as mdates
import numpy as np

from earthkit.plots import identifiers
from earthkit.plots.core.extractors import (
    configure_style,
    extract_plottables_2D,
    extract_plottables_3D,
)
from earthkit.plots.core.layers import Layer
from earthkit.plots.resample import Regrid
from earthkit.plots.sources import get_source, get_vector_sources


def plot_2D(method_name=None):
    """
    Decorator for 2D plotting methods.

    This decorator standardizes the interface for 2D plotting methods by handling
    data extraction, style configuration, and plotting through the extractors module.

    Parameters
    ----------
    method_name : str, optional
        The name of the method to call on the style object. If None, uses the
        decorated method's name.

    Returns
    -------
    function
        A decorator function that wraps the original method.

    Examples
    --------
    @plot_2D()
    def line(self, *args, **kwargs):
        pass

    @plot_2D("custom_method")
    def custom_plot(self, *args, **kwargs):
        pass
    """

    def decorator(method):
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
            """Wrapper for 2D plotting methods."""
            return extract_plottables_2D(
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


def plot_3D(method_name=None, extract_domain=False):
    """
    Decorator for 3D plotting methods.

    This decorator standardizes the interface for 3D plotting methods by handling
    data extraction, style configuration, and plotting through the extractors module.

    Parameters
    ----------
    method_name : str, optional
        The name of the method to call on the style object. If None, uses the
        decorated method's name.
    extract_domain : bool, default=False
        Whether to extract data within the subplot's domain boundaries.

    Returns
    -------
    function
        A decorator function that wraps the original method.

    Examples
    --------
    @plot_3D()
    def tripcolor(self, *args, **kwargs):
        pass

    @plot_3D(extract_domain=True)
    def pcolormesh(self, *args, **kwargs):
        pass
    """

    def decorator(method):
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
            """Wrapper for 3D plotting methods."""
            return extract_plottables_3D(
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
                **kwargs,
            )

        return wrapper

    return decorator


def plot_box(method_name=None):
    """
    Decorator for box plotting methods (bar charts, histograms).

    This decorator handles the specialized logic for box-type plots including
    time axis formatting, automatic width calculation, and axis labeling.

    Parameters
    ----------
    method_name : str, optional
        The name of the method to call on the axes object. If None, uses the
        decorated method's name.

    Returns
    -------
    function
        A decorator function that wraps the original method.

    Examples
    --------
    @plot_box()
    def bar(self, *args, **kwargs):
        pass
    """

    def decorator(method):
        def wrapper(self, data=None, x=None, y=None, z=None, style=None, **kwargs):
            """Wrapper for box plotting methods."""
            # Extract data source
            source = get_source(data=data, x=x, y=y, z=z)
            kwargs = {**self._plot_kwargs(source), **kwargs}

            # Get the plotting method from axes
            plot_method = getattr(self.ax, method_name or method.__name__)

            # Handle time-based x-axis formatting
            if source.extract_x() in identifiers.TIME:
                positions = mdates.date2num(source.x_values)
                _configure_time_axis(self.ax)
            else:
                positions = source.x_values

            # Calculate optimal bar widths
            widths = min(0.5, np.diff(positions).min() * 0.7)

            # Create the plot
            mappable = plot_method(
                source.z_values, positions=positions, widths=widths, **kwargs
            )

            # Store layer and configure axes
            self.layers.append(Layer(source, mappable, self, style))
            _configure_box_axes(self.ax, source)

            return mappable

        return wrapper

    return decorator


def plot_vector(method_name=None):
    """
    Decorator for vector plotting methods (quiver, barbs).

    This decorator handles vector data extraction, resampling, and plotting
    with support for domain extraction and coordinate transformations.

    Parameters
    ----------
    method_name : str, optional
        The name of the method to call on the style object. If None, uses the
        decorated method's name.

    Returns
    -------
    function
        A decorator function that wraps the original method.

    Examples
    --------
    @plot_vector()
    def quiver(self, *args, **kwargs):
        pass

    @plot_vector()
    def barbs(self, *args, **kwargs):
        pass
    """

    def decorator(method):
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
            source_units=None,
            resample=Regrid(40),
            **kwargs,
        ):
            """Wrapper for vector plotting methods."""
            # Extract vector sources
            u_source, v_source = _extract_vector_sources(args, x, y, u, v, source_units)

            # Configure style and get plotting method
            kwargs = {**self._plot_kwargs(u_source), **kwargs}
            style = configure_style(
                method_name or method.__name__,
                style,
                u_source,
                units,
                False,
                kwargs,
            )
            plot_method = getattr(style, method_name or method.__name__)

            # Extract and process vector data
            x_values, y_values, u_values, v_values = _process_vector_data(
                self, u_source, v_source, style, resample
            )

            # Prepare plotting arguments
            plot_args = [x_values, y_values, u_values, v_values]
            if colors:
                plot_args.append((u_values**2 + v_values**2) ** 0.5)

            # Create the plot
            mappable = plot_method(self.ax, *plot_args, **kwargs)

            # Store layer and configure axes
            self.layers.append(Layer([u_source, v_source], mappable, self, style))
            _configure_vector_axes(self.ax, u_source)

            return mappable

        return wrapper

    return decorator


# Helper functions for the decorators


def _configure_time_axis(ax):
    """Configure time-based x-axis formatting."""
    locator = mdates.AutoDateLocator(maxticks=30)
    formatter = mdates.ConciseDateFormatter(
        locator,
        formats=["%Y", "%b", "%-d %b", "%H:%M", "%H:%M", "%S.%f"],
    )
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)


def _configure_box_axes(ax, source):
    """Configure axes labels for box plots."""
    if isinstance(source._x, str) and source._x not in identifiers.TIME:
        ax.set_xlabel(source._x)
    if isinstance(source._z, str):
        ax.set_ylabel(source._z)


def _extract_vector_sources(args, x, y, u, v, source_units):
    """Extract u and v vector sources from arguments or keyword parameters."""
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
    else:
        raise ValueError("Vector plotting requires 0, 1, or 2 positional arguments")

    return u_source, v_source


def _process_vector_data(subplot, u_source, v_source, style, resample):
    """Process vector data including domain extraction and resampling."""
    x_values = u_source.x_values
    y_values = u_source.y_values
    u_values = style.convert_units(u_source.z_values, u_source.units)
    v_values = style.convert_units(v_source.z_values, v_source.units)

    # Apply domain extraction if available
    if subplot.domain is not None:
        x_values, y_values, _, [u_values, v_values] = subplot.domain.extract(
            x_values,
            y_values,
            extra_values=[u_values, v_values],
            source_crs=u_source.crs,
        )

    # Apply resampling if specified
    if resample is not None:
        kwargs = {}
        kwargs.pop("regrid_shape", None)
        if resample.__class__.__name__ == "Regrid":
            kwargs.pop("transform", None)

        x_values, y_values, u_values, v_values = resample.apply(
            x_values,
            y_values,
            u_values,
            v_values,
            source_crs=u_source.crs,
            target_crs=subplot.crs,
            extents=subplot.ax.get_extent(),
        )

    return x_values, y_values, u_values, v_values


def _configure_vector_axes(ax, u_source):
    """Configure axes labels for vector plots."""
    if isinstance(u_source._x, str):
        ax.set_xlabel(u_source._x)
    if isinstance(u_source._y, str):
        ax.set_ylabel(u_source._y)
