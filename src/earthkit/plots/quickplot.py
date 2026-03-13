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

import earthkit.data
from earthkit.data import FieldList
from earthkit.data.core import Base

from earthkit.plots.components import layouts
from earthkit.plots.components.figures import Figure
from earthkit.plots.metadata.units import are_equal
from earthkit.plots.schemas import schema


def _coerce_to_fieldlist(*args):
    """Convert positional data arguments to a FieldList."""
    field_list = []
    for arg in args:
        if isinstance(arg, FieldList):
            field_list.extend(list(arg))
        else:
            if not isinstance(arg, Base):
                arg = earthkit.data.from_object(arg)
            field_list.append(arg)
    return FieldList.from_fields(field_list)


_DEFAULT_SINGLE_SIZE = (7, 8)
_MULTI_PANEL_WIDTH = 5.0
_MULTI_PANEL_HEIGHT = 4.0
_MAX_FIGURE_SIZE = (40.0, 40.0)


def _auto_figure_size(rows, columns):
    """
    Return a ``(width, height)`` tuple scaled to the panel grid.

    Single panels use ``_DEFAULT_SINGLE_SIZE``.  Multi-panel layouts use
    ``_MULTI_PANEL_WIDTH × _MULTI_PANEL_HEIGHT`` per panel, capped at
    ``_MAX_FIGURE_SIZE``.
    """
    if rows == 1 and columns == 1:
        return _DEFAULT_SINGLE_SIZE
    width = min(_MULTI_PANEL_WIDTH * columns, _MAX_FIGURE_SIZE[0])
    height = min(_MULTI_PANEL_HEIGHT * rows, _MAX_FIGURE_SIZE[1])
    return (width, height)


def _iter_plot_groups(args, groupby, mode, combine_vectors=False):
    """
    Dispatch to the correct source-type group iterator.

    Yields ``(key, [data_item, ...])`` tuples consumed by :func:`plot`.

    Parameters
    ----------
    args : tuple
        Positional arguments passed to :func:`plot`.
    groupby : str or None
        Metadata key / coordinate name to split on.
    mode : str
        ``"auto"``, ``"overlay"``, or ``"split"``.
    combine_vectors : bool
        Passed through to the xarray group iterator.
    """
    import xarray as xr

    from earthkit.plots.sources import _is_xarray_backed_earthkit

    if len(args) == 1 and isinstance(args[0], (xr.DataArray, xr.Dataset)):
        from earthkit.plots.sources.extractors.xarray import iter_plot_groups

        yield from iter_plot_groups(
            args[0], groupby, mode, combine_vectors=combine_vectors
        )
    elif len(args) == 1 and _is_xarray_backed_earthkit(args[0]):
        from earthkit.plots.sources.extractors.xarray import iter_plot_groups

        yield from iter_plot_groups(
            args[0].to_xarray(), groupby, mode, combine_vectors=combine_vectors
        )
    elif all(isinstance(a, xr.DataArray) for a in args):
        # Multiple DataArrays — merge into a Dataset so each variable gets its
        # own panel with the correct auto-style.
        from earthkit.plots.sources.extractors.xarray import iter_plot_groups

        ds = xr.merge(args, compat="override")
        yield from iter_plot_groups(ds, groupby, mode, combine_vectors=combine_vectors)
    elif all(isinstance(a, FieldList) for a in args):
        from earthkit.plots.sources.extractors.earthkit import iter_plot_groups

        yield from iter_plot_groups(
            _coerce_to_fieldlist(*args), groupby, mode, combine_vectors=combine_vectors
        )
    else:
        # Numpy arrays or other raw data — yield directly, one panel.
        yield None, list(args)


