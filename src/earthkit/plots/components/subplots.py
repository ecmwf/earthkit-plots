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
from cartopy.util import add_cyclic_point

from earthkit.plots import identifiers
from earthkit.plots.components.layers import Layer
from earthkit.plots.geo import coordinate_reference_systems, grids
from earthkit.plots.metadata.formatters import (
    LayerFormatter,
    SourceFormatter,
    SubplotFormatter,
)
from earthkit.plots.resample import Interpolate, Regrid
from earthkit.plots.schemas import schema
from earthkit.plots.sources import get_source, get_vector_sources
from earthkit.plots.sources.numpy import NumpySource
from earthkit.plots.styles import _STYLE_KWARGS, Contour, Quiver, Style, auto
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

    def plot_2D(method_name=None):
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
                return self._extract_plottables_2D(
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

    def plot_box(method_name=None):
        def decorator(method):
            def wrapper(self, data=None, x=None, y=None, z=None, style=None, **kwargs):
                source = get_source(data=data, x=x, y=y, z=z)
                kwargs = {**self._plot_kwargs(source), **kwargs}
                m = getattr(self.ax, method_name or method.__name__)
                if source.extract_x() in identifiers.TIME:
                    positions = mdates.date2num(source.x_values)
                else:
                    positions = source.x_values
                widths = min(0.5, np.diff(positions).min() * 0.7)
                mappable = m(
                    source.z_values, positions=positions, widths=widths, **kwargs
                )
                self.layers.append(Layer(source, mappable, self, style))
                if isinstance(source._x, str):
                    if source._x in identifiers.TIME:
                        locator = mdates.AutoDateLocator(maxticks=30)
                        formatter = mdates.ConciseDateFormatter(
                            locator,
                            formats=["%Y", "%b", "%-d %b", "%H:%M", "%H:%M", "%S.%f"],
                        )
                        self.ax.xaxis.set_major_locator(locator)
                        self.ax.xaxis.set_major_formatter(formatter)
                    else:
                        self.ax.set_xlabel(source._x)
                if isinstance(source._z, str):
                    self.ax.set_ylabel(source._z)
                return mappable

            return wrapper

        return decorator

    def plot_3D(method_name=None, extract_domain=False):
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
                return self._extract_plottables(
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

    def plot_vector(method_name=None):
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

                kwargs = {**self._plot_kwargs(u_source), **kwargs}

                style = self._configure_style(
                    method_name or method.__name__,
                    style,
                    u_source,
                    units,
                    False,
                    kwargs,
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

    def _extract_plottables_2D(
        self,
        method_name,
        args,
        x=None,
        y=None,
        z=None,
        style=None,
        no_style=False,
        units=None,
        every=None,
        source_units=None,
        auto_style=False,
        regrid=False,
        metadata=None,
        **kwargs,
    ):
        # Step 1: Initialize the source
        source = get_source(
            *args, x=x, y=y, z=z, units=source_units, metadata=metadata, regrid=regrid
        )
        kwargs.update(self._plot_kwargs(source))

        # Step 2: Configure the style
        style = self._configure_style(
            method_name, style, source, units, auto_style, kwargs
        )

        # Step 3: Process z values
        z_values = self._process_z_values(style, source, z)

        # Step 5: Process x, y values, apply sampling if specified
        x_values, y_values = source.x_values, source.y_values
        x_values, y_values, z_values = self._apply_sampling(
            x_values, y_values, z_values, every
        )

        if no_style and z_values is None:
            # We do this to ensure that the Style class has a consistent
            # representation of z values
            z_values = kwargs.pop("c", None)

        mappable = getattr(style, method_name)(
            self.ax, x_values, y_values, z_values, **kwargs
        )

        # Step 8: Store layer and return
        self.layers.append(Layer(source, mappable, self, style))
        return mappable

    def _extract_plottables(
        self,
        method_name,
        args,
        x=None,
        y=None,
        z=None,
        style=None,
        no_style=False,
        units=None,
        every=None,
        source_units=None,
        extract_domain=False,
        auto_style=False,
        regrid=False,
        metadata=None,
        **kwargs,
    ):
        if method_name.startswith("contour"):
            regrid = True
        # Step 1: Initialize the source
        source = get_source(
            *args, x=x, y=y, z=z, units=source_units, metadata=metadata, regrid=regrid
        )
        kwargs.update(self._plot_kwargs(source))

        # Step 2: Configure the style
        style = self._configure_style(
            method_name, style, source, units, auto_style, kwargs
        )

        # Step 3: Process z values
        z_values = self._process_z_values(style, source, z)

        # Step 4: Handle specific grid types
        gs = source.gridspec
        mappable = None
        if method_name == "pcolormesh":
            gs = source.gridspec
            if gs is not None:
                opt = {
                    "healpix": self._plot_healpix,
                    "reduced_gg": self._plot_octahedral,
                }
                method = opt.get(gs.name, None)
                if method:
                    mappable = method(source, z_values, style, kwargs)

        if not mappable:
            # Step 5: Process x, y values, apply sampling if specified
            x_values, y_values = source.x_values, source.y_values
            x_values, y_values, z_values = self._apply_sampling(
                x_values, y_values, z_values, every
            )

            if no_style and z_values is None:
                z_values = kwargs.pop("c", None)

            # Step 6: Domain extraction
            if self.domain and extract_domain and not no_style:
                x_values, y_values, z_values = self.domain.extract(
                    x_values, y_values, z_values, source_crs=source.crs
                )

            if method_name.startswith("contour") and grids.needs_cyclic_point(x_values):
                n_x = None
                if len(x_values.shape) != 1:
                    n_x = x_values.shape[0]
                    x_values = x_values[0]
                z_values, x_values = add_cyclic_point(z_values, coord=x_values)
                if n_x:
                    x_values = np.tile(x_values, (n_x, 1))
                    y_values = np.hstack((y_values, y_values[:, -1][:, np.newaxis]))
            # Step 7: Plot with or without interpolation
            if "transform_first" in kwargs:
                if (
                    self.crs.__class__
                    in coordinate_reference_systems.CANNOT_TRANSFORM_FIRST
                ):
                    kwargs["transform_first"] = False
            if not no_style:
                mappable = self._plot_with_interpolation(
                    style, method_name, x_values, y_values, z_values, source.crs, kwargs
                )
            else:
                print("Warning: Style not set.")
                mappable = getattr(self.ax, method_name)(
                    x_values, y_values, z_values, **kwargs
                )

        # Step 8: Store layer and return
        self.layers.append(Layer(source, mappable, self, style))
        return mappable

    def _configure_style(self, method_name, style, source, units, auto_style, kwargs):
        """Configures style based on method name, style, source, and units."""
        if style:
            return style
        style_kwargs = {k: kwargs.pop(k) for k in _STYLE_KWARGS if k in kwargs}
        # override_kwargs = {k: style_kwargs.pop(k, None) for k in _OVERRIDE_KWARGS}
        style_class = (
            Contour
            if method_name.startswith("contour")
            else (Quiver if method_name in ["quiver", "barbs"] else Style)
        )
        style = (
            style_class(**{**style_kwargs, "units": units})
            if not auto_style
            else auto.guess_style(source, units=units or source.units)
        )
        return style

    def _process_z_values(self, style, source, z):
        """Processes z values by converting units and applying a scale factor."""
        if source._data is None and z is None:
            return None

        z_values = style.convert_units(source.z_values, source.units)
        return style.apply_scale_factor(z_values)

    def _apply_sampling(self, x_values, y_values, z_values, every):
        """Applies sampling to x, y, and z values if 'every' is specified."""
        if every:
            x_values = x_values[::every]
            y_values = y_values[::every]
            if z_values is not None:
                z_values = z_values[::every, ::every]
        return x_values, y_values, z_values

    def _plot_healpix(self, source, z_values, style, kwargs):
        """Handles plotting for 'healpix' grid type."""
        from earthkit.plots.geo import healpix

        nest = source.metadata("orderingConvention", default=None) == "nested"
        kwargs["transform"] = self.crs
        return healpix.nnshow(z_values, ax=self.ax, nest=nest, style=style, **kwargs)

    def _plot_octahedral(self, source, z_values, style, kwargs):
        """Handles plotting for 'healpix' grid type."""
        from earthkit.plots.geo import octahedral

        return octahedral.plot_octahedral_grid(
            source.x_values,
            source.y_values,
            z_values,
            self.ax,
            style=style,
            **kwargs,
        )

    # def _plot_reduced_gg(self, source, z_values, style, kwargs):
    #     """Handles plotting for 'reduced_gg' grid type."""
    #     from earthkit.plots.geo import octahedral

    #     kwargs["transform"] = self.crs
    #     return octahedral.nnshow(
    #         z_values,
    #         source.x_values,
    #         source.y_values,
    #         ax=self.ax,
    #         style=style,
    #         **kwargs,
    #     )

    def _plot_with_interpolation(
        self, style, method_name, x_values, y_values, z_values, source_crs, kwargs
    ):
        """Attempts to plot with or without interpolation as needed."""
        if "interpolate" not in kwargs:
            try:
                return getattr(style, method_name)(
                    self.ax, x_values, y_values, z_values, **kwargs
                )
            except (ValueError, TypeError):
                warnings.warn(
                    f"{method_name} failed with raw data, attempting interpolation to structured grid with default interpolation options."
                )

        # TODO: handle interpolate kwarg in decorator
        interpolate = kwargs.pop("interpolate", dict())
        if interpolate is True:
            interpolate = Interpolate()
        if isinstance(interpolate, dict):
            interpolate = Interpolate(**interpolate)
        x_values, y_values, z_values = interpolate.apply(
            x_values,
            y_values,
            z_values,
            source_crs=source_crs,
            target_crs=self.crs,
        )
        _ = kwargs.pop("transform_first", None)
        if interpolate.transform:
            _ = kwargs.pop("transform", None)
        return getattr(style, method_name)(
            self.ax, x_values, y_values, z_values, **kwargs
        )

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
        if source_units is not None:
            source = get_source(data=data, x=x, y=y, z=z, units=source_units)
        else:
            source = get_source(data=data, x=x, y=y, z=z)
        kwargs = {**self._plot_kwargs(source), **kwargs}

        if (data is None and z is None) or (z is not None and not z):
            z_values = None
        else:
            z_values = source.z_values

        x_values = source.x_values
        y_values = source.y_values

        if every is not None:
            x_values = x_values[::every]
            y_values = y_values[::every]
            if z_values is not None:
                z_values = z_values[::every, ::every]

        if self.domain is not None and extract_domain:
            x_values, y_values, z_values = self.domain.extract(
                x_values,
                y_values,
                z_values,
                source_crs=source.crs,
            )
        return x_values, y_values, z_values

    @property
    def figure(self):
        from earthkit.plots.components.figures import Figure

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
        x1, y1, _ = self._extract_plottables_envelope(y=data_1, **kwargs)
        x2, y2, _ = self._extract_plottables_envelope(y=data_2, **kwargs)
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

    def rgb_composite(self, *args):
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

    def format_string(self, string, unique=True, grouped=True):
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
        """
        if not grouped:
            return string_utils.list_to_human(
                [LayerFormatter(layer).format(string) for layer in self.layers]
            )
        else:
            return SubplotFormatter(self, unique=unique).format(string)

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
