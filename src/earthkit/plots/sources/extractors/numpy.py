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

from earthkit.plots.sources.core import (
    AxisType,
    DimensionSet,
    DimensionInfo,
    DimensionSource,
    PlotContext,
    PlotType,
    create_index_dimension,
)
from earthkit.plots.sources.extractors.base import DataExtractor
from earthkit.plots.sources.extractors.exceptions import (
    InvalidSpecificationError,
    IncompatibleDimensionsError,
    MissingDimensionError,
)

class NumpyExtractor(DataExtractor):
    """
    Extractor for numpy arrays.
    
    Numpy arrays have no inherent metadata, so extraction is straightforward.
    Unlike other extractors, x/y/z parameters are the actual data arrays,
    not selectors into a data structure.
    
    Usage patterns:
    - plot_line(data=[1,2,3]) → data becomes y, x generated as index
    - plot_line(x=[1,2,3]) → x is x-axis, y generated as index
    - plot_line(y=[1,2,3]) → y is y-axis, x generated as index
    - plot_line(x=[1,2,3], y=[4,5,6]) → explicit x and y
    """
    
    def extract_dimensions(
        self,
        data: Optional[Union[np.ndarray, list]] = None,
        plot_context: PlotContext = None,
        x: Optional[Union[np.ndarray, list]] = "auto",
        y: Optional[Union[np.ndarray, list]] = "auto",
        z: Optional[Union[np.ndarray, list]] = "auto",
        crs: Optional[Any] = "auto",
        metadata: Optional[dict] = None,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Extract dimensions from numpy array(s).

        Args:
            data: Optional primary data array (treated as y for 1D, z for 2D if provided)
            plot_context: Context about the plot type
            x: x dimension array ("auto" to infer, None to skip extraction)
            y: y dimension array ("auto" to infer, None to skip extraction)
            z: z dimension array ("auto" to infer, None to skip extraction, not used for 1D plots)
            crs: Coordinate Reference System ("auto" to infer, None for Cartesian, or explicit CRS)
            metadata: Optional metadata dict with structure:
                {
                    'units': 'K',  # Global metadata
                    'long_name': 'Temperature',  # Global metadata
                    'x': {'units': 'm', 'long_name': 'Distance'},  # x-specific
                    'y': {'units': 'K'},  # y-specific
                    'z': {...}  # z-specific
                }

        Returns:
            DimensionSet with extracted dimensions

        Raises:
            InvalidSpecificationError: If specifications are invalid
            IncompatibleDimensionsError: If dimensions don't match
            MissingDimensionError: If no data provided at all
        """
        # Convert "auto" to None for backward compatibility with existing logic
        if isinstance(x, str) and x == "auto":
            x = None
        if isinstance(y, str) and y == "auto":
            y = None
        if isinstance(z, str) and z == "auto":
            z = None

        # Handle CRS - numpy arrays have no inherent CRS, so "auto" means None
        if crs == "auto":
            crs = None

        # Check that at least something was provided
        if data is None and x is None and y is None and z is None:
            raise MissingDimensionError(
                "Must provide at least one of: data, x, y, or z"
            )

        # Convert inputs to numpy arrays if needed
        if data is not None:
            data = self._ensure_array(data, "data")
        if x is not None:
            x = self._ensure_array(x, "x")
        if y is not None:
            y = self._ensure_array(y, "y")
        if z is not None:
            z = self._ensure_array(z, "z")
        
        # Parse metadata
        metadata = metadata or {}
        global_metadata = {k: v for k, v in metadata.items() if k not in ('x', 'y', 'z')}
        x_metadata = {**global_metadata, **metadata.get('x', {})}
        y_metadata = {**global_metadata, **metadata.get('y', {})}
        z_metadata = {**global_metadata, **metadata.get('z', {})}
        
        # Store original data reference (use first non-None array)
        original_data = data if data is not None else (x if x is not None else (y if y is not None else z))
        
        # Check for z in 1D plots (not allowed for now)
        if plot_context.is_1d and z is not None:
            raise InvalidSpecificationError(
                "z dimension is not supported for 1D plots. "
                "For point coloring, use a different mechanism."
            )
        
        # Handle 2D array passed for 1D plot (error immediately)
        if plot_context.is_1d:
            for name, arr in [("data", data), ("x", x), ("y", y)]:
                if arr is not None and arr.ndim == 2:
                    raise InvalidSpecificationError(
                        f"Cannot use 2D array {name} (shape {arr.shape}) for 1D plot. "
                        f"Please specify which column/row to use, or reshape to 1D."
                    )
        
        # Early exit: all required dimensions explicitly specified (no data needed)
        if self._all_specified(plot_context, x, y, z):
            return self._validate_and_wrap(
                plot_context,
                x=x,
                y=y,
                z=z,
                crs=crs,
                x_metadata=x_metadata,
                y_metadata=y_metadata,
                z_metadata=z_metadata,
                original_data=original_data,
                user_metadata=global_metadata,
                regrid=regrid,
            )

        # Infer and resolve based on what's provided
        if plot_context.is_1d:
            return self._extract_1d(data, x, y, crs, x_metadata, y_metadata, original_data, global_metadata, regrid)
        else:  # 2D plots
            return self._extract_2d(data, plot_context, x, y, z, crs, x_metadata, y_metadata, z_metadata, original_data, global_metadata, regrid)
    
    def extract_metadata(
        self,
        original_data: Any,
        key: str,
        dimension_name: Optional[str] = None,
    ) -> Any:
        """
        Extract metadata from numpy arrays.

        Since numpy arrays have no inherent metadata, this returns None.
        All metadata must be provided explicitly by the user.

        Args:
            original_data: The original numpy array
            key: The metadata key to look up
            dimension_name: Optional dimension name (unused for numpy)

        Returns:
            None (numpy arrays have no metadata)
        """
        return None

    def extract_datetime(self, original_data: Any) -> dict:
        """
        Extract datetime information from numpy arrays.

        Since numpy arrays have no inherent datetime metadata, this returns None.
        Datetime information must be provided explicitly by the user.

        Args:
            original_data: The original numpy array

        Returns:
            Dictionary with None values for 'base_time' and 'valid_time'
        """
        return {"base_time": None, "valid_time": None}

    def _extract_1d(
        self,
        data: Optional[np.ndarray],
        x: Optional[np.ndarray],
        y: Optional[np.ndarray],
        crs: Optional[Any],
        x_metadata: dict,
        y_metadata: dict,
        original_data: np.ndarray,
        global_metadata: dict,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Extract dimensions for 1D plots.
        
        Logic:
        - If only data: data → y, generate index → x
        - If only x: x → x, generate index → y
        - If only y: y → y, generate index → x
        - If data + x: data → y, use x
        - If data + y: data → x, use y
        - If x + y: use both directly
        """
        plot_context = PlotContext(PlotType.CARTESIAN_1D)
        
        # Ensure all arrays are 1D
        for name, arr in [("data", data), ("x", x), ("y", y)]:
            if arr is not None and arr.ndim != 1:
                raise InvalidSpecificationError(
                    f"{name} must be 1D for 1D plots, got shape {arr.shape}"
                )
        
        # Case 1: Only data provided → data is y, generate x
        if data is not None and x is None and y is None:
            x_dim = create_index_dimension(len(data), name="x", axis="X", original_data=original_data, extractor=self)
            y_dim = self._create_dimension_info("y", data, DimensionSource.VARIABLE, y_metadata, axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, crs, original_data, global_metadata, regrid=regrid)

        # Case 2: Only x provided → x is x, generate y
        if x is not None and data is None and y is None:
            x_dim = self._create_dimension_info("x", x, DimensionSource.USER_SPECIFIED, x_metadata, axis="X", original_data=original_data)
            y_dim = create_index_dimension(len(x), name="y", axis="Y", original_data=original_data, extractor=self)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, crs, original_data, global_metadata, regrid=regrid)

        # Case 3: Only y provided → y is y, generate x
        if y is not None and data is None and x is None:
            x_dim = create_index_dimension(len(y), name="x", axis="X", original_data=original_data, extractor=self)
            y_dim = self._create_dimension_info("y", y, DimensionSource.USER_SPECIFIED, y_metadata, axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, crs, original_data, global_metadata, regrid=regrid)

        # Case 4: data + x provided → data is y, use x
        if data is not None and x is not None and y is None:
            if len(x) != len(data):
                raise IncompatibleDimensionsError(
                    f"x and data must have same length. Got x: {len(x)}, data: {len(data)}"
                )
            x_dim = self._create_dimension_info("x", x, DimensionSource.USER_SPECIFIED, x_metadata, axis="X", original_data=original_data)
            y_dim = self._create_dimension_info("y", data, DimensionSource.VARIABLE, y_metadata, axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, crs, original_data, global_metadata, regrid=regrid)

        # Case 5: data + y provided → data is x, use y
        if data is not None and y is not None and x is None:
            if len(y) != len(data):
                raise IncompatibleDimensionsError(
                    f"y and data must have same length. Got y: {len(y)}, data: {len(data)}"
                )
            x_dim = self._create_dimension_info("x", data, DimensionSource.VARIABLE, x_metadata, axis="X", original_data=original_data)
            y_dim = self._create_dimension_info("y", y, DimensionSource.USER_SPECIFIED, y_metadata, axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, crs, original_data, global_metadata, regrid=regrid)

        # Case 6: x + y provided (no data) → use both directly
        if x is not None and y is not None and data is None:
            if len(x) != len(y):
                raise IncompatibleDimensionsError(
                    f"x and y must have same length. Got x: {len(x)}, y: {len(y)}"
                )
            x_dim = self._create_dimension_info("x", x, DimensionSource.USER_SPECIFIED, x_metadata, axis="X", original_data=original_data)
            y_dim = self._create_dimension_info("y", y, DimensionSource.USER_SPECIFIED, y_metadata, axis="Y", original_data=original_data)
            return self._create_dimension_set(x_dim, y_dim, None, plot_context, crs, original_data, global_metadata, regrid=regrid)
        
        # Case 7: All three provided → ambiguous
        if data is not None and x is not None and y is not None:
            raise InvalidSpecificationError(
                "Cannot specify data, x, and y simultaneously for 1D plot. "
                "Use either (data), (x), (y), (data+x), (data+y), or (x+y)."
            )
        
        # Should never reach here
        raise RuntimeError("Unexpected combination of arguments")
    
    def _extract_2d(
        self,
        data: Optional[np.ndarray],
        plot_context: PlotContext,
        x: Optional[np.ndarray],
        y: Optional[np.ndarray],
        z: Optional[np.ndarray],
        crs: Optional[Any],
        x_metadata: dict,
        y_metadata: dict,
        z_metadata: dict,
        original_data: np.ndarray,
        global_metadata: dict,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Extract dimensions for 2D plots.
        
        Logic:
        - If only data: data → z (must be 2D), generate indices for x and y
        - If only z: z → z, generate x and y
        - If data + x + y: data → z
        - If z + x + y: use all three
        - Flexible about which dimension of z matches x vs y
        """
        # Determine which array is z
        if z is not None and data is not None:
            raise InvalidSpecificationError(
                "Cannot specify both data and z for 2D plot. Use one or the other."
            )
        
        z_array = z if z is not None else data
        
        if z_array is None:
            # Maybe x and y are 2D and define a mesh?
            raise MissingDimensionError(
                "For 2D plots, must provide either data or z dimension"
            )
        
        # Ensure z is 2D
        if z_array.ndim != 2:
            raise InvalidSpecificationError(
                f"z dimension must be 2D for 2D plots, got shape {z_array.shape}"
            )
        
        z_dim = self._create_dimension_info(
            "z",
            z_array,
            DimensionSource.USER_SPECIFIED if z is not None else DimensionSource.VARIABLE,
            z_metadata,
            original_data=original_data,
        )
        
        # Handle x dimension
        if x is not None:
            if x.ndim != 1:
                raise InvalidSpecificationError(
                    f"x must be 1D for 2D plots, got shape {x.shape}"
                )
            x_dim = self._create_dimension_info("x", x, DimensionSource.USER_SPECIFIED, x_metadata, axis="X", original_data=original_data)
        else:
            # Generate x based on z shape - we'll figure out which dimension matches later
            x_dim = create_index_dimension(z_array.shape[1], name="x", axis="X", original_data=original_data, extractor=self)
        
        # Handle y dimension
        if y is not None:
            if y.ndim != 1:
                raise InvalidSpecificationError(
                    f"y must be 1D for 2D plots, got shape {y.shape}"
                )
            y_dim = self._create_dimension_info("y", y, DimensionSource.USER_SPECIFIED, y_metadata, axis="Y", original_data=original_data)
        else:
            # Generate y based on z shape
            y_dim = create_index_dimension(z_array.shape[0], name="y", axis="Y", original_data=original_data, extractor=self)
        
        # Validate and handle flexible dimension matching
        return self._create_dimension_set_2d_flexible(x_dim, y_dim, z_dim, plot_context, crs, original_data, global_metadata, regrid)
    
    def _create_dimension_set_2d_flexible(
        self,
        x_dim: DimensionInfo,
        y_dim: DimensionInfo,
        z_dim: DimensionInfo,
        plot_context: PlotContext,
        crs: Optional[Any],
        original_data: np.ndarray,
        global_metadata: dict,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Create a 2D dimension set with flexible dimension matching.
        
        This allows x to match either z.shape[0] or z.shape[1], and same for y,
        as long as they're consistent.
        """
        z_shape = z_dim.shape
        
        # Check if dimensions are compatible
        x_matches_dim0 = x_dim.size == z_shape[0]
        x_matches_dim1 = x_dim.size == z_shape[1]
        y_matches_dim0 = y_dim.size == z_shape[0]
        y_matches_dim1 = y_dim.size == z_shape[1]
        
        # x must match at least one dimension
        if not (x_matches_dim0 or x_matches_dim1):
            raise IncompatibleDimensionsError(
                f"x dimension size {x_dim.size} doesn't match either dimension of z shape {z_shape}"
            )
        
        # y must match at least one dimension
        if not (y_matches_dim0 or y_matches_dim1):
            raise IncompatibleDimensionsError(
                f"y dimension size {y_dim.size} doesn't match either dimension of z shape {z_shape}"
            )
        
        # For non-square matrices, x and y should match different dimensions
        if z_shape[0] != z_shape[1]:
            if (x_matches_dim0 and y_matches_dim0 and not (x_matches_dim1 or y_matches_dim1)):
                raise IncompatibleDimensionsError(
                    f"Both x and y match the same dimension of z. "
                    f"x.size={x_dim.size}, y.size={y_dim.size}, z.shape={z_shape}"
                )
            if (x_matches_dim1 and y_matches_dim1 and not (x_matches_dim0 or y_matches_dim0)):
                raise IncompatibleDimensionsError(
                    f"Both x and y match the same dimension of z. "
                    f"x.size={x_dim.size}, y.size={y_dim.size}, z.shape={z_shape}"
                )
        
        # Create the dimension set (it will do its own validation too)
        return self._create_dimension_set(x_dim, y_dim, z_dim, plot_context, crs, original_data, global_metadata, regrid=regrid)
    
    def _validate_and_wrap(
        self,
        plot_context: PlotContext,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray],
        crs: Optional[Any],
        x_metadata: dict,
        y_metadata: dict,
        z_metadata: dict,
        original_data: np.ndarray,
        user_metadata: dict,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Validate and wrap user-provided arrays when all dimensions are specified.
        """
        x_dim = self._create_dimension_info("x", x, DimensionSource.USER_SPECIFIED, x_metadata, axis="X", original_data=original_data)
        y_dim = self._create_dimension_info("y", y, DimensionSource.USER_SPECIFIED, y_metadata, axis="Y", original_data=original_data)
        z_dim = None

        if z is not None:
            z_dim = self._create_dimension_info("z", z, DimensionSource.USER_SPECIFIED, z_metadata, original_data=original_data)

        if plot_context.is_2d and z_dim is not None:
            return self._create_dimension_set_2d_flexible(x_dim, y_dim, z_dim, plot_context, crs, original_data, user_metadata, regrid)
        else:
            return self._create_dimension_set(x_dim, y_dim, z_dim, plot_context, crs, original_data, user_metadata, regrid=regrid)
    
    def _ensure_array(self, data: Union[np.ndarray, list, Any], name: str) -> np.ndarray:
        """
        Ensure data is a numpy array, converting if necessary.
        
        Args:
            data: Data to convert
            name: Name of the parameter (for error messages)
        
        Returns:
            Numpy array
        
        Raises:
            InvalidSpecificationError: If data cannot be converted
        """
        if data is None:
            return None
        
        try:
            if not isinstance(data, np.ndarray):
                data = np.asarray(data)
            return data
        except (ValueError, TypeError) as e:
            raise InvalidSpecificationError(
                f"Could not convert {name} to numpy array: {e}"
            )
    
    def _create_dimension_info(
        self,
        name: str,
        values: np.ndarray,
        source: DimensionSource,
        metadata: dict,
        axis: Optional[str] = None,
        original_data: Optional[np.ndarray] = None,
    ) -> DimensionInfo:
        """
        Create a DimensionInfo object with metadata.

        Args:
            name: Dimension name
            values: Data array
            source: How the dimension was determined
            metadata: Metadata dict (may contain units, long_name, etc.)
            axis: Axis type ('X', 'Y', 'Z', 'T')
            original_data: Reference to original data

        Returns:
            DimensionInfo object
        """
        return DimensionInfo(
            name=name,
            _values=values,
            source=source,
            _source_units=metadata.get('units'),
            long_name=metadata.get('long_name'),
            standard_name=metadata.get('standard_name'),
            axis=axis,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )