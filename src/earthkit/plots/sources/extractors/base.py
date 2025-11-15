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
        metadata: Optional[dict] = None,
    ) -> DimensionSet:
        """
        Extract dimensions for plotting from the given data.

        Args:
            data: The data object to extract dimensions from
            plot_context: Context about the plot type being created
            x: User specification for x dimension ("auto" to infer, None to skip extraction)
            y: User specification for y dimension ("auto" to infer, None to skip extraction)
            z: User specification for z dimension ("auto" to infer, None to skip extraction)
            metadata: User-provided metadata (takes precedence over extracted metadata)

        Returns:
            DimensionSet containing validated x, y, and optionally z dimensions

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
            
            # Case 2: Gridded data (z is 2D, x and y are 1D)
            if z.values.ndim == 2:
                if x.values.ndim != 1 or y.values.ndim != 1:
                    raise IncompatibleDimensionsError(
                        f"For gridded 2D data, x and y must be 1D. "
                        f"Got x.ndim={x.values.ndim}, y.ndim={y.values.ndim}"
                    )
                
                z_shape = z.shape
                
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
            else:
                # z is not 1D or 2D
                raise IncompatibleDimensionsError(
                    f"For 2D plots, z must be either 1D (point data) or 2D (gridded data). "
                    f"Got z.ndim={z.values.ndim}"
                )
    
    def _create_dimension_set(
        self,
        x: DimensionInfo,
        y: DimensionInfo,
        z: Optional[DimensionInfo],
        plot_context: PlotContext,
        original_data: Any = None,
        user_metadata: Optional[dict] = None,
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
            original_data: Reference to original data object
            user_metadata: User-provided metadata (takes precedence)
        
        Returns:
            Validated DimensionSet
        
        Raises:
            IncompatibleDimensionsError: If dimensions are incompatible
        """
        # Validate compatibility
        self._validate_dimension_compatibility(x, y, z, plot_context)
        
        # Create and return (DimensionSet will validate again in __post_init__)
        return DimensionSet(
            x=x,
            y=y,
            z=z,
            plot_context=plot_context,
            _original_data=original_data,
            _extractor=self,
            _metadata=user_metadata or {},
        )