def _iter_plot_groups_2d(args, row_dim, col_dim, groupby, mode):
    """
    Dispatch to the 2-D group iterator for structured row/column layout.

    Yields ``(row_key, col_key, [data_item, ...])`` tuples.
    """
    import xarray as xr

    if len(args) == 1 and isinstance(args[0], (xr.DataArray, xr.Dataset)):
        from earthkit.plots.sources.extractors.xarray import iter_plot_groups_2d

        yield from iter_plot_groups_2d(args[0], row_dim, col_dim, groupby, mode)
    else:
        raise NotImplementedError(
            "row/column dimension layout is only supported for xarray data."
        )


def plot(
    *args,
    domain=None,
    crs=None,
    groupby=None,
    row=None,
    column=None,
    rows=None,
    columns=None,
    size=None,
    units=None,
    style="auto",
    subplot_titles=None,
    method="quickplot",
    mode="auto",
    combine_vectors=False,
    **kwargs,
):
    """
    Plot geospatial data as one or more map panels.

    This is the primary high-level function in earthkit-plots.  Pass a single
    data object to get a single map; pass ``groupby`` to get a grid of panels,
    one per unique value of that metadata key (e.g. forecast step, ensemble
    member, pressure level).

    Parameters
    ----------
    *args :
        The data to plot.  Accepts any format supported by earthkit-data
        (GRIB FieldList, xarray DataArray/Dataset, numpy array, …).
    domain : str or list, optional
        Named domain (e.g. ``"Europe"``) or bounding box
        ``[lon_min, lon_max, lat_min, lat_max]``.  If omitted the extent is
        inferred from the data.
    crs : cartopy.crs.CRS, optional
        Map projection.  If omitted an appropriate projection is chosen
        automatically for the domain.
    groupby : str, optional
        Metadata key along which to split the data into separate panels
        (e.g. ``"step"``, ``"number"``, ``"pressure_level"``).
    row : str, optional
        Dimension name (or ``"variable"`` for Dataset variables) to lay out
        along the row axis of the panel grid.  Determines the number of rows
        automatically from unique values.  Use together with *column* to create
        a structured 2-D grid, e.g. ``row="valid_time", column="variable"``.
    column : str, optional
        Dimension name (or ``"variable"``) to lay out along the column axis.
    rows : int, optional
        Number of rows in the panel grid.  If only one of *rows* / *columns*
        is given the other is calculated automatically.  Ignored when *row* is
        a dimension name.
    columns : int, optional
        Number of columns in the panel grid.  Ignored when *column* is a
        dimension name.
    size : tuple of float, optional
        Explicit ``(width, height)`` in inches for the whole figure.  When not
        provided the size is chosen automatically based on the panel grid
        (approximately 5 × 4 inches per panel, capped at 40 inches).
    units : str or list of str, optional
        Units to convert the data to at plot time.
    style : str or Style, optional
        Named style or :class:`~earthkit.plots.styles.Style` object.
        Defaults to ``"auto"`` which selects a style based on the variable.
    subplot_titles : str, optional
        Format string for per-panel titles.  Metadata placeholders like
        ``{step}`` or ``{valid_time}`` are resolved from each panel's data.
        When *groupby* is set this defaults to ``"{<groupby key>}"``.
    method : str, optional
        The plotting method to call on each subplot (default ``"quickplot"``).
    **kwargs :
        Additional keyword arguments forwarded to the plotting method.

    Returns
    -------
    Map or Figure
        A :class:`~earthkit.plots.components.maps.Map` when a single panel is
        produced, or a :class:`~earthkit.plots.components.figures.Figure` for
        multi-panel layouts.  Both support ``.show()`` and ``.save()``.

    Examples
    --------
    Single panel:

    >>> import earthkit.plots as ekp
    >>> ekp.plot(data, domain="Europe", units="celsius").show()

    Grid of panels, one per forecast step:

    >>> ekp.plot(data, groupby="step", domain="Europe", columns=4).show()

    Structured 2-D grid — variables in columns, time steps in rows:

    >>> ekp.plot(ds, row="valid_time", column="variable").show()

    Override the plot method:

    >>> ekp.plot(data, method="contourf", domain="Europe").show()
    """
    # --- 2-D structured layout (row/column as dimension names) ---
    if row is not None or column is not None:
        groups_2d = list(_iter_plot_groups_2d(args, row, column, groupby, mode))
        # Determine grid dimensions from unique row/col keys
        row_keys = list(dict.fromkeys(rk for rk, _, _ in groups_2d))
        col_keys = list(dict.fromkeys(ck for _, ck, _ in groups_2d))
        n_rows = len(row_keys) if row_keys != [None] else (rows or 1)
        n_cols = len(col_keys) if col_keys != [None] else (columns or 1)
        figure = Figure(
            rows=n_rows, columns=n_cols, size=size or _auto_figure_size(n_rows, n_cols)
        )

        if not isinstance(units, (list, tuple)):
            units_flat = [units] * len(groups_2d)
        else:
            units_flat = list(units)

        for i, (row_key, col_key, targets) in enumerate(groups_2d):
            r = row_keys.index(row_key) if row_keys != [None] else 0
            c = col_keys.index(col_key) if col_keys != [None] else 0
            subplot = figure.add_map(row=r, column=c, domain=domain, crs=crs)
            unit = units_flat[i] if i < len(units_flat) else None
            for target in targets:
                try:
                    getattr(subplot, method)(target, units=unit, style=style, **kwargs)
                except Exception as err:
                    warnings.warn(
                        f"ekp.plot: failed to call '{method}' on panel ({r},{c}):\n"
                        f"{err}\n\n"
                        "Consider building the plot manually using ekp.Figure and ekp.Map."
                    )
                    raise
            if subplot_titles:
                try:
                    subplot.title(subplot_titles)
                except Exception:
                    pass

        for m in schema.quickmap_figure_workflow:
            try:
                getattr(figure, m)()
            except Exception as err:
                warnings.warn(
                    f"ekp.plot: figure workflow step '{m}' failed with:\n{err}"
                )
        return _unwrap_if_single(figure)

    # --- Flat layout (original behaviour) ---
    if subplot_titles is None and groupby:
        subplot_titles = f"{{{groupby}}}"

    groups = list(
        _iter_plot_groups(args, groupby, mode, combine_vectors=combine_vectors)
    )
    n_plots = len(groups)

    rows, columns = layouts.rows_cols(n_plots, rows, columns)
    figure = Figure(
        rows=rows, columns=columns, size=size or _auto_figure_size(rows, columns)
    )

    if not isinstance(units, (list, tuple)):
        units = [units] * n_plots

    for i, (key, targets) in enumerate(groups):
        subplot = figure.add_map(domain=domain, crs=crs)
        unit = units[i] if i < len(units) else None
        is_vector = isinstance(key, tuple) and key[0] == "__vector__"
        try:
            if is_vector:
                import xarray as xr

                target = targets[0]
                if isinstance(target, xr.Dataset):
                    # xarray UV pair sub-Dataset
                    subplot.quiver(target, units=unit, **kwargs)
                else:
                    # earthkit: targets is [u_field, v_field]
                    from earthkit.data import FieldList

                    fl = FieldList.from_fields(targets)
                    subplot.quiver(fl, units=unit, **kwargs)
            else:
                for target in targets:
                    getattr(subplot, method)(target, units=unit, style=style, **kwargs)
        except Exception as err:
            warnings.warn(
                f"ekp.plot: failed to call '{method}' on panel {i} with:\n"
                f"{err}\n\n"
                "Consider building the plot manually using ekp.Figure and ekp.Map."
            )
            raise
        if subplot_titles:
            try:
                subplot.title(subplot_titles)
            except Exception:
                pass

    for m in schema.quickmap_figure_workflow:
        if m == "legend" and len(figure.subplots) > 1:
            # Multiple subplots: give each one its own per-subplot legend so
            # different variables don't share a single colorbar.
            for subplot in figure.subplots:
                try:
                    subplot.legend()
                except Exception as err:
                    warnings.warn(f"ekp.plot: subplot legend failed with:\n{err}")
        else:
            try:
                getattr(figure, m)()
            except Exception as err:
                warnings.warn(
                    f"ekp.plot: figure workflow step '{m}' failed with:\n{err}"
                )

    return _unwrap_if_single(figure)


