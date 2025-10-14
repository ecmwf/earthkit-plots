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
import os
import re

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from earthkit.plots.ancillary import find_logo
from earthkit.plots.components.layers import LayerGroup
from earthkit.plots.components.layouts import rows_cols
from earthkit.plots.components.maps import Map
from earthkit.plots.components.subplots import Subplot
from earthkit.plots.metadata import formatters
from earthkit.plots.schemas import schema
from earthkit.plots.utils import string_utils


class Figure:
    """
    The overall canvas onto which subplots are drawn.

    A Figure is a container for one or more Subplots, each of which can contain
    one or more Layers. The Figure is responsible for managing the layout of
    Subplots and Layers, as well as providing methods for adding common
    elements like legends and titles.

    Parameters
    ----------
    rows : int, optional
        The number of rows in the figure.
    columns : int, optional
        The number of columns in the figure.
    size : list, optional
        The size of the figure in inches. This can be a list or tuple of two
        floats representing the width and height of the figure.
    domain : earthkit.geo.Domain, optional
        The domain of the data being plotted. This is used to set the extent
        and projection of the map.
    crs : cartopy.crs.CRS, optional
        The CRS of the map. If not provided, it will be inferred from the
        domain. See https://cartopy.readthedocs.io/stable/reference/projections.html#cartopy-projections for a list of available CRSs.
    kwargs : dict, optional
        Additional keyword arguments to pass to :class:`matplotlib.gridspec.GridSpec`.
    """

    def __init__(
        self, rows=None, columns=None, size=None, domain=None, crs=None, **kwargs
    ):
        self.rows = rows
        self.columns = columns

        self.fig = None
        self.gridspec = None

        self._row = 0
        self._col = 0

        self._figsize = self._parse_size(size)
        self._gridspec_kwargs = kwargs

        self._domain = domain
        self._crs = crs

        self.subplots = []
        self._last_subplot_location = None
        self._isubplot = 0

        self._queue = []
        self._subplot_queue = []

        self.attributions = []
        self.logos = []

        if None not in (self.rows, self.columns):
            self._setup()

    def _setup(self):
        """Set up the figure the first time it is needed."""
        self.fig = plt.figure(figsize=self._figsize, constrained_layout=True)
        self.gridspec = self.fig.add_gridspec(
            self.rows, self.columns, **self._gridspec_kwargs
        )

    def _defer_until_setup(method):
        """Decorator to defer calling a method until the figure is setup."""

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.subplots:
                self._queue.append((method, args, kwargs))
            else:
                return method(self, *args, **kwargs)

        return wrapper

    def _defer_subplot(method):
        """Decorator to defer calling a method until the subplots are setup."""

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if self.rows is None or self.columns is None:
                self._subplot_queue.append((method, args, kwargs))
            else:
                return method(self, *args, **kwargs)

        return wrapper

    def __len__(self):
        return len(self.subplots)

    def __getitem__(self, i):
        return self.subplots[i]

    def _parse_size(self, size):
        """Parse the size of the figure."""
        if size is not None:
            figsize = []
            for length in size:
                if isinstance(length, str):
                    if length.isnumeric():
                        length = float(length)
                    else:
                        match = re.match(r"([0-9]+)([a-z]+)", length, re.I)
                        value, units = match.groups()
                        value = float(value)
                        if units == "px":
                            length = value / schema.figure.dpi
                        elif units == "cm":
                            length = value * 2.54
                figsize.append(length)
        else:
            figsize = size
        return figsize

    def apply_to_subplots(method):
        """Decorator to apply a method to all subplots in the figure."""

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            success = False
            for subplot in self.subplots:
                # try:
                getattr(subplot, method.__name__)(*args, **kwargs)
                success = True
            # except (NotImplementedError, AttributeError):
            #     continue
            if not success:
                raise NotImplementedError(
                    f"No subplots have method '{method.__name__}'"
                )

        return wrapper

    def iterate_subplots(method):
        """Decorator to iterate simultaneously over data and subplots."""

        @functools.wraps(method)
        def wrapper(self, data, *args, **kwargs):
            if not hasattr(data, "__len__"):
                data = [data]
            if not self.subplots:
                self.rows, self.columns = rows_cols(
                    len(data), rows=self.rows, columns=self.columns
                )
                self._setup()
                for _ in range(len(data)):
                    self.add_map()
            for datum, subplot in zip(data, self.subplots):
                getattr(subplot, method.__name__)(datum, *args, **kwargs)

        return wrapper

    def _determine_row_column(self, row, column):
        """Determine the row and column of the next subplot."""
        if row is not None and column is not None:
            pass
        else:
            if self._last_subplot_location is None:
                row, column = (0, -1)
            if row is None:
                row = self._last_subplot_location[0]
            if column is None:
                column = self._last_subplot_location[1]
            if column < self.columns - 1:
                column = column + 1
            else:
                column = 0
                row = row + 1
        self._last_subplot_location = row, column
        return row, column

    def add_subplot(self, row=None, column=None, **kwargs):
        """
        Add a subplot to the figure.

        Parameters
        ----------
        row : int, optional
            The row in which to place the subplot.
        column : int, optional
            The column in which to place the subplot.
        kwargs : dict, optional
            Additional keyword arguments to pass to the :class:`Subplot` constructor.
        """
        row, column = self._determine_row_column(row, column)
        subplot = Subplot(row=row, column=column, figure=self, **kwargs)
        self.subplots.append(subplot)
        return subplot

    @_defer_subplot
    def add_map(self, row=None, column=None, domain=None, crs=None, **kwargs):
        """
        Add a map to the figure.

        Parameters
        ----------
        row : int, optional
            The row in which to place the subplot.
        column : int, optional
            The column in which to place the subplot.
        domain : earthkit.geo.Domain, optional
            The domain of the data being plotted. This is used to set the extent
            and projection of the map.
        crs : cartopy.crs.CRS, optional
            The CRS of the map. If not provided, it will be inferred from the
            domain or set to PlateCarree (regular lat-lon).
        kwargs : dict, optional
            Additional keyword arguments to pass to the :class:`Map` constructor.
        """
        if domain is None:
            domain = self._domain
        if crs is None:
            crs = self._crs
        row, column = self._determine_row_column(row, column)
        subplot = Map(
            row=row, column=column, domain=domain, crs=crs, figure=self, **kwargs
        )
        self.subplots.append(subplot)
        return subplot

    def subplot_titles(self, *args, **kwargs):
        """
        Set the titles of all subplots.

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
        kwargs : dict, optional
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.title`.
        """
        return [subplot.title(*args, **kwargs) for subplot in self.subplots]

    def distinct_legend_layers(self, subplots=None):
        """
        Get a list of layers with distinct styles.

        Parameters
        ----------
        subplots : list, optional
            If provided, only these subplots will be considered when identifying
            unique styles.
        """
        if subplots is None:
            subplots = self.subplots

        subplot_layers = [subplot.distinct_legend_layers for subplot in subplots]
        subplot_layers = [item for sublist in subplot_layers for item in sublist]

        groups = []
        for layer in subplot_layers:
            for i in range(len(groups)):
                if groups[i][0].style == layer.style:
                    groups[i].append(layer)
                    break
            else:
                groups.append([layer])

        groups = [LayerGroup(layers) for layers in list(groups)]

        return groups

    @_defer_until_setup
    @schema.legend.apply()
    def legend(self, *args, subplots=None, location=None, **kwargs):
        """
        Add legends to the figure.

        Parameters
        ----------
        subplots : list, optional
            If provided, only these subplots will have legends.
        location : str or list, optional
            The location of the legend. If a list, each item is the location
            for the corresponding subplot.
        kwargs : dict, optional
            Additional keyword arguments to pass to the Subplot legend method.
        """
        legends = []

        anchor = None
        non_cbar_layers = []
        for i, layer in enumerate(self.distinct_legend_layers(subplots)):
            if isinstance(location, (list, tuple)):
                loc = location[i]
            else:
                loc = location
            if layer.style is not None:
                legend = layer.style.legend(
                    layer,
                    *args,
                    location=loc,
                    **kwargs,
                )
            if legend.__class__.__name__ != "Colorbar":
                non_cbar_layers.append(layer)
            else:
                anchor = layer.axes[0].get_anchor()
            legends.append(legend)

        if anchor is not None:
            for layer in non_cbar_layers:
                for ax in layer.axes:
                    ax.set_anchor(anchor)

        return legends

    @_defer_until_setup
    @apply_to_subplots
    def cities(self, *args, **kwargs):
        """
        Add cities to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.cities`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def coastlines(self, *args, **kwargs):
        """
        Add coastlines to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.coastlines`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def countries(self, *args, **kwargs):
        """
        Add countries to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.countries`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def urban_areas(self, *args, **kwargs):
        """
        Add urban areas to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.urban_areas`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def land(self, *args, **kwargs):
        """
        Add land polygons to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.land`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def borders(self, *args, **kwargs):
        """
        Add borders to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.borders`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def standard_layers(self, *args, **kwargs):
        """
        Add quick layers to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.quick_layers`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def administrative_areas(self, *args, **kwargs):
        """
        Add administrative areas to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.administrative_areas`.
        """

    @_defer_until_setup
    @apply_to_subplots
    def stock_img(self, *args, **kwargs):
        """
        Add a stock image to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.stock_img`.
        """

    @iterate_subplots
    def block(self, *args, **kwargs):
        """
        Plot a pcolormesh on every subplot in the figure.

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

    @iterate_subplots
    def gridpoints(self, *args, **kwargs):
        """
        Plot grid point centroids on every subplot in the figure.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot grid_points.
        x : str, optional
            The name of the x-coordinate variable in the data source.
        y : str, optional
            The name of the y-coordinate variable in the data source.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.scatter`.
        """

    @iterate_subplots
    def plot(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def quickplot(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def pcolormesh(self, *args, **kwargs):
        """
        Plot a pcolormesh on every subplot in the figure.

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
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.pcolormesh`.
        """

    @iterate_subplots
    def contourf(self, *args, **kwargs):
        """
        Plot a filled contour plot on every subplot in the figure.

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
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.contourf`.
        """

    @iterate_subplots
    def contour(self, *args, **kwargs):
        """
        Plot a line contour plot on every subplot in the figure.

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
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.contourf`.
        """

    @_defer_until_setup
    def gridlines(self, *args, sharex=True, sharey=True, **kwargs):
        """
        Add gridlines to every :class:`Map` subplot in the figure.

        Parameters
        ----------
        sharex : bool, optional
            If True, only the bottom row of subplots will have x-axis gridlines.
        sharey : bool, optional
            If True, only the leftmost column of subplots will have y-axis
            gridlines.
        kwargs : dict, optional
            Additional keyword arguments to pass to the :meth:`Map.gridlines` method.
        """
        draw_labels = kwargs.pop("draw_labels", ["left", "bottom"])
        if draw_labels is True:
            draw_labels = ["left", "right", "bottom", "top"]
        for subplot in self.subplots:
            if draw_labels:
                subplot_draw_labels = [item for item in draw_labels]
                if sharex and all(
                    sp.domain == subplot.domain
                    for sp in [s for s in self.subplots if s.column == subplot.column]
                ):
                    if "top" in draw_labels and subplot.row != 0:
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "top"
                        ]
                    if "bottom" in draw_labels and subplot.row != max(
                        sp.row for sp in self.subplots
                    ):
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "bottom"
                        ]
                if sharey and all(
                    sp.domain == subplot.domain
                    for sp in [s for s in self.subplots if s.row == subplot.row]
                ):
                    if "left" in draw_labels and subplot.column != 0:
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "left"
                        ]
                    if "right" in draw_labels and subplot.column != max(
                        sp.column for sp in self.subplots
                    ):
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "right"
                        ]
            else:
                subplot_draw_labels = False
            subplot.gridlines(*args, draw_labels=subplot_draw_labels, **kwargs)

    @schema.suptitle.apply()
    def title(self, label=None, unique=True, grouped=True, y=None, **kwargs):
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
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.suptitle`.
        """
        if label is None:
            label = self._default_title_template
        label = self.format_string(label, unique, grouped)

        if y is None:
            y = self._get_suptitle_y()

        result = self.fig.suptitle(label, y=y, **kwargs)
        return result

    def draw(self):
        """
        Draw the figure and all its subplots.

        This calls :meth:`matplotlib.backend_bases.FigureCanvasBase.draw` to render
        the figure and then resets face colors for all layers.
        """
        self.fig.canvas.draw()
        for subplot in self.subplots:
            for layer in subplot.layers:
                layer.reset_facecolors()

    def _get_suptitle_y(self):
        """
        Calculate suptitle y position by using the axis positions and estimated
        title heights.

        This method uses :meth:`matplotlib.axes.Axes.get_position` to determine
        the position of axes and calculates an appropriate y position for the
        suptitle based on the highest subplot and estimated title height.

        Returns
        -------
        float
            The y position for the suptitle in figure coordinates.
        """
        if not self.subplots:
            return 0.95  # Default fallback

        # Find the highest subplot position
        max_ax_top = max(ax.get_position().y1 for ax in self.fig.axes)

        fig_height = self.fig.get_size_inches()[1]

        # Get the default title font size (or use a reasonable default)
        title_fontsize = 12
        try:
            # Try to get font size from the first subplot's title
            first_ax = self.fig.axes[0]
            if first_ax.get_title():
                title_fontsize = first_ax.title.get_fontsize()
        except IndexError:
            # IndexError: self.fig.axes is empty
            pass

        # Convert font size to figure-relative units using actual figure DPI
        fig_dpi = self.fig.get_dpi()
        title_height_fig = (title_fontsize / fig_dpi) / fig_height

        # Add some padding above the title
        title_padding = 0.15  # 15% of figure height

        suptitle_y = max_ax_top + title_height_fig + title_padding

        return suptitle_y

    def format_string(self, string, unique=True, grouped=True):
        """
        Format a string with the subplot titles.

        Parameters
        ----------
        string : str
            The string to format.
        unique : bool, optional
            If True, format keys which are uniform across subplots/layers will
            produce a single result. For example, if all data layers have the
            same `variable_name`, only one variable name will appear in the
            title.
        grouped : bool, optional
            If True, a single title will be generated to represent all data
            layers, with each format key evaluating to a list where layers
            differ - e.g. `"{variable} at {time}"` might be evaluated to
            `"temperature and wind at 2023-01-01 00:00".
            If False, the title will be duplicated by the number of subplots/
            layers - e.g. `"{variable} at {time}"` might be evaluated to
            `"temperature at 2023-01-01 00:00 and wind at 2023-01-01 00:00".
        """
        if not grouped:
            results = [
                subplot.format_string(string, unique, grouped)
                for subplot in self.subplots
            ]
            result = string_utils.list_to_human(results)
        else:
            result = formatters.FigureFormatter(self.subplots, unique=unique).format(
                string
            )
        return result

    @property
    def _default_title_template(self):
        return self.subplots[0]._default_title_template

    def _release_queue(self):
        if self._subplot_queue:
            self.rows, self.columns = rows_cols(
                len(self._subplot_queue), rows=self.rows, columns=self.columns
            )
            self._setup()
        for item in self._subplot_queue:
            method, args, kwargs = item
            method(self, *args, **kwargs)
        for queued_method, queued_args, queued_kwargs in self._queue:
            queued_method(self, *queued_args, **queued_kwargs)
        if self.attributions:
            attribution_text = "; ".join(self.attributions)
            x = 0.5 if not self.logos else 0.05
            y = -0.02
            ha = "center" if not self.logos else "left"

            self.fig.text(
                x,
                y,
                attribution_text,
                ha=ha,
                va="top",
                fontsize=9,
                color="gray",
                wrap=True,
            )
        if self.logos:
            # Place each logo horizontally, bottom-right, with some spacing
            logo_width = 0.12  # fraction of figure width
            logo_height = 0.05  # fraction of figure height
            spacing = 0.01  # horizontal spacing
            # Start from right, go left
            for i, image_file in enumerate(reversed(self.logos)):
                if not os.path.exists(image_file):
                    image_file = find_logo(image_file)
                logo = mpimg.imread(image_file)
                left = 1.0 - (i + 1) * logo_width - i * spacing - 0.05
                bottom = -0.05  # 0.01 margin from bottom
                ax_logo = self.fig.add_axes(
                    [left, bottom, logo_width, logo_height], zorder=100
                )
                ax_logo.imshow(logo)
                ax_logo.axis("off")
        return self

    def show(self, *args, **kwargs):
        """
        Display the figure.

        This calls :func:`matplotlib.pyplot.show` to display the figure.
        """
        self._release_queue()
        return plt.show(*args, **kwargs)

    def save(self, *args, bbox_inches="tight", **kwargs):
        """
        Save the figure to a file.

        Parameters
        ----------
        fname : str or file-like object
            The file to which to save the figure.
        bbox_inches : str, optional
            The bounding box in inches to use when saving the figure.
        kwargs : dict, optional
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.savefig`.
        """
        self._release_queue()
        return plt.savefig(
            *args,
            bbox_inches=bbox_inches,
            dpi=kwargs.pop("dpi", schema.figure.dpi),
            **kwargs,
        )

    def _resize(self):
        """Resize the figure to fit its axes."""
        self._release_queue()
        return resize_figure_to_fit_axes(self.fig)

    def add_attribution(self, attribution):
        """
        Add an attribution to the figure.

        Parameters
        ----------
        attribution : str
            The attribution text to add to the figure.
        """
        if attribution not in self.attributions:
            self.attributions.append(attribution)

    def add_logo(self, logo):
        """
        Add a logo to the figure.

        Parameters
        ----------
        logo : str
            Either the name of a built-in logo, or a path to the logo image file to add to the figure.
        """
        if logo not in self.logos:
            self.logos.append(logo)


def resize_figure_to_fit_axes(fig):
    """
    Adjust the size of a Matplotlib figure so that it fits its axes perfectly.

    This function calculates the bounding box of all axes in the figure and
    resizes the figure to fit them exactly, removing any extra whitespace.

    Parameters
    ----------
    fig : :class:`matplotlib.figure.Figure`
        A Matplotlib Figure object to resize.

    Returns
    -------
    :class:`matplotlib.figure.Figure`
        The resized figure object.
    """
    # Get the current size of the figure and its DPI
    current_size = fig.get_size_inches()

    # Initialize variables to find the min/max extents of all axes
    min_left = 1.0
    max_right = 0.0
    min_bottom = 1.0
    max_top = 0.0

    # Loop through all axes to find the outer bounds
    for ax in fig.axes:
        bbox = ax.get_position()
        min_left = min(min_left, bbox.x0)
        max_right = max(max_right, bbox.x1)
        min_bottom = min(min_bottom, bbox.y0)
        max_top = max(max_top, bbox.y1)

    # Calculate new figure size
    new_width = (max_right - min_left) * current_size[0]
    new_height = (max_top - min_bottom) * current_size[1]

    # Resize figure
    fig.set_size_inches(new_width, new_height)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    return fig
