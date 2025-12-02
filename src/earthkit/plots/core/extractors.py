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
import time
import logging
from typing import Any, Optional, Union

import numpy as np
from cartopy.util import add_cyclic_point

from earthkit.plots.geo import coordinate_reference_systems
from earthkit.plots.resample import Interpolate
from earthkit.plots.sources import get_dimension_set
from earthkit.plots.sources.core import DimensionSet, PlotType
from earthkit.plots.styles import Style, Contour

# Set up logger for performance tracking
logger = logging.getLogger(__name__)
ENABLE_TIMING = True  # Set to False to disable timing logs

# Cache expensive cartopy CRS objects to avoid repeated instantiation
# Creating CRS objects is VERY expensive (100-200ms each), so we cache them
_PLATECARREE_CACHE = None

def _get_platecarree():
    """Get cached PlateCarree CRS instance to avoid expensive re-creation."""
    global _PLATECARREE_CACHE
    if _PLATECARREE_CACHE is None:
        import cartopy.crs as ccrs
        _PLATECARREE_CACHE = ccrs.PlateCarree()
    return _PLATECARREE_CACHE


# Keys that should NOT be included in Style objects
# These are data/coordinate parameters or meta parameters
NON_STYLE_KEYS = {
    'data', 'x', 'y', 'z',           # Data/coordinate parameters
    'regrid', 'every', 'interpolate', # Data processing parameters
    'auto_style', 'no_style',         # Meta parameters
    'extract_domain',                 # Domain extraction parameter
    'label',                          # Legend parameter (not style-specific)
    'transform',                      # Cartopy CRS transform (plot-specific, not style)
    'missing_values',                 # Missing values parameter (earthkit-specific, not matplotlib)
    'metadata',                       # Metadata parameter (for dimension set, not style)
    'type',                           # Data type metadata (analysis/forecast, not matplotlib)
    'units', 'xunits', 'yunits',     # Units parameters (handled separately, not matplotlib kwargs)
}


def _ensure_style_from_kwargs(
    style: Optional[Style],
    kwargs: dict[str, Any],
) -> tuple[Optional[Style], dict[str, Any]]:
    """
    Ensure a Style object exists by creating or merging with kwargs as needed.

    This handles three cases:
    1. Style provided, no style kwargs: Return style as-is
    2. Style provided + style kwargs: Create new Style merging both
    3. No style, has style kwargs: Create new Style from kwargs

    Parameters
    ----------
    style : Style or None
        The existing style object (if any).
    kwargs : dict
        All keyword arguments passed to the plotting function.

    Returns
    -------
    tuple[Style or None, dict]
        A tuple of (style_object, remaining_kwargs).
        The style_object may be None if no style could be created.
        remaining_kwargs contains only non-style parameters.
    """
    # Separate style-relevant kwargs from others
    style_kwargs = {}
    remaining_kwargs = {}

    for key, value in kwargs.items():
        if key in NON_STYLE_KEYS:
            remaining_kwargs[key] = value
        else:
            style_kwargs[key] = value

    # Map common aliases
    if 'cmap' in style_kwargs:
        style_kwargs['colors'] = style_kwargs.pop('cmap')

    # Case 1: Style with no extra style kwargs - return as-is
    if style is not None and not style_kwargs:
        return style, remaining_kwargs

    # Case 2: Style + kwargs - create new merged style
    if style is not None and style_kwargs:
        # Start with existing style's parameters
        merged_params = {
            'colors': style_kwargs.pop('colors', style._colors),
            'levels': style_kwargs.pop('levels', style._levels),
            'units': style_kwargs.pop('units', style._units),
            'units_label': style_kwargs.pop('units_label', style._units_label),
            'scale_factor': style_kwargs.pop('scale_factor', style.scale_factor),
            'normalize': style_kwargs.pop('normalize', style._normalize),
            'anomaly': style_kwargs.pop('anomaly', style.anomaly),
            'legend_type': style_kwargs.pop('legend_type', style.legend_type),
            'plot_type': style_kwargs.pop('plot_type', style.plot_type),
        }
        # Merge remaining style kwargs with existing style's kwargs
        merged_kwargs = {**style._kwargs, **style_kwargs}

        new_style = Style(**merged_params, **merged_kwargs)
        return new_style, remaining_kwargs

    # Case 3: No style, but has style kwargs - create new style
    if style is None and style_kwargs:
        new_style = Style(**style_kwargs)
        return new_style, remaining_kwargs

    # Case 4: No style, no style kwargs - return None
    return None, remaining_kwargs


