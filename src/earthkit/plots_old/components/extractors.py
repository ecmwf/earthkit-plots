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
from typing import Any, Optional, Union

import numpy as np
from cartopy.util import add_cyclic_point

from earthkit.plots.geo import coordinate_reference_systems
from earthkit.plots.geo.grids import needs_cyclic_point
from earthkit.plots.identifiers import identify_primary
from earthkit.plots.resample import Interpolate
from earthkit.plots.sources import get_source
from earthkit.plots.styles import _STYLE_KWARGS, Contour, Quiver, Style, auto


def extract_plottables_2D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: Optional[Union[str, np.ndarray, list[float]]] = None,
    y: Optional[Union[str, np.ndarray, list[float]]] = None,
    z: Optional[Union[str, np.ndarray, list[float]]] = None,
    style: Optional[Style] = None,
    no_style: bool = False,
    units: Optional[str] = None,
    xunits: Optional[str] = None,
    yunits: Optional[str] = None,
    every: Optional[int] = None,
    source_units: Optional[str] = None,
    auto_style: bool = False,
    regrid: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    label: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for 2D plotting methods.

    This function handles the complete data pipeline for 2D plots including:
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
    style : Style, optional
        The style object to use for plotting. If None, one will be created.
    no_style : bool, default=False
        Whether to skip style processing and use raw matplotlib methods.
    units : str, optional
        Units for the data values.
    every : int, optional
        Sampling interval for data reduction.
    source_units : str, optional
        Units of the source data.
    auto_style : bool, default=False
        Whether to automatically guess the appropriate style.
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
    # Step 1: Initialize the data source
    source = get_source(
        *args, x=x, y=y, z=z, units=source_units, metadata=metadata, regrid=regrid
    )
    kwargs.update(subplot._plot_kwargs(source))

    # Step 2: Configure the plotting style
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Step 3: Process z values (convert units, apply scale factors)
    if z is not None or source.z_values is not None:
        z_values = process_z_values(style, source, z)
    else:
        z_values = None

    # Step 4: Apply unit conversion to x and y values if needed
    x_values, y_values = _apply_coordinate_unit_conversion(
        source, units, xunits, yunits, x, y, method_name
    )

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
    primary_axis = _identify_primary_axis(source, source._x, source._y)

    # Store axis-specific units for formatter
    axis_units = {}
    if xunits is not None:
        axis_units["x"] = xunits
    if yunits is not None:
        axis_units["y"] = yunits
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


def _apply_coordinate_unit_conversion(source, units, xunits, yunits, x, y, method_name):
    """
    Apply unit conversion to x and y coordinate values if needed.

    This function applies unit conversion to coordinate axes based on explicit
    axis-specific units (xunits, yunits) or falls back to primary axis detection
    when only general units are specified.

    Parameters
    ----------
    source : Source
        The data source object.
    units : str or None
        The target units for conversion applied to primary data axis. If None, no conversion is applied.
    xunits : str or None
        The target units for x-axis conversion. Takes precedence over `units` for x-axis.
    yunits : str or None
        The target units for y-axis conversion. Takes precedence over `units` for y-axis.
    x, y : str, array-like, or None
        X and Y coordinate values or names.
    method_name : str
        The name of the plotting method being used.

    Returns
    -------
    tuple
        A tuple of (x_values, y_values) with unit conversion applied if needed.
    """
    import warnings

    from earthkit.plots.metadata import units as metadata_units

    x_values = source.x_values
    y_values = source.y_values

    # Determine target units for each axis
    target_x_units = xunits
    target_y_units = yunits

    # If axis-specific units not provided, use general units for primary axis only
    if target_x_units is None and target_y_units is None and units is not None:
        primary_axis = _identify_primary_axis(source, source._x, source._y)
        if primary_axis == "x":
            target_x_units = units
        elif primary_axis == "y":
            target_y_units = units

    # Apply x-axis unit conversion
    if target_x_units is not None:
        x_meta = getattr(source, "x_metadata", {})
        if "units" in x_meta and x_meta["units"] != target_x_units:
            try:
                x_values = metadata_units.convert(
                    x_values, x_meta["units"], target_x_units
                )
            except Exception as e:
                warnings.warn(f"Failed to convert x values to {target_x_units}: {e}")

    # Apply y-axis unit conversion
    if target_y_units is not None:
        y_meta = getattr(source, "y_metadata", {})
        if "units" in y_meta and y_meta["units"] != target_y_units:
            try:
                y_values = metadata_units.convert(
                    y_values, y_meta["units"], target_y_units
                )
            except Exception as e:
                warnings.warn(f"Failed to convert y values to {target_y_units}: {e}")

    return x_values, y_values