def contourf(*args, **kwargs):
    """
    Plot filled contours on a map.

    Equivalent to ``ekp.plot(*args, method="contourf", **kwargs)``.
    Accepts all the same arguments as :func:`plot`.
    """
    return plot(*args, method="contourf", **kwargs)


def contour(*args, **kwargs):
    """
    Plot contour lines on a map.

    Equivalent to ``ekp.plot(*args, method="contour", **kwargs)``.
    Accepts all the same arguments as :func:`plot`.
    """
    return plot(*args, method="contour", **kwargs)


def pcolormesh(*args, **kwargs):
    """
    Plot a pseudocolor mesh on a map.

    Equivalent to ``ekp.plot(*args, method="pcolormesh", **kwargs)``.
    Accepts all the same arguments as :func:`plot`.
    """
    return plot(*args, method="pcolormesh", **kwargs)


def _unwrap_if_single(figure):
    """Return the sole subplot when the figure has exactly one panel."""
    if len(figure.subplots) == 1:
        return figure.subplots[0]
    return figure


def _single_map_function(method_name, data_args, domain, crs, kwargs):
    """Shared helper: create a single-panel Map and call *method_name* on it."""
    import xarray as xr

    figure = Figure(rows=1, columns=1)
    subplot = figure.add_map(domain=domain, crs=crs)
    if not data_args:
        getattr(subplot, method_name)(**kwargs)
    elif all(isinstance(a, (xr.DataArray, xr.Dataset)) for a in data_args):
        getattr(subplot, method_name)(*data_args, **kwargs)
    else:
        fields = _coerce_to_fieldlist(*data_args)
        getattr(subplot, method_name)(fields, **kwargs)
    for m in schema.quickmap_figure_workflow:
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(
                f"ekp.{method_name}: figure workflow step '{m}' failed with:\n{err}"
            )
    return _unwrap_if_single(figure)


