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

import inspect

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d, make_interp_spline

from earthkit.plots import metadata, plottypes, styles
from earthkit.plots.schemas import schema
from earthkit.plots.styles import auto, colors, legends, levels
from earthkit.plots.styles.colors import magics_colors_to_rgb

__all__ = [
    "colors",
    "legends",
    "levels",
    "auto",
    "Style",
    "DEFAULT_STYLE",
    "_STYLE_KWARGS",
    "_OVERRIDE_KWARGS",
]


def linspace_datetime64(start_date, end_date, n):
    """
    Generate a linearly spaced array of datetime64 objects.

    Parameters
    ----------
    start_date : numpy.datetime64
        The starting date.
    end_date : numpy.datetime64
        The ending date.
    n : int
        The number of dates to generate.
    """
    return np.linspace(0, 1, n) * (end_date - start_date) + start_date


class Style:
    """
    A style for plotting data.

    Parameters
    ----------
    colors : str or list or matplotlib.colors.Colormap, optional
        The colors to be used in this `Style`. This can be a
        `named matplotlib colormap
        <https://matplotlib.org/stable/gallery/color/colormap_reference.html>`__,
        a list of colors (as named CSS4 colors, hexadecimal colors or three
        (four)-element lists of RGB(A) values), or a pre-defined matplotlib
        colormap object. If not provided, the default colormap of the active
        `schema` will be used.
    levels : list or earthkit.maps.styles.levels.Levels, optional
        The levels to use in this `Style`. This can be a list of specific
        levels, or an earthkit `Levels` object. If not provided, some suitable
        levels will be generated automatically (experimental!).
    gradients : list, optional
        The number of colors to insert between each level in `levels`. If None,
        one color level will be inserted between each level.
    normalize : bool, optional
        If `True` (default), then the colors will be normalized over the level
        range.
    units : str, optional
        The units in which the levels are defined. If this `Style` is used with
        data not using the given units, then a conversion will be attempted;
        any data incompatible with these units will not be able to use this
        `Style`. If `units` are not provided, then data plotted using this
        `Style` will remain in their original units.
    units_label : str, optional
        The label to use in titles and legends to represent the units of the
        data.
    legend_style : str, optional
        The style of legend to use by default with this style. Must be one of
        `colorbar` (default), `disjoint`, `histogram`, or `None` (no legend).
    bin_labels : list, optional
        A list of categorical labels for each bin in the legend.
    """

    @classmethod
    def from_dict(cls, kwargs):
        """Create a `Style` from a dictionary."""
        style_type = kwargs.pop("type")
        if "levels" in kwargs:
            kwargs["levels"] = levels.Levels.from_config(kwargs["levels"])
        return getattr(styles, style_type)(**kwargs)

    def __init__(
        self,
        colors=schema.default_cmap,
        levels=None,
        gradients=None,
        normalize=True,
        units=None,
        scale_factor=None,
        units_label=None,
        legend_style="colorbar",
        legend_kwargs=None,
        categories=None,
        ticks=None,
        preferred_method="contourf",
        resample=None,
        **kwargs,
    ):
        if categories is not None and levels is None:
            levels = range(len(categories) + 1)
        self._colors = colors
        if isinstance(self._colors, (list, tuple)) and schema.color_mode == "magics":
            self._colors = magics_colors_to_rgb(self._colors)

        if isinstance(levels, dict):
            levels = styles.levels.Levels(**levels)
        self._levels = (
            levels
            if isinstance(levels, styles.levels.Levels)
            else styles.levels.Levels(
                levels,
                categorical=categories is not None
                or self.__class__.__name__ == "Categorical",
            )
        )
        self.normalize = normalize
        self.gradients = gradients
        self.resample = resample

        self._units = units
        self._units_label = units_label
        self.scale_factor = scale_factor

        self._legend_style = legend_style
        if self._legend_style == "None":
            self._legend_style = None

        self._bin_labels = categories
        self._legend_kwargs = legend_kwargs or dict()
        if ticks is not None:
            self._legend_kwargs["ticks"] = ticks

        if "extend" in kwargs:
            self._legend_kwargs["extend"] = kwargs["extend"]

        self._kwargs = kwargs
        self._preferred_method = preferred_method

    # TODO
    # def to_yaml(self):
    #     pass

    # TODO
    # def to_magics_style(self):
    #     pass

    def __eq__(self, other):
        keys = ["_levels", "_colors"]
        return compare_attributes(self, other, keys)

    def levels(self, data=None):
        """
        Generate levels specific to some data.

        Parameters
        ----------
        data : numpy.ndarray or xarray.DataArray or earthkit.data.core.Base
            The data for which to generate a list of levels.

        Returns
        -------
        list
        """
        if data is None:
            if self._levels._levels is not None:
                return self._levels._levels
            else:
                raise ValueError(
                    "this style uses dynamic levels; include the `data` "
                    "argument to generate levels"
                )
        return self._levels.apply(data)

    @property
    def extend(self):
        """Convenience access to 'extend' kwarg."""
        return self._kwargs.get("extend")

    @property
    def units(self):
        """Formatted units for use in figure text."""
        if self._units_label is not None:
            return self._units_label
        elif self._units is not None:
            return self._units

    def apply_scale_factor(self, values):
        """Apply the scale factor to some values."""
        if self.scale_factor is not None:
            values *= self.scale_factor
        return values

    def convert_units(self, values, source_units, short_name=""):
        """
        Convert some values from their source units to this `Style`'s units.

        Parameters
        ----------
        values : numpy.ndarray
            The values to convert from their source units to this `Style`'s
            units.
        source_units : str
            The source units of the given values.
        short_name : str, optional
            The short name of the variable, which is used to make extra
            assumptions about the data's unit covnersion (for example,
            temperature anomalies need special consideration when converting
            between Celsius and Kelvin).
        """
        if self._units is None or source_units is None:
            return values

        # For temperature anomalies we do not want to convert values, just
        # change the units string
        if "anomaly" in short_name.lower() and metadata.units.anomaly_equivalence(
            source_units
        ):
            return values

        return metadata.units.convert(values, source_units, self._units)

    def to_matplotlib_kwargs(self, data, extend_levels=True):
        """
        Generate matplotlib arguments required for plotting data in this `Style`.

        Parameters
        ----------
        data : numpy.ndarray
            The data to be plotted using this `Style`.
        """
        levels = self.levels(data)

        if self.gradients is not None:
            self._legend_kwargs.setdefault(
                "ticks", None
            )  # Let matplotlib auto-generate ticks
            return colors.gradients(
                levels,
                self._colors,
                self.gradients,
                self.normalize,
                **self._kwargs,
            )

        cmap, norm = styles.colors.cmap_and_norm(
            self._colors,
            levels,
            self.normalize,
            self.extend,
            extend_levels=extend_levels,
        )

        cmap.set_bad(alpha=0)

        return {
            **{"cmap": cmap, "norm": norm, "levels": levels},
            **self._kwargs,
        }

    @staticmethod
    def _xy_for_contour(x, y):
        if x.ndim == 1 and y.ndim == 1:
            x, y = np.meshgrid(x, y)
        return x, y

    @staticmethod
    def _xy_for_scatter(x, y):
        if x.ndim == 1 and y.ndim == 1 and len(x) != len(y):
            x, y = np.meshgrid(x, y)
            x = x.flatten()
            y = y.flatten()
        elif x.ndim == 2 and y.ndim == 2 and x.shape == y.shape:
            x = x.flatten()
            y = y.flatten()
        return x, y

    def to_contourf_kwargs(self, data):
        """
        Generate `contourf` arguments required for plotting data in this `Style`.

        Parameters
        ----------
        data : numpy.ndarray
            The data to be plotted using this `Style`.
        """
        kwargs = self.to_matplotlib_kwargs(data)
        kwargs.pop("linewidths", None)
        kwargs.pop("hatches", None)
        kwargs.pop("linecolors", None)
        kwargs.pop("labels", None)
        return kwargs

    def to_contour_kwargs(self, data):
        """
        Generate `contour` arguments required for plotting data in this `Style`.

        Parameters
        ----------
        data : numpy.ndarray
            The data to be plotted using this `Style`.
        """
        return self.to_matplotlib_kwargs(data)

    def to_pcolormesh_kwargs(self, data):
        """
        Generate `pcolormesh` arguments required for plotting data in this `Style`.

        Parameters
        ----------
        data : numpy.ndarray
            The data to be plotted using this `Style`.
        """
        kwargs = self.to_matplotlib_kwargs(data, extend_levels=False)
        kwargs.pop("levels", None)
        kwargs.pop("transform_first", None)
        kwargs.pop("extend", None)
        kwargs.pop("labels", None)
        kwargs.pop("linecolors", None)
        kwargs.pop("hatches", None)
        return kwargs

    def to_scatter_kwargs(self, data):
        """
        Generate `scatter` arguments required for plotting data in this `Style`.

        Parameters
        ----------
        data : numpy.ndarray
            The data to be plotted using this `Style`.
        """
        kwargs = self.to_matplotlib_kwargs(data, extend_levels=False)
        kwargs.pop("levels", None)
        return kwargs

    def to_quiver_kwargs(self, data):
        """
        Generate `quiver` arguments required for plotting data in this `Style`.

        Parameters
        ----------
        data : numpy.ndarray
            The data to be plotted using this `Style`.
        """
        kwargs = self.to_matplotlib_kwargs(data)
        kwargs.pop("levels", None)
        return kwargs

    def plot(self, *args, **kwargs):
        """Plot the data using the `Style`'s defaults."""
        return self.pcolormesh(*args, **kwargs)

    def contourf(self, ax, x, y, values, *args, **kwargs):
        """
        Plot shaded contours using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.contourf`.
        """
        kwargs = {**self.to_contourf_kwargs(values), **kwargs}
        x, y = self._xy_for_contour(x, y)
        return ax.contourf(x, y, values, *args, **kwargs)

    def quiver(self, ax, x, y, u, v, *args, **kwargs):
        """
        Plot quiver arrows using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        u : numpy.ndarray
            The u-component of the data to be plotted.
        v : numpy.ndarray
            The v-component of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.quiver`.
        """
        cmap = None
        norm = None
        kwargs = {**self._kwargs, **kwargs}
        if self._colors:
            magnitude = np.sqrt(u**2 + v**2)
            kwargs = {**self.to_quiver_kwargs(magnitude), **kwargs}
            cmap = kwargs.pop("cmap", None)
            norm = kwargs.pop("norm", None)
            if cmap and norm:
                kwargs["color"] = cmap(norm(magnitude))[0]
        mappable = ax.quiver(x, y, u, v, *args, **kwargs)
        mappable.cmap = cmap
        mappable.norm = norm
        if cmap is None:
            mappable._colorbar = False
        else:
            mappable._colorbar = True
        return mappable

    def barbs(self, ax, x, y, u, v, *args, **kwargs):
        return ax.barbs(x, y, u, v, *args, **kwargs)

    def tricontourf(self, ax, x, y, values, *args, **kwargs):
        """
        Plot triangulated shaded contours using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.tricontourf`.
        """
        kwargs = {**self.to_contourf_kwargs(values), **kwargs}
        return ax.tricontourf(x, y, values, *args, **kwargs)

    def tripcolor(self, ax, x, y, values, *args, **kwargs):
        """
        Plot triangulated shaded contours using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.tricontourf`.
        """
        kwargs = {**self.to_pcolormesh_kwargs(values), **kwargs}
        return ax.tripcolor(x, y, values, *args, **kwargs)

    def contour(self, ax, x, y, values, *args, **kwargs):
        """
        Plot line contours using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.contour`.
        """
        kwargs = {**self.to_contour_kwargs(values), **kwargs}
        kwargs.pop("labels", None)
        x, y = self._xy_for_contour(x, y)
        return ax.contour(x, y, values, *args, **kwargs)

    def pcolormesh(self, ax, x, y, values, *args, **kwargs):
        """
        Plot a pcolormesh using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.pcolormesh`.
        """
        kwargs.pop("transform_first", None)
        kwargs = {**self.to_pcolormesh_kwargs(values), **kwargs}
        result = ax.pcolormesh(x, y, values, *args, **kwargs)
        return result

    def imshow(self, ax, x, y, values, *args, **kwargs):
        """
        Plot a pcolormesh using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.pcolormesh`.
        """
        kwargs.pop("transform_first", None)
        kwargs = {**self.to_pcolormesh_kwargs(values), **kwargs}
        result = ax.imshow(x, y, values, *args, **kwargs)
        return result

    def scatter(self, ax, x, y, values, s=3, *args, **kwargs):
        """
        Plot a scatter plot using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.scatter`.
        """
        kwargs.pop("transform_first", None)
        missing_values = kwargs.pop("missing_values", None)
        original_kwargs = kwargs.copy()

        if values is not None:
            kwargs = {**self.to_scatter_kwargs(values), **kwargs}
            kwargs.pop("extend", None)
        if (
            values is not None
            and missing_values is not None
            and np.isnan(values).any()
            and len(values.shape) > 1
        ):
            missing_idx = np.where(np.isnan(values))
            missing_x = x[missing_idx]
            missing_y = y[missing_idx]
            x = x[np.invert(missing_idx)]
            y = y[np.invert(missing_idx)]
            values = values[np.invert(missing_idx)]
            if missing_values:
                ax.scatter(
                    missing_x,
                    missing_y,
                    s=s,
                    *args,
                    **{**original_kwargs, **missing_values},
                )
        if values is not None:
            kwargs["c"] = kwargs.pop("c", values)
        if isinstance(kwargs.get("c"), str):
            kwargs.pop("cmap", None)
            kwargs.pop("norm", None)
        x, y = self._xy_for_scatter(x, y)
        return ax.scatter(x, y, s=s, *args, **kwargs)

    def quantiles(
        self,
        ax,
        x,
        y,
        values,
        *args,
        type="band",
        quantiles=[0, 0.25, 0.5, 0.75, 1],
        **kwargs,
    ):
        """
        Compute and plot quantiles using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The coordinates of the data to be plotted.
        values : numpy.ndarray
            The data of which to compute the statistics. The computation
            is applied along axis 0, so the size along axis 1 must match
            the size of the coordinates.
        type : "box" | "band"
            The type of plot used to represent the quantile ranges.
        quantiles : array_like
            Probabilities of the quantiles to compute. Values must be
            between 0 and 1 inclusive.
        """
        quantiles = np.sort(quantiles)
        stats = np.quantile(values, quantiles, axis=0)
        if type == "box":
            mappable = self.boxplot(ax, x, stats, *args, **kwargs)
        elif type == "band":
            mappable = self.bandplot(ax, x, stats, *args, **kwargs)
        else:
            raise NotImplementedError(f"Plot of type {type} not yet implemented.")
        return mappable

    def to_quantiles_kwargs(self, n, c=None):
        if c is None:
            c = self._colors
        if isinstance(c, str):
            # Generate symmetric colors
            if c in mpl.colormaps:
                c = mpl.colormaps[c](np.abs(np.linspace(-1.0, 1.0, n)))
            else:
                c = colors.symmetric_from_color(c, n)
        return {"colors": c, **self._kwargs}

    def bandplot(self, ax, x, values, colors=None, *args, **kwargs):
        num_bands = len(values) - 1
        kwargs = {**self.to_quantiles_kwargs(num_bands, c=colors), **kwargs}
        return plottypes.bandplot(ax, x, values, *args, **kwargs)

    def boxplot(self, ax, x, values, colors=None, *args, **kwargs):
        num_bands = len(values) - 1
        kwargs = {**self.to_quantiles_kwargs(num_bands, c=colors), **kwargs}
        return plottypes.boxplot(ax, x, values, *args, **kwargs)

    def line(self, ax, x, y, values, *args, mode="linear", **kwargs):
        """
        Plot a scatter plot using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.scatter`.
        """
        kwargs.pop("transform_first", None)

        if values is not None:
            kwargs = {**self.to_scatter_kwargs(values), **kwargs}
            kwargs.pop("extend", None)
            kwargs["c"] = kwargs.pop("c", values)

        if mode == "spline":
            if np.issubdtype(x.dtype, np.datetime64):
                x_smooth = linspace_datetime64(x.min(), x.max(), max(300, len(x) * 5))
            else:
                x_smooth = np.linspace(x.min(), x.max(), max(300, len(x) * 5))

            spline = make_interp_spline(x, y, k=3)
            y_smooth = spline(x_smooth)

            marker = kwargs.pop("marker", None)
            mappable = ax.plot(x_smooth, y_smooth, *args, **kwargs)
            if marker is not None:
                kwargs.pop("linewidth", None)
                color = mappable[0].get_color()
                self.line(
                    ax,
                    x,
                    y,
                    values,
                    *args,
                    marker=marker,
                    color=color,
                    linewidth=0,
                    **kwargs,
                )

        elif mode == "smooth":
            if np.issubdtype(x.dtype, np.datetime64):
                x_smooth = linspace_datetime64(x.min(), x.max(), max(300, len(x) * 5))
            else:
                x_smooth = np.linspace(x.min(), x.max(), max(300, len(x) * 5))
            func = interp1d(
                x,
                y,
                axis=0,  # interpolate along columns
                bounds_error=False,
                kind="linear",
                fill_value=(y[0], y[-1]),
            )
            y_smooth = func(x_smooth)

            marker = kwargs.pop("marker", None)
            mappable = ax.plot(x_smooth, y_smooth, *args, **kwargs)
            if marker is not None:
                kwargs.pop("linewidth", None)
                color = mappable[0].get_color()
                self.line(
                    ax,
                    x,
                    y,
                    values,
                    *args,
                    marker=marker,
                    color=color,
                    linewidth=0,
                    **kwargs,
                )
        else:
            mappable = ax.plot(x, y, *args, **kwargs)

        return mappable

    def bar(self, ax, x, y, values, *args, mode="linear", **kwargs):
        """
        Plot a scatter plot using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.scatter`.
        """
        kwargs.pop("transform_first", None)

        if values is not None:
            kwargs = {**self.to_scatter_kwargs(values), **kwargs}
            kwargs.pop("extend", None)
            kwargs["c"] = kwargs.pop("c", values)

        mappable = ax.bar(x, y, *args, **kwargs)

        return mappable

    def values_to_colors(self, values, data=None):
        """
        Convert a value or list of values to colors based on this `Style`.

        Parameters
        ----------
        values : float or list of floats
            The values to convert to colors on this `Style`'s color scale.
        """
        mpl_kwargs = self.to_matplotlib_kwargs(data=data)
        cmap = mpl_kwargs["cmap"]
        norm = mpl_kwargs["norm"]
        return cmap(norm(values))

    def legend(self, *args, **kwargs):
        """
        Create the default legend for this `Style`.

        Parameters
        ----------
        *args : list
            Arguments to be passed to the legend method.
        **kwargs : dict
            Keyword arguments to be passed to the legend method.
        """
        if self._legend_style is None:
            return

        try:
            method = getattr(self, self._legend_style)
        except AttributeError:
            raise AttributeError(f"invalid legend type '{self._legend_style}'")

        return method(*args, **kwargs)

    def colorbar(self, *args, **kwargs):
        """Create a colorbar legend for this `Style`."""
        ticks = self._legend_kwargs.get("ticks")
        if ticks is None and self._levels._levels is not None:
            if len(np.unique(np.ediff1d(self._levels._levels))) != 1:
                self._legend_kwargs["ticks"] = self._levels._levels
        return styles.legends.colorbar(*args, **kwargs)

    def disjoint(self, *args, **kwargs):
        """Create a disjoint legend for this `Style`."""
        return styles.legends.disjoint(*args, **kwargs)

    def vector(self, *args, **kwargs):
        """Create a vector legend for this `Style`."""
        return styles.legends.vector(*args, **kwargs)

    def save_legend(
        self, data=None, label=None, filename="legend.png", transparent=True, **kwargs
    ):
        """
        Save a standalone image of the legend associated with this `Style`.

        Parameters
        ----------
        data : earthkit.data.core.Base, optional
            It can sometimes be useful to pass some data in order to
            automatically generate legend labels or color ranges, depending on
            the `Style`.
        label : str, optional
            The label to use for the legend. If not provided, the label will be
            generated automatically based on the `Style`'s units.
        filename : str
            The name of the file to save the legend to. The file format will
            be determined by the file extension (e.g., `.png`, `.pdf`, etc.).
            By default, the legend will be saved as a file named `legend.png`.
        transparent : bool, optional
            If `True`, the saved legend will have a transparent background.
            Otherwise, it will have a white background. Default is `True`.
        **kwargs
            Additional keyword arguments to be passed to the legend method.
        """
        from earthkit.plots import Subplot

        if label is None and data is None:
            label = "{units}" if self.units is not None else ""

        plot_data = [[1, 2], [3, 4]]

        chart = Subplot()
        chart.contourf(plot_data, style=self)

        legend = chart.legend(label=label, **kwargs)[0]

        chart.fig.canvas.draw()
        bbox = legend.ax.get_window_extent().transformed(
            chart.fig.dpi_scale_trans.inverted()
        )

        title_bbox = legend.ax.xaxis.label.get_window_extent().transformed(
            chart.fig.dpi_scale_trans.inverted()
        )

        x, y = chart.fig.get_size_inches()

        xmod, ymod = (
            (0.05, 0.01) if legend.orientation == "horizontal" else (0.01, 0.05)
        )

        bbox.x0 = min(bbox.x0, title_bbox.x0) - x * xmod
        bbox.x1 = max(bbox.x1, title_bbox.x1) + x * xmod
        bbox.y0 = min(bbox.y0, title_bbox.y0) - y * ymod
        bbox.y1 = max(bbox.y1, title_bbox.y1) + y * ymod

        chart.ax.set_xlim(bbox.x0, bbox.x1)
        chart.ax.set_ylim(bbox.y0, bbox.y1)

        plt.savefig(filename, dpi="figure", bbox_inches=bbox, transparent=transparent)


