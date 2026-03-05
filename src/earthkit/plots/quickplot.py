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
from earthkit.plots.identifiers import group_vectors
from earthkit.plots.schemas import schema
from earthkit.plots.utils import iter_utils


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


def _group_data(fields, groupby):
    """
    Split a FieldList into an ordered dict of groups.

    If *groupby* is a string, groups are keyed by the unique values of that
    metadata key.  If *groupby* is None every field becomes its own group
    (one panel per field).
    """
    if groupby:
        unique_values = iter_utils.flatten(field.metadata(groupby) for field in fields)
        unique_values = list(dict.fromkeys(unique_values))
        return {val: fields.sel(**{groupby: val}) for val in unique_values}
    else:
        return {i: field for i, field in enumerate(fields)}


def _xarray_multivar_panels(data, groupby=None):
    """
    For an xr.Dataset with multiple data variables, return a panel mapping and
    layout dimensions.

    Returns
    -------
    panels : dict or None
        Ordered dict mapping ``(var_name, group_val)`` to an ``xr.DataArray``.
        ``group_val`` is ``None`` when *groupby* is not used.
        Returns ``None`` when *data* is not a multi-variable Dataset (caller
        should fall through to its single-panel path).
    n_vars : int
        Number of distinct variables (rows).
    n_groups : int
        Number of distinct group values (columns).  1 when *groupby* is None.
    """
    import xarray as xr

    if not isinstance(data, xr.Dataset) or len(data.data_vars) <= 1:
        return None, 0, 0

    var_names = list(data.data_vars)

    if groupby is not None:
        # Collect unique group values from the first variable's coordinate
        coord_values = data[var_names[0]][groupby].values
        group_vals = list(dict.fromkeys(coord_values.tolist()))
    else:
        group_vals = [None]

    panels = {}
    for var in var_names:
        for grp in group_vals:
            if grp is not None:
                panels[(var, grp)] = data[var].sel({groupby: grp})
            else:
                panels[(var, grp)] = data[var]

    return panels, len(var_names), len(group_vals)


