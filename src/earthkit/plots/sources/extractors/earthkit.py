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


from typing import Any, Optional, Union, List
import numpy as np

from earthkit.plots.sources.core import (
    DimensionSet,
    DimensionInfo,
    DimensionSource,
    PlotContext,
)
from earthkit.plots.sources.extractors.base import DataExtractor
from earthkit.plots.sources.extractors.exceptions import (
    InvalidSpecificationError,
    MissingDimensionError,
)


# Variable keys to try when selecting fields
VARIABLE_KEYS = [
    "short_name",
    "standard_name",
    "long_name",
    "name",
]


class EarthkitExtractor(DataExtractor):
    """
    Extractor for earthkit-data objects (FieldLists).
    
    Earthkit-data objects are GRIB-like lists of fields. For these objects:
    - x/y are rarely specified by user (auto-extracted from coordinates)
    - z can be a variable name to select specific fields
    - Multi-field data returns a list of DimensionSets
    
    Coordinate extraction priority:
    1. .to_points() if available (returns {'x': ..., 'y': ...})
    2. .to_latlon() as fallback (returns {'lon': ..., 'lat': ...})
    """
    
    def extract_dimensions(
        self,
        data: Any,  # earthkit-data FieldList
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]] = "auto",
        y: Optional[Union[str, np.ndarray]] = "auto",
        z: Optional[Union[str, np.ndarray]] = "auto",
        crs: Optional[Any] = "auto",
        metadata: Optional[dict] = None,
        regrid: str = "auto",
    ) -> Union[DimensionSet, List[DimensionSet]]:
        """
        Extract dimensions from earthkit-data FieldList.

        Args:
            data: earthkit-data FieldList object
            plot_context: Context about the plot type
            x: x dimension ("auto" to infer, None to skip extraction, or variable name or array)
            y: y dimension ("auto" to infer, None to skip extraction, or variable name or array)
            z: z dimension ("auto" to infer, None to skip extraction, or variable name to select or array)
            crs: Coordinate Reference System ("auto" to infer, None for Cartesian, or explicit CRS)
            metadata: Optional user-provided metadata (takes precedence)

        Returns:
            DimensionSet or list of DimensionSets (for multi-field data)

        Raises:
            InvalidSpecificationError: If specifications are invalid
            MissingDimensionError: If required dimensions cannot be determined
        """
        # Track whether z was explicitly set to None (don't extract) vs "auto" (do extract)
        skip_z_extraction = z is None

        # For 1D plots, convert to xarray and use xarray extractor
        # But skip this for geographic 2D data with z=None (grid_points)
        if plot_context.is_1d and not (plot_context.is_geographic and skip_z_extraction):
            return self._extract_1d_via_xarray(data, plot_context, x, y, z, crs, metadata, regrid)

        # Convert "auto" to None for backward compatibility with existing logic
        if x == "auto":
            x = None
        if y == "auto":
            y = None
        if z == "auto":
            z = None

        # Handle CRS
        # Extract CRS for all geographic plots (both 1D and 2D)
        if crs == "auto" and plot_context.is_geographic:
            crs = self.extract_crs(data)

        # Store original data for metadata extraction
        original_data = data

        # Parse metadata
        user_metadata = metadata or {}
        global_metadata = user_metadata.copy()

        # For 2D plots, handle multi-field case
        if self._is_multi_field(data):
            return self._extract_multi_field_2d(data, plot_context, x, y, z, crs, original_data, global_metadata, regrid, skip_z_extraction)
        else:
            return self._extract_single_field_2d(data, plot_context, x, y, z, crs, original_data, global_metadata, regrid, skip_z_extraction)
    
    def extract_metadata(
        self,
        original_data: Any,
        key: str,
        dimension_name: Optional[str] = None,
    ) -> Any:
        """
        Extract metadata from earthkit-data objects.

        Args:
            original_data: The original earthkit-data FieldList
            key: The metadata key to look up
            dimension_name: Optional dimension name (unused for earthkit)

        Returns:
            Metadata value or None if not found
        """
        try:
            return original_data.metadata(key, default=None)
        except (AttributeError, NotImplementedError):
            return None

    def extract_datetime(self, original_data: Any) -> dict:
        """
        Extract datetime information from earthkit-data objects.

        Earthkit-data objects have a .datetime() method that returns
        datetime information directly.

        Args:
            original_data: The original earthkit-data FieldList

        Returns:
            Dictionary with 'base_time' and 'valid_time' keys
        """
        try:
            return original_data.datetime()
        except (AttributeError, NotImplementedError):
            return {"base_time": None, "valid_time": None}

    def extract_crs(self, original_data: Any) -> Optional[Any]:
        """
        Extract Coordinate Reference System from earthkit-data objects.

        Earthkit-data objects have a .projection().to_cartopy_crs() method
        that returns the CRS.

        Args:
            original_data: The original earthkit-data FieldList

        Returns:
            cartopy.crs.CRS object or None (PlateCarree as fallback)
        """
        try:
            return original_data.projection().to_cartopy_crs()
        except (AttributeError, NotImplementedError):
            # Default to PlateCarree for earthkit data
            import cartopy.crs as ccrs
            return ccrs.PlateCarree()        

    def _extract_1d_via_xarray(
        self,
        data: Any,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        crs: Optional[Any],
        user_metadata: dict,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Convert to xarray and use xarray extractor for 1D plots.

        Note: We keep the original earthkit data reference so that grid
        information can be extracted later.
        """
        # Store original earthkit data before conversion
        original_earthkit_data = data

        try:
            xr_data = data.to_xarray()
        except (AttributeError, NotImplementedError) as e:
            raise InvalidSpecificationError(
                f"Cannot convert earthkit-data to xarray for 1D plot: {e}"
            )

        # Import here to avoid circular dependency
        from earthkit.plots.sources.extractors.xarray import XarrayExtractor

        xr_extractor = XarrayExtractor()
        dimension_set = xr_extractor.extract_dimensions(
            xr_data, plot_context, x=x, y=y, z=z, crs=crs, metadata=user_metadata, regrid=regrid
        )

        # Override the original_data with earthkit data so grid detection works
        # Create a new DimensionSet with updated original_data
        from earthkit.plots.sources.core import DimensionSet
        return DimensionSet(
            x=dimension_set.x,
            y=dimension_set.y,
            z=dimension_set.z,
            plot_context=dimension_set.plot_context,
            crs=dimension_set.crs,
            grid=self.extract_grid(original_earthkit_data),  # Extract grid from earthkit data
            _original_data=original_earthkit_data,  # Use earthkit data, not xarray
            _extractor=self,  # Use earthkit extractor, not xarray
            _metadata=dimension_set._metadata,
            _regridded=dimension_set._regridded,
            _has_cyclic_point=dimension_set._has_cyclic_point,
        )
    
    def _is_multi_field(self, data: Any) -> bool:
        """Check if data contains multiple fields."""
        # Check if data is a sequence and has length > 1
        if hasattr(data, '__len__'):
            try:
                return len(data) > 1
            except (TypeError, NotImplementedError):
                pass
        return False
    
    def _extract_multi_field_2d(
        self,
        data: Any,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        crs: Optional[Any],
        original_data: Any,
        global_metadata: dict,
        regrid: str = "auto",
        skip_z_extraction: bool = False,
    ) -> List[DimensionSet]:
        """
        Extract dimensions for multi-field 2D data.

        Returns a list of DimensionSets, one per field.
        """
        dimension_sets = []

        # Extract x and y once (shared across all fields)
        x_values, y_values, is_latlon = self._extract_xy_coords(data, x, y)

        # Use appropriate names based on projection
        x_name = "longitude" if is_latlon else "x"
        y_name = "latitude" if is_latlon else "y"

        x_dim = self._create_dimension_from_coords(x_values, x_name, "X", original_data)
        y_dim = self._create_dimension_from_coords(y_values, y_name, "Y", original_data)

        # Extract z for each field
        for i, field in enumerate(data):
            if skip_z_extraction:
                # User explicitly passed z=None - don't extract z
                z_dim = None
            elif z is not None:
                # User specified z - select or use as-is
                if isinstance(z, str):
                    z_values = self._select_field(field, z)
                else:
                    z_values = np.asarray(z)
                z_dim = self._create_dimension_from_field(z_values, field, original_data)
            else:
                # Default: extract field values
                z_values = self._extract_field_values(field)
                z_dim = self._create_dimension_from_field(z_values, field, original_data)

            dim_set = self._create_dimension_set(
                x_dim, y_dim, z_dim, plot_context, crs, original_data, global_metadata, regrid=regrid
            )
            dimension_sets.append(dim_set)

        return dimension_sets

    def _extract_single_field_2d(
        self,
        data: Any,
        plot_context: PlotContext,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        crs: Optional[Any],
        original_data: Any,
        global_metadata: dict,
        regrid: str = "auto",
        skip_z_extraction: bool = False,
    ) -> DimensionSet:
        """Extract dimensions for single-field 2D data."""
        # Handle single-element list
        if hasattr(data, '__len__') and len(data) == 1:
            data = data[0]

        # Extract x and y coordinates
        x_values, y_values, is_latlon = self._extract_xy_coords(data, x, y)

        # Use appropriate names based on projection
        x_name = "longitude" if is_latlon else "x"
        y_name = "latitude" if is_latlon else "y"

        x_dim = self._create_dimension_from_coords(x_values, x_name, "X", original_data)
        y_dim = self._create_dimension_from_coords(y_values, y_name, "Y", original_data)

        # Extract z values
        if skip_z_extraction:
            # User explicitly passed z=None - don't extract z
            z_dim = None
        elif z is not None:
            if isinstance(z, str):
                z_values = self._select_field(data, z)
            else:
                z_values = np.asarray(z)
            z_dim = self._create_dimension_from_field(z_values, data, original_data)
        else:
            z_values = self._extract_field_values(data)
            z_dim = self._create_dimension_from_field(z_values, data, original_data)

        return self._create_dimension_set(
            x_dim, y_dim, z_dim, plot_context, crs, original_data, global_metadata, regrid=regrid
        )

    def _is_latlon_projection(self, data: Any) -> bool:
        """
        Check if data has a lat/lon projection.
        
        Returns:
            True if projection is lat/lon based, False otherwise
        """
        try:
            projection = data.projection()
            if hasattr(projection, 'PROJ_NAME'):
                proj_name = projection.PROJ_NAME.lower()
                # Common lat/lon projection names
                return proj_name in ['longlat', 'latlong', 'latlon', 'lonlat', 'eqc']
        except (AttributeError, NotImplementedError):
            pass
        
        # If we can't determine, assume False
        return False

    def _extract_xy_coords(
        self,
        data: Any,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract x and y coordinates from earthkit-data.
        
        Priority:
        1. User-specified x/y (as variable names or arrays)
        2. .to_points() method (returns {'x': ..., 'y': ...})
        3. .to_latlon() method (returns {'lon': ..., 'lat': ...})
        
        Returns:
            Tuple of (x_values, y_values)
        """
        # Check if this is a lat/lon projection
        is_latlon = self._is_latlon_projection(data)
        
        # Handle user-specified x
        if x is not None:
            if isinstance(x, str):
                x_values = self._select_field(data, x)
            else:
                x_values = np.asarray(x)
        else:
            x_values = None
        
        # Handle user-specified y
        if y is not None:
            if isinstance(y, str):
                y_values = self._select_field(data, y)
            else:
                y_values = np.asarray(y)
        else:
            y_values = None
        
        # If both specified, return them
        if x_values is not None and y_values is not None:
            return x_values, y_values, is_latlon
        
        # Try to_points() first
        try:
            points = data.to_points(flatten=False)
            if x_values is None:
                x_values = points.get('x')
            if y_values is None:
                y_values = points.get('y')
            
            if x_values is not None and y_values is not None:
                return x_values, y_values, is_latlon
        except (AttributeError, NotImplementedError):
            pass
        
        # Fallback to to_latlon()
        try:
            latlon = data.to_latlon(flatten=False)
            if x_values is None:
                x_values = latlon.get('lon')
            if y_values is None:
                y_values = latlon.get('lat')
            
            if x_values is not None and y_values is not None:
                # If we got coords from to_latlon, they are definitely lat/lon
                return x_values, y_values, True
        except (AttributeError, NotImplementedError):
            pass
        
        # If we still don't have both, raise error
        if x_values is None or y_values is None:
            raise MissingDimensionError(
                "Could not extract x/y coordinates from earthkit-data. "
                "Neither .to_points() nor .to_latlon() methods are available. "
                "Please specify x and y explicitly."
            )
        
        return x_values, y_values, is_latlon
    
    def _extract_field_values(self, field: Any) -> np.ndarray:
        """Extract values from a field using .to_numpy()."""
        try:
            return field.to_numpy(flatten=False)
        except (AttributeError, NotImplementedError) as e:
            raise InvalidSpecificationError(
                f"Could not extract field values: {e}"
            )
    
    def _select_field(self, data: Any, variable_name: str) -> np.ndarray:
        """
        Select a field by variable name, trying multiple keys.
        
        Tries: short_name, standard_name, long_name, name
        """
        for key in VARIABLE_KEYS:
            try:
                selected = data.sel(**{key: variable_name})
                if selected is not None:
                    return self._extract_field_values(selected)
            except (AttributeError, KeyError, NotImplementedError):
                continue
        
        raise InvalidSpecificationError(
            f"Could not find field with name '{variable_name}'. "
            f"Tried keys: {VARIABLE_KEYS}"
        )
    
    def _create_dimension_from_coords(
        self,
        values: np.ndarray,
        name: str,
        axis: str,
        original_data: Any,
    ) -> DimensionInfo:
        """Create DimensionInfo from coordinate values."""
        metadata = {
            'source_type': 'coordinates',
            'coord_name': name,
        }
        
        return DimensionInfo(
            name=name,
            _values=values,
            source=DimensionSource.COORDINATE,
            axis=axis,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )
    
    def _create_dimension_from_field(
        self,
        values: np.ndarray,
        field: Any,
        original_data: Any,
    ) -> DimensionInfo:
        """Create DimensionInfo from field values."""
        # Try to get field name from metadata
        field_name = "data"
        for key in VARIABLE_KEYS:
            try:
                field_name = field.metadata(key, default=None)
                if field_name is not None:
                    break
            except (AttributeError, NotImplementedError):
                continue
        
        metadata = {
            'source_type': 'field',
            'field_name': field_name,
        }
        
        # Try to extract units and other metadata
        try:
            units = field.metadata('units', default=None)
            long_name = field.metadata('long_name', default=None)
            standard_name = field.metadata('standard_name', default=None)
        except (AttributeError, NotImplementedError):
            units = None
            long_name = None
            standard_name = None
        
        return DimensionInfo(
            name=field_name or "data",
            _values=values,
            source=DimensionSource.VARIABLE,
            _source_units=units,
            long_name=long_name,
            standard_name=standard_name,
            _metadata=metadata,
            _original_data=original_data,
            _extractor=self,
        )