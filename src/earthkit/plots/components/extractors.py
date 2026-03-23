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
Data extraction and processing functions for plotting.

This module provides functions that handle the extraction, processing, and preparation
of data for various types of plots. It centralizes the logic for data source creation,
style configuration, value processing, and specialized plotting operations.

The module is organized into three main categories:
1. Main extraction functions for different plot types
2. Style and data processing utilities
3. Specialized plotting functions for specific grid types
"""

import warnings
from typing import Any

import cartopy.crs as ccrs
import numpy as np
from cartopy.util import add_cyclic_point

from earthkit.plots.geo import coordinate_reference_systems
from earthkit.plots.identifiers import identify_primary
from earthkit.plots.resample import Unstructured
from earthkit.plots.resample.grids import needs_cyclic_point
from earthkit.plots.sources import get_source
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.styles import (
    _STYLE_KWARGS,
    DEFAULT_STYLE,
    Contour,
    Quiver,
    Style,
    auto,
)

# Private sentinel used internally by grid_cells to signal that the fast
# nearest-neighbour pixel-sampling path should be used.  This is distinct from
# plain False (which pcolormesh uses to mean "no resampling") so that
# _handle_specialized_grids can tell the two apart.
_USE_NN = object()


# ---------------------------------------------------------------------------
# Auto-resample policy
# ---------------------------------------------------------------------------
# This is the single place that defines what resample="auto" means for each
# combination of (method, grid_type).  Edit this table to change behaviour.
#
# Each entry maps (method_name, is_structured_grid) to either:
#   - a callable that returns a Resample instance  (deferred to avoid import
#     cycles; called at resolution time)
#   - the string "error"  (raises ValueError with a descriptive message)
#   - False  (no resampling)
#
# "structured grid" means HEALPix or reduced Gaussian — grids that require
# earthkit-geo to convert to a regular lat/lon array before plotting.
# "regular grid" means anything else (standard lat/lon, rotated, etc.).
#
# method_name is matched by prefix so "contourf" matches "contour".
# ---------------------------------------------------------------------------


def _auto_resample_policy(
    method_name: str, is_structured: bool, is_unstructured: bool = False
):
    """
    Return the resample object to use when ``resample='auto'``.

    Auto-resample policy table
    --------------------------

    +--------------------------+-------------------+----------------------------------+
    | Method                   | Grid type         | Auto resample                    |
    +==========================+===================+==================================+
    | contour / contourf       | structured        | Chain(Regrid(), Bilinear())      |
    +--------------------------+-------------------+----------------------------------+
    | contour / contourf       | unstructured      | Unstructured()                   |
    +--------------------------+-------------------+----------------------------------+
    | contour / contourf       | regular           | Bilinear()                       |
    +--------------------------+-------------------+----------------------------------+
    | pcolormesh               | structured        | error — must be explicit         |
    +--------------------------+-------------------+----------------------------------+
    | pcolormesh               | unstructured      | Unstructured()                   |
    +--------------------------+-------------------+----------------------------------+
    | pcolormesh               | regular           | False (native pcolormesh)        |
    +--------------------------+-------------------+----------------------------------+

    Parameters
    ----------
    method_name : str
        The name of the plotting method (e.g. ``"contourf"``, ``"pcolormesh"``).
    is_structured : bool
        Whether the source data is on a structured grid (HEALPix / reduced Gaussian).
    is_unstructured : bool
        Whether the source data is on a scattered/unstructured grid (not regular
        rectilinear and not HEALPix/reduced Gaussian).

    Returns
    -------
    Resample | False
        The resolved resample object, or ``False`` to skip resampling.

    Raises
    ------
    ValueError
        When the method/grid combination is explicitly unsupported (e.g.
        pcolormesh with a structured grid).
    """
    from earthkit.plots.resample import Bilinear, Chain, Regrid

    is_contour = method_name.startswith("contour")
    is_pcolormesh = method_name == "pcolormesh"

    if is_contour:
        if is_structured:
            # Regrid to a regular lat/lon grid first, then pixel-sample onto
            # the target projection for smooth rendering.
            return Chain(Regrid(), Bilinear())
        if is_unstructured:
            return Unstructured()
        return Bilinear()

    if is_pcolormesh:
        if is_structured:
            raise ValueError(
                "pcolormesh cannot render structured grid data (HEALPix / reduced "
                "Gaussian) with resample='auto'.  Pass an explicit resample strategy, "
                "e.g. resample=Regrid() to convert to a regular grid first, or use "
                "grid_cells() for automatic nearest-neighbour cell rendering."
            )
        if is_unstructured:
            return Unstructured()
        # Regular grid: pcolormesh renders natively via transform=PlateCarree().
        return False

    # All other methods: no resampling.
    return False


def _infer_plot_context(subplot: Any, method_name: str) -> PlotContext:
    """
    Infer plot context from subplot type and method name.

    Parameters
    ----------
    subplot : Any
        The subplot instance.
    method_name : str
        Name of the plotting method.

    Returns
    -------
    PlotContext
        Inferred plot context.
    """
    # Import here to avoid circular imports
    from earthkit.plots.components.maps import Map

    # Check if subplot is a Map
    is_map = isinstance(subplot, Map)

    # Check if method is 1D or 2D based on common method names
    is_1d = method_name in ("line", "scatter", "bar", "barh", "plot", "stripes")

    # Check if this is a vector plot
    is_vector = method_name in ("quiver", "barbs", "streamplot")

    if is_map:
        if is_vector:
            return PlotContext.GEOGRAPHIC_VECTOR_2D
        return PlotContext.GEOGRAPHIC_1D if is_1d else PlotContext.GEOGRAPHIC_2D
    else:
        if is_vector:
            return PlotContext.CARTESIAN_VECTOR_2D
        return PlotContext.CARTESIAN_1D if is_1d else PlotContext.CARTESIAN_2D


def _prepare_style_and_units(style, units, auto_style):
    """
    Handle common style/units preparation shared by all extraction functions.

    Emits a deprecation warning for auto_style, and extracts units from a
    provided Style object when not already supplied by the caller.

    When *style* is a named-style string (anything other than ``"auto"``), it
    is resolved to a :class:`~earthkit.plots.styles.Style` object here so that
    its ``_units`` can be read.  The resolved object is returned as a second
    value so that callers can pass it straight to ``configure_style`` and avoid
    a second YAML lookup.

    Returns the (possibly updated) ``(units, style)`` pair.
    """
    if auto_style:
        warnings.warn(
            "The 'auto_style' parameter is deprecated and will be removed in a future version. "
            "Please use style='auto' instead.",
            DeprecationWarning,
            stacklevel=4,
        )

    # Resolve named-style strings early so we can read their _units below.
    if isinstance(style, str) and style != "auto":
        style = auto.load_style(style)

    if units is None and style is not None and style != "auto":
        if hasattr(style, "_units") and style._units is not None:
            units = style._units

    return units, style


def extract_plottables_1D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    z: str | np.ndarray | list[float] | None = None,
    style: Style | str | None = None,
    no_style: bool = False,
    units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    z_units: str | None = None,
    every: int | None = None,
    resample: Any = False,
    source_units: str | None = None,
    auto_style: bool = False,
    metadata: dict[str, Any] | None = None,
    label: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for 1D plotting methods.

    This function handles the complete data pipeline for 1D plots including:
    source creation, style configuration, value processing, sampling, and plotting.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    method_name : str
        The name of the plotting method to call on the style object.
    args : tuple
        Positional arguments passed to the plotting method.
    x, y, z : str, array-like, or None, optional
        Data coordinates. If strings, they are treated as coordinate names.
    style : Style, str, or None, optional
        The style object to use for plotting. If None, one will be created.
        If the string "auto", automatic style detection will be used.
    no_style : bool, default=False
        Whether to skip style processing and use raw matplotlib methods.
    units : str, optional
        Units for the data values.
    every : int, optional
        Sampling interval for data reduction.
    source_units : str, optional
        Units of the source data.
    auto_style : bool, default=False
        Deprecated. Use style="auto" instead. Whether to automatically guess the appropriate style.
    metadata : dict, optional
        Additional metadata for the data source.
    label : str, optional
        The label to use for the legend.
    **kwargs
        Additional keyword arguments passed to the plotting method.

    Returns
    -------
    Any
        The matplotlib mappable object created by the plotting method.

    Examples
    --------
    >>> mappable = extract_plottables_2D(subplot, "line", (), x=[1, 2, 3], y=[4, 5, 6])
    """
    # Step 0: Handle deprecation and extract units from style
    units, style = _prepare_style_and_units(style, units, auto_style)

    # Step 1: Infer plot context and initialize the data source
    context = _infer_plot_context(subplot, method_name)
    source = get_source(
        *args,
        x=x,
        y=y,
        z=z,
        context=context,
        units=units,  # Target units for unit conversion (from call or style)
        x_units=x_units,  # Target units for x coordinates
        y_units=y_units,  # Target units for y coordinates
        z_units=z_units,  # Target units for z coordinates
        metadata=metadata,
    )
    kwargs.update(subplot._plot_kwargs(source))

    # Step 2: Configure the plotting style
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Step 3: Process z values (convert units, apply scale factors)
    if z is not None or (source.z is not None and source.z.values is not None):
        z_values = apply_scale_factor(style, source, z)
        # apply_scale_factor returns None when source.z is None (e.g. numpy arrays
        # passed as x=/y=/z= in a geographic 1D context where the extractor doesn't
        # populate source.z). Fall back to the raw z array in that case.
        if z_values is None and isinstance(z, np.ndarray):
            z_values = z
    else:
        z_values = None

    # Step 4: Apply unit conversion to x and y values if needed
    x_values, y_values = _apply_coordinate_unit_conversion(source)

    # Step 5: Apply sampling if specified
    x_values, y_values, z_values = apply_sampling(x_values, y_values, z_values, every)

    # Step 5.1: Clip to domain before any further processing
    if subplot.domain is not None:
        x_values, y_values, z_values = subplot.domain.extract(
            x_values, y_values, z_values, source_crs=source.crs
        )

    # Step 5.5: Apply data-space resampling if requested.
    # Note: pixel-samplers (_PixelSampler subclasses like Bilinear/NearestNeighbour)
    # cannot be applied to scatter — they produce a regular pixel grid that only
    # makes sense for pcolormesh/contour/contourf.  Raise an informative error so
    # the user knows to use Regrid() instead.
    if resample is not False and resample is not None:
        from earthkit.plots.resample import Chain, Regrid, Resample, _PixelSampler

        # Check for pixel-samplers at the top level or inside a Chain
        _top_level_pixel = isinstance(resample, _PixelSampler)
        _chain_pixel = isinstance(resample, Chain) and resample.pixel_step is not None
        if _top_level_pixel or _chain_pixel:
            raise ValueError(
                f"{resample.__class__.__name__} is a pixel-sampler and cannot be "
                "used with scatter (it produces a regular image grid, not discrete "
                "points).  Use Regrid() to resample to a regular lat/lon grid "
                "before scattering, e.g. resample=Regrid()."
            )

        if isinstance(resample, Chain):
            data_steps = resample.data_steps
        else:
            data_steps = [resample]

        for step in data_steps:
            if isinstance(step, Regrid):
                context = _infer_plot_context(subplot, method_name)
                x_values, y_values, z_values = step.apply(
                    x_values,
                    y_values,
                    z_values,
                    gridspec=source.gridspec,
                    context=context,
                )
            elif isinstance(step, Unstructured):
                x_values, y_values, z_values = step.apply(
                    x_values,
                    y_values,
                    z_values,
                    source_crs=source.crs,
                    target_crs=getattr(subplot, "crs", None),
                )
            elif isinstance(step, Resample):
                x_values, y_values, z_values = step.apply(x_values, y_values, z_values)

    # Step 6: Handle no-style case for z values
    if no_style and z_values is None:
        z_values = kwargs.pop("c", None)

    # Step 7: Create the plot using the style object
    mappable = getattr(style, method_name)(
        subplot.ax, x_values, y_values, z_values, **kwargs
    )

    # Step 8: Store the layer and return the mappable
    from earthkit.plots.components.layers import Layer

    # Determine primary axis for unit conversion display
    primary_axis = _identify_primary_axis(source, source._x_spec, source._y_spec)

    # Store axis-specific units for formatter
    axis_units = {}
    if x_units is not None:
        axis_units["x"] = x_units
    if y_units is not None:
        axis_units["y"] = y_units
    if (
        units is not None
        and primary_axis is not None
        and primary_axis not in axis_units
    ):
        axis_units[primary_axis] = units

    layer = Layer(
        source,
        mappable,
        subplot,
        style,
        primary_axis=primary_axis,
        axis_units=axis_units,
    )

    if label is not None:
        label = layer.format_string(label)
        if isinstance(mappable, list):
            # Only the first line in the group gets the label; the rest are
            # hidden from the legend so that grouped calls (e.g. color_by=)
            # produce exactly one legend entry per group.
            for i, m in enumerate(mappable):
                m.set_label(label if i == 0 else "_nolegend_")
        else:
            mappable.set_label(label)

    subplot.layers.append(layer)

    return mappable


