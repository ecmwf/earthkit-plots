"""
Pandas dimension extractor.

This module provides dimension extraction for pandas Series and DataFrames.
For pandas objects, x/y/z parameters can be:
- Column names (strings) that reference DataFrame columns
- Index references (for x)
- Actual arrays to override

Currently supports single-layer extraction only. Multi-layer support
(multiple DataFrame columns) will be added in the future.
"""

from typing import Any, Optional, Union
import numpy as np
import pandas as pd

from earthkit.plots.sources.core import (
    DimensionSet,
    DimensionInfo,
    DimensionSource,
    PlotContext,
    PlotType,
)
from earthkit.plots.sources.extractors.base import DataExtractor
from earthkit.plots.sources.extractors.exceptions import (
    InvalidSpecificationError,
    MissingDimensionError,
    AmbiguousDimensionError,
)
from earthkit.plots.sources.identifiers import find_geographic_coords


class PandasExtractor(DataExtractor):
    """
    Extractor for pandas Series and DataFrames.
    
    For pandas objects, x/y/z parameters can be column names (strings) or arrays.
    
    Default behavior:
    - Series: index → x, values → y
    - DataFrame (1D): index → x, first/specified column → y
    - DataFrame (2D): index → y, columns → x, values → z
    
    Multi-layer support (multiple columns) coming soon.
    """
    
    def extract_dimensions(
        self,
        data: Union[pd.Series, pd.DataFrame],
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]] = "auto",
        y: Optional[Union[str, np.ndarray]] = "auto",
        z: Optional[Union[str, np.ndarray]] = "auto",
        metadata: Optional[dict] = None,
    ) -> DimensionSet:
        """
        Extract dimensions from pandas Series or DataFrame.

        Args:
            data: pandas Series or DataFrame
            plot_context: Context about the plot type
            x: x dimension selector ("auto" to infer, None to skip extraction, or index/column name or array)
            y: y dimension selector ("auto" to infer, None to skip extraction, or column name or array)
            z: z dimension selector ("auto" to infer, None to skip extraction, or column name or array)
            metadata: Optional user-provided metadata (takes precedence)

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

        # Parse metadata - extract attrs if available
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
        Extract metadata from pandas objects.
        
        Args:
            original_data: The original pandas Series or DataFrame
            key: The metadata key to look up
            dimension_name: Optional column/index name for dimension-specific lookup
        
        Returns:
            Metadata value or None if not found
        """
        # Try attrs dictionary
        if hasattr(original_data, 'attrs') and key in original_data.attrs:
            return original_data.attrs[key]
        
        # For DataFrames, try to get column values
        if isinstance(original_data, pd.DataFrame):
            if key in original_data.columns:
                return original_data[key].values
            # Check if it's the index
            if hasattr(original_data.index, 'name') and key == original_data.index.name:
                return original_data.index.values

        return None

    def extract_datetime(self, original_data: Any) -> dict:
        """
        Extract datetime information from pandas objects.

        Checks for datetime index or columns containing datetime values.

        Args:
            original_data: The original pandas Series or DataFrame

        Returns:
            Dictionary with 'base_time' and 'valid_time' keys
        """
        from earthkit.plots.utils import time_utils

        datetimes = None

        # Check if index is datetime
        if hasattr(original_data, 'index') and pd.api.types.is_datetime64_any_dtype(original_data.index):
            try:
                datetimes = [time_utils.to_pydatetime(dt) for dt in original_data.index]
            except (ValueError, TypeError):
                pass

        # Check for time/date columns in DataFrames
        if datetimes is None and isinstance(original_data, pd.DataFrame):
            time_cols = [col for col in ['time', 'date', 'datetime', 'valid_time'] if col in original_data.columns]
            if time_cols:
                try:
                    time_col = time_cols[0]
                    if pd.api.types.is_datetime64_any_dtype(original_data[time_col]):
                        datetimes = [time_utils.to_pydatetime(dt) for dt in original_data[time_col]]
                except (ValueError, TypeError, KeyError):
                    pass

        return {
            "base_time": datetimes,
            "valid_time": datetimes,
        }

    def _extract_1d(
        self,
        data: Union[pd.Series, pd.DataFrame],
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        original_data: Union[pd.Series, pd.DataFrame],
        global_metadata: dict,
    ) -> DimensionSet:
        """
        Extract dimensions for 1D plots.
        
        Default: index → x, values/column → y
        Context-aware swapping: similar to xarray
        """
        # Resolve selectors
        x_spec = self._resolve_selector(data, x, "x") if x is not None else None
        y_spec = self._resolve_selector(data, y, "y") if y is not None else None
        
        # Handle Series
        if isinstance(data, pd.Series):
            return self._extract_1d_series(data, x_spec, y_spec, original_data, global_metadata)
        
        # Handle DataFrame
        return self._extract_1d_dataframe(data, x_spec, y_spec, original_data, global_metadata)
    
    def _extract_1d_series(
        self,
        data: pd.Series,
        x_spec: Optional[Union[str, np.ndarray]],
        y_spec: Optional[Union[str, np.ndarray]],
        original_data: pd.Series,
        global_metadata: dict,
    ) -> DimensionSet:
        """Extract dimensions from a Series for 1D plots."""
        plot_context = PlotContext(PlotType.CARTESIAN_1D)
        
        # Infer defaults: index → x, values → y
        default_x_name = data.index.name or "index"
        default_y_name = data.name or "values"
        
        # Case 1: Neither specified - use defaults
        if x_spec is None and y_spec is None:
            x_dim = self._create_dimension_from_index(data, original_data, axis="X")
            y_dim = self._create_dimension_from_series_values(data, original_data, axis="Y")
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 2: Only x specified
        if x_spec is not None and y_spec is None:
            # If they specified the values as x, swap
            if isinstance(x_spec, str) and x_spec == data.name:
                x_dim = self._create_dimension_from_series_values(data, original_data, axis="X")
                y_dim = self._create_dimension_from_index(data, original_data, axis="Y")
            else:
                x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
                y_dim = self._create_dimension_from_series_values(data, original_data, axis="Y")
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 3: Only y specified
        if y_spec is not None and x_spec is None:
            x_dim = self._create_dimension_from_index(data, original_data, axis="X")
            y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 4: Both specified
        x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
        y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
        return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
    
    def _extract_1d_dataframe(
        self,
        data: pd.DataFrame,
        x_spec: Optional[Union[str, np.ndarray]],
        y_spec: Optional[Union[str, np.ndarray]],
        original_data: pd.DataFrame,
        global_metadata: dict,
    ) -> DimensionSet:
        """Extract dimensions from a DataFrame for 1D plots."""
        plot_context = PlotContext(PlotType.CARTESIAN_1D)
        
        # For now, require y to be specified if DataFrame has multiple columns
        if y_spec is None and len(data.columns) > 1:
            raise AmbiguousDimensionError(
                f"DataFrame has multiple columns: {list(data.columns)}. "
                f"Please specify which column to use for y. "
                f"(Multi-layer support coming soon)"
            )
        
        # Infer defaults: index → x, first/specified column → y
        default_x_name = data.index.name or "index"
        if y_spec is None:
            default_y_name = data.columns[0]
        else:
            default_y_name = y_spec if isinstance(y_spec, str) else None
        
        # Case 1: Neither specified - use defaults
        if x_spec is None and y_spec is None:
            x_dim = self._create_dimension_from_index(data, original_data, axis="X")
            y_dim = self._create_dimension_from_column(data, data.columns[0], original_data, axis="Y")
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 2: Only x specified
        if x_spec is not None and y_spec is None:
            # Check if x_spec is a column name (meaning they want to swap)
            if isinstance(x_spec, str) and x_spec in data.columns:
                # They specified a column as x, but we need y too
                if len(data.columns) == 1:
                    # Only one column, use index as y
                    x_dim = self._create_dimension_from_column(data, x_spec, original_data, axis="X")
                    y_dim = self._create_dimension_from_index(data, original_data, axis="Y")
                else:
                    raise AmbiguousDimensionError(
                        f"When specifying a column as x, please also specify y. "
                        f"Available columns: {list(data.columns)}"
                    )
            else:
                x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
                y_dim = self._create_dimension_from_column(data, data.columns[0], original_data, axis="Y")
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 3: Only y specified
        if y_spec is not None and x_spec is None:
            x_dim = self._create_dimension_from_index(data, original_data, axis="X")
            y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
        
        # Case 4: Both specified - could be two columns plotted against each other
        x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
        y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
        return self._create_dimension_set(x_dim, y_dim, None, plot_context, original_data, global_metadata)
    
    def _extract_2d(
        self,
        data: Union[pd.Series, pd.DataFrame],
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        original_data: Union[pd.Series, pd.DataFrame],
        global_metadata: dict,
    ) -> DimensionSet:
        """
        Extract dimensions for 2D plots.
        
        Supports:
        - DataFrames as gridded data (values → z, index → y, columns → x)
        - DataFrames with lat/lon columns as point data (for geospatial)
        """
        if isinstance(data, pd.Series):
            raise InvalidSpecificationError(
                "Cannot create 2D plot from Series. Use a DataFrame instead."
            )
        
        # Check if this is geospatial point data
        if plot_context.is_geospatial:
            return self._extract_2d_geospatial(data, x, y, z, original_data, global_metadata)
        
        # Otherwise, treat DataFrame as gridded data
        return self._extract_2d_gridded(data, plot_context, x, y, z, original_data, global_metadata)
    
    def _extract_2d_geospatial(
        self,
        data: pd.DataFrame,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        original_data: pd.DataFrame,
        global_metadata: dict,
    ) -> DimensionSet:
        """Extract dimensions for geospatial 2D plots (point data)."""
        plot_context = PlotContext(PlotType.GEOSPATIAL_2D)
        
        # Try to find geographic coordinates in columns
        lon_col, lat_col = find_geographic_coords(data)
        
        if lon_col is None or lat_col is None:
            raise MissingDimensionError(
                f"Could not find latitude/longitude columns in DataFrame. "
                f"Available columns: {list(data.columns)}. "
                f"Please specify x and y explicitly."
            )
        
        # Resolve specifications
        x_spec = self._resolve_selector(data, x, "x") if x is not None else None
        y_spec = self._resolve_selector(data, y, "y") if y is not None else None
        z_spec = self._resolve_selector(data, z, "z") if z is not None else None
        
        # Determine x (longitude)
        if x_spec is not None:
            x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
        else:
            x_dim = self._create_dimension_from_column(data, lon_col, original_data, axis="X")
        
        # Determine y (latitude)
        if y_spec is not None:
            y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
        else:
            y_dim = self._create_dimension_from_column(data, lat_col, original_data, axis="Y")
        
        # Determine z (values)
        if z_spec is None:
            # Need to pick a column for z - exclude lat/lon
            value_cols = [col for col in data.columns if col not in (lon_col, lat_col)]
            if len(value_cols) == 0:
                raise MissingDimensionError(
                    "No value columns found for z (only lat/lon present). "
                    "Please specify z explicitly."
                )
            elif len(value_cols) > 1:
                raise AmbiguousDimensionError(
                    f"Multiple value columns available: {value_cols}. "
                    f"Please specify which to use for z."
                )
            z_dim = self._create_dimension_from_column(data, value_cols[0], original_data)
        else:
            z_dim = self._resolve_to_dimension_info(data, z_spec, "z", original_data=original_data)
        
        return self._create_dimension_set(x_dim, y_dim, z_dim, plot_context, original_data, global_metadata)
    
    def _extract_2d_gridded(
        self,
        data: pd.DataFrame,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        original_data: pd.DataFrame,
        global_metadata: dict,
    ) -> DimensionSet:
        """Extract dimensions for 2D gridded plots (DataFrame as matrix)."""
        # Resolve specifications
        x_spec = self._resolve_selector(data, x, "x") if x is not None else None
        y_spec = self._resolve_selector(data, y, "y") if y is not None else None
        z_spec = self._resolve_selector(data, z, "z") if z is not None else None
        
        # Default: columns → x, index → y, values → z
        if x_spec is None:
            x_dim = self._create_dimension_from_columns(data, original_data, axis="X")
        else:
            x_dim = self._resolve_to_dimension_info(data, x_spec, "x", axis="X", original_data=original_data)
        
        if y_spec is None:
            y_dim = self._create_dimension_from_index(data, original_data, axis="Y")
        else:
            y_dim = self._resolve_to_dimension_info(data, y_spec, "y", axis="Y", original_data=original_data)
        
        if z_spec is None:
            z_dim = self._create_dimension_from_dataframe_values(data, original_data)
        else:
            z_dim = self._resolve_to_dimension_info(data, z_spec, "z", original_data=original_data)
        
        return self._create_dimension_set(x_dim, y_dim, z_dim, plot_context, original_data, global_metadata)
    
    def _resolve_selector(
        self,
        data: Union[pd.Series, pd.DataFrame],
        selector: Optional[Union[str, np.ndarray]],
        axis_name: str,
    ) -> Optional[Union[str, np.ndarray]]:
        """Resolve a selector to either a string name or array."""
        if selector is None:
            return None
        
        # If it's an array, return as-is
        if isinstance(selector, (np.ndarray, list)):
            return np.asarray(selector)
        
        # If it's a string, validate it exists
        if isinstance(selector, str):
            if isinstance(data, pd.DataFrame):
                if selector in data.columns:
                    return selector
                if selector == data.index.name or selector == "index":
                    return selector
            elif isinstance(data, pd.Series):
                if selector == data.name or selector == data.index.name or selector == "index":
                    return selector
            
            raise InvalidSpecificationError(
                f"Specified {axis_name}='{selector}' not found in data. "
                f"Available: {list(data.columns) if isinstance(data, pd.DataFrame) else [data.name, data.index.name]}"
            )
        
        raise InvalidSpecificationError(
            f"Invalid {axis_name} specification: {selector}. Must be a string name or array."
        )
    
    def _resolve_to_dimension_info(
        self,
        data: Union[pd.Series, pd.DataFrame],
        spec: Union[str, np.ndarray],
        axis_name: str,
        axis: Optional[str] = None,
        original_data: Optional[Union[pd.Series, pd.DataFrame]] = None,
    ) -> DimensionInfo:
        """Resolve a specification to a DimensionInfo object."""
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
        
        # spec is a string
        if isinstance(data, pd.DataFrame):
            if spec in data.columns:
                return self._create_dimension_from_column(data, spec, original_data or data, axis)
            elif spec == data.index.name or spec == "index":
                return self._create_dimension_from_index(data, original_data or data, axis)
        elif isinstance(data, pd.Series):
            if spec == data.name:
                return self._create_dimension_from_series_values(data, original_data or data, axis)
            elif spec == data.index.name or spec == "index":
                return self._create_dimension_from_index(data, original_data or data, axis)
        
        raise InvalidSpecificationError(
            f"Could not resolve '{spec}' to a column, index, or values"
        )
    
    def _create_dimension_from_index(
        self,
        data: Union[pd.Series, pd.DataFrame],
        original_data: Union[pd.Series, pd.DataFrame],
        axis: Optional[str] = None,
    ) -> DimensionInfo:
        """Create DimensionInfo from pandas index."""
        index_name = data.index.name or "index"
        
        metadata = {
            'source_type': 'index',
            'index_name': data.index.name,
        }
        
        return DimensionInfo(
            name=index_name,
            values=data.index.values,
            source=DimensionSource.DIMENSION,
            axis=axis,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )
    
    def _create_dimension_from_column(
        self,
        data: pd.DataFrame,
        column_name: str,
        original_data: pd.DataFrame,
        axis: Optional[str] = None,
    ) -> DimensionInfo:
        """Create DimensionInfo from DataFrame column."""
        column = data[column_name]
        
        metadata = {
            'source_type': 'column',
            'column_name': column_name,
        }
        
        return DimensionInfo(
            name=column_name,
            values=column.values,
            source=DimensionSource.VARIABLE,
            axis=axis,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )
    
    def _create_dimension_from_columns(
        self,
        data: pd.DataFrame,
        original_data: pd.DataFrame,
        axis: Optional[str] = None,
    ) -> DimensionInfo:
        """Create DimensionInfo from DataFrame column labels."""
        metadata = {
            'source_type': 'columns',
        }
        
        return DimensionInfo(
            name="columns",
            values=data.columns.values,
            source=DimensionSource.DIMENSION,
            axis=axis,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )
    
    def _create_dimension_from_series_values(
        self,
        data: pd.Series,
        original_data: pd.Series,
        axis: Optional[str] = None,
    ) -> DimensionInfo:
        """Create DimensionInfo from Series values."""
        series_name = data.name or "values"
        
        metadata = {
            'source_type': 'series_values',
            'series_name': data.name,
        }
        
        return DimensionInfo(
            name=series_name,
            values=data.values,
            source=DimensionSource.VARIABLE,
            axis=axis,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )
    
    def _create_dimension_from_dataframe_values(
        self,
        data: pd.DataFrame,
        original_data: pd.DataFrame,
    ) -> DimensionInfo:
        """Create DimensionInfo from entire DataFrame values (as 2D array)."""
        metadata = {
            'source_type': 'dataframe_values',
        }
        
        return DimensionInfo(
            name="values",
            values=data.values,
            source=DimensionSource.VARIABLE,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )
    
    def _all_arrays_specified(
        self,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
    ) -> bool:
        """Check if all required dimensions are specified as arrays (not selectors)."""
        def is_array(val):
            return isinstance(val, (np.ndarray, list))
        
        if plot_context.is_1d:
            return x is not None and y is not None and is_array(x) and is_array(y)
        else:
            return (x is not None and y is not None and z is not None and
                    is_array(x) and is_array(y) and is_array(z))
    
    def _validate_and_wrap_arrays(
        self,
        data: Union[pd.Series, pd.DataFrame],
        plot_context: PlotContext,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray],
        original_data: Union[pd.Series, pd.DataFrame],
        global_metadata: dict,
    ) -> DimensionSet:
        """Wrap user-provided arrays when all dimensions are specified as arrays."""
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