def extract_plottables_1d(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: Optional[Union[str, np.ndarray, list[float]]] = "auto",
    y: Optional[Union[str, np.ndarray, list[float]]] = "auto",
    z: Optional[Union[str, np.ndarray, list[float]]] = None,
    style: Optional[Union[str, Style]] = None,
    no_style: bool = False,
    units: Optional[str] = None,
    xunits: Optional[str] = None,
    yunits: Optional[str] = None,
    every: Optional[int] = None,
    auto_style: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    label: Optional[str] = None,
    regrid: str = "auto",
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
    style : str, Style, or None, optional
        The style to use for plotting. Can be:
        - A Style object
        - "auto" to automatically match style based on data metadata
        - A style name string (e.g., "MEAN_SEA_LEVEL_PRESSURE_IN_HPA")
        - None (one will be created from kwargs if needed)
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
    # For geographic plots, let the extractor determine the data's native CRS
    # (we'll use the subplot's CRS as the target projection, but need data's CRS for transform)
    dimension_set = get_dimension_set(
        *args,
        x=x,
        y=y,
        z=z,
        plot_type=plot_type,
        crs="auto",  # Let extractor determine data's CRS
        metadata=metadata,
        regrid=regrid,
    )

    # Step 2.5: Allow subplot to react to first data being plotted (e.g., infer CRS for maps)
    if hasattr(subplot, '_on_first_data_plot'):
        subplot._on_first_data_plot(dimension_set)

    kwargs.update(subplot._plot_kwargs())

    # Step 2.6: For geographic plots, set transform to data's CRS
    if plot_type in {PlotType.GEOGRAPHIC_1D, PlotType.GEOGRAPHIC_2D}:
        # Use the data's CRS for the transform (tells cartopy what CRS the data is in)
        import cartopy.crs as ccrs
        data_crs = dimension_set.crs if (dimension_set.crs is not None and dimension_set.crs != "auto") else ccrs.PlateCarree()
        kwargs['transform'] = data_crs

    # Step 2.7: Resolve string styles to Style objects
    from earthkit.plots.styles.utils import resolve_style
    # Pass dimension_set if auto_style is True OR if style is "auto"
    need_data_for_matching = auto_style or (isinstance(style, str) and style == "auto")
    style = resolve_style(style, data=dimension_set if need_data_for_matching else None, auto_style=auto_style, units=units)

    # Step 2.8: Ensure we have a Style object (create from kwargs if needed)
    style, kwargs = _ensure_style_from_kwargs(style, kwargs)

    # Step 3: Configure the plotting style
    style = _configure_style_from_dimension_set(
        method_name, style, dimension_set, units, auto_style, kwargs
    )

    # Step 4: Set target units and scale factor on dimensions for automatic conversion
    # Priority: explicit parameter > style units/scale_factor > no conversion
    target_units = units
    target_xunits = xunits
    target_yunits = yunits
    scale_factor = None

    if style is not None:
        if target_units is None and hasattr(style, '_units'):
            target_units = style._units
        if hasattr(style, 'scale_factor') and style.scale_factor is not None:
            scale_factor = style.scale_factor
        # Note: Style doesn't currently have xunits/yunits, but we keep this for future compatibility
        # if target_xunits is None and hasattr(style, '_xunits'):
        #     target_xunits = style._xunits
        # if target_yunits is None and hasattr(style, '_yunits'):
        #     target_yunits = style._yunits

    if target_xunits is not None:
        dimension_set.x.set_target_units(target_xunits)
    if target_yunits is not None or target_units is not None:
        # For 1D plots, y is the primary data dimension
        # Priority: yunits > units > style units
        y_target_units = target_yunits or target_units
        dimension_set.y.set_target_units(y_target_units)

    # Apply scale factor to y dimension (primary data dimension for 1D plots)
    if scale_factor is not None:
        dimension_set.y.set_scale_factor(scale_factor)

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
        try:
            style_kwargs = getattr(style, f"to_{method_name}_kwargs")(y_values)
        except Exception:
            style_kwargs = style.to_matplotlib_kwargs(y_values)
        kwargs = {**style_kwargs, **kwargs}

    # Step 8.5: Remove earthkit-specific parameters that shouldn't reach matplotlib
    # These were already filtered from Style but may still be in remaining kwargs
    kwargs.pop('missing_values', None)

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
    from earthkit.plots.core.maps import Map
    # Check if subplot is a Map or Map subclass (geographic)
    # This works for Map and any Map subclasses (like Tile)
    is_geographic = isinstance(subplot, Map)

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
    # If a style is provided, use it
    if style is not None:
        return style

    # For 1D plots without explicit style, create a default Style object
    # so that legend() can work properly
    if dimension_set.plot_context and dimension_set.plot_context.is_1d:
        from earthkit.plots.styles import Style
        return Style()

    # For 2D plots, return None and let matplotlib use its defaults
    # In the future, auto_style could be implemented here to create smart defaults
    return None


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
    grid_type = dimension_set._extractor.extract_grid(dimension_set._original_data)
    return grid_type is not None


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

    This function identifies specialized grid types and delegates plotting
    to the appropriate GridIdentifier.grid_cells() method.

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
    # Try to get the GridIdentifier from the extractor
    if dimension_set._extractor and dimension_set._original_data is not None:
        grid_identifier = dimension_set._extractor.extract_grid(dimension_set._original_data)

        if grid_identifier is not None and hasattr(grid_identifier, 'grid_cells'):
            # Delegate to the GridIdentifier's grid_cells method
            return grid_identifier.grid_cells(
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
    style: Optional[Union[str, Style]] = None,
    no_style: bool = False,
    units: Optional[str] = None,
    xunits: Optional[str] = None,
    yunits: Optional[str] = None,
    every: Optional[int] = None,
    extract_domain: bool = False,
    auto_style: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    label: Optional[str] = None,
    regrid: str = "auto",
    reproject_to_target: bool = True,
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
        The name of the plotting method (e.g., 'contourf', 'pcolormesh', 'grid_cells').
    args : tuple
        Positional arguments passed to the plotting method.
    x, y, z : str, array-like, or "auto", optional
        Data coordinates. If strings, they are treated as coordinate names.
        If "auto" (default), coordinates are inferred from data.
    style : str, Style, or None, optional
        The style to use for plotting. Can be:
        - A Style object
        - "auto" to automatically match style based on data metadata
        - A style name string (e.g., "MEAN_SEA_LEVEL_PRESSURE_IN_HPA")
        - None (one will be created from kwargs if needed)
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
    label : str, optional
        The label to use for the legend.
    regrid : str, optional
        Regridding parameter. For grid_cells method, this should not be used.
    reproject_to_target : bool, default=True
        Whether to reproject data to the target map CRS when there is a CRS mismatch.
        If True (default), data will be reprojected using reproject_to_grid instead of
        relying on cartopy's transform argument. This only applies to contour/contourf
        methods on geographic plots. Set to False to use cartopy's transform (old behavior).
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
    t_start = time.time() if ENABLE_TIMING else None

    # Step 1: Get plot type from subplot
    t0 = time.time() if ENABLE_TIMING else None
    plot_type = _infer_plot_type_from_subplot(subplot, is_1d=False)
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 1 - Infer plot type: {(time.time() - t0)*1000:.2f}ms")

    # Step 2: Create DimensionSet
    # For geographic plots, let the extractor determine the data's native CRS
    # (we'll use the subplot's CRS as the target projection, but need data's CRS for transform)
    # For grid_cells, disable regridding to preserve native grid cells
    t0 = time.time() if ENABLE_TIMING else None
    effective_regrid = False if method_name == "grid_cells" else regrid

    dimension_set = get_dimension_set(
        *args,
        x=x,
        y=y,
        z=z,
        plot_type=plot_type,
        crs="auto",  # Let extractor determine data's CRS
        metadata=metadata,
        regrid=effective_regrid,
    )
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 2 - Create DimensionSet: {(time.time() - t0)*1000:.2f}ms")

    # Step 2.5: Allow subplot to react to first data being plotted (e.g., infer CRS for maps)
    t0 = time.time() if ENABLE_TIMING else None
    if hasattr(subplot, '_on_first_data_plot'):
        subplot._on_first_data_plot(dimension_set)

    kwargs.update(subplot._plot_kwargs())
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 2.5 - First data plot hook: {(time.time() - t0)*1000:.2f}ms")

    # Step 2.6: For geographic plots, set transform to data's CRS
    # IMPORTANT: Cache dimension_set.crs early to avoid multiple accesses (each is expensive!)
    # OPTIMIZATION: If user explicitly passes 'transform' kwarg, use that and skip expensive CRS resolution
    t0 = time.time() if ENABLE_TIMING else None
    # Cache the raw CRS value from dimension_set (used later in Step 6.5)
    cached_data_crs_raw = None
    user_provided_transform = 'transform' in kwargs  # Check if user explicitly provided transform
    tile_matplotlib_only = kwargs.pop('_tile_matplotlib_only', False)  # Check if Tile wants matplotlib-only

    if plot_type in {PlotType.GEOGRAPHIC_1D, PlotType.GEOGRAPHIC_2D}:
        if user_provided_transform:
            # User explicitly provided transform - use it as the data's CRS
            # This skips expensive dimension_set.crs access (saves 100-200ms!)
            t1 = time.time() if ENABLE_TIMING else None
            cached_data_crs_raw = kwargs['transform']
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] Step 2.6 - Using user-provided transform (FAST PATH): {(time.time() - t1)*1000:.2f}ms")

            # For Tile matplotlib-only mode, convert transform to _source_crs
            if tile_matplotlib_only:
                kwargs['_source_crs'] = kwargs.pop('transform')
        else:
            # No user-provided transform - need to determine data's CRS
            t1 = time.time() if ENABLE_TIMING else None
            cached_data_crs_raw = dimension_set.crs  # Cache this - it's expensive to access!
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] Step 2.6a - Access dimension_set.crs: {(time.time() - t1)*1000:.2f}ms")

            t1 = time.time() if ENABLE_TIMING else None
            # Use cached PlateCarree to avoid expensive CRS creation (saves 100ms!)
            data_crs = cached_data_crs_raw if (cached_data_crs_raw is not None and cached_data_crs_raw != "auto") else _get_platecarree()
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] Step 2.6b - Resolve data CRS: {(time.time() - t1)*1000:.2f}ms")

            # For Tile matplotlib-only mode, store the source CRS but don't set transform yet
            # The Tile will handle transformation itself
            if not tile_matplotlib_only:
                kwargs['transform'] = data_crs
            else:
                # Store source CRS for later transformation by Tile
                kwargs['_source_crs'] = data_crs
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 2.6 - Set transform CRS: {(time.time() - t0)*1000:.2f}ms")

    # Step 2.7: Resolve string styles to Style objects
    t0 = time.time() if ENABLE_TIMING else None
    from earthkit.plots.styles.utils import resolve_style
    # Pass dimension_set if auto_style is True OR if style is "auto"
    need_data_for_matching = auto_style or (isinstance(style, str) and style == "auto")
    style = resolve_style(style, data=dimension_set if need_data_for_matching else None, auto_style=auto_style, units=units)
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 2.7 - Resolve style: {(time.time() - t0)*1000:.2f}ms")

    # Step 2.8: Ensure we have a Style object (create from kwargs if needed)
    t0 = time.time() if ENABLE_TIMING else None
    style, kwargs = _ensure_style_from_kwargs(style, kwargs)
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 2.8 - Ensure style from kwargs: {(time.time() - t0)*1000:.2f}ms")

    # Step 2.9: Special handling for grid_cells method
    # Try to identify specialized grids and get their grid_cells method
    grid_cells_callable = None
    effective_method_name = method_name

    if method_name == "grid_cells":
        # Try to get the GridIdentifier from the extractor
        if dimension_set._extractor and dimension_set._original_data is not None:
            grid_identifier = dimension_set._extractor.extract_grid(dimension_set._original_data)

            if grid_identifier is not None and hasattr(grid_identifier, 'grid_cells'):
                # Found a specialized grid with grid_cells method
                grid_cells_callable = grid_identifier.grid_cells

        # Fall back to pcolormesh for the extraction process
        # (we'll use grid_cells_callable later if it exists)
        effective_method_name = "pcolormesh"

    # Step 3: Configure the plotting style
    t0 = time.time() if ENABLE_TIMING else None
    style = _configure_style_from_dimension_set(
        effective_method_name, style, dimension_set, units, auto_style, kwargs
    )
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 3 - Configure style: {(time.time() - t0)*1000:.2f}ms")

    # Step 4: Set target units and scale factor on dimensions for automatic conversion
    t0 = time.time() if ENABLE_TIMING else None
    # Priority: explicit parameter > style units/scale_factor > no conversion
    target_units = units
    target_xunits = xunits
    target_yunits = yunits
    scale_factor = None

    if style is not None:
        if target_units is None and hasattr(style, '_units'):
            target_units = style._units
        if hasattr(style, 'scale_factor') and style.scale_factor is not None:
            scale_factor = style.scale_factor
        # Note: Style doesn't currently have xunits/yunits, but we keep this for future compatibility
        # if target_xunits is None and hasattr(style, '_xunits'):
        #     target_xunits = style._xunits
        # if target_yunits is None and hasattr(style, '_yunits'):
        #     target_yunits = style._yunits

    if target_xunits is not None:
        dimension_set.x.set_target_units(target_xunits)
    if target_yunits is not None:
        dimension_set.y.set_target_units(target_yunits)
    if target_units is not None:
        # For 2D plots, z is the primary data dimension
        dimension_set.z.set_target_units(target_units)

    # Apply scale factor to z dimension (primary data dimension for 2D plots)
    if scale_factor is not None:
        dimension_set.z.set_scale_factor(scale_factor)
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 4 - Set target units/scale: {(time.time() - t0)*1000:.2f}ms")

    # Step 5: Extract values (with automatic unit conversion via .values property)
    t0 = time.time() if ENABLE_TIMING else None
    x_values = dimension_set.x.values
    y_values = dimension_set.y.values
    z_values = dimension_set.z.values
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 5 - Extract values: {(time.time() - t0)*1000:.2f}ms (shapes: x={x_values.shape}, y={y_values.shape}, z={z_values.shape})")

    # Step 5.5: Handle multi-wrap longitude for cylindrical projections
    # If the domain extends beyond 360° longitude, tile the data horizontally
    t0 = time.time() if ENABLE_TIMING else None
    multi_wrap_applied = False  # Track if we applied multi-wrap tiling

    if (plot_type in {PlotType.GEOGRAPHIC_2D} and
        hasattr(subplot, 'domain') and subplot.domain is not None and
        hasattr(subplot, 'crs')):

        from earthkit.plots.geo.coordinate_reference_systems import is_cylindrical

        if is_cylindrical(subplot.crs):
            # Get domain bounds
            domain_bounds = subplot.domain.bbox.to_cartopy_bounds()
            lon_min, lon_max = domain_bounds[0], domain_bounds[1]
            lon_extent = lon_max - lon_min

            # Check if we need multi-wrap (extent >= 360°)
            # Even a single wrap (e.g., -360 to 0 vs 0 to 360) needs handling
            if lon_extent >= 360:
                # Only wrap if data looks global (covers most/all of 360°)
                # Check the span of x_values
                x_min = float(x_values.min())
                x_max = float(x_values.max())
                x_span = x_max - x_min

                # Data should span at least 300° to be considered wrappable
                # (allows for some regional data that shouldn't be wrapped)
                if x_span >= 300:
                    import numpy as np

                    if ENABLE_TIMING:
                        logger.info(f"  [TIMING] Step 5.5 - Multi-wrap detected: domain=[{lon_min}, {lon_max}] ({lon_extent:.1f}°), data x=[{x_min:.1f}, {x_max:.1f}] ({x_span:.1f}°)")

                    # Calculate which 360° tiles we need to cover the domain
                    # The key insight: we need to place copies of the data at different
                    # longitude offsets so that the domain is filled

                    # Determine how many complete 360° wraps are needed
                    num_complete_wraps = int(np.ceil(lon_extent / 360))

                    # Generate offsets that will cover the domain
                    # Start from the leftmost position that makes sense for the data
                    # Find which multiple of 360 to start from
                    start_offset = int(np.floor(lon_min / 360)) * 360

                    offsets = []
                    for i in range(num_complete_wraps + 1):  # +1 to ensure full coverage
                        offset = start_offset + (i * 360)
                        # Check if this offset would place data within the domain
                        offset_x_min = x_min + offset
                        offset_x_max = x_max + offset

                        # Include this tile if it overlaps with the domain
                        if offset_x_max >= lon_min and offset_x_min <= lon_max:
                            offsets.append(offset)

                    if len(offsets) >= 1:  # Proceed with tiling
                        multi_wrap_applied = True  # Mark that we're doing multi-wrap

                        if ENABLE_TIMING or True:  # Always log for now to help debug
                            logger.info(f"  [TIMING] Step 5.5 - BEFORE tiling: x.shape={x_values.shape} ({x_values.min():.1f} to {x_values.max():.1f}), y.shape={y_values.shape}, z.shape={z_values.shape}")
                            logger.info(f"  [TIMING] Step 5.5 - Will create {len(offsets)} tiles with offsets={offsets}")

                        # Tile the data
                        # For 1D coordinates (x, y separate), tile appropriately
                        if x_values.ndim == 1:
                            # Create repeated x coordinates with offsets
                            x_tiles = [x_values + offset for offset in offsets]
                            x_values = np.concatenate(x_tiles)

                            # Tile z_values horizontally (along last dimension)
                            # z_values is typically (lat, lon), so tile along axis 1 (lon)
                            z_values = np.tile(z_values, (1, len(offsets)))

                            # y_values stays the same (no tiling in latitude)
                            # But if it's 2D (meshgrid), tile it to match
                            if y_values.ndim == 2:
                                y_values = np.tile(y_values, (1, len(offsets)))

                        elif x_values.ndim == 2:
                            # 2D coordinates (meshgrid format)
                            # Tile x horizontally with offsets
                            x_tiles = [x_values + offset for offset in offsets]
                            x_values = np.concatenate(x_tiles, axis=1)

                            # Tile y and z horizontally (no offset for y)
                            y_values = np.tile(y_values, (1, len(offsets)))
                            z_values = np.tile(z_values, (1, len(offsets)))

                        if ENABLE_TIMING or True:  # Always log for now
                            logger.info(f"  [TIMING] Step 5.5 - AFTER tiling: x.shape={x_values.shape} ({x_values.min():.1f} to {x_values.max():.1f}), y.shape={y_values.shape}, z.shape={z_values.shape}")
                            logger.info(f"  [TIMING] Step 5.5 - Tiled data {len(offsets)}x, new shapes: x={x_values.shape}, y={y_values.shape}, z={z_values.shape}")

    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 5.5 - Multi-wrap handling: {(time.time() - t0)*1000:.2f}ms")

    # Step 6: Check for specialized grid types (healpix, octahedral)
    # Mark if this is a specialized grid that will need special handling
    is_specialized = _is_specialized_grid(dimension_set)

    # For scatter, we always need standard processing (no specialized grid rendering)
    # (scatter doesn't use the specialized grid rendering paths)
    do_standard_processing = not is_specialized or method_name == 'scatter'

    # Step 6.5: Determine if reprojection will be done
    # We need to know this early so we can skip domain extraction and cyclic points
    t0 = time.time() if ENABLE_TIMING else None
    will_reproject = False
    target_crs = None  # Cache target CRS for later use

    if (
        reproject_to_target
        and method_name in ('contour', 'contourf')
        and plot_type in {PlotType.GEOGRAPHIC_1D, PlotType.GEOGRAPHIC_2D}
        and hasattr(subplot, 'crs')
    ):
        t_crs_access = time.time() if ENABLE_TIMING else None
        target_crs = subplot.crs  # This might trigger expensive CRS/axes initialization
        if ENABLE_TIMING:
            logger.info(f"  [TIMING] Step 6.5a - Access subplot.crs: {(time.time() - t_crs_access)*1000:.2f}ms")

        if target_crs is not None and cached_data_crs_raw is not None:
            # Check if CRS mismatch exists
            t_crs_check = time.time() if ENABLE_TIMING else None

            # FAST PATH: If user provided transform, we already have the data CRS
            # This skips expensive "auto" resolution
            data_crs = cached_data_crs_raw

            # Handle "auto" data CRS (use cached PlateCarree)
            if data_crs == "auto":
                data_crs = _get_platecarree()

            # OPTIMIZATION: Quick type name comparison instead of expensive CRS equality checks
            # Compare CRS: they're different if they're not the same class
            if type(data_crs).__name__ != type(target_crs).__name__:
                will_reproject = True
                if ENABLE_TIMING:
                    logger.info(f"  [TIMING] Step 6.5b - CRS mismatch detected: {type(data_crs).__name__} → {type(target_crs).__name__}: {(time.time() - t_crs_check)*1000:.2f}ms")
            elif ENABLE_TIMING:
                logger.info(f"  [TIMING] Step 6.5b - CRS match (no reprojection): {type(data_crs).__name__}: {(time.time() - t_crs_check)*1000:.2f}ms")
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 6.5 - Check reprojection needed: {(time.time() - t0)*1000:.2f}ms (will_reproject={will_reproject})")

    if do_standard_processing:
        # Step 7: Apply sampling if specified
        t0 = time.time() if ENABLE_TIMING else None
        x_values, y_values, z_values = apply_sampling(
            x_values, y_values, z_values, every
        )
        if ENABLE_TIMING:
            logger.info(f"[TIMING] Step 7 - Apply sampling: {(time.time() - t0)*1000:.2f}ms")

        # Step 8: Handle no-style case for z values
        if no_style and z_values is None:
            z_values = kwargs.pop("c", None)

    # Step 9: Domain extraction - applies to ALL methods except grid_cells
    # Skip domain extraction if we're going to reproject (reprojection handles the domain via bbox)
    t0 = time.time() if ENABLE_TIMING else None
    if method_name != 'grid_cells' and not will_reproject:
        # Step 9a: Remove cyclic point before domain extraction if it was added
        # Domain extraction needs data without cyclic points to correctly handle dateline crossing
        cyclic_point_was_added = dimension_set._has_cyclic_point
        if cyclic_point_was_added and subplot.domain and extract_domain and not no_style:
            # Remove the cyclic point temporarily for domain extraction
            if x_values.ndim == 1:
                x_values = x_values[:-1]
                if z_values is not None:
                    z_values = z_values[:-1] if z_values.ndim == 1 else z_values[:, :-1]
            else:
                x_values = x_values[:, :-1]
                y_values = y_values[:, :-1]
                if z_values is not None:
                    z_values = z_values[:, :-1]

        # Step 9b: Extract data within domain boundaries if requested
        if subplot.domain and extract_domain and not no_style:
            # Resolve "auto" CRS to None so domain.extract can use its default (PlateCarree)
            extract_crs = dimension_set.crs if (dimension_set.crs is not None and dimension_set.crs != "auto") else None
            x_values, y_values, z_values = subplot.domain.extract(
                x_values, y_values, z_values, source_crs=extract_crs
            )
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 9 - Domain extraction: {(time.time() - t0)*1000:.2f}ms")

    # Step 10: Reproject data to target CRS if needed
    # This applies to contour/contourf on geographic plots when CRS doesn't match
    t0_reproj = time.time() if ENABLE_TIMING else None
    if will_reproject:
        from earthkit.plots.geo.reproject import reproject_to_grid

        # Get CRS objects - IMPORTANT: use cached values to avoid expensive re-access!
        # We cached both data_crs_raw (Step 2.6) and target_crs (Step 6.5)
        data_crs = cached_data_crs_raw if (cached_data_crs_raw is not None and cached_data_crs_raw != "auto") else None
        if data_crs == "auto":
            data_crs = _get_platecarree()
        # Use cached target_crs from Step 6.5 instead of accessing subplot.crs again!

        # Get the target bbox from the map's extent
        # ax.get_extent() returns (x0, x1, y0, y1) in the map's CRS
        # For matplotlib-only mode (tiles with PlateCarree), use domain instead
        try:
            extent = subplot.ax.get_extent(crs=target_crs)
        except AttributeError:
            # Axes doesn't have get_extent (matplotlib-only mode)
            # Fall back to using the subplot's domain
            if hasattr(subplot, 'domain') and subplot.domain is not None:
                extent = subplot.domain.bbox.to_cartopy_bounds()
            else:
                # Last resort: use a default extent
                extent = (-180, 180, -90, 90)
        bbox_target = extent  # (xmin, xmax, ymin, ymax)

        # Use default resolution of 500x500
        # TODO: Make this configurable via a parameter if needed
        nx, ny = 500, 500

        # Reproject the data
        # Before reprojection, ensure coordinates are in the right format
        # reproject_to_grid expects 1D or 2D coordinate arrays
        x_src = x_values
        y_src = y_values

        # If coordinates are 2D from meshgrid, extract the 1D arrays
        if x_values.ndim == 2:
            x_src = x_values[0, :]
            y_src = y_values[:, 0]

        t0 = time.time() if ENABLE_TIMING else None
        x_values, y_values, z_values = reproject_to_grid(
            x_src, y_src, z_values,
            crs_src=data_crs,
            bbox_target=bbox_target,
            crs_target=target_crs,
            nx=nx,
            ny=ny,
        )
        if ENABLE_TIMING:
            logger.info(f"[TIMING] Step 10a - reproject_to_grid call: {(time.time() - t0)*1000:.2f}ms")

        # Update the transform kwarg to target CRS since data is now in target CRS
        kwargs['transform'] = target_crs
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 10 - TOTAL Reprojection: {(time.time() - t0_reproj)*1000:.2f}ms")

    if do_standard_processing:
        # Step 11: Handle cyclic point wrapping for contour plots
        # Skip cyclic points if we reprojected (reprojected data is already a complete grid)
        t0 = time.time() if ENABLE_TIMING else None
        if method_name.startswith("contour") and plot_type in (PlotType.GEOGRAPHIC_1D, PlotType.GEOGRAPHIC_2D) and not will_reproject:
            x_values, y_values, z_values = _handle_cyclic_points(
                x_values, y_values, z_values
            )
        if ENABLE_TIMING:
            logger.info(f"[TIMING] Step 11 - Handle cyclic points: {(time.time() - t0)*1000:.2f}ms")

        # Step 12: Handle coordinate transformation settings
        t0 = time.time() if ENABLE_TIMING else None
        kwargs = _handle_transform_settings(subplot, kwargs)
        if ENABLE_TIMING:
            logger.info(f"[TIMING] Step 12 - Handle transform settings: {(time.time() - t0)*1000:.2f}ms")

        # Step 13: Handle meshgrid for geographic 2D plots with 1D coordinates
        # For maps, cartopy expects 2D coordinate arrays
        t0 = time.time() if ENABLE_TIMING else None
        is_geographic = plot_type in {PlotType.GEOGRAPHIC_1D, PlotType.GEOGRAPHIC_2D}
        if is_geographic and x_values.ndim == 1 and y_values.ndim == 1:
            x_values, y_values = np.meshgrid(x_values, y_values)
        if ENABLE_TIMING:
            logger.info(f"[TIMING] Step 13 - Handle meshgrid: {(time.time() - t0)*1000:.2f}ms")

    # Step 14: Get matplotlib kwargs from style
    t0 = time.time() if ENABLE_TIMING else None
    if not no_style and style is not None:
        # For 2D plots, we use z_values as the data for style processing
        try:
            style_kwargs = getattr(style, f"to_{method_name}_kwargs")(z_values)
        except Exception:
            style_kwargs = style.to_matplotlib_kwargs(z_values)
        kwargs = {**style_kwargs, **kwargs}
    if ENABLE_TIMING:
        logger.info(f"[TIMING] Step 14 - Get matplotlib kwargs from style: {(time.time() - t0)*1000:.2f}ms")

    # Step 14.5: Remove earthkit-specific parameters that shouldn't reach matplotlib
    # These were already filtered from Style but may still be in remaining kwargs
    kwargs.pop('missing_values', None)

    # Step 15: Add metadata to kwargs for layer creation
    kwargs['_dimension_set'] = dimension_set
    kwargs['_style'] = style
    kwargs['_primary_axis'] = 'z'  # For 2D plots, z is the data axis
    kwargs['_units'] = units
    kwargs['_xunits'] = xunits
    kwargs['_yunits'] = yunits
    kwargs['_is_specialized'] = is_specialized
    kwargs['_method_name'] = method_name
    kwargs['_no_style'] = no_style
    kwargs['_label'] = label
    if method_name == "grid_cells":
        kwargs['_grid_cells_callable'] = grid_cells_callable  # For grid_cells method

    if ENABLE_TIMING:
        total_time = (time.time() - t_start) * 1000
        logger.info(f"[TIMING] ═══ TOTAL extract_plottables_2d: {total_time:.2f}ms ═══")

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
    # Handle 2D coordinate arrays
    n_x = None
    if len(x_values.shape) != 1:
        n_x = x_values.shape[0]
        x_values = x_values[0]

    # Try to add cyclic points using cartopy's function
    # If it fails (e.g., due to floating point precision issues with regridded data),
    # manually add the cyclic point
    try:
        z_values, x_values = add_cyclic_point(z_values, coord=x_values)
    except ValueError:
        # Manually add cyclic point
        # Calculate the expected spacing
        delta_x = x_values[1] - x_values[0]
        # Add one more point at the end
        x_values = np.concatenate([x_values, [x_values[-1] + delta_x]])
        # Add the first column of z to the end
        if z_values.ndim == 2:
            z_values = np.concatenate([z_values, z_values[:, 0:1]], axis=1)
        else:
            z_values = np.concatenate([z_values, z_values[0:1]])

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
