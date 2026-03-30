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

import numpy as np

from earthkit.plots.components._pipeline import plot_1D, plot_2D, plot_vector
from earthkit.plots.components.layers import Layer
from earthkit.plots.metadata.formatters import (
    LayerFormatter,
    SourceFormatter,
    SubplotFormatter,
)
from earthkit.plots.schemas import schema
from earthkit.plots.sources import get_source
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.styles import auto
from earthkit.plots.utils import string_utils

DEFAULT_SINGLE_SIZE = (7, 8)

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

    def __init__(
        self,
        row=0,
        column=0,
        figure=None,
        figsize=DEFAULT_SINGLE_SIZE,
        ax=None,
        size=None,
        **kwargs,
    ):
        if size is not None:
            import warnings

            warnings.warn(
                "The 'size' argument is deprecated and will be removed in a future release. "
                "Use 'figsize' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if figsize is DEFAULT_SINGLE_SIZE:
                figsize = size

        # When an existing axes is supplied we bypass the lazy-creation path
        # entirely: _ax is pre-populated and _figure is derived from ax.figure
        # so self.fig always returns the correct matplotlib Figure.
        if ax is not None:
            self._ax = ax
            self._figure = figure  # may still be None; figure property handles it
            self._size = None
        else:
            self._ax = None
            self._figure = figure
            self._size = None if figure is not None else figsize

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

    @property
    def figure(self):
        """The :class:`earthkit.plots.components.figures.Figure` object."""
        from earthkit.plots.components.figures import Figure

        if self._figure is None:
            if self._ax is not None:
                # Wrap the existing matplotlib Figure so self.fig is consistent,
                # but skip gridspec setup — we don't own this figure's layout.
                self._figure = Figure.__new__(Figure)
                self._figure.fig = self._ax.figure
                self._figure.gridspec = None
                self._figure.subplots = [self]
                self._figure._style_context = None
                self._figure.attributions = []
                self._figure.logos = []
                self._figure._ancillary_cache = {}
            else:
                self._figure = Figure(1, 1, figsize=self._size)
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
        Add a y-axis label to the subplot.

        If no label is provided, one is generated automatically from the
        plotted data's metadata (variable name and units).

        Parameters
        ----------
        label : str, optional
            The label text. Supports metadata format placeholders such as
            ``"{variable_name}"`` and ``"{units}"``. If ``None``, a label is
            inferred from the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.set_ylabel`.
        """
        if label is None:
            # Check if units metadata exists
            units = self.layers[0].sources[0].y.units
            if units is not None:
                label = "{variable_name} ({units})"
            else:
                label = "{variable_name}"
        label = self.format_string(label, axis="y")
        self.ax.set_ylabel(label, **kwargs)
        return self

    def xlabel(self, label=None, **kwargs):
        """
        Add an x-axis label to the subplot.

        If no label is provided, one is generated automatically from the
        plotted data's metadata (variable name and units).

        Parameters
        ----------
        label : str, optional
            The label text. Supports metadata format placeholders such as
            ``"{variable_name}"`` and ``"{units}"``. If ``None``, a label is
            inferred from the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.set_xlabel`.
        """
        if label is None:
            # Check if units metadata exists
            units = self.layers[0].sources[0].x.units
            if units is not None:
                label = "{variable_name} ({units})"
            else:
                label = "{variable_name}"
        label = self.format_string(label, axis="x")
        self.ax.set_xlabel(label, **kwargs)
        return self

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
        """
        Plot a quantile fill (shaded uncertainty band) on the Subplot.

        Draws one shaded band per quantile pair (e.g. p10–p90, p25–p75)
        centred around the median, using progressively lighter shading for
        outer quantiles.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base
            The data to plot. Must contain a quantile coordinate or dimension.
        x : str or array-like, optional
            The x-axis coordinate name or values.
        style : earthkit.plots.styles.Style, optional
            Style to apply. If ``None``, a style is generated automatically.
        units : str, optional
            Target units for value conversion.
        **kwargs
            Additional keyword arguments forwarded to
            :meth:`matplotlib.axes.Axes.fill_between`.
        """

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
        from earthkit.plots.metadata.formatters import LayerFormatter
        from earthkit.plots.plottypes.multiboxplot import draw_multiboxplot

        # Resolve subplot-level fixed units; y_units takes precedence over units.
        if self._fixed_y_units is not None and units is None and y_units is None:
            units = self._fixed_y_units
        if self._fixed_x_units is not None and x_units is None:
            x_units = self._fixed_x_units
        target_yunits = y_units or units

        result = draw_multiboxplot(
            self.ax,
            data,
            x=x,
            dim=dim,
            quantiles=quantiles,
            color=color,
            target_yunits=target_yunits,
            boxprops=boxprops,
            whiskerprops=whiskerprops,
            medianprops=medianprops,
            capprops=capprops,
            showcaps=showcaps,
        )

        # Build a representative Source from the median (or midpoint) slice so
        # the Layer carries correct metadata for titles and formatters.
        n_q = len(result.quantiles)
        median_idx = n_q // 2 if n_q % 2 == 1 else None
        median_or_mid = median_idx if median_idx is not None else n_q // 2
        rep_data = result.quantile_data.isel({result.quantile_dim: median_or_mid})
        source = get_source(rep_data, context=PlotContext.CARTESIAN_1D)

        axis_units = {}
        if target_yunits is not None:
            axis_units["y"] = target_yunits
        if x_units is not None:
            axis_units["x"] = x_units

        layer = Layer(
            source,
            result.mappables,
            self,
            style=None,
            primary_axis="y",
            axis_units=axis_units,
        )

        if label is not None:
            formatted_label = LayerFormatter(layer).format(label)
            if result.mappables:
                result.mappables[0].set_label(formatted_label)

        # Attach the typed result so multiboxplot_legend() can read it without
        # relying on ad-hoc attribute names.
        layer._multiboxplot_result = result

        self.layers.append(layer)
        return self

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
        from earthkit.plots.plottypes.multiboxplot import draw_multiboxplot_legend

        mbp_layers = [
            layer
            for layer in self.layers
            if getattr(layer, "_multiboxplot_result", None) is not None
        ]
        if not mbp_layers:
            raise ValueError(
                "No multiboxplot has been drawn yet. "
                "Call multiboxplot() before multiboxplot_legend()."
            )

        draw_multiboxplot_legend(
            self.ax,
            mbp_layers[-1]._multiboxplot_result,
            location=location,
            fontsize=fontsize,
            color=color,
            boxprops=boxprops,
            whiskerprops=whiskerprops,
            medianprops=medianprops,
            size=kwargs.pop("size", 0.75),
            pad=kwargs.pop("pad", 0.1),
        )
        return self

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
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.plot`.
            See the `matplotlib plot documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html>`_
            for the full list of accepted arguments.
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
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.fill_between`.
            See the `matplotlib fill_between documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.fill_between.html>`_
            for the full list of accepted arguments.
        """
        x = kwargs.pop("x", None)
        drawstyle = kwargs.pop("drawstyle", None)
        if units is None and self._fixed_y_units is not None:
            units = self._fixed_y_units
        source_1 = get_source(
            data_1, x=x, context=PlotContext.CARTESIAN_1D, units=units
        )
        x_values, y1_values = source_1.x.values, source_1.y.values

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
            _, y2_values = source_2.x.values, source_2.y.values

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
            :meth:`matplotlib.axes.Axes.fill_between`.
            See the `matplotlib fill_between documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.fill_between.html>`_
            for the full list (e.g. ``color``, ``zorder``, ``label``).

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
            x_val, y_val = source.x.values, source.y.values
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
            x_val, y_val = source.x.values, source.y.values
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
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.annotate`.
        """
        source = get_source(data=data, x=x, y=y)
        labels = SourceFormatter(source).format(label)
        for label, x, y in zip(labels, source.x.values, source.y.values):
            self.ax.annotate(label, (x, y), **kwargs)

    def plot(self, data, style=None, units=None, **kwargs):
        """
        Auto-detect the best plot type and render the data.

        Inspects data metadata to choose the most appropriate method
        (e.g. :meth:`contourf`, :meth:`grid_cells`, :meth:`pcolormesh`).
        You can override the selection by passing an explicit *style*.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base
            The data to plot.
        style : earthkit.plots.styles.Style, optional
            An explicit :class:`~earthkit.plots.styles.Style` to use.
            If ``None``, a style is detected automatically from the data metadata.
        units : str, optional
            Target units for value conversion (e.g. ``"celsius"``).
        **kwargs
            Additional keyword arguments forwarded to the resolved plot method.
        """
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

        if not kwargs.pop("auto_style", True):
            warnings.warn("`auto_style` cannot be switched off for `quickplot`.")
        x = kwargs.get("x", None)
        y = kwargs.get("y", None)
        metadata = kwargs.get("metadata", None)
        source = get_source(data, x=x, y=y, metadata=metadata)
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

        self.pcolormesh(c=rgb, x=x_values, y=y_values, no_style=True)

        self.layers[-1].sources = [red_source, green_source, blue_source]
        self.layers[-1].style = None

        return self

    def rgb_composite(self, *args):
        """
        Plot an RGB composite on the Subplot.

        Parameters
        ----------
        *args : xarray.DataArray or earthkit.data.core.Base
            The data sources for the R, G, and B channels. If a single argument
            is provided, it is assumed to be a tuple of (R, G, B).
        """
        from earthkit.plots.plottypes.rgb_composite import prepare_rgb_composite

        if len(args) == 1:
            red, green, blue = args[0]
        else:
            red, green, blue = args

        red_source = get_source(red)
        green_source = get_source(green)
        blue_source = get_source(blue)

        result = prepare_rgb_composite(red_source, green_source, blue_source)

        self.pcolormesh(
            result.rgb_array, x=result.x_values, y=result.y_values, no_style=True
        )

        # Replace the single source the pcolormesh layer recorded with all
        # three channel sources so metadata formatters have the full picture.
        self.layers[-1].sources = [red_source, green_source, blue_source]
        self.layers[-1].style = None

        return self

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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.

        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.bar`.
            See the `matplotlib bar documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.bar.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.scatter`.
            See the `matplotlib scatter documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.scatter.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        resample : earthkit.plots.resample.Resample, bool, or dict, optional
            Controls resampling of data before plotting. Pass a
            :class:`~earthkit.plots.resample.Unstructured` (or subclass) instance to
            interpolate unstructured data onto a regular grid, a dict of keyword
            arguments to construct one, or ``True`` for defaults. Default is ``False``
            for pcolormesh.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.pcolormesh`.
            See the `matplotlib pcolormesh documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.pcolormesh.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        resample : earthkit.plots.resample.Resample, bool, or False, optional
            Controls resampling before plotting. Pass a
            :class:`~earthkit.plots.resample.Bilinear` or :class:`~earthkit.plots.resample.NearestNeighbour` instance (or ``True`` for
            defaults) to reproject onto a regular target grid, or ``False`` to
            disable. Default is ``Bilinear()`` (1000 × 1000 pixels).
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.contour`.
            See the `matplotlib contour documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.contour.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        resample : earthkit.plots.resample.Resample, bool, or False, optional
            Controls resampling before plotting. Pass a
            :class:`~earthkit.plots.resample.Bilinear` or :class:`~earthkit.plots.resample.NearestNeighbour` instance (or ``True`` for
            defaults) to reproject onto a regular target grid, or ``False`` to
            disable. Default is ``Bilinear()`` (1000 × 1000 pixels). Pass an
            :class:`~earthkit.plots.resample.Unstructured` instance to interpolate
            unstructured data onto a structured grid instead.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.contourf`.
            See the `matplotlib contourf documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.contourf.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.tripcolor`.
            See the `matplotlib tripcolor documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.tripcolor.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.tricontour`.
            See the `matplotlib tricontour documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.tricontour.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.tricontourf`.
            See the `matplotlib tricontourf documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.tricontourf.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.quiver`.
            See the `matplotlib quiver documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.quiver.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.streamplot`.
            See the `matplotlib streamplot documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.streamplot.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.barbs`.
            See the `matplotlib barbs documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.barbs.html>`_
            for the full list of accepted arguments.
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
            Target units for value conversion (e.g. ``"celsius"``). Unit
            conversion relies on CF-compliant ``units`` metadata in the data.
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
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.contour` for each member.
            See the `matplotlib contour documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.contour.html>`_
            for the full list. Common parameters include ``linewidths``,
            ``alpha``, and ``labels``.
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
        return self

    @schema.title.apply()
    def title(self, label=None, unique=True, wrap=True, capitalize="auto", **kwargs):
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
        capitalize : bool or str, optional
            Whether to capitalize the first letter of the title. Default is "auto".
            If "auto", capitalization is determined based on whether the title starts
            with a format key (e.g. "{variable_name}"), in which case it is capitalized.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.title`.
        """
        if capitalize == "auto":
            capitalize = label is not None and label[0] == "{"
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
        self.ax.set_title(label, wrap=wrap, **kwargs)
        return self

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