def _identify_primary_axis(source, x, y):
    """
    Identify which axis (x or y) contains the primary data for unit conversion.

    This function uses the identify_primary function from identifiers.py to determine
    which variable contains the actual data values (as opposed to coordinate dimensions).

    Parameters
    ----------
    source : Source
        The data source object.
    x, y : str, array-like, or None
        X and Y coordinate values or names.

    Returns
    -------
    str or None
        'x', 'y', or None if no primary axis can be identified.
    """
    # Try to get the underlying data object for analysis
    data = None
    if hasattr(source, "data") and source.data is not None:
        data = source.data
    elif hasattr(source, "_data") and source._data is not None:
        data = source._data

    if data is None:
        return None

    # Use identify_primary to find the primary variable/dimension
    primary = identify_primary(data)

    if primary is None:
        return None

    # Check if the primary variable/name corresponds to x or y coordinates
    # If x or y were specified as strings, check if primary matches them
    if isinstance(x, str) and primary == x:
        return "x"
    if isinstance(y, str) and primary == y:
        return "y"

    # For xarray data, check if we can infer the axis from the data structure
    if hasattr(data, "dims"):
        # If primary is a variable name (Dataset case), check where it maps
        if hasattr(data, "data_vars") and primary in data.data_vars:
            # The primary is a data variable - we need to figure out which axis it maps to
            # This is tricky without more context, so we'll use heuristics

            # If x and y are dimension names, check which one the primary variable uses
            if isinstance(x, str) and isinstance(y, str):
                var_dims = list(data[primary].dims)
                if x in var_dims and y not in var_dims:
                    return "x"
                elif y in var_dims and x not in var_dims:
                    return "y"
                elif len(var_dims) == 1:
                    # Single dimension - check if it's more likely x or y
                    dim = var_dims[0]
                    if dim == x:
                        return "x"
                    elif dim == y:
                        return "y"

            # Default heuristic: if it's a 1D variable, assume it maps to y (values)
            if len(data[primary].dims) == 1:
                return "y"

        # If primary is a DataArray name, assume it maps to y (the data values)
        elif hasattr(data, "name") and primary == data.name:
            return "y"

        # If primary is a dimension name (fallback case), use position heuristics
        elif primary in data.dims:
            dims = list(data.dims)
            if len(dims) == 2 and dims.index(primary) == 1:
                return "y"
            else:
                return "x"

    return None


