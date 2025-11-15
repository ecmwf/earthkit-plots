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
from earthkit.plots.resample import Interpolate
from earthkit.plots.sources import get_dimension_set
from earthkit.plots.sources.core import DimensionSet, PlotType
from earthkit.plots.styles import _STYLE_KWARGS, Contour, Quiver, Style, auto


def extract_plottables_1d(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: Optional[Union[str, np.ndarray, list[float]]] = "auto",
    y: Optional[Union[str, np.ndarray, list[float]]] = "auto",
    z: Optional[Union[str, np.ndarray, list[float]]] = None,
    style: Optional[Style] = None,
    no_style: bool = False,
    units: Optional[str] = None,
    xunits: Optional[str] = None,
    yunits: Optional[str] = None,
    every: Optional[int] = None,
    auto_style: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    label: Optional[str] = None,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray, Optional[np.ndarray], dict]:
    """
    Extract and process data for 1D plotting methods (line plots, scatter).

    This function handles the complete data pipeline for 1D plots including:
    dimension extraction, style configuration, value processing, and sampling.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    method_name : str
        The name of the plotting method (e.g., 'plot', 'scatter').
    args : tuple
        Positional arguments passed to the plotting method.
    x, y : str, array-like, or "auto", optional
        Data coordinates. If strings, they are treated as coordinate names.
        If "auto" (default), coordinates are inferred from data.
    z : str, array-like, or None, optional
        Optional z values for colored scatter plots.
    style : Style, optional
        The style object to use for plotting. If None, one will be created.
    no_style : bool, default=False
        Whether to skip style processing and use raw matplotlib methods.
    units : str, optional
        Units for the data values (applies to primary dimension).
    xunits, yunits : str, optional
        Units for x and y coordinates specifically.
    every : int, optional
        Sampling interval for data reduction.
    auto_style : bool, default=False
        Whether to automatically guess the appropriate style.
    metadata : dict, optional
        Additional metadata for the dimension set.
    label : str, optional
        The label to use for the legend.
    **kwargs
        Additional keyword arguments passed to the plotting method.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, Optional[np.ndarray], dict]
        Tuple containing (x_values, y_values, z_values, plot_kwargs) where:
        - x_values: Processed x coordinate array
        - y_values: Processed y coordinate array
        - z_values: Processed z coordinate array (or None)
        - plot_kwargs: Dictionary of kwargs including style parameters and dimension_set

    Examples
    --------
    >>> x, y, z, kwargs = extract_plottables_1d(subplot, "plot", (), x=[1, 2, 3], y=[4, 5, 6])
    """
    # Step 1: Get plot type from subplot or infer
    plot_type = _infer_plot_type_from_subplot(subplot, is_1d=True)

    # Step 2: Create DimensionSet
    dimension_set = get_dimension_set(
        *args,
        x=x,
        y=y,
        z=z,
        plot_type=plot_type,
        crs=getattr(subplot, 'crs', None),
        metadata=metadata,
    )

    kwargs.update(subplot._plot_kwargs())

    # Step 3: Configure the plotting style
    style = _configure_style_from_dimension_set(
        method_name, style, dimension_set, units, auto_style, kwargs
    )

    # Step 4: Set target units on dimensions for automatic conversion
    if xunits is not None:
        dimension_set.x.set_target_units(xunits)
    if yunits is not None or units is not None:
        # For 1D plots, y is the primary data dimension
        target_units = yunits or units
        dimension_set.y.set_target_units(target_units)

    # Step 5: Extract values (with automatic unit conversion via .values property)
    x_values = dimension_set.x.values
    y_values = dimension_set.y.values
    z_values = dimension_set.z.values if dimension_set.z is not None else None

    # Handle z values if provided separately (for colored scatter plots)
    if z is not None and not isinstance(z, str):
        z_values = np.asarray(z)

    # Step 6: Apply sampling if specified
    x_values, y_values, z_values = apply_sampling(x_values, y_values, z_values, every)

    # Step 7: Handle no-style case for z values
    if no_style and z_values is None:
        z_values = kwargs.pop("c", None)

    # Step 8: Get matplotlib kwargs from style
    if not no_style and style is not None:
        # For 1D plots, we use y_values as the data for style processing
        style_kwargs = style.to_matplotlib_kwargs(y_values)
        kwargs = {**style_kwargs, **kwargs}

    # Step 9: Add metadata to kwargs for layer creation
    kwargs['_dimension_set'] = dimension_set
    kwargs['_style'] = style
    kwargs['_primary_axis'] = 'y'  # For 1D plots, y is the data axis
    kwargs['_units'] = units
    kwargs['_xunits'] = xunits
    kwargs['_yunits'] = yunits
    kwargs['_label'] = label

    return x_values, y_values, z_values, kwargs