def grid_cells(
    *args,
    domain=None,
    crs=None,
    **kwargs,
):
    """
    Plot data as grid cells on a map.

    Uses specialised nnshow backends for HEALPix and octahedral reduced
    Gaussian grids; falls back to pcolormesh for other grid types.  This is
    the fastest way to visualise the native grid structure of your data.

    Parameters
    ----------
    *args :
        The data to plot.
    domain : str or list, optional
        Named domain or bounding box ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.
    **kwargs :
        Additional keyword arguments forwarded to :meth:`Map.grid_cells`.

    Returns
    -------
    Map
    """
    return _single_map_function("grid_cells", args, domain, crs, kwargs)


def grid_points(
    *args,
    domain=None,
    crs=None,
    **kwargs,
):
    """
    Plot grid point centroids as scatter points on a map.

    Useful for inspecting the spatial coverage and density of a dataset's
    native grid.

    Parameters
    ----------
    *args :
        The data whose grid points to plot.
    domain : str or list, optional
        Named domain or bounding box ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.
    **kwargs :
        Additional keyword arguments forwarded to :meth:`Map.grid_points`
        (and ultimately to :func:`matplotlib.pyplot.scatter`).

    Returns
    -------
    Map
    """
    return _single_map_function("grid_points", args, domain, crs, kwargs)


def point_cloud(
    *args,
    domain=None,
    crs=None,
    **kwargs,
):
    """
    Plot data values as a coloured point cloud on a map.

    Each data point is rendered as a scatter point coloured by its value.
    Suitable for sparse or unstructured observation data.

    Parameters
    ----------
    *args :
        The data to plot.
    domain : str or list, optional
        Named domain or bounding box ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.
    **kwargs :
        Additional keyword arguments forwarded to :meth:`Map.point_cloud`
        (and ultimately to :func:`matplotlib.pyplot.scatter`).

    Returns
    -------
    Map
    """
    return _single_map_function("point_cloud", args, domain, crs, kwargs)