def _apply_coordinate_unit_conversion(source):
    """
    Get x and y coordinate values from source (unit conversion already applied).

    Unit conversion is now handled inside the Source class when units/x_units/y_units
    are passed to get_source(). This function simply extracts the already-converted
    values from the source.

    Parameters
    ----------
    source : Source
        The data source object (already configured with target units).

    Returns
    -------
    tuple
        A tuple of (x_values, y_values) with unit conversion already applied.
    """
    # Unit conversion is handled by Source class when accessing these properties
    x_values = source.x.values
    y_values = source.y.values

    return x_values, y_values


def extract_plottables_2D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    z: str | np.ndarray | list[float] | None = None,
    style: Style | str | None = None,
    no_style: bool = False,
    units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    z_units: str | None = None,
    every: int | None = None,
    source_units: str | None = None,
    extract_domain: bool = False,
    auto_style: bool = False,
    metadata: dict[str, Any] | None = None,
    resample=None,
    grid="auto",
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for 2D plotting methods.

    This function handles the complete data pipeline for 2D plots including:
    source creation, style configuration, value processing, domain extraction,
    cyclic point handling, and specialized grid type plotting.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    method_name : str
        The name of the plotting method to call on the style object.
    args : tuple
        Positional arguments passed to the plotting method.
    x, y, z : str, array-like, or None, optional
        Data coordinates. If strings, they are treated as coordinate names.
    style : Style, str, or None, optional
        The style object to use for plotting. If None, one will be created.
        If the string "auto", automatic style detection will be used.
    no_style : bool, default=False
        Whether to skip style processing and use raw matplotlib methods.
    units : str, optional
        Units for the data values.
    every : int, optional
        Sampling interval for data reduction.
    source_units : str, optional
        Units of the source data.
    extract_domain : bool, default=False
        Whether to extract data within the subplot's domain boundaries.
    auto_style : bool, default=False
        Deprecated. Use style="auto" instead. Whether to automatically guess the appropriate style.
    metadata : dict, optional
        Additional metadata for the data source.
    resample : Bilinear, NearestNeighbour, False, or None, default=None
        Controls pixel-sampling on the target projection.
        Pass a :class:`~earthkit.plots.resample.Bilinear` or
        :class:`~earthkit.plots.resample.NearestNeighbour` instance to
        enable sampling at a custom resolution, ``False`` to disable, or
        ``None`` to use the method's default. Only applies to contour/contourf/pcolormesh
        on geographic plots.
    **kwargs
        Additional keyword arguments passed to the plotting method.

    Returns
    -------
    Any
        The matplotlib mappable object created by the plotting method.

    Examples
    --------
    >>> mappable = extract_plottables_3D(
    ...     subplot, "pcolormesh", (), x=[1, 2, 3], y=[4, 5, 6], z=[[1, 2], [3, 4]]
    ... )
    """
    # Step 0: Handle deprecation and extract units from style
    units, style = _prepare_style_and_units(style, units, auto_style)

    from earthkit.plots.resample import _AUTO

    # Translate legacy `interpolate` kwarg to `resample`
    if "interpolate" in kwargs and resample is None:
        interp = kwargs.pop("interpolate")
        warnings.warn(
            "The 'interpolate' keyword argument is deprecated. "
            "Use 'resample=Unstructured(...)' instead.",
            DeprecationWarning,
            stacklevel=5,
        )
        if interp is True:
            resample = Unstructured()
        elif isinstance(interp, dict):
            resample = Unstructured(**interp)
        elif isinstance(interp, Unstructured):
            resample = interp

    _resample_is_auto = resample == _AUTO

    # Step 2: Infer plot context and initialize the data source
    context = _infer_plot_context(subplot, method_name)
    source = get_source(
        *args,
        x=x,
        y=y,
        z=z,
        context=context,
        units=units,  # Target units for unit conversion (from call or style)
        x_units=x_units,  # Target units for x coordinates
        y_units=y_units,  # Target units for y coordinates
        z_units=z_units,  # Target units for z coordinates
        metadata=metadata,
    )
    kwargs.update(subplot._plot_kwargs(source))

    if grid != "auto":
        source._gridspec_override = grid

    # Step 2.5: Resolve resample="auto" — delegates to _auto_resample_policy
    # which contains the full policy table (see top of this module).
    if _resample_is_auto:
        from earthkit.plots.resample import _is_structured_grid
        from earthkit.plots.resample.grids import is_structured as _is_regular_grid

        _healpix_structured = _is_structured_grid(source.gridspec)
        # Only check regularity when it's not already a HEALPix/reduced-Gaussian
        # grid, and only when the source coordinates are available.
        _unstructured = False
        if not _healpix_structured:
            try:
                _unstructured = not _is_regular_grid(source.x.values, source.y.values)
            except Exception:
                pass

        resample = _auto_resample_policy(
            method_name, _healpix_structured, is_unstructured=_unstructured
        )

    # Step 3: Configure the plotting style
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Strip internal earthkit-plots keys injected by schema defaults that are
    # not valid matplotlib kwargs (e.g. 'regrid' from contour/contourf schema).
    kwargs.pop("regrid", None)

    # Intercept `label` before it reaches matplotlib. ContourSet objects don't
    # participate in the auto-legend mechanism, so we handle it ourselves via
    # proxy artists stored on the layer. Also snapshot the line colour now,
    # before kwargs are consumed by the plot call.
    proxy_label = kwargs.pop("label", None)
    proxy_color = kwargs.get("colors") or kwargs.get("color")

    # Step 4: Process z values (convert units, apply scale factors)
    z_values = apply_scale_factor(style, source, z)

    # Step 5: Handle specialized grid types (healpix, octahedral)
    mappable = _handle_specialized_grids(
        subplot, source, z_values, style, method_name, kwargs, resample=resample
    )

    if not mappable:
        # Step 6: Process x, y values and apply sampling
        # For 3D plots, use source coordinates directly (no coordinate unit conversion)
        x_values, y_values = source.x.values, source.y.values
        x_values, y_values, z_values = apply_sampling(
            x_values, y_values, z_values, every
        )

        # If _USE_NN reached here it means _handle_regular_grid_nn returned None
        # (e.g. CRS matched, so NN was not needed). Treat it as False for the
        # remainder of the pipeline so the plain pcolormesh path is used.
        if resample is _USE_NN:
            resample = False

        # Step 6.5: Apply data-space resampling if requested.
        # _PixelSampler subclasses (Bilinear, NearestNeighbour) are handled
        # later in Step 8.5 since they need subplot/CRS/bbox context that is
        # unavailable at construction time.  All other Resample subclasses
        # operate directly on coordinate arrays here.
        if resample is not False and resample is not None:
            from earthkit.plots.resample import Chain, Regrid, Resample, _PixelSampler

            # Unwrap Chain into its data-space steps; the pixel step (if any)
            # will be picked up at Step 8.5.
            if isinstance(resample, Chain):
                data_steps = resample.data_steps
            elif not isinstance(resample, _PixelSampler):
                data_steps = [resample]
            else:
                data_steps = []

            for step in data_steps:
                if isinstance(step, Regrid):
                    # Regrid resamples to a regular lat/lon grid in data space
                    # via earthkit-geo.  Pass the source gridspec so the
                    # resampler can validate that the grid type is supported.
                    context = _infer_plot_context(subplot, method_name)
                    x_values, y_values, z_values = step.apply(
                        x_values,
                        y_values,
                        z_values,
                        gridspec=source.gridspec,
                        context=context,
                    )
                elif isinstance(step, Unstructured):
                    # Unstructured needs CRS context to transform coordinates
                    # before building the output grid.
                    x_values, y_values, z_values = step.apply(
                        x_values,
                        y_values,
                        z_values,
                        source_crs=source.crs,
                        target_crs=subplot.crs,
                    )
                    # The output is already in the target CRS, so drop any
                    # cartopy transform kwarg to avoid a double-transformation,
                    # and skip domain extraction (coordinates are already clipped
                    # to the valid projection area by the non-finite filter).
                    if step.transform:
                        kwargs.pop("transform", None)
                        kwargs.pop("transform_first", None)
                        extract_domain = False
                elif isinstance(step, Resample):
                    x_values, y_values, z_values = step.apply(
                        x_values, y_values, z_values
                    )

        # Step 7: Handle no-style case for z values
        if no_style and z_values is None:
            z_values = kwargs.pop("c", None)

        # Step 8: Extract data within domain boundaries if requested
        if subplot.domain and extract_domain and not no_style:
            x_values, y_values, z_values = subplot.domain.extract(
                x_values, y_values, z_values, source_crs=source.crs
            )

        # Step 8.5: Pixel-sampling on the target projection (Bilinear /
        # NearestNeighbour).  These cannot use apply() like other resamplers
        # because they need subplot/CRS/bbox context unavailable at construction
        # time.  All other Resample subclasses were already applied in Step 6.5.
        will_reproject = False
        from earthkit.plots.resample import Chain, NearestNeighbour, _PixelSampler

        # Extract the effective pixel sampler — handles plain sampler and Chain.
        _pixel_sampler = (
            resample.pixel_step
            if isinstance(resample, Chain)
            else resample
            if isinstance(resample, _PixelSampler)
            else None
        )
        if (
            _pixel_sampler is not None
            and not no_style
            and (method_name.startswith("contour") or method_name == "pcolormesh")
            and hasattr(subplot, "crs")
        ):
            target_crs = subplot.crs
            # source.crs may be None for plain lat/lon data; fall back to the
            # transform already placed in kwargs by _plot_kwargs, then PlateCarree.
            data_crs = source.crs or kwargs.get("transform") or ccrs.PlateCarree()
            _is_scattered = (
                x_values.ndim == 1 and z_values is not None and z_values.ndim == 1
            )
            if target_crs is not None and (
                type(data_crs).__name__ != type(target_crs).__name__ or _is_scattered
            ):
                try:
                    bbox_target = subplot.ax.get_extent(crs=target_crs)
                except AttributeError:
                    if subplot.domain is not None:
                        bbox_target = subplot.domain.bbox.to_cartopy_bounds()
                    else:
                        bbox_target = (-180, 180, -90, 90)

                nx, ny = _pixel_sampler.resolve(bbox_target, crs=target_crs)

                if isinstance(_pixel_sampler, NearestNeighbour):
                    # NearestNeighbour path: only valid for regular rectilinear
                    # grids; fall back to Bilinear if the grid is curvilinear.
                    is_regular = (
                        x_values.ndim == 2
                        and y_values.ndim == 2
                        and np.allclose(x_values, x_values[0, :])
                        and np.allclose(y_values.T, y_values[:, 0])
                    )
                    if is_regular:
                        from earthkit.plots.resample.reproject import _reproject_nn

                        image, extent = _reproject_nn(
                            x_values[0, :],
                            y_values[:, 0],
                            z_values,
                            crs_src=data_crs,
                            bbox_target=bbox_target,
                            crs_target=target_crs,
                            nx=nx,
                            ny=ny,
                        )
                        plot_kwargs = dict(kwargs)
                        if style is not None:
                            plot_kwargs.update(style.to_pcolormesh_kwargs(image))
                        plot_kwargs.pop("transform", None)
                        plot_kwargs.pop("transform_first", None)
                        mappable = subplot.ax.imshow(
                            image, extent=extent, origin="lower", **plot_kwargs
                        )
                        will_reproject = True  # suppress Steps 9 and 11

                if not will_reproject:
                    # Bilinear (or NearestNeighbour fallback for curvilinear grids)
                    from earthkit.plots.resample.reproject import reproject_to_grid

                    # Extract 1D coordinate arrays if data came as a regular meshgrid.
                    # For curvilinear (2D) grids, pass the 2D arrays directly so
                    # reproject_to_grid uses its scattered-interpolation path.
                    if x_values.ndim == 2 and y_values.ndim == 2:
                        # Check if it's a proper regular meshgrid (rows/cols constant)
                        if np.allclose(x_values, x_values[0, :]) and np.allclose(
                            y_values.T, y_values[:, 0]
                        ):
                            x_src = x_values[0, :]
                            y_src = y_values[:, 0]
                        else:
                            x_src = x_values
                            y_src = y_values
                    else:
                        x_src = x_values
                        y_src = y_values

                    x_values, y_values, z_values = reproject_to_grid(
                        x_src,
                        y_src,
                        z_values,
                        crs_src=data_crs,
                        bbox_target=bbox_target,
                        crs_target=target_crs,
                        nx=nx,
                        ny=ny,
                        method="nearest"
                        if isinstance(_pixel_sampler, NearestNeighbour)
                        else "linear",
                    )
                    kwargs["transform"] = target_crs
                    will_reproject = True

        # Step 9: Handle cyclic point wrapping for contour plots
        # Skip if we already reprojected (reprojected data is already a complete regular grid)
        if method_name.startswith("contour") and not will_reproject:
            x_values, y_values, z_values = _handle_cyclic_points(
                x_values, y_values, z_values
            )

        # Step 10: Handle coordinate transformation settings
        kwargs = _handle_transform_settings(subplot, kwargs)

        # Step 11: Create the plot
        # (skipped when the NearestNeighbour path already produced a mappable)
        if not mappable:
            if not no_style:
                mappable = getattr(style, method_name)(
                    subplot.ax, x_values, y_values, z_values, **kwargs
                )
            else:
                mappable = getattr(subplot.ax, method_name)(
                    x_values, y_values, z_values, **kwargs
                )

    # Step 12: Store the layer and return the mappable
    from earthkit.plots.components.layers import Layer

    # For 3D plots, the primary data is typically on the z-axis
    primary_axis = "z"

    # Store axis-specific units for formatter
    axis_units = {}
    if x_units is not None:
        axis_units["x"] = x_units
    if y_units is not None:
        axis_units["y"] = y_units
    if units is not None and "z" not in axis_units:
        axis_units["z"] = units

    layer = Layer(
        source,
        mappable,
        subplot,
        style,
        primary_axis=primary_axis,
        axis_units=axis_units,
    )

    if proxy_label is not None:
        layer.style = None
        layer.proxy_label = proxy_label
        # Normalise colour: colors may be a list like ["orange"]
        if isinstance(proxy_color, (list, tuple)):
            proxy_color = proxy_color[0]
        layer._proxy_color = proxy_color
        layer._proxy_linewidth = kwargs.get("linewidths", 1.0)
    else:
        layer.proxy_label = None
        layer._proxy_color = None
        layer._proxy_linewidth = None

    subplot.layers.append(layer)
    return mappable


def extract_plottables_vector_2D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    u: str | np.ndarray | list[float] | None = None,
    v: str | np.ndarray | list[float] | None = None,
    style: Style | str | None = None,
    no_style: bool = False,
    units: str | None = None,
    u_units: str | None = None,
    v_units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    source_units: str | None = None,
    extract_domain: bool = False,
    auto_style: bool = False,
    resample: Any | None = None,
    colors: bool = False,
    metadata: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for vector plotting methods (quiver, barbs).

    This function handles the complete data pipeline for vector plots including:
    source creation, style configuration, u/v component extraction, domain extraction,
    and resampling.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    method_name : str
        The name of the plotting method to call on the style object.
    args : tuple
        Positional arguments. Can be:
        - Empty: requires u and v keyword arguments
        - Single data object: will auto-detect u/v or use u/v keyword args
        - Two data objects: first is u, second is v (legacy)
    x, y : str, array-like, or None, optional
        Data coordinates. If strings, they are treated as coordinate names.
    u, v : str, array-like, or None, optional
        U and V components. Can be variable names or arrays.
    style : Style, str, or None, optional
        The style object to use for plotting. If None, one will be created.
        If the string "auto", automatic style detection will be used.
    no_style : bool, default=False
        Whether to skip style processing and use raw matplotlib methods.
    units : str, optional
        Units for the data values.
    u_units, v_units : str, optional
        Target units for u and v components.
    x_units, y_units : str, optional
        Target units for x and y coordinates.
    source_units : str, optional
        Deprecated. Use 'units' instead.
    extract_domain : bool, default=False
        Whether to extract data within the subplot's domain boundaries.
    auto_style : bool, default=False
        Deprecated. Use style="auto" instead. Whether to automatically guess the appropriate style.
    resample : Resample or None, optional
        Resampling strategy for the vector field.
    colors : bool, default=False
        Whether to color vectors by magnitude.
    metadata : dict, optional
        Additional metadata for the data source.
    **kwargs
        Additional keyword arguments passed to the plotting method.

    Returns
    -------
    Any
        The matplotlib mappable object created by the plotting method.

    Examples
    --------
    >>> # Auto-detection from single data source
    >>> mappable = extract_plottables_vector_3D(subplot, "barbs", (data,))

    >>> # Explicit u/v specification
    >>> mappable = extract_plottables_vector_3D(
    ...     subplot, "quiver", (data,), u="u_component", v="v_component"
    ... )

    >>> # Legacy two-source approach
    >>> mappable = extract_plottables_vector_3D(subplot, "barbs", (u_data, v_data))
    """
    # Support deprecated source_units parameter
    if source_units is not None and units is None:
        units = source_units

    # Handle deprecation and extract units from style
    units, style = _prepare_style_and_units(style, units, auto_style)

    # Step 1: Handle different argument patterns and create a unified source
    source = None
    u_values_raw = None
    v_values_raw = None
    context = _infer_plot_context(subplot, method_name)

    if not args:
        # No positional args - u and v must be keyword arguments
        # This could be: chart.barbs(u=u_data, v=v_data)
        if u is not None and v is not None:
            # Create temporary sources to extract u and v data, then validate coordinates match
            u_source = get_source(
                u, x=x, y=y, context=context, units=units, metadata=metadata
            )
            v_source = get_source(
                v, x=x, y=y, context=context, units=units, metadata=metadata
            )

            # Validate that x and y coordinates match
            if not np.array_equal(u_source.x.values, v_source.x.values):
                raise ValueError(
                    "X coordinates from u and v sources do not match. "
                    "U and V components must be defined on the same grid."
                )
            if not np.array_equal(u_source.y.values, v_source.y.values):
                raise ValueError(
                    "Y coordinates from u and v sources do not match. "
                    "U and V components must be defined on the same grid."
                )

            # Extract u and v values from their respective z fields.
            # Squeeze out any leading size-1 dimensions that arise when a
            # single Field is wrapped into a length-1 FieldList by get_source.
            u_array = u_source.z.values.squeeze() if u_source.z else None
            v_array = v_source.z.values.squeeze() if v_source.z else None

            # Use u_source as the primary source (preserves CRS, metadata, etc.)
            # but supply u/v values directly to avoid a second round-trip through
            # get_source which can re-introduce shape inconsistencies.
            source = u_source
            u_values_raw = u_array
            v_values_raw = v_array
        else:
            raise ValueError(
                "Vector plots require both u and v components. "
                "Provide as: chart.barbs(data) with auto-detection, "
                "chart.barbs(data, u='u_var', v='v_var'), or "
                "chart.barbs(u=u_data, v=v_data)"
            )
    elif len(args) == 1:
        # Single data object - unified approach with auto-detection or explicit u/v
        source = get_source(
            args[0],
            x=x,
            y=y,
            u=u,
            v=v,
            context=context,
            units=units,
            u_units=u_units,
            v_units=v_units,
            x_units=x_units,
            y_units=y_units,
            metadata=metadata,
        )

        # Check if source has u and v components
        if source.u is not None and source.v is not None:
            u_values_raw = source.u.values
            v_values_raw = source.v.values
        else:
            raise ValueError(
                "Could not extract u and v components from data. "
                "Either specify them explicitly (u='u_var', v='v_var') or "
                "ensure the data contains recognizable U/V variable names."
            )
    elif len(args) == 2:
        # Two separate data objects for u and v (legacy)
        u_source = get_source(
            args[0], x=x, y=y, context=context, units=units, metadata=metadata
        )
        v_source = get_source(
            args[1], x=x, y=y, context=context, units=units, metadata=metadata
        )

        # Validate that x and y coordinates match
        if not np.array_equal(u_source.x.values, v_source.x.values):
            raise ValueError(
                "X coordinates from u and v sources do not match. "
                "U and V components must be defined on the same grid."
            )
        if not np.array_equal(u_source.y.values, v_source.y.values):
            raise ValueError(
                "Y coordinates from u and v sources do not match. "
                "U and V components must be defined on the same grid."
            )

        # Extract values - use z if available, otherwise y.
        # Squeeze out any leading size-1 dimensions from single-field FieldLists.
        u_array = (u_source.z.values if u_source.z else u_source.y.values).squeeze()
        v_array = (v_source.z.values if v_source.z else v_source.y.values).squeeze()

        # Create a properly unified source with u and v as numpy arrays
        # This ensures the source has proper .u and .v properties
        source = get_source(
            u_source._data,  # Use the underlying data from u_source
            x=x if x is not None else u_source.x.values,
            y=y if y is not None else u_source.y.values,
            u=u_array,  # Pass u as numpy array
            v=v_array,  # Pass v as numpy array
            context=context,
            units=units,
            u_units=u_units,
            v_units=v_units,
            x_units=x_units,
            y_units=y_units,
            metadata=metadata,
        )

        # Extract u and v from the unified source
        u_values_raw = source.u.values if source.u else None
        v_values_raw = source.v.values if source.v else None
    else:
        raise ValueError("Invalid arguments for vector plot")

    # Step 2: Update kwargs with plot-specific settings
    kwargs.update(subplot._plot_kwargs(source))

    # Step 2.5: If no domain was set, auto-fit the map extent to the data.
    # This mirrors the behaviour of scalar plots (contourf etc.) where cartopy
    # auto-scales to the plotted data.  For vector plots the resampling step
    # later calls subplot.ax.get_extent(), so the extent must be set first.
    if subplot.domain is None and hasattr(subplot, "ax"):
        try:
            from earthkit.plots.geo import domains as _domains
            from earthkit.plots.geo.domains import force_minus_180_to_180

            x_ext = source.x.values.squeeze()
            y_ext = source.y.values.squeeze()
            if np.any(x_ext > 180):
                x_ext = force_minus_180_to_180(x_ext)
            subplot.domain = _domains.Domain.from_bbox(
                bbox=[x_ext.min(), x_ext.max(), y_ext.min(), y_ext.max()],
                source_crs=source.crs,
                target_crs=subplot.crs,
            )
            subplot.ax.set_extent(
                subplot.domain.bbox.to_cartopy_bounds(),
                subplot.domain.bbox.crs,
            )
        except Exception:
            pass

    # Step 3: Configure the plotting style
    # Only forward `colors` to configure_style when it was explicitly provided
    # (i.e. not the False sentinel default), so that a user-supplied style's
    # own colors are not overwritten.
    style_kwargs = {**kwargs}
    if colors is not False:
        style_kwargs["colors"] = colors
    style = configure_style(method_name, style, source, units, auto_style, style_kwargs)

    # Step 4: Extract x, y coordinate values.
    # Squeeze to remove any leading size-1 field-count dimension that arises
    # when a single earthkit Field is internally wrapped into a FieldList.
    # Also normalise longitudes > 180 into [-180, 180] so cartopy renders the
    # data correctly (e.g. 240–280° → -120–-80°), rolling u/v to match.
    x_values = source.x.values.squeeze()
    y_values = source.y.values.squeeze()
    if np.any(x_values > 180):
        from earthkit.plots.geo.domains import (
            force_minus_180_to_180,
            roll_from_0_360_to_minus_180_180,
        )

        ref = x_values[0] if x_values.ndim == 2 else x_values
        roll_by = roll_from_0_360_to_minus_180_180(ref)
        if x_values.ndim == 2:
            x_values = np.roll(x_values, roll_by, axis=1)
            u_values_raw = np.roll(u_values_raw, roll_by, axis=1)
            v_values_raw = np.roll(v_values_raw, roll_by, axis=1)
        else:
            x_values = np.roll(x_values, roll_by)
            u_values_raw = np.roll(u_values_raw, roll_by)
            v_values_raw = np.roll(v_values_raw, roll_by)
        x_values = force_minus_180_to_180(x_values)

    # Step 5: Validate u and v values exist
    if u_values_raw is None or v_values_raw is None:
        raise ValueError("Vector plots require u and v components")

    # Step 6: Get u and v values (already converted by Source if target units were specified)
    # Source handles unit conversion internally when u_units/v_units are passed to get_source()
    u_values = u_values_raw
    v_values = v_values_raw

    # Apply style-specific scale factors if needed (styles can have scale factors)
    # Note: Style.convert_units() also applies scale factors, but since Source already
    # did the unit conversion, we should only apply scale factors here if Style has them
    # Currently Quiver/Style classes don't have scale factors like Contour does, so this is a no-op
    # but we keep it for consistency with how scalar fields are processed

    # Step 7: Use style's resample setting if not explicitly provided.
    if resample is None:
        resample = style.resample

    # Step 8: Extract data within domain boundaries if requested
    if subplot.domain and extract_domain:
        x_values, y_values, _, [u_values, v_values] = subplot.domain.extract(
            x_values,
            y_values,
            extra_values=[u_values, v_values],
            source_crs=source.crs,
        )

    # Step 9: Apply resampling — use reproject_to_grid for _PixelSampler
    # (Bilinear / NearestNeighbour), applied independently to u and v.
    from earthkit.plots.resample import Resample, Unstructured, _PixelSampler

    if resample is not None:
        if isinstance(resample, _PixelSampler) and hasattr(subplot, "crs"):
            from earthkit.plots.resample.reproject import reproject_to_grid

            target_crs = subplot.crs or ccrs.PlateCarree()
            data_crs = source.crs or ccrs.PlateCarree()
            try:
                bbox_target = subplot.ax.get_extent(crs=target_crs)
            except Exception:
                bbox_target = (-180, 180, -90, 90)
            nx, ny = resample.resolve(bbox_target, crs=target_crs)
            # Extract 1D axes from meshgrid if regular
            if x_values.ndim == 2 and y_values.ndim == 2:
                if np.allclose(x_values, x_values[0, :]) and np.allclose(
                    y_values.T, y_values[:, 0]
                ):
                    x_src, y_src = x_values[0, :], y_values[:, 0]
                else:
                    x_src, y_src = x_values, y_values
            else:
                x_src, y_src = x_values, y_values
            x_values, y_values, u_values = reproject_to_grid(
                x_src,
                y_src,
                u_values,
                crs_src=data_crs,
                bbox_target=bbox_target,
                crs_target=target_crs,
                nx=nx,
                ny=ny,
            )
            _, _, v_values = reproject_to_grid(
                x_src,
                y_src,
                v_values,
                crs_src=data_crs,
                bbox_target=bbox_target,
                crs_target=target_crs,
                nx=nx,
                ny=ny,
            )
            kwargs["transform"] = target_crs
        elif isinstance(resample, Unstructured):
            x_values, y_values, u_values = resample.apply(
                x_values,
                y_values,
                u_values,
                source_crs=source.crs,
                target_crs=subplot.crs,
            )
            _, _, v_values = resample.apply(
                x_values,
                y_values,
                v_values,
                source_crs=source.crs,
                target_crs=subplot.crs,
            )
        elif isinstance(resample, Resample):
            x_values, y_values, u_values, v_values = resample.apply(
                x_values, y_values, u_values, v_values
            )

    # Step 10: Prepare arguments for plotting method
    plot_args = [x_values, y_values, u_values, v_values]

    # Step 11: Add magnitude coloring if requested
    if colors:
        # Use source.z which computes magnitude for vector fields
        magnitude = (
            source.z.values if source.z else np.sqrt(u_values**2 + v_values**2)
        )
        plot_args.append(magnitude)

    # Step 12: Create the plot
    mappable = getattr(style, method_name)(subplot.ax, *plot_args, **kwargs)

    # Step 13: Store the layer and return the mappable
    from earthkit.plots.components.layers import Layer

    # Always use single unified source
    subplot.layers.append(Layer(source, mappable, subplot, style))

    # Step 14: Set axis labels if coordinate names were provided
    if isinstance(source._x_spec, str):
        subplot.ax.set_xlabel(source._x_spec)
    if isinstance(source._y_spec, str):
        subplot.ax.set_ylabel(source._y_spec)

    return mappable