def extract_plottables_3D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: Optional[Union[str, np.ndarray, list[float]]] = None,
    y: Optional[Union[str, np.ndarray, list[float]]] = None,
    z: Optional[Union[str, np.ndarray, list[float]]] = None,
    style: Optional[Style] = None,
    no_style: bool = False,
    units: Optional[str] = None,
    xunits: Optional[str] = None,
    yunits: Optional[str] = None,
    every: Optional[int] = None,
    source_units: Optional[str] = None,
    extract_domain: bool = False,
    auto_style: bool = False,
    regrid: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for 3D plotting methods.

    This function handles the complete data pipeline for 3D plots including:
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
    style : Style, optional
        The style object to use for plotting. If None, one will be created.
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
        Whether to automatically guess the appropriate style.
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
    # Step 1: Enable regridding for contour methods
    if method_name.startswith("contour"):
        regrid = True

    # Step 2: Initialize the data source
    source = get_source(
        *args, x=x, y=y, z=z, units=source_units, metadata=metadata, regrid=regrid
    )
    kwargs.update(subplot._plot_kwargs(source))

    # Step 3: Configure the plotting style
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Step 4: Process z values (convert units, apply scale factors)
    z_values = process_z_values(style, source, z)

    # Step 5: Handle specialized grid types (healpix, octahedral)
    mappable = _handle_specialized_grids(
        subplot, source, z_values, style, method_name, kwargs
    )

    if not mappable:
        # Step 6: Process x, y values and apply sampling
        # For 3D plots, use source coordinates directly (no coordinate unit conversion)
        x_values, y_values = source.x_values, source.y_values
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
    if xunits is not None:
        axis_units["x"] = xunits
    if yunits is not None:
        axis_units["y"] = yunits
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


def extract_plottables_envelope(
    subplot: Any,
    data: Optional[Union[np.ndarray, list[float]]] = None,
    x: Optional[Union[str, np.ndarray, list[float]]] = None,
    y: Optional[Union[str, np.ndarray, list[float]]] = None,
    z: Optional[Union[str, np.ndarray, list[float]]] = None,
    every: Optional[int] = None,
    source_units: Optional[str] = None,
    extract_domain: bool = False,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
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
    source_units : str, optional
        Units of the source data.
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
    # Step 1: Create data source
    if source_units is not None:
        source = get_source(data=data, x=x, y=y, z=z, units=source_units)
    else:
        source = get_source(data=data, x=x, y=y, z=z)

    kwargs = {**subplot._plot_kwargs(source), **kwargs}

    # Step 2: Determine z values
    if (data is None and z is None) or (z is not None and not z):
        z_values = None
    else:
        z_values = source.z_values

    # Step 3: Extract x, y values
    x_values = source.x_values
    y_values = source.y_values

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
    style: Optional[Style],
    source: Any,
    units: Optional[str],
    auto_style: bool,
    kwargs: dict[str, Any],
) -> Style:
    """
    Configure the plotting style based on method name and data characteristics.

    This function determines the appropriate style class and creates a style
    instance with the given parameters. It handles automatic style selection
    and parameter extraction from kwargs.

    Parameters
    ----------
    method_name : str
        The name of the plotting method.
    style : Style or None
        An existing style object, or None to create a new one.
    source : Any
        The data source object.
    units : str or None
        Units for the data values.
    auto_style : bool
        Whether to automatically guess the appropriate style.
    kwargs : dict
        Keyword arguments that may contain style parameters.

    Returns
    -------
    Style
        A configured style object.

    Examples
    --------
    >>> style = configure_style("contour", None, source, "K", False, {})
    """
    if style is not None:
        return style

    # Extract style-specific keyword arguments
    style_kwargs = {k: kwargs.pop(k) for k in _STYLE_KWARGS if k in kwargs}

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

    return style


def process_z_values(
    style: Style, source: Any, z: Optional[Union[str, np.ndarray, list[float]]]
) -> Optional[np.ndarray]:
    """
    Process z values by converting units and applying scale factors.

    This function handles the conversion of z values from source units to
    target units and applies any scale factors defined in the style.

    Parameters
    ----------
    style : Style
        The style object containing unit conversion and scaling logic.
    source : Any
        The data source object.
    z : str, array-like, or None
        Z values or coordinate name. If None, uses source.z_values.

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

    # Convert units and apply scale factors
    z_values = style.convert_units(source.z_values, source.units)
    return style.apply_scale_factor(z_values)


def apply_sampling(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: Optional[np.ndarray],
    every: Optional[int],
) -> tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
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
) -> Optional[Any]:
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
        source.x_values,
        source.y_values,
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


# =============================================================================
# Backward Compatibility
# =============================================================================

# Alias for backward compatibility
extract_plottables = extract_plottables_3D