def rgb_composite(
    *args,
    domain=None,
    crs=None,
    **kwargs,
):
    """
    Plot an RGB composite image on a map.

    Combines three data fields (red, green, blue channels) into a single
    colour image. Each channel is normalised to [0, 1] before compositing.

    Parameters
    ----------
    *args :
        Either three separate data objects (red, green, blue) or a single
        iterable of three data objects.
    domain : str or list, optional
        Named domain or bounding box ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.
    **kwargs :
        Additional keyword arguments forwarded to :meth:`Map.rgb_composite`.

    Returns
    -------
    Map
    """
    figure = Figure(rows=1, columns=1)
    subplot = figure.add_map(domain=domain, crs=crs)
    subplot.rgb_composite(*args, **kwargs)
    for m in schema.quickmap_figure_workflow:
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(
                f"ekp.rgb_composite: figure workflow step '{m}' failed with:\n{err}"
            )
    return _unwrap_if_single(figure)


def choropleth(
    data,
    domain=None,
    crs=None,
    **kwargs,
):
    """
    Create a choropleth map from a GeoDataFrame.

    Parameters
    ----------
    data : geopandas.GeoDataFrame or earthkit-data object
        The data to plot. GeoDataFrame objects are used directly; earthkit-data
        objects are converted via ``to_geopandas()`` first.
    domain : str or list, optional
        Named domain or bounding box ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.
    **kwargs :
        Additional keyword arguments forwarded to :meth:`Map.choropleth`.

    Returns
    -------
    Map
    """
    figure = Figure(rows=1, columns=1)
    subplot = figure.add_map(domain=domain, crs=crs)
    subplot.choropleth(data, **kwargs)
    for m in schema.quickmap_figure_workflow:
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(
                f"ekp.choropleth: figure workflow step '{m}' failed with:\n{err}"
            )
    return _unwrap_if_single(figure)


def spaghetti(
    *args,
    domain=None,
    crs=None,
    levels=None,
    color="#0673e0",
    label=None,
    highlight=None,
    highlight_kwargs=None,
    highlight_label=None,
    **kwargs,
):
    """
    Plot spaghetti contours for ensemble data on a single map.

    Each ensemble member is drawn as a thin contour line.  An optional
    ``highlight`` selector can draw specific members (e.g. the control
    forecast) with a different style.

    Parameters
    ----------
    *args :
        The ensemble data to plot.  Accepts any format supported by
        earthkit-data (GRIB FieldList, xarray DataArray, …).  All fields
        are plotted on the same map as individual contour lines.
    domain : str or list, optional
        Named domain (e.g. ``"Europe"``) or bounding box
        ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.
    levels : float or list of float, optional
        Contour level(s) to draw for each member.  Accepts a single value
        (e.g. ``5400``) or multiple values (e.g. ``[5400, 5700, 5900]``).
        If omitted, contour levels are chosen automatically.
    color : str, default ``"#0673e0"``
        Line colour for normal ensemble members.
    label : str, optional
        Legend label for the ensemble members.  When set, a legend is
        automatically added to the plot.
    highlight : dict, optional
        Metadata criteria used to select members for highlighted rendering,
        e.g. ``{"dataType": "cf"}`` to pick out the control forecast.
    highlight_kwargs : dict, optional
        Keyword arguments passed to the contour method for highlighted
        members.  Defaults to ``{"color": "red", "linewidths": 1.5}``.
    highlight_label : str, optional
        Legend label for the highlighted members.  Defaults to
        ``"Control"`` when ``label`` is set and ``highlight`` is used.
    **kwargs :
        Additional keyword arguments forwarded to the underlying
        ``contour`` call (e.g. ``linewidths``, ``alpha``).

    Returns
    -------
    Map
        An earthkit-plots :class:`~earthkit.plots.components.maps.Map`.

    Examples
    --------
    Single contour level across all members:

    >>> import earthkit.plots as ekp
    >>> ekp.spaghetti(data, levels=5400, domain="Europe").show()

    Multiple levels, with control forecast highlighted and a legend:

    >>> ekp.spaghetti(
    ...     data,
    ...     levels=[5400, 5700],
    ...     domain="Europe",
    ...     label="Ensemble",
    ...     highlight={"dataType": "cf"},
    ...     highlight_label="Control",
    ... ).show()
    """
    fields = _coerce_to_fieldlist(*args)

    figure = Figure(rows=1, columns=1)
    subplot = figure.add_map(domain=domain, crs=crs)
    subplot.spaghetti(
        fields,
        levels=levels,
        color=color,
        label=label,
        highlight=highlight,
        highlight_kwargs=highlight_kwargs,
        highlight_label=highlight_label,
        **kwargs,
    )

    for m in schema.quickmap_figure_workflow:
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(
                f"ekp.spaghetti: figure workflow step '{m}' failed with:\n{err}"
            )

    return _unwrap_if_single(figure)


