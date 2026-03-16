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
        self._style_context = None

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
        self._released = False

        self.attributions = []
        self.logos = []
        self._ancillary_cache = {}

        self._style_context = None
        self._jupyter_display_hook = None

        if None not in (self.rows, self.columns):
            self._setup()

    def _setup(self):
        """Set up the figure the first time it is needed."""
        self._style_context = schema.style_context()
        self._style_context.__enter__()
        self.fig = plt.figure(figsize=self._figsize, constrained_layout=True)
        self.gridspec = self.fig.add_gridspec(
            self.rows, self.columns, **self._gridspec_kwargs
        )
        self._register_jupyter_display()

    def _register_jupyter_display(self):
        """Register a post_execute hook so the figure auto-displays in Jupyter."""
        try:
            ip = get_ipython()  # noqa: F821
        except NameError:
            return
        if ip is None:
            return

        def _display_once():
            self._jupyter_display_hook = None
            ip.events.unregister("post_execute", _display_once)
            self._prepare_for_display()
            try:
                plt.show()
            finally:
                self._exit_style_context()

        self._jupyter_display_hook = (_display_once, ip)
        ip.events.register("post_execute", _display_once)

    def _cancel_jupyter_display(self):
        """Unregister the auto-display hook (called when show/save is explicit)."""
        if self._jupyter_display_hook is not None:
            hook_fn, ip = self._jupyter_display_hook
            self._jupyter_display_hook = None
            try:
                ip.events.unregister("post_execute", hook_fn)
            except ValueError:
                pass

    def _exit_style_context(self):
        """Exit the style context, restoring matplotlib's global rcParams."""
        if self._style_context is not None:
            self._style_context.__exit__(None, None, None)
            self._style_context = None

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
                            from matplotlib import rcParams as _rc

                            length = value / _rc["figure.dpi"]
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
            import xarray as xr

            groupby = kwargs.pop("groupby", None)
            if groupby is not None:
                from earthkit.plots.quickplot import _coerce_to_fieldlist, _group_data

                fields = _coerce_to_fieldlist(data)
                grouped = _group_data(fields, groupby)
                data_items = list(grouped.values())
            elif isinstance(data, xr.Dataset):
                # Yield one DataArray per variable so subplots pair correctly.
                data_items = [data[v] for v in data.data_vars]
            else:
                if not hasattr(data, "__len__"):
                    data = [data]
                data_items = list(data)
            if not self.subplots:
                self.rows, self.columns = rows_cols(
                    len(data_items), rows=self.rows, columns=self.columns
                )
                self._setup()
                for _ in range(len(data_items)):
                    self.add_map()
            for datum, subplot in zip(data_items, self.subplots):
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

    @apply_to_subplots
    def xticks(self, *args, **kwargs):
        """
        Set x-ticks on all subplots.

        Parameters
        ----------
        Accepts the same arguments as `matplotlib.axes.Axes.set_xticks`.
        """

    @apply_to_subplots
    def yticks(self, *args, **kwargs):
        """
        Set y-ticks on all subplots.

        Parameters
        ----------
        Accepts the same arguments as `matplotlib.axes.Axes.set_yticks`.
        """

    @apply_to_subplots
    def xlabel(self, *args, **kwargs):
        """
        Set x-label on all subplots.

        Parameters
        ----------
        Accepts the same arguments as `matplotlib.axes.Axes.set_xlabel`.
        """

    @apply_to_subplots
    def ylabel(self, *args, **kwargs):
        """
        Set y-label on all subplots.

        Parameters
        ----------
        Accepts the same arguments as `matplotlib.axes.Axes.set_ylabel`.
        """

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

    @_defer_subplot
    def add_timeseries(self, row=None, column=None, **kwargs):
        """
        Add a :class:`~earthkit.plots.temporal.timeseries.TimeSeries` subplot
        to the figure.

        Returns a :class:`TimeSeries` instance pre-configured for time series
        visualisation (sensible default size, automatic time-axis margin
        removal on show/save).

        Parameters
        ----------
        row : int, optional
            The row in which to place the subplot.
        column : int, optional
            The column in which to place the subplot.
        kwargs : dict, optional
            Additional keyword arguments passed to the
            :class:`~earthkit.plots.temporal.timeseries.TimeSeries` constructor.

        Returns
        -------
        TimeSeries

        Examples
        --------
        >>> fig = ekp.Figure(rows=2, columns=1)
        >>> ts1 = fig.add_timeseries()
        >>> ts1.line(t2m_da, x="valid_time", units="celsius")
        >>> ts2 = fig.add_timeseries()
        >>> ts2.band(mean_da, std_da, x="valid_time", units="celsius")
        >>> fig.show()
        """
        from earthkit.plots.temporal.timeseries import TimeSeries

        row, column = self._determine_row_column(row, column)
        subplot = TimeSeries(row=row, column=column, size=None, figure=self, **kwargs)
        self.subplots.append(subplot)
        return subplot

    def add_hovmoller(self, row=None, column=None, **kwargs):
        """
        Add a :class:`~earthkit.plots.temporal.hovmoller.Hovmoller` subplot
        to the figure.

        Returns a :class:`Hovmoller` instance pre-configured for Hovmöller
        diagrams (time on one axis, pressure/height on the other, with
        automatic axis inversion for pressure coordinates).

        Parameters
        ----------
        row : int, optional
            The row in which to place the subplot.
        column : int, optional
            The column in which to place the subplot.
        **kwargs :
            Additional keyword arguments passed to the
            :class:`~earthkit.plots.temporal.hovmoller.Hovmoller` constructor.
            Key options include ``time_axis`` (``"x"`` or ``"y"``) and
            ``invert_vertical`` (``True``, ``False``, or ``"auto"``).

        Returns
        -------
        Hovmoller

        Examples
        --------
        >>> fig = ekp.Figure()
        >>> hov = fig.add_hovmoller()
        >>> hov.contourf(da, style="auto")
        >>> fig.show()
        """
        from earthkit.plots.temporal.hovmoller import Hovmoller

        row, column = self._determine_row_column(row, column)
        subplot = Hovmoller(row=row, column=column, size=None, figure=self, **kwargs)
        self.subplots.append(subplot)
        return subplot

    def add_climatology(self, row=None, column=None, **kwargs):
        """
        Add a :class:`~earthkit.plots.temporal.climatology.Climatology` subplot
        to the figure.

        Returns a :class:`Climatology` instance whose :meth:`line` method
        automatically splits multi-year data by year and remaps each year onto
        a common Jan-to-Dec x-axis.

        Parameters
        ----------
        row : int, optional
            The row in which to place the subplot.
        column : int, optional
            The column in which to place the subplot.
        **kwargs :
            Additional keyword arguments passed to the
            :class:`~earthkit.plots.temporal.climatology.Climatology` constructor.

        Returns
        -------
        Climatology

        Examples
        --------
        >>> fig = ekp.Figure(rows=1, columns=1)
        >>> ax = fig.add_climatology()
        >>> ax.line(da)
        >>> fig.show()
        """
        from earthkit.plots.temporal.climatology import Climatology

        row, column = self._determine_row_column(row, column)
        subplot = Climatology(row=row, column=column, size=None, figure=self, **kwargs)
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
        import matplotlib.lines as mlines

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

        # Collect proxy-label layers (e.g. from spaghetti or labelled contours)
        # and render them as a line legend on each subplot that has them.
        _subplots = subplots if subplots is not None else self.subplots
        for subplot in _subplots:
            proxy_handles = []
            for layer in subplot.layers:
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
                        mlines.Line2D(
                            [], [], color=color, linewidth=lw, label=proxy_label
                        )
                    )
            if proxy_handles:
                subplot.ax.legend(handles=proxy_handles)

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
        interpolate: earthkit.plots.resample.Unstructured, dict, optional
            A :class:`plots.resample.Unstructured` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Unstructured` class.
            If not provided and the data is unstructured, an `Unstructured` class is created
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
        interpolate: earthkit.plots.resample.Unstructured, dict, optional
            A :class:`plots.resample.Unstructured` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Unstructured` class.
            If not provided and the data is unstructured, an `Unstructured` class is created
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
        interpolate: earthkit.plots.resample.Unstructured, dict, optional
            A :class:`plots.resample.Unstructured` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Unstructured` class.
            If not provided and the data is unstructured, an `Unstructured` class is created
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
        interpolate: earthkit.plots.resample.Unstructured, dict, optional
            A :class:`plots.resample.Unstructured` class which will be applied to data
            prior to plotting. This is required for unstructured data with no grid information,
            but it can also be useful if you want to view structured data at a different resolution.
            If a dictionary, it is passed as keyword arguments to instantiate the `Unstructured` class.
            If not provided and the data is unstructured, an `Unstructured` class is created
            by detecting the resolution of the data.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.contourf`.
        """

    @iterate_subplots
    def line(self, *args, **kwargs):
        """
        Plot a line on every subplot in the figure.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            The data to plot.
        **kwargs
            Additional keyword arguments forwarded to each subplot's
            :meth:`~earthkit.plots.components.subplots.Subplot.line`.
        """

    @iterate_subplots
    def multiboxplot(self, *args, **kwargs):
        """
        Plot a multiboxplot on every subplot in the figure.

        Parameters
        ----------
        data : xarray.DataArray
            The data to plot.
        **kwargs
            Additional keyword arguments forwarded to each subplot's
            :meth:`~earthkit.plots.components.subplots.Subplot.multiboxplot`.
        """

    def plot(
        self,
        method,
        data,
        *args,
        row=None,
        col=None,
        subplot_class=None,
        subplot_titles=None,
        rows=None,
        columns=None,
        size=None,
        **kwargs,
    ):
        """
        Apply a plotting method across panels of an xarray Dataset.

        This is the generic FacetGrid-style engine for ``Figure``.  It splits
        *data* into a grid of subplots according to *row* and *col*, creates
        one subplot per panel using *subplot_class*, and calls *method* on
        each panel's data slice.

        Parameters
        ----------
        method : str
            Name of the subplot method to call on each panel
            (e.g. ``"line"``, ``"bar"``, ``"contourf"``).
        data : xarray.Dataset or xarray.DataArray
            The data to distribute across panels.  When *data* is a Dataset,
            ``"variable"`` is a special token for *row* / *col* that means
            "split by data variable".  Any other string is treated as a
            coordinate name along which to select unique values.
        *args :
            Positional arguments forwarded to the subplot method.
        row : str or None, optional
            Dimension to vary along rows.  Use ``"variable"`` to put each
            Dataset variable in its own row, or pass a coordinate name
            (e.g. ``"step"``).  Default is ``None`` (single row).
        col : str or None, optional
            Dimension to vary along columns.  Same tokens as *row*.
            Default is ``None`` (single column).
        subplot_class : type, optional
            Subplot class to instantiate for each panel.  Defaults to
            :class:`~earthkit.plots.components.subplots.Subplot`.
        subplot_titles : str or None, optional
            Format string for per-panel titles.  Supports metadata
            placeholders such as ``"{variable_name}"``.  Set to ``None``
            to suppress titles.
        rows : int, optional
            Override the total number of rows in the Figure grid.
        columns : int, optional
            Override the total number of columns in the Figure grid.
        size : tuple, optional
            Figure size ``(width, height)`` in inches.  Defaults to
            ``(8 * n_cols, 4 * n_rows)``.
        **kwargs :
            Additional keyword arguments forwarded to the subplot method.

        Returns
        -------
        self
            Returns the Figure so calls can be chained.

        Examples
        --------
        Two-variable Dataset, one row per variable:

        >>> fig = ekp.Figure()
        >>> fig.plot("line", ds, row="variable")
        >>> fig.show()

        Variable × step grid:

        >>> fig = ekp.Figure()
        >>> fig.plot("line", ds, row="variable", col="step")
        >>> fig.show()

        Single DataArray across ensemble members:

        >>> fig = ekp.Figure()
        >>> fig.plot("line", ds["t2m"], col="number")
        >>> fig.show()
        """
        import xarray as xr

        if subplot_class is None:
            subplot_class = Subplot

        # --- Resolve row/col dimensions into (row_vals, col_vals) lists ------
        def _dim_vals(data, dim):
            """Return the unique values for a panel dimension token."""
            if dim is None:
                return [None]
            if dim == "variable":
                if isinstance(data, xr.Dataset):
                    return list(data.data_vars)
                return [None]
            # Treat as a coordinate name
            if isinstance(data, xr.Dataset):
                coord = data[list(data.data_vars)[0]][dim]
            else:
                coord = data[dim]
            return list(dict.fromkeys(coord.values.tolist()))

        row_vals = _dim_vals(data, row)
        col_vals = _dim_vals(data, col)

        n_rows = rows if rows is not None else len(row_vals)
        n_cols = columns if columns is not None else len(col_vals)

        # --- Set up the Figure grid if not already done ----------------------
        if self.rows is None or self.columns is None:
            self.rows = n_rows
            self.columns = n_cols
        if self.fig is None:
            if size is None:
                size = (8 * n_cols, 4 * n_rows)
            self._figsize = self._parse_size(size)
            self._setup()

        # --- Build panels -----------------------------------------------------
        def _slice(data, row_dim, row_val, col_dim, col_val):
            """Extract the DataArray/Dataset slice for one panel."""
            result = data
            for dim, val in ((row_dim, row_val), (col_dim, col_val)):
                if dim is None or val is None:
                    continue
                if dim == "variable":
                    result = result[val] if isinstance(result, xr.Dataset) else result
                else:
                    result = result.sel({dim: val})
            return result

        for r_i, r_val in enumerate(row_vals):
            for c_i, c_val in enumerate(col_vals):
                panel_data = _slice(data, row, r_val, col, c_val)
                sp = subplot_class(row=r_i, column=c_i, figure=self)
                self.subplots.append(sp)
                getattr(sp, method)(panel_data, *args, **kwargs)
                if subplot_titles is not None:
                    try:
                        sp.title(subplot_titles)
                    except Exception:
                        pass

        return self

    def timeseries(
        self,
        data,
        *args,
        row=None,
        col=None,
        plot="line",
        subplot_titles="{variable_name}",
        rows=None,
        columns=None,
        size=None,
        xticks=None,
        yticks=None,
        xlabel=None,
        ylabel=None,
        **kwargs,
    ):
        """
        Plot time series data across a grid of panels.

        A convenience wrapper around :meth:`plot` that uses
        :class:`~earthkit.plots.temporal.timeseries.TimeSeries` subplots and
        applies time-axis formatting.

        When *data* is an xarray Dataset with more than one variable, ``row``
        defaults to ``"variable"`` so each variable appears in its own row.

        Parameters
        ----------
        data : xarray.Dataset or xarray.DataArray
            The time series data to distribute across panels.
        *args :
            Positional arguments forwarded to the subplot plot method.
        row : str or None, optional
            Dimension to vary along rows.  Defaults to ``"variable"`` when
            *data* is a multi-variable Dataset.
        col : str or None, optional
            Dimension to vary along columns (e.g. a coordinate name like
            ``"step"`` or ``"number"``).  Default is ``None``.
        plot : str, optional
            Subplot method to call on each panel.  Default is ``"line"``.
        subplot_titles : str or None, optional
            Per-panel title format string.  Default is ``"{variable_name}"``.
        rows : int, optional
            Override the total number of rows.
        columns : int, optional
            Override the total number of columns.
        size : tuple, optional
            Figure size ``(width, height)`` in inches.
        xticks : str or dict, optional
            Tick configuration for the x-axis of every panel.
        yticks : str or dict, optional
            Tick configuration for the y-axis of every panel.
        xlabel : str, optional
            x-axis label applied to every panel.
        ylabel : str, optional
            y-axis label applied to every panel.
        **kwargs :
            Additional keyword arguments forwarded to the subplot method.

        Returns
        -------
        self

        Examples
        --------
        Multi-variable Dataset – one row per variable:

        >>> fig = ekp.Figure()
        >>> fig.timeseries(ds)
        >>> fig.show()

        Variable × step grid:

        >>> fig = ekp.Figure()
        >>> fig.timeseries(ds, row="variable", col="step")
        >>> fig.show()
        """
        import xarray as xr

        from earthkit.plots.temporal.timeseries import TimeSeries

        # Default row to "variable" for multi-variable Datasets
        if (
            row is None
            and col is None
            and isinstance(data, xr.Dataset)
            and len(data.data_vars) > 1
        ):
            row = "variable"

        self.plot(
            plot,
            data,
            *args,
            row=row,
            col=col,
            subplot_class=TimeSeries,
            subplot_titles=subplot_titles,
            rows=rows,
            columns=columns,
            size=size,
            **kwargs,
        )

        # Apply time-axis formatting to every TimeSeries subplot
        for sp in self.subplots:
            if isinstance(sp, TimeSeries):
                if xlabel is not None:
                    sp.xlabel(xlabel)
                if ylabel is not None:
                    sp.ylabel(ylabel)
                if xticks is not None:
                    if isinstance(xticks, str):
                        sp.xticks(frequency=xticks)
                    else:
                        sp.xticks(**xticks)
                if yticks is not None:
                    if isinstance(yticks, str):
                        sp.yticks(frequency=yticks)
                    else:
                        sp.yticks(**yticks)

        return self

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

    def set_title(self, label=None, **kwargs):
        """
        Set the top-level title of the figure.

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
        if self._released:
            return self
        self._released = True
        if self._subplot_queue:
            self.rows, self.columns = rows_cols(
                len(self._subplot_queue), rows=self.rows, columns=self.columns
            )
            self._setup()
        for item in self._subplot_queue:
            method, args, kwargs = item
            method(self, *args, **kwargs)
        self._subplot_queue.clear()
        for queued_method, queued_args, queued_kwargs in self._queue:
            queued_method(self, *queued_args, **queued_kwargs)
        self._queue.clear()
        if self.attributions:
            _location_coords = {
                "upper left": (0.0, 1.0, "left", "bottom"),
                "upper center": (0.5, 1.0, "center", "bottom"),
                "upper right": (1.0, 1.0, "right", "bottom"),
                "center left": (0.0, 0.5, "left", "center"),
                "center": (0.5, 0.5, "center", "center"),
                "center right": (1.0, 0.5, "right", "center"),
                "lower left": (0.0, -0.02, "left", "top"),
                "lower center": (0.5, -0.02, "center", "top"),
                "lower right": (1.0, -0.02, "right", "top"),
            }
            # Group attributions by location
            from collections import defaultdict

            groups = defaultdict(list)
            group_kwargs = {}
            for text, loc, kw in self.attributions:
                groups[loc].append(text)
                if loc not in group_kwargs:
                    group_kwargs[loc] = kw
            for loc, texts in groups.items():
                combined = "; ".join(texts)
                x, y, ha, va = _location_coords.get(loc, (0.5, -0.02, "center", "top"))
                text_kwargs = dict(
                    ha=ha,
                    va=va,
                    fontsize=9,
                    color="gray",
                    wrap=True,
                )
                text_kwargs.update(group_kwargs[loc])
                self.fig.text(x, y, combined, **text_kwargs)
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

    def _exit_style_context(self):
        """Exit the style context if one is active, restoring global rcParams."""
        if self._style_context is not None:
            self._style_context.__exit__(None, None, None)
            self._style_context = None

    def _apply_subplot_pre_render(self):
        """Apply any pre-render hooks on subplots (e.g. tight time axis)."""
        from earthkit.plots.temporal.timeseries import TimeSeries

        for subplot in self.subplots:
            if isinstance(subplot, TimeSeries):
                subplot._apply_tight_time_axis()

    def show(self, *args, **kwargs):
        """
        Display the figure.

        This calls :func:`matplotlib.pyplot.show` to display the figure.
        """
        self._cancel_jupyter_display()
        self._prepare_for_display()
        try:
            return plt.show(*args, **kwargs)
        finally:
            self._exit_style_context()

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
        self._cancel_jupyter_display()
        self._prepare_for_display()
        try:
            return plt.savefig(
                *args,
                bbox_inches=bbox_inches,
                dpi=kwargs.pop("dpi", schema.figure.dpi),
                **kwargs,
            )
        finally:
            self._exit_style_context()

    def _prepare_for_display(self):
        """Flush the queue and apply pre-render hooks. Safe to call multiple times."""
        self._apply_subplot_pre_render()
        self._release_queue()

    def _resize(self):
        """Resize the figure to fit its axes."""
        self._release_queue()
        return resize_figure_to_fit_axes(self.fig)

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
        entry = (attribution, location, kwargs)
        if entry not in self.attributions:
            self.attributions.append(entry)

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
