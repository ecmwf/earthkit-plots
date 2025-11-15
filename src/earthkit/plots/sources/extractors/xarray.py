"""
Xarray dimension extractor.

This module provides dimension extraction for xarray DataArrays and Datasets.
For xarray, x/y/z are selectors (strings or arrays) that reference dimensions,
coordinates, or variables within the xarray object.
"""

from typing import Any, Optional, Union
import numpy as np
import xarray as xr

from earthkit.plots.sources.core import (
    DimensionSet,
    DimensionInfo,
    DimensionSource,
    PlotContext,
    create_index_dimension,
)
from earthkit.plots.sources.extractors.base import DataExtractor
from earthkit.plots.sources.extractors.exceptions import (
    InvalidSpecificationError,
    MissingDimensionError,
    AmbiguousDimensionError,
)


class XarrayExtractor(DataExtractor):
    """
    Extractor for xarray DataArrays and Datasets.
    
    For xarray objects, x/y/z parameters are selectors (string names or arrays)
    that reference dimensions, coordinates, or variables within the data structure.
    
    Default behavior:
    - 1D plots: dimension → x, variable → y
    - 2D plots: dimensions → x and y, variable → z
    - Geospatial: looks for lat/lon using identifiers
    
    Context-aware swapping:
    - If user specifies the default y as x, swaps to use default x as y
    """
    
    def extract_dimensions(
        self,
        data: Union[xr.DataArray, xr.Dataset],
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]] = "auto",
        y: Optional[Union[str, np.ndarray]] = "auto",
        z: Optional[Union[str, np.ndarray]] = "auto",
        metadata: Optional[dict] = None,
    ) -> DimensionSet:
        """
        Extract dimensions from xarray DataArray or Dataset.

        Args:
            data: xarray DataArray or Dataset
            plot_context: Context about the plot type
            x: x dimension selector ("auto" to infer, None to skip extraction, or dim/coord/var name or array)
            y: y dimension selector ("auto" to infer, None to skip extraction, or dim/coord/var name or array)
            z: z dimension selector ("auto" to infer, None to skip extraction, or dim/coord/var name or array)
            metadata: Optional user-provided metadata (takes precedence over xarray metadata)

        Returns:
            DimensionSet with extracted dimensions

        Raises:
            InvalidSpecificationError: If specifications are invalid
            IncompatibleDimensionsError: If dimensions don't match
            MissingDimensionError: If required dimensions cannot be determined
            AmbiguousDimensionError: If multiple valid options exist
        """
        # Convert "auto" to None for backward compatibility with existing logic
        if x == "auto":
            x = None
        if y == "auto":
            y = None
        if z == "auto":
            z = None

        # Store original data for metadata extraction
        original_data = data

        # Squeeze size-1 dimensions while preserving metadata
        data = data.squeeze()
        
        # Handle Dataset with single variable - extract the DataArray
        if isinstance(data, xr.Dataset):
            if len(data.data_vars) == 0:
                raise MissingDimensionError(
                    "Dataset has no data variables"
                )
            elif len(data.data_vars) == 1:
                var_name = list(data.data_vars.keys())[0]
                data = data[var_name]
            else:
                # Multiple variables - for now, require user to specify
                # (future: support multiple layers)
                raise AmbiguousDimensionError(
                    f"Dataset has multiple variables: {list(data.data_vars.keys())}. "
                    f"Please specify which variable to use for y or z."
                )
        
        # Parse metadata - extract global attrs
        user_metadata = metadata or {}
        global_metadata = dict(data.attrs) if hasattr(data, 'attrs') else {}
        # User metadata takes precedence
        global_metadata.update(user_metadata)
        
        # Early exit: all required dimensions specified with arrays (not selectors)
        if self._all_arrays_specified(plot_context, x, y, z):
            return self._validate_and_wrap_arrays(
                data, plot_context, x, y, z, original_data, global_metadata
            )
        
        # Infer and resolve based on plot type
        if plot_context.is_1d:
            return self._extract_1d(data, plot_context, x, y, original_data, global_metadata)
        else:  # 2D plots
            return self._extract_2d(data, plot_context, x, y, z, original_data, global_metadata)
    
    def extract_metadata(
        self,
        original_data: Any,
        key: str,
        dimension_name: Optional[str] = None,
    ) -> Any:
        """
        Extract metadata from xarray objects.
        
        This provides fallback access to xarray attributes, coordinate values,
        and dimension values that weren't captured during initial extraction.
        
        Args:
            original_data: The original xarray DataArray or Dataset
            key: The metadata key to look up. Can be:
                - An attribute name (e.g., 'units', 'long_name')
                - A coordinate name (e.g., 'latitude', 'longitude') to get values
                - A dimension name to get coordinate values
            dimension_name: Optional dimension/variable/coordinate name for
                        dimension-specific metadata lookup
        
        Returns:
            Metadata value, coordinate values, or None if not found
        """
        if not hasattr(original_data, 'attrs'):
            return None
        
        # If looking for dimension-specific metadata
        if dimension_name:
            # Try coordinate attributes
            if hasattr(original_data, 'coords') and dimension_name in original_data.coords:
                coord = original_data.coords[dimension_name]
                # Check if key is an attribute
                if key in coord.attrs:
                    return coord.attrs[key]
                # Check if key matches the coordinate name itself (return values)
                if key == dimension_name:
                    return coord.values
            
            # Try dimension attributes (for datasets)
            if isinstance(original_data, xr.Dataset) and dimension_name in original_data.data_vars:
                var = original_data[dimension_name]
                if key in var.attrs:
                    return var.attrs[key]
                # Return variable values if key matches variable name
                if key == dimension_name:
                    return var.values
            
            # Try data array attributes (if dimension_name matches the array name)
            if isinstance(original_data, xr.DataArray) and original_data.name == dimension_name:
                if key in original_data.attrs:
                    return original_data.attrs[key]
        
        # Try to find key as a coordinate name (regardless of dimension_name)
        if hasattr(original_data, 'coords') and key in original_data.coords:
            return original_data.coords[key].values
        
        # Try to find key as a dimension with coordinates
        if hasattr(original_data, 'dims') and key in original_data.dims:
            # If there's a coordinate for this dimension, return its values
            if hasattr(original_data, 'coords') and key in original_data.coords:
                return original_data.coords[key].values
            # Otherwise, return the dimension size
            return original_data.sizes[key]
        
        # Try to find key as a data variable (for Datasets)
        if isinstance(original_data, xr.Dataset) and key in original_data.data_vars:
            return original_data[key].values
        
        # Fall back to global attributes
        if key in original_data.attrs:
            return original_data.attrs[key]

        return None

    def extract_datetime(self, original_data: Any) -> dict:
        """
        Extract datetime information from xarray objects.

        Looks for time coordinates using identifiers (time, valid_time, etc.)
        and converts them to Python datetime objects. Falls back to checking
        attributes for date/time metadata.

        Args:
            original_data: The original xarray DataArray or Dataset

        Returns:
            Dictionary with 'base_time' and 'valid_time' keys containing
            lists of datetime objects, or None values if not found
        """
        from datetime import datetime
        from earthkit.plots.sources.identifiers import find_time
        from earthkit.plots.utils import time_utils

        datetimes = None

        # Try to find time coordinate
        time_coord = find_time(original_data)
        if time_coord is not None:
            try:
                time_values = np.atleast_1d(original_data[time_coord])
                datetimes = [
                    time_utils.to_pydatetime(dt)
                    for dt in time_values
                ]
            except (ValueError, TypeError, AttributeError):
                pass

        # Fallback: check for date/time in attributes
        if datetimes is None:
            if hasattr(original_data, 'attrs'):
                if all(key in original_data.attrs for key in ("date", "time")):
                    try:
                        date = original_data.attrs["date"]
                        time = original_data.attrs["time"]
                        datetimes = [datetime.strptime(f"{date}{time:04d}", "%Y%m%d%H%M")]
                    except (ValueError, TypeError, KeyError):
                        pass

        return {
            "base_time": datetimes,
            "valid_time": datetimes,
        }

    def _extract_1d(
        self,
        data: xr.DataArray,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        original_data: xr.DataArray,
        global_metadata: dict,
    ) -> DimensionSet:
        """
        Extract dimensions for 1D plots.
        
        Default: dimension → x, variable → y
        Context-aware swapping: if user specifies variable as x, swap to dim as y
        """
        # Handle multi-dimensional DataArray - error for now
        if data.ndim > 1:
            raise InvalidSpecificationError(
                f"DataArray has {data.ndim} dimensions: {list(data.dims)}. "
                f"For 1D plots, data must be 1D. Try selecting or squeezing dimensions."
            )
        
        if data.ndim == 0:
            raise InvalidSpecificationError(
                "DataArray has no dimensions (scalar value)"
            )
        
        # Infer defaults
        default_x_name = data.dims[0]  # The dimension name
        default_y_name = data.name or "data"  # The variable name
        
        # Determine what user specified and apply context-aware swapping
        x_spec = self._resolve_selector(data, x, "x") if x is not None else None
        y_spec = self._resolve_selector(data, y, "y") if y is not None else None
        
        # Case 1: Neither specified - use defaults
        if x_spec is None and y_spec is None:
            x_dim = self._create_dimension_from_dim(data, default_x_name, axis="X", original_data=original_data)
            y_dim = self._create_dimension_from_variable(data, axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 2: Only x specified
        if x_spec is not None and y_spec is None:
            # Check if user specified what we thought was y (the variable)
            if self._is_variable_reference(data, x_spec, default_y_name):
                # Swap: variable → x, dimension → y
                x_dim = self._create_dimension_from_variable(data, axis="X", original_data=original_data)
                y_dim = self._create_dimension_from_dim(data, default_x_name, axis="Y", original_data=original_data)
            else:
                # User specified something else (dim/coord) for x, keep variable as y
                x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
                y_dim = self._create_dimension_from_variable(data, axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 3: Only y specified
        if y_spec is not None and x_spec is None:
            # Check if user specified what we thought was x (the dimension)
            if self._is_dimension_reference(data, y_spec, default_x_name):
                # Swap: dimension → y, variable → x
                x_dim = self._create_dimension_from_variable(data, axis="X", original_data=original_data)
                y_dim = self._create_dimension_from_dim(data, default_x_name, axis="Y", original_data=original_data)
            else:
                # User specified something else for y, keep dimension as x
                x_dim = self._create_dimension_from_dim(data, default_x_name, axis="X", original_data=original_data)
                y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 4: Both specified - use directly
        x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
        y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
        return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
    
    def _extract_2d(
        self,
        data: xr.DataArray,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        original_data: xr.DataArray,
        global_metadata: dict,
    ) -> DimensionSet:
        """
        Extract dimensions for 2D plots.
        
        Default: dimensions → x and y, variable → z
        For geographic: use lat/lon identifiers
        """        
        # Infer defaults based on plot type
        if plot_context.is_geographic:
            default_x_name, default_y_name = self._infer_geographic_dims(data)
        else:
            # Standard 2D: dims[0] → y (rows), dims[1] → x (cols) to match numpy
            default_y_name = data.dims[0]
            default_x_name = data.dims[1]
        
        default_z_name = data.name or "data"
        
        # Resolve user specifications
        x_spec = self._resolve_selector(data, x, "x") if x is not None else None
        y_spec = self._resolve_selector(data, y, "y") if y is not None else None
        z_spec = self._resolve_selector(data, z, "z") if z is not None else None
        
        # Determine z (the variable/field)
        if z_spec is not None:
            z_dim = self._resolve_to_dimension_info(data, z_spec, "z", original_data=original_data)
        else:
            z_dim = self._create_dimension_from_variable(data, original_data=original_data)
        
        # Determine x
        if x_spec is not None:
            x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
        else:
            x_dim = self._create_dimension_from_dim(data, default_x_name, axis="X", original_data=original_data)
        
        # Determine y
        if y_spec is not None:
            y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
        else:
            y_dim = self._create_dimension_from_dim(data, default_y_name, axis="Y", original_data=original_data)
        
        return self._create_dimension_set(x_dim, y_dim, z_dim, plot_context, original_data, global_metadata)
    
    def _infer_geographic_dims(self, data: xr.DataArray) -> tuple[str, str]:
        """
        Infer longitude and latitude dimensions for geographic plots.
        
        Uses geographic coordinate identifiers with fallback to standard
        2D Cartesian behavior if geographic coordinates cannot be found.
        
        Returns:
            (x_name, y_name) tuple
        """
        from ..identifiers import find_geographic_coords
        
        # Try to find geographic coordinates
        x_name, y_name = find_geographic_coords(data)
        
        # If found, return them
        if x_name is not None and y_name is not None:
            return x_name, y_name
        
        # Fallback: standard 2D Cartesian behavior (dims[0] → y, dims[1] → x)
        if data.ndim >= 2:
            return data.dims[1], data.dims[0]
        
        # If we still can't determine, raise an error
        raise MissingDimensionError(
            f"Could not identify geographic coordinates for geographic plot. "
            f"Available dims: {list(data.dims)}, coords: {list(data.coords.keys())}. "
            f"Please specify x and y explicitly."
        )
    
    def _resolve_selector(
        self,
        data: xr.DataArray,
        selector: Union[str, np.ndarray, None],
        axis_name: str
    ) -> Union[str, np.ndarray]:
        """
        Resolve a selector to either a string name or array.
        
        If selector is already an array, return it.
        If selector is a string, validate it exists and return it.
        """
        if selector is None:
            return None
        
        # If it's an array, return as-is
        if isinstance(selector, (np.ndarray, list)):
            return np.asarray(selector)
        
        # If it's a string, validate it exists
        if isinstance(selector, str):
            if selector in data.dims:
                return selector
            elif selector in data.coords:
                return selector
            elif data.name == selector:
                return selector
            else:
                raise InvalidSpecificationError(
                    f"Specified {axis_name}='{selector}' not found in data. "
                    f"Available dims: {list(data.dims)}, coords: {list(data.coords)}, "
                    f"variable: {data.name}"
                )
        
        raise InvalidSpecificationError(
            f"Invalid {axis_name} specification: {selector}. "
            f"Must be a string name or array."
        )
    
    def _is_variable_reference(
        self,
        data: xr.DataArray,
        spec: Union[str, np.ndarray],
        var_name: str
    ) -> bool:
        """Check if a specification references the variable (not a dim/coord)."""
        if isinstance(spec, np.ndarray):
            return False
        return isinstance(spec, str) and spec == var_name
    
    def _is_dimension_reference(
        self,
        data: xr.DataArray,
        spec: Union[str, np.ndarray],
        dim_name: str
    ) -> bool:
        """Check if a specification references a dimension."""
        if isinstance(spec, np.ndarray):
            return False
        return isinstance(spec, str) and spec == dim_name
    
    def _resolve_to_dimension_info(
        self,
        data: xr.DataArray,
        spec: Union[str, np.ndarray],
        axis_name: str,
        axis: Optional[str] = None,
        original_data: Optional[xr.DataArray] = None,
    ) -> DimensionInfo:
        """
        Resolve a specification to a DimensionInfo object.
        
        Handles:
        - String dimension name → extract coordinate values
        - String coordinate name → extract coordinate values
        - String variable name → extract variable values
        - Array → wrap directly
        """
        # If spec is an array, wrap it directly
        if isinstance(spec, np.ndarray):
            return DimensionInfo(
                name=axis_name,
                values=spec,
                source=DimensionSource.USER_SPECIFIED,
                axis=axis,
                _original_data=original_data or data,
                _extractor=self,
            )
        
        # spec is a string - determine what it references
        if spec in data.dims:
            return self._create_dimension_from_dim(data, spec, axis=axis, original_data=original_data)
        elif spec in data.coords:
            return self._create_dimension_from_coord(data, spec, axis=axis, original_data=original_data)
        elif spec == data.name:
            return self._create_dimension_from_variable(data, axis=axis, original_data=original_data)
        else:
            raise InvalidSpecificationError(
                f"Could not resolve '{spec}' to a dimension, coordinate, or variable"
            )
    
    def _create_dimension_from_dim(
        self,
        data: xr.DataArray,
        dim_name: str,
        axis: Optional[str] = None,
        original_data: Optional[xr.DataArray] = None,
    ) -> DimensionInfo:
        """
        Create DimensionInfo from a dimension.
        
        Uses the coordinate values for that dimension if available,
        otherwise generates an index.
        """
        if dim_name in data.coords:
            coord = data.coords[dim_name]
            values = coord.values
            
            # Extract metadata from coordinate attributes
            coord_metadata = dict(coord.attrs)
            coord_metadata.update({
                'source_type': 'dimension',
                'dim_name': dim_name,
            })
            
            return DimensionInfo(
                name=dim_name,
                values=values,
                source=DimensionSource.DIMENSION,
                units=coord.attrs.get('units'),
                long_name=coord.attrs.get('long_name'),
                standard_name=coord.attrs.get('standard_name'),
                axis=axis or coord.attrs.get('axis'),
                _metadata=coord_metadata,
                _original_data=original_data or data,
                _extractor=self,
            )
        else:
            # No coordinate for this dimension, generate index
            size = data.sizes[dim_name]
            return create_index_dimension(
                size,
                name=dim_name,
                axis=axis,
                original_data=original_data or data,
                extractor=self,
            )
    
    def _create_dimension_from_coord(
        self,
        data: xr.DataArray,
        coord_name: str,
        axis: Optional[str] = None,
        original_data: Optional[xr.DataArray] = None,
    ) -> DimensionInfo:
        """Create DimensionInfo from a coordinate."""
        coord = data.coords[coord_name]
        
        coord_metadata = dict(coord.attrs)
        coord_metadata.update({
            'source_type': 'coordinate',
            'coord_name': coord_name,
        })
        
        return DimensionInfo(
            name=coord_name,
            values=coord.values,
            source=DimensionSource.COORDINATE,
            units=coord.attrs.get('units'),
            long_name=coord.attrs.get('long_name'),
            standard_name=coord.attrs.get('standard_name'),
            axis=axis or coord.attrs.get('axis'),
            _metadata=coord_metadata,
            _original_data=original_data or data,
            _extractor=self,
        )
    
    def _create_dimension_from_variable(
        self,
        data: xr.DataArray,
        axis: Optional[str] = None,
        original_data: Optional[xr.DataArray] = None,
    ) -> DimensionInfo:
        """Create DimensionInfo from the DataArray variable itself."""
        var_metadata = dict(data.attrs)
        var_metadata.update({
            'source_type': 'variable',
            'var_name': data.name,
        })
        
        return DimensionInfo(
            name=data.name or "data",
            values=data.values,
            source=DimensionSource.VARIABLE,
            units=data.attrs.get('units'),
            long_name=data.attrs.get('long_name'),
            standard_name=data.attrs.get('standard_name'),
            axis=axis,
            _metadata=var_metadata,
            _original_data=original_data or data,
            _extractor=self,
        )
    
    def _all_arrays_specified(
        self,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
    ) -> bool:
        """
        Check if all required dimensions are specified as arrays (not selectors).
        """
        def is_array(val):
            return isinstance(val, (np.ndarray, list))
        
        if plot_context.is_1d:
            return x is not None and y is not None and is_array(x) and is_array(y)
        else:
            return (x is not None and y is not None and z is not None and
                    is_array(x) and is_array(y) and is_array(z))
    
    def _validate_and_wrap_arrays(
        self,
        data: xr.DataArray,
        plot_context: PlotContext,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray],
        original_data: xr.DataArray,
        global_metadata: dict,
    ) -> DimensionSet:
        """
        Wrap user-provided arrays when all dimensions are specified as arrays.
        """
        x_dim = DimensionInfo(
            name="x",
            values=np.asarray(x),
            source=DimensionSource.USER_SPECIFIED,
            axis="X",
            _original_data=original_data,
            _extractor=self,
        )
        
        y_dim = DimensionInfo(
            name="y",
            values=np.asarray(y),
            source=DimensionSource.USER_SPECIFIED,
            axis="Y",
            _original_data=original_data,
            _extractor=self,
        )
        
        z_dim = None
        if z is not None:
            z_dim = DimensionInfo(
                name="z",
                values=np.asarray(z),
                source=DimensionSource.USER_SPECIFIED,
                _original_data=original_data,
                _extractor=self,
            )
        
        return self._create_dimension_set(x_dim, y_dim, z_dim, plot_context, original_data, global_metadata)