def quiver(*args, domain=None, crs=None, **kwargs):
    """
    Plot wind / vector data as arrows on a map.

    Equivalent to creating a single-panel Map and calling ``quiver`` on it.
    Accepts all the same arguments as :meth:`~earthkit.plots.components.maps.Map.quiver`.
    """
    return _single_map_function("quiver", args, domain, crs, kwargs)


def streamplot(*args, domain=None, crs=None, **kwargs):
    """
    Plot wind / vector data as streamlines on a map.

    Equivalent to creating a single-panel Map and calling ``streamplot`` on it.
    Accepts all the same arguments as
    :meth:`~earthkit.plots.components.subplots.Subplot.streamplot`.
    """
    return _single_map_function("streamplot", args, domain, crs, kwargs)


def barbs(*args, domain=None, crs=None, **kwargs):
    """
    Plot wind barbs on a map.

    Equivalent to creating a single-panel Map and calling ``barbs`` on it.
    Accepts all the same arguments as
    :meth:`~earthkit.plots.components.subplots.Subplot.barbs`.
    """
    return _single_map_function("barbs", args, domain, crs, kwargs)


def quickplot(*args, **kwargs):
    """
    Alias for :func:`plot`. Use ``ekp.plot()`` instead.
    """
    return plot(*args, **kwargs)


def climatology(
    data,
    *args,
    plot="line",
    title=None,
    xticks=None,
    yticks=None,
    xlabel=None,
    ylabel=None,
    **kwargs,
):
    """
    Create a climatology (annual-cycle) plot.

    Splits multi-year timeseries data by calendar year and plots each year
    on a common Jan-to-Dec x-axis.  Leap years are mapped onto the reference
    year 2000; non-leap years onto 2001, so Feb 29 is naturally absent for
    non-leap years.

    Parameters
    ----------
    data : xarray.DataArray
        Multi-year timeseries data with a time coordinate.
    plot : str, optional
        The plotting method to call on the Climatology subplot.  One of
        ``"line"``, ``"scatter"``, ``"bar"``, ``"fill_between"``.
        Default ``"line"``.
    title : str, optional
        Plot title.
    xticks : str or dict, optional
        X-axis tick configuration.  If a string, treated as a frequency
        (e.g. ``"M"``, ``"M3"``).  If a dict, passed as kwargs to
        ``xticks()``.
    yticks : str or dict, optional
        Y-axis tick configuration.  Same format as *xticks*.
    xlabel : str, optional
        Label for the x-axis.
    ylabel : str, optional
        Label for the y-axis.
    **kwargs :
        Additional keyword arguments forwarded to the plotting method
        (e.g. ``color``, ``linewidth``).

    Returns
    -------
    Climatology
        An earthkit-plots
        :class:`~earthkit.plots.temporal.climatology.Climatology` subplot
        that can be further customised and displayed with ``.show()`` or
        saved with ``.save()``.

    Examples
    --------
    >>> import earthkit.plots as ekp
    >>> ekp.climatology.line(da).show()

    >>> ekp.climatology.bar(da, ylabel="Temperature (°C)", title="Annual cycle").show()
    """
    from earthkit.plots.temporal.climatology import Climatology

    class_kwargs = {k: kwargs.pop(k) for k in _TIMESERIES_CLASS_KWARGS if k in kwargs}
    ts = Climatology(**class_kwargs)
    getattr(ts, plot)(data, *args, **kwargs)
    if xlabel is not None:
        ts.xlabel(xlabel)
    if ylabel is not None:
        ts.ylabel(ylabel)
    _apply_ticks(ts, xticks, yticks)
    if title:
        ts.title(title)
    ts.figure.legend()
    return ts


