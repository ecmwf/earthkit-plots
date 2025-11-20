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

from typing import Any, Optional, Union
import numpy as np

from earthkit.plots.sources import core, extractors, identifiers
from earthkit.plots.sources.core import DimensionSet, PlotContext, PlotType


def get_dimension_set(
    *args: Any,
    x: Optional[Union[str, np.ndarray]] = "auto",
    y: Optional[Union[str, np.ndarray]] = "auto",
    z: Optional[Union[str, np.ndarray]] = "auto",
    plot_type: Optional[Union[str, PlotType]] = None,
    crs: Optional[str] = None,
    metadata: Optional[dict] = None,
    regrid: str = "auto",
    **kwargs: Any,
) -> DimensionSet:
    """
    Create a DimensionSet from various data types.

    This is the main entry point for converting user data into the internal
    DimensionSet representation used throughout earthkit-plots. The plot_type
    is typically provided by plotting function decorators (e.g., @plot_1d, @plot_2d).

    Parameters
    ----------
    *args : Any
        Positional arguments containing the data. Can be:
        - xarray DataArray/Dataset
        - pandas Series/DataFrame
        - numpy arrays (can provide 2-3 arrays for x, y, z)
        - earthkit-data FieldList
        - Other array-like objects
    x, y, z : str, array-like, or "auto", optional
        Dimension/coordinate specifications:
        - "auto" (default): Infer from data structure
        - str: Name of coordinate/dimension/variable
        - array-like: Explicit coordinate values
        - None: Don't extract that dimension
    plot_type : str or PlotType, optional
        The type of plot to create. Typically provided by decorator:
        - "cartesian_1d"/PlotType.CARTESIAN_1D: line plots, scatter (no z)
        - "cartesian_2d"/PlotType.CARTESIAN_2D: contour, pcolormesh (has z)
        - "geographic_1d"/PlotType.GEOGRAPHIC_1D: map scatter (no z)
        - "geographic_2d"/PlotType.GEOGRAPHIC_2D: map contour (has z)
        If None, will be inferred from data and crs.
    crs : str, optional
        Coordinate reference system for geographic plots.
    metadata : dict, optional
        Additional metadata to attach to the DimensionSet.
    regrid : str, optional
        Regridding parameter. "auto" (default) enables automatic regridding for
        irregular grids (e.g., HEALPix, Reduced Gaussian) to regular lat-lon grids.
    **kwargs : Any
        Additional keyword arguments (currently unused, reserved for future use).

    Returns
    -------
    DimensionSet
        The extracted dimension set ready for plotting.

    Raises
    ------
    ValueError
        If data type is not recognized or dimensions cannot be extracted.

    Examples
    --------
    >>> import xarray as xr
    >>> data = xr.DataArray([[1, 2], [3, 4]], coords={'x': [0, 1], 'y': [0, 1]})
    >>> # Typically plot_type comes from decorator, but can be explicit:
    >>> dim_set = get_dimension_set(data, plot_type="cartesian_2d")
    >>> dim_set.x.values
    array([0, 1])
    """
    # Step 1: Get the data object
    if len(args) == 0:
        raise ValueError("No data provided to get_dimension_set()")
    elif len(args) == 1:
        data = args[0]
    else:
        # Multiple args - treat as x, y, z arrays for numpy
        data = args

    # Step 2: Convert plot_type string to enum if needed
    if plot_type is None:
        plot_type = _infer_plot_type(data, x, y, z, crs)
    elif isinstance(plot_type, str):
        plot_type = PlotType(plot_type)

    # Step 3: Create plot context
    plot_context = PlotContext(plot_type=plot_type, crs=crs)

    # Step 4: Select appropriate extractor based on data type
    extractor = _get_extractor_for_data(data)

    # Step 5: Handle multiple numpy arrays case
    if isinstance(data, (tuple, list)) and all(isinstance(d, np.ndarray) for d in data):
        # Multiple numpy arrays provided as positional args
        if len(data) == 2:
            x, y = data
            z = None
        elif len(data) == 3:
            x, y, z = data
        else:
            raise ValueError(f"Expected 2 or 3 numpy arrays, got {len(data)}")
        data = y if z is None else z  # Use the data array as the primary data

    # Step 6: Extract dimensions
    dimension_set = extractor.extract_dimensions(
        data=data,
        plot_context=plot_context,
        x=x,
        y=y,
        z=z,
        crs=crs if crs is not None else "auto",
        metadata=metadata,
        regrid=regrid,
    )

    return dimension_set


def _infer_plot_type(
    data: Any,
    x: Any,
    y: Any,
    z: Any,
    crs: Optional[str],
) -> PlotType:
    """
    Infer the plot type from the data and arguments.

    This is a fallback when plot_type is not provided by decorator.

    Parameters
    ----------
    data : Any
        The data object.
    x, y, z : Any
        The dimension specifications.
    crs : str, optional
        Coordinate reference system.

    Returns
    -------
    PlotType
        The inferred plot type.
    """
    # If CRS is specified, assume geographic
    is_geographic = crs is not None

    # Check if we have z data (2D plot) or not (1D plot)
    has_z = z is not None and z != "auto"

    # For data types that we can inspect
    if not has_z:
        if hasattr(data, 'ndim'):
            # numpy array or similar
            has_z = data.ndim == 2
        elif hasattr(data, 'dims'):
            # xarray
            has_z = len(data.dims) >= 2

    # Determine plot type
    if is_geographic:
        return PlotType.GEOGRAPHIC_2D if has_z else PlotType.GEOGRAPHIC_1D
    else:
        return PlotType.CARTESIAN_2D if has_z else PlotType.CARTESIAN_1D


def _get_extractor_for_data(data: Any):
    """
    Get the appropriate extractor for the given data type.

    Parameters
    ----------
    data : Any
        The data object.

    Returns
    -------
    DataExtractor
        The appropriate extractor instance.

    Raises
    ------
    ValueError
        If data type is not recognized.
    """
    import pandas as pd
    import xarray as xr

    # Check for xarray
    if isinstance(data, (xr.DataArray, xr.Dataset)):
        from earthkit.plots.sources.extractors.xarray import XarrayExtractor
        return XarrayExtractor()

    # Check for pandas
    if isinstance(data, (pd.Series, pd.DataFrame)):
        from earthkit.plots.sources.extractors.pandas import PandasExtractor
        return PandasExtractor()

    # Check for numpy
    if isinstance(data, np.ndarray):
        from earthkit.plots.sources.extractors.numpy import NumpyExtractor
        return NumpyExtractor()

    # Check for earthkit-data
    try:
        import earthkit.data
        if isinstance(data, earthkit.data.core.Base):
            from earthkit.plots.sources.extractors.earthkit import EarthkitExtractor
            return EarthkitExtractor()
    except ImportError:
        pass

    # Check for tuple/list of arrays (numpy case)
    if isinstance(data, (tuple, list)) and len(data) > 0:
        if all(isinstance(d, np.ndarray) for d in data):
            from earthkit.plots.sources.extractors.numpy import NumpyExtractor
            return NumpyExtractor()

    raise ValueError(
        f"Unsupported data type: {type(data)}. "
        "Supported types: xarray.DataArray, xarray.Dataset, pandas.Series, "
        "pandas.DataFrame, numpy.ndarray, earthkit.data FieldList"
    )