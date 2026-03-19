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

import numpy as np
from cartopy.util import add_cyclic_point

from earthkit.plots.geo import coordinate_reference_systems
from earthkit.plots.geo.grids import needs_cyclic_point
from earthkit.plots.identifiers import identify_primary
from earthkit.plots.resample import Interpolate
from earthkit.plots.sources import get_source
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.styles import _STYLE_KWARGS, Contour, Quiver, Style, auto


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
    is_1d = method_name in ("line", "scatter", "bar", "barh", "plot")

    # Check if this is a vector plot
    is_vector = method_name in ("quiver", "barbs")

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

    Returns the (possibly updated) units value.
    """
    if auto_style:
        warnings.warn(
            "The 'auto_style' parameter is deprecated and will be removed in a future version. "
            "Please use style='auto' instead.",
            DeprecationWarning,
            stacklevel=4,
        )

    if units is None and style is not None and style != "auto":
        if hasattr(style, "_units") and style._units is not None:
            units = style._units

    return units


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
    source_units: str | None = None,
    auto_style: bool = False,
    regrid: bool = False,
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
    regrid : bool, default=False
        Whether to enable regridding for the data source.
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
    units = _prepare_style_and_units(style, units, auto_style)

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
        regrid=regrid,
    )
    kwargs.update(subplot._plot_kwargs(source))

    # Step 2: Configure the plotting style
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Step 3: Process z values (convert units, apply scale factors)
    if z is not None or (source.z is not None and source.z.values is not None):
        z_values = apply_scale_factor(style, source, z)
    else:
        z_values = None

    # Step 4: Apply unit conversion to x and y values if needed
    x_values, y_values = _apply_coordinate_unit_conversion(source)

    # Step 5: Apply sampling if specified
    x_values, y_values, z_values = apply_sampling(x_values, y_values, z_values, every)

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
            for mappable in mappable:
                mappable.set_label(label)
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
    regrid: bool = False,
    metadata: dict[str, Any] | None = None,
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
    regrid : bool, default=False
        Whether to enable regridding for the data source.
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
    >>> mappable = extract_plottables_3D(
    ...     subplot, "pcolormesh", (), x=[1, 2, 3], y=[4, 5, 6], z=[[1, 2], [3, 4]]
    ... )
    """
    # Step 0: Handle deprecation and extract units from style
    units = _prepare_style_and_units(style, units, auto_style)

    # Step 1: Enable regridding for contour methods
    if method_name.startswith("contour"):
        regrid = True

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
        regrid=regrid,
    )
    kwargs.update(subplot._plot_kwargs(source))

    # Step 3: Configure the plotting style
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Step 4: Process z values (convert units, apply scale factors)
    z_values = apply_scale_factor(style, source, z)

    # Step 5: Handle specialized grid types (healpix, octahedral)
    mappable = _handle_specialized_grids(
        subplot, source, z_values, style, method_name, kwargs
    )

    if not mappable:
        # Step 6: Process x, y values and apply sampling
        # For 3D plots, use source coordinates directly (no coordinate unit conversion)
        x_values, y_values = source.x.values, source.y.values
        x_values, y_values, z_values = apply_sampling(
            x_values, y_values, z_values, every
        )

        # Step 7: Handle no-style case for z values
        if no_style and z_values is None:
            z_values = kwargs.pop("c", None)

        # Step 8: Extract data within domain boundaries if requested
        if subplot.domain and extract_domain and not no_style:
            x_values, y_values, z_values = subplot.domain.extract(
                x_values, y_values, z_values, source_crs=source.crs
            )

        # Step 9: Handle cyclic point wrapping for contour plots
        if method_name.startswith("contour"):
            x_values, y_values, z_values = _handle_cyclic_points(
                x_values, y_values, z_values
            )

        # Step 10: Handle coordinate transformation settings
        kwargs = _handle_transform_settings(subplot, kwargs)

        # Step 11: Create the plot with or without interpolation
        if not no_style:
            mappable = plot_with_interpolation(
                subplot,
                style,
                method_name,
                x_values,
                y_values,
                z_values,
                source.crs,
                kwargs,
            )
        else:
            warnings.warn("Style not set - using raw matplotlib method.")
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

    subplot.layers.append(
        Layer(
            source,
            mappable,
            subplot,
            style,
            primary_axis=primary_axis,
            axis_units=axis_units,
        )
    )
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
    units = _prepare_style_and_units(style, units, auto_style)

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

            # Extract u and v values from their respective z fields
            u_array = u_source.z.values if u_source.z else None
            v_array = v_source.z.values if v_source.z else None

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

        # Extract values - use z if available, otherwise y
        u_array = u_source.z.values if u_source.z else u_source.y.values
        v_array = v_source.z.values if v_source.z else v_source.y.values

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

    # Step 3: Configure the plotting style
    style = configure_style(
        method_name, style, source, units, auto_style, {**kwargs, "colors": colors}
    )

    # Step 4: Extract x, y coordinate values
    x_values = source.x.values
    y_values = source.y.values

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

    # Step 7: Use style's resample setting if not explicitly provided
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

    # Step 9: Apply resampling if specified
    if resample is not None:
        kwargs.pop("regrid_shape", None)
        if resample.__class__.__name__ == "Regrid":
            kwargs.pop("transform", None)
        args_resampled = resample.apply(
            x_values,
            y_values,
            u_values,
            v_values,
            source_crs=source.crs,
            target_crs=subplot.crs,
            extents=subplot.ax.get_extent(),
        )
        x_values, y_values, u_values, v_values = args_resampled

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
    style : Style or None
        An existing style object, or None to create a new one. If the string "auto",
        automatic style detection will be used. If a Style object is provided along
        with additional style kwargs, a copy with overrides will be created.
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

    # Create the style instance
    if not auto_style:
        style = style_class(**{**style_kwargs, "units": units})
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
) -> Any | None:
    """
    Handle plotting for specialized grid types like healpix and octahedral.

    This function checks if the data source has a specialized grid specification
    and delegates plotting to the appropriate handler.

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

    Returns
    -------
    Any or None
        The matplotlib mappable object if handled, None otherwise.
    """
    if method_name != "pcolormesh":
        return None

    gridspec = source.gridspec
    if gridspec is None:
        return None

    # Map grid types to their plotting functions
    grid_handlers = {
        "healpix": plot_healpix,
        "reduced_gg": plot_octahedral,
    }

    handler = grid_handlers.get(gridspec.name)
    if handler is not None:
        return handler(subplot, source, z_values, style, kwargs)

    return None


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
    from earthkit.plots.geo import healpix

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
    from earthkit.plots.geo import octahedral

    return octahedral.plot_octahedral_grid(
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


def plot_with_interpolation(
    subplot: Any,
    style: Style,
    method_name: str,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    source_crs: Any,
    kwargs: dict[str, Any],
) -> Any:
    """
    Attempt to plot with or without interpolation as needed.

    This function first tries to plot the raw data. If that fails, it
    automatically falls back to interpolation to create a structured grid.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    style : Style
        The style object for plotting.
    method_name : str
        The name of the plotting method.
    x_values, y_values, z_values : array-like
        The coordinate and value arrays.
    source_crs : Any
        The coordinate reference system of the source data.
    kwargs : dict
        Keyword arguments for plotting.

    Returns
    -------
    Any
        The matplotlib mappable object.

    Examples
    --------
    >>> mappable = plot_with_interpolation(
    ...     subplot, style, "pcolormesh", x, y, z, crs, {}
    ... )
    """
    # Try plotting without interpolation first
    if "interpolate" not in kwargs:
        try:
            return getattr(style, method_name)(
                subplot.ax, x_values, y_values, z_values, **kwargs
            )
        except (ValueError, TypeError):
            warnings.warn(
                f"{method_name} failed with raw data, attempting interpolation "
                f"to structured grid with default interpolation options."
            )

    # Handle interpolation parameters
    interpolate = kwargs.pop("interpolate", dict())
    if interpolate is True:
        interpolate = Interpolate()
    elif isinstance(interpolate, dict):
        interpolate = Interpolate(**interpolate)

    # Apply interpolation
    x_values, y_values, z_values = interpolate.apply(
        x_values,
        y_values,
        z_values,
        source_crs=source_crs,
        target_crs=subplot.crs,
    )

    # Handle transform settings after interpolation
    _ = kwargs.pop("transform_first", None)
    if interpolate.transform:
        _ = kwargs.pop("transform", None)

    # Plot the interpolated data
    return getattr(style, method_name)(
        subplot.ax, x_values, y_values, z_values, **kwargs
    )