_TIMESERIES_CLASS_KWARGS = {"size"}


def _apply_ticks(subplot, xticks, yticks):
    """Apply xticks/yticks configuration to a subplot."""
    if xticks is not None:
        if isinstance(xticks, str):
            subplot.xticks(frequency=xticks)
        else:
            subplot.xticks(**xticks)
    if yticks is not None:
        if isinstance(yticks, str):
            subplot.yticks(frequency=yticks)
        else:
            subplot.yticks(**yticks)


def timeseries(
    data,
    *args,
    overlay=False,
    groupby=None,
    rows=None,
    columns=None,
    title=None,
    subplot_titles="{variable_name}",
    xticks=None,
    yticks=None,
    xlabel=None,
    ylabel=None,
    plot="line",
    **kwargs,
):
    """
    Create a time series plot with automatic configuration.

    This is a convenience function that creates a TimeSeries subplot (or a
    Figure of multiple TimeSeries subplots) with sensible defaults for time
    series visualization.

    When *data* is an xarray Dataset with more than one data variable, a
    separate subplot is created for each variable by default (one per row).
    Pass ``overlay=True`` to plot all variables on a single subplot instead.
    Use ``groupby`` to split the data along a coordinate dimension (produces
    one panel per unique value).

    Parameters
    ----------
    data : array-like, xarray DataArray/Dataset, or earthkit data source
        The time series data to plot.
    *args : tuple
        Additional positional arguments passed to the plotting method.
    overlay : bool, optional
        When *data* is a multi-variable Dataset, plot all variables on a single
        subplot instead of creating one subplot per variable. Default is False.
    groupby : str, optional
        Coordinate name along which to split the data into separate panels.
    rows : int, optional
        Override the number of rows in the Figure layout.
    columns : int, optional
        Override the number of columns in the Figure layout.
    title : str, optional
        Figure-level title. Supports format strings like ``{variable_name}``.
    subplot_titles : str, optional
        Per-panel title format string. Default is ``"{variable_name}"``.
    xticks : str or dict, optional
        Configuration for x-axis ticks. If a string, treated as frequency
        (e.g. ``"Y"``, ``"M6"``, ``"D7"``, ``"h"``). If a dict, passed as
        kwargs to ``xticks()``.
    yticks : str or dict, optional
        Configuration for y-axis ticks. Same format as *xticks*.
    xlabel : str, optional
        Label for the x-axis.
    ylabel : str, optional
        Label for the y-axis.
    plot : str, optional
        Plotting method to call on each TimeSeries subplot. Default is ``"line"``.
    **kwargs :
        Additional keyword arguments passed to the plotting method.

    Returns
    -------
    TimeSeries or Figure
    """
    import xarray as xr

    from earthkit.plots.metadata.formatters import LayerFormatter
    from earthkit.plots.temporal.timeseries import TimeSeries

    # ------------------------------------------------------------------
    # Multi-variable Dataset, not overlaid → one row per variable
    # ------------------------------------------------------------------
    if not overlay and isinstance(data, xr.Dataset) and len(data.data_vars) > 1:
        size = kwargs.pop("size", None)
        col = groupby if groupby is not None else None
        fig = Figure()
        fig.timeseries(
            data,
            *args,
            row="variable",
            col=col,
            plot=plot,
            subplot_titles=subplot_titles,
            rows=rows,
            columns=columns,
            size=size,
            xticks=xticks,
            yticks=yticks,
            xlabel=xlabel,
            ylabel=ylabel,
            **kwargs,
        )
        if title:
            try:
                fig.title(title)
            except Exception:
                pass
        fig.legend()
        return fig

    # ------------------------------------------------------------------
    # Multi-variable Dataset, overlaid → all vars on one subplot
    # ------------------------------------------------------------------
    if overlay and isinstance(data, xr.Dataset) and len(data.data_vars) > 1:
        class_kwargs = {
            k: kwargs.pop(k) for k in _TIMESERIES_CLASS_KWARGS if k in kwargs
        }
        ts = TimeSeries(**class_kwargs)
        axes_by_units = {}
        layers_by_ax = {}
        primary_ax = None
        for var_name in data.data_vars:
            da = data[var_name]
            var_units = da.attrs.get("units", None)
            if not axes_by_units:
                layers_before = len(ts.layers)
                getattr(ts, plot)(da, *args, **kwargs)
                primary_ax = ts._ax
                axes_by_units[var_units] = primary_ax
                layers_by_ax[primary_ax] = ts.layers[layers_before:]
            else:
                target_ax = next(
                    (ax for u, ax in axes_by_units.items() if are_equal(var_units, u)),
                    None,
                )
                if target_ax is None:
                    target_ax = primary_ax.twinx()
                    axes_by_units[var_units] = target_ax
                    layers_by_ax[target_ax] = []
                original_ax = ts._ax
                ts._ax = target_ax
                layers_before = len(ts.layers)
                getattr(ts, plot)(da, *args, **kwargs)
                ts._ax = original_ax
                layers_by_ax[target_ax].extend(ts.layers[layers_before:])
        ts.xlabel(xlabel)
        _apply_ticks(ts, xticks, yticks)
        for ax, ax_layers in layers_by_ax.items():
            if ylabel is not None:
                ax.set_ylabel(ylabel)
            elif ax_layers:
                try:
                    src = ax_layers[0].sources[0]
                    units = src.y.metadata("units")
                    lbl = "{variable_name} ({units})" if units else "{variable_name}"
                    ax.set_ylabel(LayerFormatter(ax_layers[0]).format(lbl))
                except Exception:
                    pass
        if title:
            ts.title(title)
        ts.figure.legend()
        return ts

    # ------------------------------------------------------------------
    # groupby → one panel per unique value (DataArray or single-var Dataset)
    # ------------------------------------------------------------------
    if groupby is not None:
        groups = list(_iter_plot_groups((data,), groupby, mode="split"))
        n_plots = len(groups)
        _rows, _cols = layouts.rows_cols(n_plots, rows, columns)
        kwargs.pop("size", None)
        fig = Figure(rows=_rows, columns=_cols)
        for _, targets in groups:
            ts = fig.add_timeseries()
            for target in targets:
                getattr(ts, plot)(target, *args, **kwargs)
            if xlabel is not None:
                ts.xlabel(xlabel)
            if ylabel is not None:
                ts.ylabel(ylabel)
            _apply_ticks(ts, xticks, yticks)
            if subplot_titles:
                try:
                    ts.title(subplot_titles)
                except Exception:
                    pass
        if title:
            try:
                fig.title(title)
            except Exception:
                pass
        fig.legend()
        return fig

    # ------------------------------------------------------------------
    # Single panel
    # ------------------------------------------------------------------
    class_kwargs = {k: kwargs.pop(k) for k in _TIMESERIES_CLASS_KWARGS if k in kwargs}
    ts = TimeSeries(**class_kwargs)
    getattr(ts, plot)(data, *args, **kwargs)
    if xlabel is not None:
        ts.xlabel(xlabel)
    if ylabel is not None:
        ts.ylabel(ylabel)
    _apply_ticks(ts, xticks, yticks)
    if title:
        ts.title(title)
    ts.figure.legend()
    return ts