class Categorical(Style):
    """A style for plotting categorical data."""

    def __init__(self, *args, **kwargs):
        kwargs["legend_style"] = "disjoint"
        if isinstance(kwargs.get("levels"), dict):
            kwargs["levels"], kwargs["categories"] = zip(*kwargs["levels"].items())
        if "categories" not in kwargs:
            kwargs["categories"] = kwargs.get("levels")
        super().__init__(*args, **kwargs)


class Quiver(Style):
    """A style for plotting vector data."""

    def __init__(self, *args, colors=None, **kwargs):
        kwargs["legend_style"] = "vector"
        super().__init__(*args, colors=colors, **kwargs)


class Contour(Style):
    """
    A style for plotting contour data.

    Parameters
    ----------
    colors : str or list or matplotlib.colors.Colormap, optional
        The colors to be used in this `Style`. This can be a named matplotlib
        colormap, a list of colors (as named CSS4 colors, hexadecimal colors or
        three (four)-element lists of RGB(A) values), or a pre-defined
        matplotlib colormap object. If not provided, the default colormap of the
        active `schema` will be used.
    linecolors : str or list or matplotlib.colors.Colormap, optional
        The colors to be used for contour lines. This can be a named matplotlib
        colormap, a list of colors (as named CSS4 colors, hexadecimal colors or
        three (four)-element lists of RGB(A) values), or a pre-defined
        matplotlib colormap object. If not provided, the default colormap of the
        active `schema` will be used.
    labels : bool, optional
        If `True`, then contour labels will be displayed.
    label_kwargs : dict, optional
        Additional keyword arguments to be passed to the `clabel` method.
    interpolate : bool, optional
        If `True`, then the data will be interpolated before plotting.
    preferred_method : str, optional
        The preferred method for plotting the data. Must be one of `contour`,
        `contourf`, or `pcolormesh`.
    **kwargs
        Additional keyword arguments to be passed to the `contour` or `contourf`
        method.
    """

    def __init__(
        self,
        colors=None,
        linecolors="viridis_r",
        labels=False,
        label_kwargs=None,
        interpolate=True,
        preferred_method="contour",
        **kwargs,
    ):
        super().__init__(colors=colors, preferred_method=preferred_method, **kwargs)
        self._linecolors = linecolors
        self.labels = labels
        self._label_kwargs = label_kwargs or dict()
        self._interpolate = interpolate
        self._kwargs["linewidths"] = kwargs.get("linewidths", 0.75)

    def plot(self, *args, **kwargs):
        """Plot the data using the `Style`'s defaults."""
        if self._colors is not None:
            if self._interpolate:
                return self.contourf(*args, **kwargs)
            else:
                return self.pcolormesh(*args, **kwargs)
        else:
            return self.contour(*args, **kwargs)

    def to_contour_kwargs(self, data):
        """
        Generate `contour` arguments required for plotting data in this `Style`.

        Parameters
        ----------
        data : numpy.ndarray
            The data to be plotted using this `Style`.
        """
        levels = self.levels(data)

        cmap, norm = styles.colors.cmap_and_norm(
            self._linecolors,
            levels,
            self.normalize,
            self.extend,
        )

        return {
            **{"cmap": cmap, "norm": norm, "levels": levels},
            **self._kwargs,
        }

    def contourf(self, ax, x, y, values, *args, **kwargs):
        """
        Plot shaded contours using this `Style`.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes on which to plot the data.
        x : numpy.ndarray
            The x coordinates of the data to be plotted.
        y : numpy.ndarray
            The y coordinates of the data to be plotted.
        values : numpy.ndarray
            The values of the data to be plotted.
        **kwargs
            Any additional arguments accepted by `matplotlib.axes.Axes.contourf`.
        """
        mappable = super().contourf(ax, x, y, values, *args, **kwargs)
        # if self._linecolors is not None:
        #     self.contour(ax, x, y, values, *args, **kwargs)
        return mappable

    def contour(self, *args, **kwargs):
        """
        Plot line contours using this `Style`.

        Parameters
        ----------
        *args
            The positional arguments to pass to the `contour` method.
        **kwargs
            The keyword arguments to pass to the `contour` method.
        """
        mappable = super().contour(*args, **kwargs)

        if self.labels:
            self.contour_labels(mappable, **self._label_kwargs)

        return mappable

    def contour_labels(
        self,
        mappable,
        label_fontsize=7,
        label_colors=None,
        label_frequency=1,
        label_background=None,
        label_fmt=None,
    ):
        """
        Add labels to a contour plot.

        Parameters
        ----------
        mappable : matplotlib.contour.ContourSet
            The contour plot to which to add labels.
        label_fontsize : int, optional
            The fontsize of the labels.
        label_colors : str or list, optional
            The colors of the labels.
        label_frequency : int, optional
            The frequency of contour levels at which to add labels.
        label_background : str, optional
            The background color of the labels.
        label_fmt : str, optional
            The string format of the labels.
        """
        clabels = mappable.axes.clabel(
            mappable,
            mappable.levels[0::label_frequency],
            inline=True,
            fontsize=label_fontsize,
            colors=label_colors,
            fmt=label_fmt,
            inline_spacing=2,
        )
        if label_background is not None:
            for label in clabels:
                label.set_backgroundcolor(label_background)

        return clabels


