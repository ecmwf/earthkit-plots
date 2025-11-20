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


from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np

from earthkit.plots.sources.core import DimensionSet, DimensionInfo, PlotContext, DimensionSource, create_index_dimension
from earthkit.plots.sources.extractors.exceptions import InvalidSpecificationError, IncompatibleDimensionsError


class DataExtractor(ABC):
    """
    Abstract base class for data-type-specific dimension extractors.
    
    Each data type (numpy, xarray, pandas, etc.) implements this interface
    to provide extraction logic appropriate for that type's structure and
    conventions.
    
    The extraction process follows this pattern:
    1. Check if all required dimensions are user-specified (early exit)
    2. Infer defaults for missing dimensions based on data structure
    3. Apply user overrides with context-aware resolution
    4. Validate and return DimensionSet
    """
    
    @abstractmethod
    def extract_dimensions(
        self,
        data: Any,
        plot_context: PlotContext,
        x: Optional[Any] = "auto",
        y: Optional[Any] = "auto",
        z: Optional[Any] = "auto",
        crs: Optional[Any] = "auto",
        metadata: Optional[dict] = None,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Extract dimensions for plotting from the given data.

        Args:
            data: The data object to extract dimensions from
            plot_context: Context about the plot type being created
            x: User specification for x dimension ("auto" to infer, None to skip extraction)
            y: User specification for y dimension ("auto" to infer, None to skip extraction)
            z: User specification for z dimension ("auto" to infer, None to skip extraction)
            crs: Coordinate Reference System ("auto" to infer from data, None for Cartesian,
                 or explicit cartopy.crs.CRS object)
            metadata: User-provided metadata (takes precedence over extracted metadata)
            regrid: Regrid parameter ("auto" to enable automatic regridding for irregular grids)

        Returns:
            DimensionSet containing validated x, y, and optionally z dimensions, and CRS

        Raises:
            MissingDimensionError: Cannot determine required dimensions
            AmbiguousDimensionError: Multiple valid options, need user input
            InvalidSpecificationError: User specification is invalid
            IncompatibleDimensionsError: Dimensions don't match plot requirements
        """
        pass
    
    def extract_metadata(
        self,
        original_data: Any,
        key: str,
        dimension_name: Optional[str] = None,
    ) -> Any:
        """
        Extract metadata from the original data object.

        This provides a fallback mechanism for accessing metadata that wasn't
        captured during initial dimension extraction. Subclasses should override
        this to provide data-type-specific metadata extraction.

        Args:
            original_data: The original data object
            key: The metadata key to look up
            dimension_name: Optional dimension/variable/coordinate name for
                           dimension-specific metadata lookup

        Returns:
            Metadata value or None if not found
        """
        return None

    def extract_datetime(self, original_data: Any) -> dict:
        """
        Extract datetime information from the original data object.

        Subclasses should override this to provide data-type-specific
        datetime extraction. The returned dictionary should contain
        'base_time' and 'valid_time' keys.

        Args:
            original_data: The original data object

        Returns:
            Dictionary with 'base_time' and 'valid_time' keys (values can be None)
        """
        return {"base_time": None, "valid_time": None}

    def extract_crs(self, original_data: Any) -> Optional[Any]:
        """
        Extract Coordinate Reference System from the original data object.

        Subclasses should override this to provide data-type-specific
        CRS extraction. The returned value should be a cartopy CRS object
        or None if no CRS can be determined.

        Args:
            original_data: The original data object

        Returns:
            cartopy.crs.CRS object or None if no CRS found
        """
        return None
    
    def extract_grid(self, original_data: Any) -> Optional[Any]:
        """
        Extract grid information from earthkit-data objects.

        Earthkit-data objects may have a .grid() method that returns
        grid information.

        Args:
            original_data: The original earthkit-data FieldList

        Returns:
            Grid information or None if not available
        """
        from earthkit.plots.sources.extractors.regrid import GridIdentifier
        return GridIdentifier.from_data(original_data)
    
    def _all_specified(
        self,
        plot_context: PlotContext,
        x: Optional[Any],
        y: Optional[Any],
        z: Optional[Any],
    ) -> bool:
        """
        Check if all required dimensions have been specified by the user.
        
        Args:
            plot_context: The plot context to check requirements against
            x: User specification for x
            y: User specification for y
            z: User specification for z
        
        Returns:
            True if all required dimensions are specified, False otherwise
        """
        # 1D plots need x and y
        if plot_context.is_1d:
            return x is not None and y is not None
        
        # 2D plots need x, y, and z
        if plot_context.is_2d:
            return x is not None and y is not None and z is not None
        
        return False
    
    def _validate_dimension_compatibility(
        self,
        x: DimensionInfo,
        y: DimensionInfo,
        z: Optional[DimensionInfo],
        plot_context: PlotContext,
    ) -> None:
        """
        Validate that dimensions are compatible with each other and the plot type.
        
        This is a helper method that can be called by extractors to perform
        common validation checks.
        
        Handles both:
        - Regular 2D grids (z is 2D, x and y are 1D matching z dimensions)
        - Point data (x, y, z are all 1D with same size)
        
        Args:
            x: X dimension info
            y: Y dimension info
            z: Z dimension info (optional)
            plot_context: The plot context
        
        Raises:
            IncompatibleDimensionsError: If dimensions are incompatible
        """
        # Check that 2D plots have z
        if plot_context.requires_z and z is None:
            raise IncompatibleDimensionsError(
                f"Plot type {plot_context.plot_type.value} requires a z dimension"
            )
        
        # For 1D plots, x and y should have compatible sizes
        if plot_context.is_1d:
            if x.size != y.size:
                raise IncompatibleDimensionsError(
                    f"For 1D plots, x and y must have the same size. "
                    f"Got x.size={x.size}, y.size={y.size}"
                )
        
        # For 2D plots, check compatibility
        if z is not None:
            # Case 1: Point data (all 1D with same size)
            if x.values.ndim == 1 and y.values.ndim == 1 and z.values.ndim == 1:
                if x.size == y.size == z.size:
                    # Valid point data
                    return
                else:
                    raise IncompatibleDimensionsError(
                        f"For point data (1D), x, y, and z must have the same size. "
                        f"Got x.size={x.size}, y.size={y.size}, z.size={z.size}"
                    )
            
            # Case 2: Gridded data (z is 2D)
            if z.values.ndim == 2:
                z_shape = z.shape

                # Sub-case 2a: 2D meshgrids (x, y, z all have same 2D shape)
                if x.values.ndim == 2 and y.values.ndim == 2:
                    if x.shape == y.shape == z_shape:
                        # Valid 2D meshgrid
                        return
                    else:
                        raise IncompatibleDimensionsError(
                            f"For 2D meshgrid data, x, y, and z must have the same shape. "
                            f"Got x.shape={x.shape}, y.shape={y.shape}, z.shape={z_shape}"
                        )

                # Sub-case 2b: 1D coordinates (x and y are 1D arrays)
                if x.values.ndim == 1 and y.values.ndim == 1:
                    # x should match one dimension of z
                    if x.size not in (z_shape[0], z_shape[1]):
                        raise IncompatibleDimensionsError(
                            f"X dimension size {x.size} doesn't match either dimension of Z shape {z_shape}"
                        )

                    # y should match one dimension of z
                    if y.size not in (z_shape[0], z_shape[1]):
                        raise IncompatibleDimensionsError(
                            f"Y dimension size {y.size} doesn't match either dimension of Z shape {z_shape}"
                        )

                    # x and y should match different dimensions of z (unless square)
                    if x.size == y.size == z_shape[0] == z_shape[1]:
                        # Special case: square matrix, can't validate further
                        pass
                    elif (x.size == z_shape[0] and y.size == z_shape[0]) or \
                        (x.size == z_shape[1] and y.size == z_shape[1]):
                        raise IncompatibleDimensionsError(
                            f"X and Y both match the same dimension of Z. "
                            f"x.size={x.size}, y.size={y.size}, z.shape={z_shape}"
                        )
                    # Valid 1D coordinate arrays
                    return

                # Mixed dimensionality (one 1D, one 2D) is not valid
                raise IncompatibleDimensionsError(
                    f"For gridded 2D data, x and y must both be 1D (coordinates) or both be 2D (meshgrids). "
                    f"Got x.ndim={x.values.ndim}, y.ndim={y.values.ndim}"
                )
            else:
                # z is not 1D or 2D
                raise IncompatibleDimensionsError(
                    f"For 2D plots, z must be either 1D (point data) or 2D (gridded data). "
                    f"Got z.ndim={z.values.ndim}"
                )
    
    def _apply_regridding(
        self,
        x: DimensionInfo,
        y: DimensionInfo,
        z: Optional[DimensionInfo],
        plot_context: PlotContext,
        original_data: Any,
        regrid: str = "auto",
    ) -> tuple[DimensionInfo, DimensionInfo, Optional[DimensionInfo], bool]:
        """
        Apply regridding if needed and return updated dimensions.

        This helper method checks if regridding should be applied based on:
        - regrid parameter ("auto" or other values)
        - plot type (only geographic plots)
        - presence of a grid identifier

        Args:
            x: X dimension info
            y: Y dimension info
            z: Z dimension info (optional)
            plot_context: The plot context
            original_data: Reference to original data object
            regrid: Regrid parameter ("auto" or explicit value)

        Returns:
            Tuple of (x, y, z, regridded_flag) where regridded_flag is True
            if regridding was actually performed

        Raises:
            ImportError: If regridding is needed but earthkit-regrid is not installed
        """
        # Only regrid if regrid="auto"/True and plot is geographic
        # Accept both "auto" string and True boolean for backwards compatibility
        should_regrid = (regrid == "auto" or regrid is True) and plot_context.is_geographic
        if not should_regrid:
            return x, y, z, False

        # Try to extract grid information
        grid_identifier = self.extract_grid(original_data)

        # If no grid found, no regridding needed
        if grid_identifier is None:
            return x, y, z, False

        # Regridding is needed - call auto_regrid on the grid identifier
        import numpy as np

        x_values = x.values
        y_values = y.values
        z_values = z.values if z is not None else None

        # Only regrid if we have z values (2D geographic plots)
        if z_values is None:
            return x, y, z, False

        # Call auto_regrid to get new coordinates and values
        x_new, y_new, z_new = grid_identifier.auto_regrid(x_values, y_values, z_values)

        # Create new DimensionInfo objects with regridded values
        x_regridded = DimensionInfo(
            name=x.name,
            _values=x_new,
            source=x.source,
            _source_units=x.source_units,
            long_name=x.long_name,
            standard_name=x.standard_name,
            axis=x.axis,
            _metadata=x._metadata,
            _original_data=original_data,
            _extractor=self,
        )

        y_regridded = DimensionInfo(
            name=y.name,
            _values=y_new,
            source=y.source,
            _source_units=y.source_units,
            long_name=y.long_name,
            standard_name=y.standard_name,
            axis=y.axis,
            _metadata=y._metadata,
            _original_data=original_data,
            _extractor=self,
        )

        z_regridded = DimensionInfo(
            name=z.name,
            _values=z_new,
            source=z.source,
            _source_units=z.source_units,
            long_name=z.long_name,
            standard_name=z.standard_name,
            axis=z.axis,
            _metadata=z._metadata,
            _original_data=original_data,
            _extractor=self,
        )

        return x_regridded, y_regridded, z_regridded, True

    def _add_cyclic_point(
        self,
        x: DimensionInfo,
        y: DimensionInfo,
        z: Optional[DimensionInfo],
        plot_context: PlotContext,
    ) -> tuple[DimensionInfo, DimensionInfo, Optional[DimensionInfo], bool]:
        """
        Add a cyclic point to global geographic data if needed.

        Cyclic points are extra columns added to global grids to ensure proper
        wrapping in contour plots. This method checks if the data is:
        - Geographic (on a lat/lon grid)
        - Global in longitude (spans approximately 0-360 degrees)
        - Missing a cyclic point (doesn't already wrap around)

        Args:
            x: X dimension info
            y: Y dimension info
            z: Z dimension info (optional)
            plot_context: The plot context

        Returns:
            Tuple of (x, y, z, has_cyclic_point_flag) where has_cyclic_point_flag
            is True if a cyclic point was added

        Notes:
            This uses cartopy's add_cyclic_point() function with a fallback to
            manual addition if the function fails due to floating point precision
            issues (common with regridded data using np.linspace).
        """
        # Only add cyclic points for geographic 2D plots with z data
        if not plot_context.is_geographic or not plot_context.is_2d or z is None:
            return x, y, z, False

        x_values = x.values
        y_values = y.values
        z_values = z.values

        # Check if data needs a cyclic point
        # Data needs a cyclic point if it's on a regular lat/lon grid
        # that spans roughly 0-360 degrees but doesn't already wrap
        if not self._needs_cyclic_point(x_values, y_values, z_values):
            return x, y, z, False

        # Handle 2D coordinate arrays
        n_x = None
        if len(x_values.shape) != 1:
            n_x = x_values.shape[0]
            x_values = x_values[0]

        # Try to add cyclic points using cartopy's function
        # If it fails (e.g., due to floating point precision issues with regridded data),
        # manually add the cyclic point
        try:
            from cartopy.util import add_cyclic_point as cartopy_add_cyclic
            z_values, x_values = cartopy_add_cyclic(z_values, coord=x_values)
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

        # Create new DimensionInfo objects with cyclic point added
        x_with_cyclic = DimensionInfo(
            name=x.name,
            _values=x_values,
            source=x.source,
            _source_units=x.source_units,
            long_name=x.long_name,
            standard_name=x.standard_name,
            axis=x.axis,
            _metadata=x._metadata,
            _original_data=x._original_data,
            _extractor=self,
        )

        y_with_cyclic = DimensionInfo(
            name=y.name,
            _values=y_values,
            source=y.source,
            _source_units=y.source_units,
            long_name=y.long_name,
            standard_name=y.standard_name,
            axis=y.axis,
            _metadata=y._metadata,
            _original_data=y._original_data,
            _extractor=self,
        )

        z_with_cyclic = DimensionInfo(
            name=z.name,
            _values=z_values,
            source=z.source,
            _source_units=z.source_units,
            long_name=z.long_name,
            standard_name=z.standard_name,
            axis=z.axis,
            _metadata=z._metadata,
            _original_data=z._original_data,
            _extractor=self,
        )

        return x_with_cyclic, y_with_cyclic, z_with_cyclic, True

    def _needs_cyclic_point(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray,
        z_values: np.ndarray,
    ) -> bool:
        """
        Check if data needs a cyclic point.

        Data needs a cyclic point if:
        - x coordinates are 1D or 2D
        - z values are 2D
        - x coordinates span roughly 0-360 degrees (global in longitude)
        - Data doesn't already have a cyclic point (first and last columns differ)

        Args:
            x_values: X coordinate values
            y_values: Y coordinate values
            z_values: Z data values

        Returns:
            True if cyclic point should be added, False otherwise
        """
        # Only for 2D z data
        if z_values.ndim != 2:
            return False

        # Get 1D x coordinate array
        if x_values.ndim == 2:
            x_1d = x_values[0]
        else:
            x_1d = x_values

        # Check if x is 1D after extraction
        if x_1d.ndim != 1:
            return False

        # Check if x spans roughly 0-360 degrees (global grid)
        # Allow some tolerance for floating point precision
        x_min = x_1d.min()
        x_max = x_1d.max()
        x_range = x_max - x_min

        # Check if it's a global grid (spans close to 360 degrees)
        # Typical range: 0 to 359.x or -180 to 179.x
        is_global = (
            (abs(x_range - 360.0) < 10.0)  # Close to 360 degree span
            or (abs(x_min) < 10.0 and abs(x_max - 360.0) < 10.0)  # 0 to ~360
            or (abs(x_min + 180.0) < 10.0 and abs(x_max - 180.0) < 10.0)  # -180 to ~180
        )

        if not is_global:
            return False

        # Check if data already has a cyclic point (first and last columns are the same)
        # Compare first and last columns of z
        first_col = z_values[:, 0]
        last_col = z_values[:, -1]

        # If they're very close, we already have a cyclic point
        already_cyclic = np.allclose(first_col, last_col, rtol=1e-5, atol=1e-8, equal_nan=True)

        return not already_cyclic

    def _create_dimension_set(
        self,
        x: DimensionInfo,
        y: DimensionInfo,
        z: Optional[DimensionInfo],
        plot_context: PlotContext,
        crs: Optional[Any] = None,
        original_data: Any = None,
        user_metadata: Optional[dict] = None,
        regrid: str = "auto",
    ) -> DimensionSet:
        """
        Create and validate a DimensionSet.

        This helper method performs validation and constructs the final
        DimensionSet object with proper metadata and references.

        Args:
            x: X dimension info
            y: Y dimension info
            z: Z dimension info (optional)
            plot_context: The plot context
            crs: Coordinate Reference System (cartopy CRS or None)
            original_data: Reference to original data object
            user_metadata: User-provided metadata (takes precedence)
            regrid: Regrid parameter ("auto" to enable automatic regridding)

        Returns:
            Validated DimensionSet

        Raises:
            IncompatibleDimensionsError: If dimensions are incompatible
        """
        # Apply regridding if needed
        x, y, z, regridded = self._apply_regridding(
            x, y, z, plot_context, original_data, regrid
        )

        # If regridding occurred, update CRS to PlateCarree (regular lat-lon)
        if regridded:
            import cartopy.crs as ccrs
            crs = ccrs.PlateCarree()

        # Add cyclic point if needed (after regridding, before validation)
        x, y, z, has_cyclic_point = self._add_cyclic_point(
            x, y, z, plot_context
        )

        # Validate compatibility
        self._validate_dimension_compatibility(x, y, z, plot_context)

        # Extract grid information if available
        grid = self.extract_grid(original_data) if original_data is not None else None

        # Create and return (DimensionSet will validate again in __post_init__)
        return DimensionSet(
            x=x,
            y=y,
            z=z,
            plot_context=plot_context,
            crs=crs,
            grid=grid,
            _original_data=original_data,
            _extractor=self,
            _metadata=user_metadata or {},
            _regridded=regridded,
            _has_cyclic_point=has_cyclic_point,
        )