def plot(
    *args,
    domain=None,
    crs=None,
    groupby=None,
    rows=None,
    columns=None,
    units=None,
    style="auto",
    subplot_titles=None,
    method="quickplot",
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
    rows : int, optional
        Number of rows in the panel grid.  If only one of *rows* / *columns*
        is given the other is calculated automatically.
    columns : int, optional
        Number of columns in the panel grid.
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
    Figure
        An earthkit-plots :class:`~earthkit.plots.components.figures.Figure`
        that can be further customised and then displayed with ``.show()`` or
        saved with ``.save()``.

    Examples
    --------
    Single panel:

    >>> import earthkit.plots as ekp
    >>> ekp.plot(data, domain="Europe", units="celsius").show()

    Grid of panels, one per forecast step:

    >>> ekp.plot(data, groupby="step", domain="Europe", columns=4).show()

    Override the plot method:

    >>> ekp.plot(data, method="contourf", domain="Europe").show()
    """
    fields = _coerce_to_fieldlist(*args)
    grouped_data = _group_data(fields, groupby)
    n_plots = len(grouped_data)

    rows, columns = layouts.rows_cols(n_plots, rows, columns)
    figure = Figure(rows=rows, columns=columns)

    if subplot_titles is None and groupby:
        subplot_titles = f"{{{groupby}}}"

    if not isinstance(units, (list, tuple)):
        units = [units] * n_plots

    for i, (group_val, group_fields) in enumerate(grouped_data.items()):
        subplot = figure.add_map(domain=domain, crs=crs)

        if isinstance(group_fields, FieldList):
            group_fields = list(group_fields)

        plot_targets = (
            group_fields if isinstance(group_fields, (list, tuple)) else [group_fields]
        )

        for field in plot_targets:
            unit = units[i] if i < len(units) else None
            try:
                getattr(subplot, method)(field, units=unit, style=style, **kwargs)
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
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(f"ekp.plot: figure workflow step '{m}' failed with:\n{err}")

    return figure


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


def _single_map_function(method_name, data_args, domain, crs, kwargs):
    """Shared helper: create a single-panel Map and call *method_name* on it."""
    fields = _coerce_to_fieldlist(*data_args)
    figure = Figure(rows=1, columns=1)
    subplot = figure.add_map(domain=domain, crs=crs)
    getattr(subplot, method_name)(fields, **kwargs)
    for m in schema.quickmap_figure_workflow:
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(
                f"ekp.{method_name}: figure workflow step '{m}' failed with:\n{err}"
            )
    return figure


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
    Figure
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
    Figure
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
    Figure
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
    Figure
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
    return figure


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
    Figure
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
    return figure


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
    Figure
        An earthkit-plots :class:`~earthkit.plots.components.figures.Figure`.

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

    return figure


def quickplot(
    *args,
    rows=None,
    columns=None,
    domain=None,
    crs=None,
    methods="quickplot",
    mode="subplots",
    groupby=None,
    units=None,
    subplot_titles=None,
    combine_vectors=False,
    **kwargs,
):
    """
    Generate a convenient plot from the given data with optional grouping.

    Parameters
    ----------
    *args : list
        The data to be plotted. Can be a single xarray or earthkit data object,
        or separate x, y, z, u, v arguments.
    rows : int, optional
        Number of rows in the subplot layout.
    columns : int, optional
        Number of columns in the subplot layout.
    domain : string or tuple, optional
        The domain of the plot.
    methods : string or list, optional
        The plot method(s) to apply.
    mode : string, optional
        'subplots' (default) or 'overlay'.
    groupby : string, optional
        Dimension along which to group the data.
    units : string or list, optional
        Units to convert the data to.
    combine_vectors : bool, optional
        Whether to combine vector components (u, v), and use vector based plotting, i.e. `quiver`.
        NOTE: This is experimental and seems to have issues with some data sources. This will be addressed in release 0.6.
    **kwargs : dict
        Additional arguments for the plot method(s).

    Example
    -------
    >>> import earthkit.data
    >>> import earthkit.plots
    >>> data = ek.data.from_source("sample", "era5-monthly-mean-2t-199312.grib")
    >>> earthkit.plots.quickplot(data, units="celsius", domain="Europe")
    """
    import xarray as xr

    # Short-circuit for a single xarray argument: bypass FieldList machinery
    # so the XarrayExtractor is used (preserving actual coordinate values).
    if len(args) == 1 and isinstance(args[0], (xr.DataArray, xr.Dataset)):
        figure = Figure(rows=1, columns=1)
        subplot = figure.add_map(domain=domain, crs=crs)
        method = methods if isinstance(methods, str) else methods[0]
        unit = units if not isinstance(units, (list, tuple)) else units[0]
        try:
            getattr(subplot, method)(args[0], units=unit, **kwargs)
        except Exception as err:
            warnings.warn(
                f"Failed to execute {method} on given data with: \n"
                f"{err}\n\n"
                "consider constructing the plot manually."
            )
            raise err
        for m in schema.quickmap_subplot_workflow:
            _args = []
            if m == "title" and subplot_titles:
                _args = [subplot_titles]
            try:
                getattr(subplot, m)(*_args)
            except Exception as err:
                warnings.warn(
                    f"ekp.quickplot: subplot workflow step '{m}' failed with:\n{err}"
                )
        for m in schema.quickmap_figure_workflow:
            try:
                getattr(figure, m)()
            except Exception as err:
                warnings.warn(
                    f"ekp.quickplot: figure workflow step '{m}' failed with:\n{err}"
                )
        return figure

    field_list = []
    for arg in args:
        if isinstance(arg, FieldList):
            field_list.extend(list(arg))
        else:
            if not isinstance(arg, Base):
                arg = earthkit.data.from_object(arg)
            field_list.append(arg)
    args = FieldList.from_fields(field_list)

    if subplot_titles is None and groupby:
        subplot_titles = f"{{{groupby}}}"

    if groupby:
        unique_values = iter_utils.flatten(arg.metadata(groupby) for arg in args)
        unique_values = list(dict.fromkeys(unique_values))
        grouped_data = {val: args.sel(**{groupby: val}) for val in unique_values}

    elif mode == "subplots":
        grouped_data = {i: field for i, field in enumerate(args)}
    else:
        grouped_data = {None: args}

    n_plots = len(grouped_data)
    if mode == "subplots":
        rows, columns = layouts.rows_cols(n_plots, rows, columns)
    else:
        rows, columns = 1, 1

    figure = Figure(rows=rows, columns=columns)
    if not isinstance(methods, (list, tuple)):
        methods = [methods] * len(args)
    if not isinstance(units, (list, tuple)):
        units = [units] * len(args)

    for i, (group_val, group_args) in enumerate(grouped_data.items()):
        subplot = figure.add_map(domain=domain, crs=crs)

        if combine_vectors:
            group_args = group_vectors(group_args)

        if isinstance(group_args, FieldList):
            group_args = list(group_args)

        if isinstance(group_args, (list, tuple)):
            for j, (arg, method) in enumerate(zip(group_args, methods)):
                unit = units[j]
                try:
                    getattr(subplot, method)(arg, units=unit, **kwargs)
                except Exception as err:
                    warnings.warn(
                        f"Failed to execute {method} on given data with: \n"
                        f"{err}\n\n"
                        "consider constructing the plot manually."
                    )
                    raise err
        else:
            unit = units[i]
            try:
                getattr(subplot, methods[i])(group_args, units=unit, **kwargs)
            except Exception as err:
                warnings.warn(
                    f"Failed to execute {methods[i]} on given data with: \n"
                    f"{err}\n\n"
                    "consider constructing the plot manually."
                )
                raise err

        for m in schema.quickmap_subplot_workflow:
            args = []
            if m == "title" and subplot_titles:
                args = [subplot_titles]
            try:
                getattr(subplot, m)(*args)
            except Exception as err:
                warnings.warn(
                    f"Failed to execute {m} on given data with: \n"
                    f"{err}\n\n"
                    "consider constructing the plot manually."
                )

    for m in schema.quickmap_figure_workflow:
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(
                f"Failed to execute {m} on given data with: \n"
                f"{err}\n\n"
                "consider constructing the plot manually."
            )

    return figure