class Hatched(Contour):
    """
    A style for plotting hatched contours.

    Parameters
    ----------
    *args
        The positional arguments to pass to the `Contour` constructor.
    hatches : str, optional
        The pattern of hatching to use.
    background_colors : list, optional
        The colors to use for the background of the hatched contours.
    **kwargs
        The keyword arguments to pass to the `Contour` constructor.
    """

    def __init__(self, *args, hatches=".", background_colors=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hatches = hatches
        self._foreground_colors = self._colors
        self._colors = background_colors or [(0, 0, 0, 0)]

    def __eq__(self, other):
        keys = ["_levels", "_colors", "_foreground_colors", "hatches"]
        return all(
            [getattr(self, key, None) == getattr(other, key, None) for key in keys]
        )

    def contourf(self, *args, **kwargs):
        """
        Plot hatched shaded contours using this `Style`.

        Parameters
        ----------
        *args
            The positional arguments to pass to the `contourf` method.
        **kwargs
            The keyword arguments to pass to the `contourf` method.
        """
        mappable = super().contourf(*args, hatches=self.hatches, **kwargs)

        linecolors = colors.expand(self._foreground_colors, mappable.levels)

        mappable.set_edgecolors(linecolors)
        mappable.set_facecolors([(0, 0, 0, 0)] * len(mappable.levels))
        mappable.set_linewidth(0)

        return mappable

    def colorbar(self, *args, **kwargs):
        """
        Create a colorbar legend for this `Style`.

        Parameters
        ----------
        *args
            The positional arguments to pass to the `colorbar` method.
        **kwargs
            The keyword arguments to pass to the `colorbar` method.
        """
        colorbar = super().colorbar(*args, **kwargs)

        levels = colorbar.mappable.levels

        linecolors = colors.expand(self._foreground_colors, levels)
        for i, artist in enumerate(colorbar.solids_patches):
            artist.set_edgecolor(linecolors[i])

        return colorbar

    def disjoint(self, layer, *args, **kwargs):
        """
        Create a disjoint legend for this `Style`.

        Parameters
        ----------
        layer : earthkit.maps.charts.layers.Layer
            The layer for which to create a legend.
        *args
            The positional arguments to pass to the `dis
        **kwargs
            The keyword arguments to pass to the `disjoint` method.
        """
        legend = super().disjoint(layer, *args, **kwargs)

        linecolors = colors.expand(self._foreground_colors, layer.mappable.levels)

        for color, artist in zip(linecolors, legend.get_patches()):
            artist.set_edgecolor(color)
            artist.set_linewidth(0.0)

        return legend


DEFAULT_STYLE = Style()

DEFAULT_QUIVER_STYLE = Quiver()

_STYLE_KWARGS = list(
    set(inspect.getfullargspec(Style)[0] + inspect.getfullargspec(Contour)[0])
)

_OVERRIDE_KWARGS = ["labels"]


def compare_attributes(self, other, keys):
    def is_equal(x, y):
        # Check if both are numpy arrays
        if isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
            return np.array_equal(x, y)
        # If one is an array and the other isn't, they are not equal
        elif isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
            return False
        # Default to standard equality check for non-array types
        else:
            return x == y

    # Use the is_equal function for each key in your check
    try:
        return all(
            is_equal(getattr(self, key, None), getattr(other, key, None))
            for key in keys
        )
    except ValueError:
        return False