def extract_plottables_envelope(
    subplot: Any,
    data: np.ndarray | list[float] | None = None,
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    z: str | np.ndarray | list[float] | None = None,
    every: int | None = None,
    units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    z_units: str | None = None,
    source_units: str | None = None,
    extract_domain: bool = False,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Extract data for envelope plotting methods (e.g., fill_between).

    This function handles data extraction for envelope plots, which typically
    need x, y coordinates and optional z values for operations like fill_between.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    data : array-like, optional
        The main data array.
    x, y, z : str, array-like, or None, optional
        Data coordinates. If strings, they are treated as coordinate names.
    every : int, optional
        Sampling interval for data reduction.
    units : str, optional
        Target units for primary data values (z for 2D plots, y for 1D plots).
    x_units : str, optional
        Target units for x coordinates.
    y_units : str, optional
        Target units for y coordinates.
    z_units : str, optional
        Target units for z coordinates.
    source_units : str, optional
        Deprecated. Use 'units' instead.
    extract_domain : bool, default=False
        Whether to extract data within the subplot's domain boundaries.
    **kwargs
        Additional keyword arguments.

    Returns
    -------
    tuple
        A tuple of (x_values, y_values, z_values) where z_values may be None.

    Examples
    --------
    >>> x, y, z = extract_plottables_envelope(
    ...     subplot, data=[[1, 2], [3, 4]], x=[1, 2], y=[3, 4]
    ... )
    """
    # Step 1: Infer plot context and create data source
    context = PlotContext.CARTESIAN_2D  # Envelope plots are always cartesian

    # Support deprecated source_units parameter
    if source_units is not None and units is None:
        units = source_units

    source = get_source(
        data=data,
        x=x,
        y=y,
        z=z,
        context=context,
        units=units,  # Target units for unit conversion
        x_units=x_units,  # Target units for x coordinates
        y_units=y_units,  # Target units for y coordinates
        z_units=z_units,  # Target units for z coordinates
    )

    kwargs = {**subplot._plot_kwargs(source), **kwargs}

    # Step 2: Determine z values
    if (data is None and z is None) or (z is not None and not z):
        z_values = None
    elif source.z is not None:
        z_values = source.z.values
    else:
        z_values = None

    # Step 3: Extract x, y values
    x_values = source.x.values
    y_values = source.y.values

    # Step 4: Apply sampling if specified
    if every is not None:
        x_values = x_values[::every]
        y_values = y_values[::every]
        if z_values is not None:
            z_values = z_values[::every, ::every]

    # Step 5: Extract data within domain boundaries if requested
    if subplot.domain is not None and extract_domain:
        x_values, y_values, z_values = subplot.domain.extract(
            x_values,
            y_values,
            z_values,
            source_crs=source.crs,
        )

    return x_values, y_values, z_values


# =============================================================================
# Style and Data Processing Utilities
# =============================================================================


def configure_style(
    method_name: str,
    style: Style | str | None,
    source: Any,
    units: str | None,
    auto_style: bool,
    kwargs: dict[str, Any],
) -> Style:
    """
    Configure the plotting style based on method name and data characteristics.

    This function determines the appropriate style class and creates a style
    instance with the given parameters. It handles automatic style selection
    and parameter extraction from kwargs.

    If a style is provided along with additional style-related kwargs, the kwargs
    will override the corresponding attributes in the style without modifying the
    original style object.

    Parameters
    ----------
    method_name : str
        The name of the plotting method.
    style : Style, str, or None
        An existing style object, or None to create a new one. If the string
        ``"auto"``, automatic style detection will be used. Any other string is
        treated as a named style and looked up via :func:`earthkit.plots.styles.load_style`.
        If a Style object is provided along with additional style kwargs, a copy
        with overrides will be created.
    source : Any
        The data source object.
    units : str or None
        Units for the data values.
    auto_style : bool
        Whether to automatically guess the appropriate style.
    kwargs : dict
        Keyword arguments that may contain style parameters. Style parameters will
        override attributes in the provided style without modifying the original.

    Returns
    -------
    Style
        A configured style object.

    Examples
    --------
    >>> style = configure_style("contour", None, source, "K", False, {})
    >>> # Override levels in existing style
    >>> style_with_overrides = configure_style(
    ...     "contour", my_style, source, None, False, {"levels": [0, 10, 20]}
    ... )
    """
    # Handle style="auto" as an alternative to auto_style=True
    # Named-style strings are already resolved to Style objects by
    # _prepare_style_and_units before this function is called.
    if style == "auto":
        auto_style = True
        style = None

    # Handle cmap as an alias for colors
    if "cmap" in kwargs and "colors" in kwargs:
        raise ValueError(
            "Cannot specify both 'cmap' and 'colors'. They are aliases for the same parameter."
        )
    if "cmap" in kwargs:
        kwargs["colors"] = kwargs.pop("cmap")

    # Extract style-specific keyword arguments
    style_kwargs = {k: kwargs.pop(k) for k in _STYLE_KWARGS if k in kwargs}

    # If a style is provided and we have style kwargs to override
    if style is not None and style_kwargs:
        # Create a copy with overrides without modifying the original
        return style.with_overrides(**style_kwargs)

    # If a style is provided without overrides, return it as-is
    if style is not None:
        return style

    # Determine the appropriate style class based on method name
    if method_name.startswith("contour"):
        style_class = Contour
    elif method_name in ["quiver", "barbs"]:
        style_class = Quiver
    else:
        style_class = Style

    # Some methods suppress the auto-legend by default; the user can still
    # override by passing legend_style= explicitly.
    _NO_DEFAULT_LEGEND = {"stripes"}
    if method_name in _NO_DEFAULT_LEGEND:
        style_kwargs.setdefault("legend_style", None)

    # Create the style instance
    if not auto_style:
        if style_kwargs or units:
            style = style_class(**{**style_kwargs, "units": units})
        elif style_class is not Style:
            style = style_class()
        else:
            style = DEFAULT_STYLE
    else:
        style = auto.guess_style(source, units=units or source.units)
        # Apply any style kwargs as overrides to the auto-detected style
        if style_kwargs and style is not None:
            style = style.with_overrides(**style_kwargs)

    return style


def apply_scale_factor(
    style: Style, source: Any, z: str | np.ndarray | list[float] | None
) -> np.ndarray | None:
    """
    Process z values by applying scale factors.

    Unit conversion is handled by the Source class when target units are passed
    to get_source(). This function only applies style-specific scale factors.

    Parameters
    ----------
    style : Style
        The style object containing scaling logic.
    source : Any
        The data source object (with units already converted).
    z : str, array-like, or None
        Z values or coordinate name. If None, uses source.z.values.

    Returns
    -------
    array-like or None
        Processed z values, or None if no data is available.

    Examples
    --------
    >>> z_processed = process_z_values(style, source, None)
    """
    if source._data is None and z is None:
        return None

    if source.z is None:
        return None

    z_values = source.z.values
    return style.apply_scale_factor(z_values)


def apply_sampling(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray | None,
    every: int | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Apply sampling to x, y, and z values if a sampling interval is specified.

    This function reduces the resolution of the data by taking every nth element,
    which can improve plotting performance for large datasets.

    Parameters
    ----------
    x_values, y_values : array-like
        X and Y coordinate arrays.
    z_values : array-like or None
        Z value array, or None if not applicable.
    every : int or None
        Sampling interval. If None, no sampling is applied.

    Returns
    -------
    tuple
        A tuple of (x_values, y_values, z_values) with sampling applied.

    Examples
    --------
    >>> x_sampled, y_sampled, z_sampled = apply_sampling(
    ...     [1, 2, 3, 4], [5, 6, 7, 8], [[1, 2], [3, 4]], 2
    ... )
    """
    if every is None:
        return x_values, y_values, z_values

    # Apply sampling to x and y values
    x_values = x_values[::every]
    y_values = y_values[::every]

    # Apply sampling to z values if they exist
    if z_values is not None:
        z_values = z_values[::every, ::every]

    return x_values, y_values, z_values


# =============================================================================
# Specialized Plotting Functions
# =============================================================================


def _handle_specialized_grids(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    method_name: str,
    kwargs: dict[str, Any],
    resample: Any = None,
) -> Any | None:
    """
    Handle plotting for specialized grid types like healpix and octahedral,
    and for regular rectilinear grids when the source CRS differs from the
    target map CRS.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    source : Any
        The data source object.
    z_values : array-like
        The z values to plot.
    style : Style
        The style object for plotting.
    method_name : str
        The name of the plotting method.
    kwargs : dict
        Keyword arguments for plotting.
    resample : Any, optional
        The resample argument from the calling method. When ``_USE_NN`` (the
        sentinel set by ``grid_cells``), the fast NN path is eligible. Any
        other value means the caller has its own resampling strategy, so the
        NN path is skipped.

    Returns
    -------
    Any or None
        The matplotlib mappable object if handled, None otherwise.
    """
    if method_name != "pcolormesh":
        return None

    gridspec = source.gridspec

    # Guard: pcolormesh cannot render HEALPix / reduced Gaussian data directly.
    # When the user passes a resample that will handle the structured grid
    # (Regrid, or a Chain whose first data step is Regrid), we let it through
    # to Step 6.5.  Otherwise raise a clear error rather than letting matplotlib
    # crash with a cryptic shape mismatch.
    if gridspec is not None and resample is not _USE_NN:
        from earthkit.plots.resample import Chain
        from earthkit.plots.resample import Regrid as _Regrid
        from earthkit.plots.resample import _is_structured_grid

        if _is_structured_grid(gridspec):
            # Check whether the supplied resample will handle the structured grid
            _has_regrid = isinstance(resample, _Regrid) or (
                isinstance(resample, Chain)
                and any(isinstance(s, _Regrid) for s in resample.data_steps)
            )
            if not _has_regrid:
                _grid_label = {
                    "healpix": "HEALPix",
                    "reduced_gg": "reduced Gaussian",
                }.get(gridspec.name, gridspec.name)
                raise ValueError(
                    f"Input data was identified as a {_grid_label} grid "
                    f"({gridspec.name!r}), which must be regridded onto a regular "
                    "lat/lon grid before it can be visualised with pcolormesh. "
                    "Pass resample=Regrid() (or a Chain that includes Regrid as its "
                    "first data step) to perform the regridding explicitly, or pass "
                    "resample='auto' to let earthkit-plots choose the best approach "
                    "automatically. For all available options see the "
                    "earthkit.plots.resample module documentation. "
                    "Alternatively, use grid_cells() for automatic cell rendering."
                )

    # Specialised grid backends (HEALPix, octahedral reduced Gaussian).
    # Only activated when the caller is grid_cells (_USE_NN sentinel).
    # When the user supplied their own resample (e.g. Regrid(5)), Step 6.5
    # handles it instead.
    if resample is _USE_NN and gridspec is not None:
        grid_handlers = {
            "healpix": plot_healpix,
            "reduced_gg": plot_octahedral,
        }
        handler = grid_handlers.get(gridspec.name)
        if handler is not None:
            return handler(subplot, source, z_values, style, kwargs)

    # Fast NN pixel-sampling for regular (non-structured) grids with a CRS
    # mismatch.  Only applies when the _USE_NN sentinel is present (grid_cells).
    if resample is _USE_NN:
        return _handle_regular_grid_nn(subplot, source, z_values, style, kwargs)

    return None


def _handle_regular_grid_nn(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    kwargs: dict[str, Any],
) -> Any | None:
    """
    Fast nearest-neighbour pixel-sampling for regular rectilinear grids when
    the source CRS differs from the target (map) CRS.

    For each output pixel the centre is back-transformed to the source CRS and
    the nearest source cell is found by :func:`numpy.searchsorted` on the 1-D
    source axes — no interpolation, O(nx×ny), crisp cell boundaries.

    Returns a mappable if the fast path was taken, ``None`` otherwise (causing
    the caller to fall through to plain pcolormesh rendering).
    """
    if not hasattr(subplot, "crs") or subplot.crs is None:
        return None

    target_crs = subplot.crs
    data_crs = source.crs or kwargs.get("transform") or ccrs.PlateCarree()

    # Only activate on a genuine CRS mismatch
    if type(data_crs).__name__ == type(target_crs).__name__:
        return None

    # Only applies to regular rectilinear (meshgrid) sources
    x_values = source.x.values
    y_values = source.y.values
    if x_values.ndim != 2 or y_values.ndim != 2:
        return None
    if not (
        np.allclose(x_values, x_values[0, :])
        and np.allclose(y_values.T, y_values[:, 0])
    ):
        return None

    # Extract 1-D axes from the meshgrid
    x_src_1d = x_values[0, :]
    y_src_1d = y_values[:, 0]

    try:
        bbox_target = subplot.ax.get_extent(crs=target_crs)
    except AttributeError:
        if subplot.domain is not None:
            bbox_target = subplot.domain.bbox.to_cartopy_bounds()
        else:
            bbox_target = (-180, 180, -90, 90)

    from earthkit.plots.resample.reproject import _reproject_nn

    image, extent = _reproject_nn(
        x_src_1d,
        y_src_1d,
        z_values,
        crs_src=data_crs,
        bbox_target=bbox_target,
        crs_target=target_crs,
    )

    plot_kwargs = dict(kwargs)
    if style is not None:
        plot_kwargs.update(style.to_pcolormesh_kwargs(image))
    plot_kwargs.pop("transform", None)
    plot_kwargs.pop("transform_first", None)

    return subplot.ax.imshow(image, extent=extent, origin="lower", **plot_kwargs)


def plot_healpix(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    kwargs: dict[str, Any],
) -> Any:
    """
    Handle plotting for HEALPix grid data.

    HEALPix (Hierarchical Equal Area isoLatitude Pixelization) grids require
    special handling due to their unique coordinate system and pixel structure.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    source : Any
        The data source object.
    z_values : array-like
        The z values to plot.
    style : Style
        The style object for plotting.
    kwargs : dict
        Keyword arguments for plotting.

    Returns
    -------
    Any
        The matplotlib mappable object.

    Examples
    --------
    >>> mappable = plot_healpix(subplot, source, z_values, style, {})
    """
    from earthkit.plots.resample import healpix

    # Determine if the grid uses nested ordering
    nest = source.metadata("orderingConvention", default=None) == "nested"

    # Set the coordinate transformation
    kwargs["transform"] = subplot.crs

    # Use the HEALPix-specific plotting function
    return healpix.nnshow(z_values, ax=subplot.ax, nest=nest, style=style, **kwargs)


def plot_octahedral(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    kwargs: dict[str, Any],
) -> Any:
    """
    Handle plotting for octahedral grid data.

    Octahedral grids are used for certain types of global atmospheric models
    and require specialized plotting functions.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    source : Any
        The data source object.
    z_values : array-like
        The z values to plot.
    style : Style
        The style object for plotting.
    kwargs : dict
        Keyword arguments for plotting.

    Returns
    -------
    Any
        The matplotlib mappable object.

    Examples
    --------
    >>> mappable = plot_octahedral(subplot, source, z_values, style, {})
    """
    from earthkit.plots.resample import octahedral

    return octahedral.nnshow(
        source.x.values,
        source.y.values,
        z_values,
        subplot.ax,
        style=style,
        **kwargs,
    )


def _handle_cyclic_points(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Handle cyclic point wrapping for contour plots.

    This function adds cyclic points to the data to ensure proper wrapping
    around the globe for longitude-based plots.

    Parameters
    ----------
    x_values, y_values, z_values : array-like
        The coordinate and value arrays.

    Returns
    -------
    tuple
        A tuple of (x_values, y_values, z_values) with cyclic points added.

    Examples
    --------
    >>> x_cyclic, y_cyclic, z_cyclic = _handle_cyclic_points(x, y, z)
    """
    if not needs_cyclic_point(x_values):
        return x_values, y_values, z_values

    # Handle 2D coordinate arrays
    n_x = None
    if len(x_values.shape) != 1:
        n_x = x_values.shape[0]
        x_values = x_values[0]

    # Add cyclic points
    z_values, x_values = add_cyclic_point(z_values, coord=x_values)

    # Restore 2D structure if needed
    if n_x:
        x_values = np.tile(x_values, (n_x, 1))
        y_values = np.hstack((y_values, y_values[:, -1][:, np.newaxis]))

    return x_values, y_values, z_values


def _handle_transform_settings(subplot: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Handle coordinate transformation settings for the plotting method.

    This function checks if the subplot's coordinate reference system
    supports transform-first operations and adjusts kwargs accordingly.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance.
    kwargs : dict
        Keyword arguments for plotting.

    Returns
    -------
    dict
        Modified keyword arguments with appropriate transform settings.

    Examples
    --------
    >>> kwargs = _handle_transform_settings(subplot, {"transform_first": True})
    """
    if "transform_first" in kwargs:
        if subplot.crs.__class__ in coordinate_reference_systems.CANNOT_TRANSFORM_FIRST:
            kwargs["transform_first"] = False

    return kwargs