# Alias for backward compatibility during transition
extract_plottables_2D = extract_plottables_1d


def _infer_plot_type_from_subplot(subplot: Any, is_1d: bool) -> PlotType:
    """
    Infer the plot type from the subplot characteristics.

    Parameters
    ----------
    subplot : Subplot
        The subplot to infer the plot type from.
    is_1d : bool
        Whether this is a 1D plot (True) or 2D plot (False).

    Returns
    -------
    PlotType
        The inferred plot type enum value.
    """
    # Check if subplot is a Map (geographic) by checking its class name
    # This avoids circular import issues
    is_geographic = subplot.__class__.__name__ == 'Map'

    if is_geographic:
        return PlotType.GEOGRAPHIC_1D if is_1d else PlotType.GEOGRAPHIC_2D
    else:
        return PlotType.CARTESIAN_1D if is_1d else PlotType.CARTESIAN_2D


def _configure_style_from_dimension_set(
    method_name: str,
    style: Optional[Style],
    dimension_set: DimensionSet,
    units: Optional[str],
    auto_style: bool,
    kwargs: dict[str, Any],
) -> Style:
    """
    Configure the plotting style based on method name and dimension set.

    This is the DimensionSet-aware version of configure_style().

    Parameters
    ----------
    method_name : str
        The name of the plotting method.
    style : Style or None
        An existing style object, or None to create a new one.
    dimension_set : DimensionSet
        The dimension set containing the data.
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

    # Get units from dimension set if not specified
    if units is None:
        units = dimension_set.primary_dimension.units

    # Create the style instance
    if not auto_style:
        style = style_class(**{**style_kwargs, "units": units})
    else:
        style = auto.guess_style(dimension_set, units=units)

    return style


def _is_specialized_grid(dimension_set: DimensionSet) -> bool:
    """
    Check if the dimension set represents a specialized grid type.

    Parameters
    ----------
    dimension_set : DimensionSet
        The dimension set to check.

    Returns
    -------
    bool
        True if the dimension set represents a specialized grid (healpix, octahedral), False otherwise.
    """
    grid_type = dimension_set.metadata("grid_type")
    return grid_type in ("healpix", "octahedral")


def _handle_specialized_grids_dimension_set(
    subplot: Any,
    dimension_set: DimensionSet,
    z_values: np.ndarray,
    style: Style,
    method_name: str,
    kwargs: dict[str, Any],
) -> Any:
    """
    Handle specialized grid types (healpix, octahedral) for DimensionSet.

    This is the DimensionSet-aware version of _handle_specialized_grids().

    Parameters
    ----------
    subplot : Subplot
        The subplot to plot on.
    dimension_set : DimensionSet
        The dimension set containing the data.
    z_values : np.ndarray
        The z values to plot.
    style : Style
        The plotting style.
    method_name : str
        The plotting method name.
    kwargs : dict
        Additional plotting kwargs.

    Returns
    -------
    Any
        The mappable object if specialized grid was handled, None otherwise.
    """
    # Check for specialized grid types in metadata
    grid_type = dimension_set.metadata("grid_type")

    if grid_type == "healpix":
        return plot_healpix(
            subplot, dimension_set, z_values, style, method_name, kwargs
        )
    elif grid_type == "octahedral":
        return plot_octahedral(
            subplot, dimension_set, z_values, style, method_name, kwargs
        )

    return None


def extract_plottables_2d(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: Optional[Union[str, np.ndarray, list[float]]] = "auto",
    y: Optional[Union[str, np.ndarray, list[float]]] = "auto",
    z: Optional[Union[str, np.ndarray, list[float]]] = "auto",
    style: Optional[Style] = None,
    no_style: bool = False,
    units: Optional[str] = None,
    xunits: Optional[str] = None,
    yunits: Optional[str] = None,
    every: Optional[int] = None,
    extract_domain: bool = False,
    auto_style: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """
    Extract and process data for 2D plotting methods (contour, pcolormesh).

    This function handles the complete data pipeline for 2D plots including:
    dimension extraction, style configuration, value processing, domain extraction,
    cyclic point handling, and specialized grid type plotting.

    Parameters
    ----------
    subplot : Subplot
        The subplot instance to plot on.
    method_name : str
        The name of the plotting method (e.g., 'contourf', 'pcolormesh').
    args : tuple
        Positional arguments passed to the plotting method.
    x, y, z : str, array-like, or "auto", optional
        Data coordinates. If strings, they are treated as coordinate names.
        If "auto" (default), coordinates are inferred from data.
    style : Style, optional
        The style object to use for plotting. If None, one will be created.
    no_style : bool, default=False
        Whether to skip style processing and use raw matplotlib methods.
    units : str, optional
        Units for the data values (applies to z dimension).
    xunits, yunits : str, optional
        Units for x and y coordinates specifically.
    every : int, optional
        Sampling interval for data reduction.
    extract_domain : bool, default=False
        Whether to extract data within the subplot's domain boundaries.
    auto_style : bool, default=False
        Whether to automatically guess the appropriate style.
    metadata : dict, optional
        Additional metadata for the dimension set.
    **kwargs
        Additional keyword arguments passed to the plotting method.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray, dict]
        Tuple containing (x_values, y_values, z_values, plot_kwargs) where:
        - x_values: Processed x coordinate array
        - y_values: Processed y coordinate array
        - z_values: Processed z coordinate array
        - plot_kwargs: Dictionary of kwargs including style parameters and dimension_set

    Examples
    --------
    >>> x, y, z, kwargs = extract_plottables_2d(
    ...     subplot, "pcolormesh", (), x=[1, 2, 3], y=[4, 5, 6], z=[[1, 2], [3, 4]]
    ... )
    """
    # Step 1: Get plot type from subplot
    plot_type = _infer_plot_type_from_subplot(subplot, is_1d=False)

    # Step 2: Create DimensionSet
    dimension_set = get_dimension_set(
        *args,
        x=x,
        y=y,
        z=z,
        plot_type=plot_type,
        crs=getattr(subplot, 'crs', None),
        metadata=metadata,
    )

    kwargs.update(subplot._plot_kwargs())

    # Step 3: Configure the plotting style
    style = _configure_style_from_dimension_set(
        method_name, style, dimension_set, units, auto_style, kwargs
    )

    # Step 4: Set target units on dimensions for automatic conversion
    if xunits is not None:
        dimension_set.x.set_target_units(xunits)
    if yunits is not None:
        dimension_set.y.set_target_units(yunits)
    if units is not None:
        # For 2D plots, z is the primary data dimension
        dimension_set.z.set_target_units(units)

    # Step 5: Extract values (with automatic unit conversion via .values property)
    x_values = dimension_set.x.values
    y_values = dimension_set.y.values
    z_values = dimension_set.z.values

    # Step 6: Check for specialized grid types (healpix, octahedral)
    # Mark if this is a specialized grid that will need special handling
    is_specialized = _is_specialized_grid(dimension_set)

    if not is_specialized:
        # Step 7: Apply sampling if specified
        x_values, y_values, z_values = apply_sampling(
            x_values, y_values, z_values, every
        )

        # Step 8: Handle no-style case for z values
        if no_style and z_values is None:
            z_values = kwargs.pop("c", None)

        # Step 9: Extract data within domain boundaries if requested
        if subplot.domain and extract_domain and not no_style:
            x_values, y_values, z_values = subplot.domain.extract(
                x_values, y_values, z_values, source_crs=getattr(subplot, 'crs', None)
            )

        # Step 10: Handle cyclic point wrapping for contour plots
        if method_name.startswith("contour"):
            x_values, y_values, z_values = _handle_cyclic_points(
                x_values, y_values, z_values
            )

        # Step 11: Handle coordinate transformation settings
        kwargs = _handle_transform_settings(subplot, kwargs)

    # Step 12: Get matplotlib kwargs from style
    if not no_style and style is not None:
        # For 2D plots, we use z_values as the data for style processing
        style_kwargs = style.to_matplotlib_kwargs(z_values)
        kwargs = {**style_kwargs, **kwargs}

    # Step 13: Add metadata to kwargs for layer creation
    kwargs['_dimension_set'] = dimension_set
    kwargs['_style'] = style
    kwargs['_primary_axis'] = 'z'  # For 2D plots, z is the data axis
    kwargs['_units'] = units
    kwargs['_xunits'] = xunits
    kwargs['_yunits'] = yunits
    kwargs['_is_specialized'] = is_specialized
    kwargs['_method_name'] = method_name
    kwargs['_no_style'] = no_style

    return x_values, y_values, z_values, kwargs


# Alias for backward compatibility during transition
extract_plottables_3D = extract_plottables_2d


# =============================================================================
# Helper Functions
# =============================================================================


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


def plot_healpix(
    subplot: Any,
    dimension_set: Union[Any, DimensionSet],
    z_values: np.ndarray,
    style: Style,
    method_name: str,
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
    dimension_set : DimensionSet or legacy source
        The dimension set or data source object.
    z_values : array-like
        The z values to plot.
    style : Style
        The style object for plotting.
    method_name : str
        The plotting method name (unused, for compatibility).
    kwargs : dict
        Keyword arguments for plotting.

    Returns
    -------
    Any
        The matplotlib mappable object.

    Examples
    --------
    >>> mappable = plot_healpix(subplot, dimension_set, z_values, style, "pcolormesh", {})
    """
    from earthkit.plots.geo import healpix

    # Determine if the grid uses nested ordering
    nest = dimension_set.metadata("orderingConvention") == "nested"

    # Set the coordinate transformation
    kwargs["transform"] = subplot.crs

    # Use the HEALPix-specific plotting function
    return healpix.nnshow(z_values, ax=subplot.ax, nest=nest, style=style, **kwargs)


def plot_octahedral(
    subplot: Any,
    dimension_set: Union[Any, DimensionSet],
    z_values: np.ndarray,
    style: Style,
    method_name: str,
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
    dimension_set : DimensionSet or legacy source
        The dimension set or data source object.
    z_values : array-like
        The z values to plot.
    style : Style
        The style object for plotting.
    method_name : str
        The plotting method name (unused, for compatibility).
    kwargs : dict
        Keyword arguments for plotting.

    Returns
    -------
    Any
        The matplotlib mappable object.

    Examples
    --------
    >>> mappable = plot_octahedral(subplot, dimension_set, z_values, style, "pcolormesh", {})
    """
    from earthkit.plots.geo import octahedral

    # Extract x and y values from dimension set
    if isinstance(dimension_set, DimensionSet):
        x_values = dimension_set.x.values
        y_values = dimension_set.y.values
    else:
        # Legacy source compatibility
        x_values = dimension_set.x_values
        y_values = dimension_set.y_values

    return octahedral.plot_octahedral_grid(
        x_values,
        y_values,
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
