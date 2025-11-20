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

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union
import numpy as np


class PlotType(Enum):
    """Types of plots with different extraction requirements."""
    CARTESIAN_1D = "cartesian_1d"
    CARTESIAN_2D = "cartesian_2d"
    GEOGRAPHIC_1D = "geographic_1d"
    GEOGRAPHIC_2D = "geographic_2d"


class DimensionSource(Enum):
    """A record of how a dimension was determined."""
    # Explicitly provided by user
    USER_SPECIFIED = "user_specified"
    
    # Extracted from data dimension (xarray, pandas index)
    DIMENSION = "dimension"

    # Extracted from data variable (xarray variable, pandas column)
    VARIABLE = "variable"

    # Extracted from coordinate array
    COORDINATE = "coordinate"

    # Generated (index) array
    GENERATED = "generated"
    
    # Inferred from metadata/conventions
    INFERRED = "inferred"

@dataclass
class DimensionInfo:
    """
    Rich container for a single dimension's data and metadata.

    This object bundles together the array data with all relevant metadata,
    allowing downstream code to use this information for labeling, unit
    conversion, validation, etc.

    Attributes:
        name: The name/identifier for this dimension (e.g., 'time', 'latitude')
        values: The actual data array (numpy array or compatible)
        source: How this dimension was determined (user, inferred, generated, etc.)
        units: Physical units - returns target units if conversion occurred, otherwise source units
        source_units: Original units before any conversion
        long_name: Human-readable description
        standard_name: CF standard name if applicable
        axis: Axis type ('X', 'Y', 'Z', 'T') if applicable
        _metadata: Internal metadata storage (use .metadata() method to access)
        _original_data: Reference to original data object for fallback lookups
        _extractor: Reference to extractor for data-type-specific metadata extraction
    """
    name: str
    _values: np.ndarray
    source: DimensionSource
    _source_units: Optional[str] = None
    long_name: Optional[str] = None
    standard_name: Optional[str] = None
    axis: Optional[str] = None  # 'X', 'Y', 'Z', 'T'
    _metadata: dict = field(default_factory=dict, repr=False)
    _original_data: Any = field(default=None, repr=False)
    _extractor: Optional['DataExtractor'] = field(default=None, repr=False)
    _target_units: Optional[str] = field(default=None, repr=False, init=False)
    _converted_values: Optional[np.ndarray] = field(default=None, repr=False, init=False)

    def __post_init__(self):
        """Validate and normalize the values array."""
        if not isinstance(self._values, np.ndarray):
            self._values = np.asarray(self._values)
        self._target_units = None
        self._converted_values = None

    @property
    def values(self) -> np.ndarray:
        """
        Get dimension values, with automatic unit conversion if target units are set.

        This property supports lazy unit conversion with caching for performance.
        If _target_units is set and differs from source units, values are
        automatically converted and cached.

        Returns
        -------
        np.ndarray
            The values array, potentially with unit conversion applied.

        Examples
        --------
        >>> dim = DimensionInfo("temperature", _values=np.array([273.15, 300]), units="K")
        >>> dim.values  # No conversion
        array([273.15, 300.])
        >>> dim.set_target_units("celsius")
        >>> dim.values  # Automatic conversion
        array([0., 26.85])
        """
        # No conversion needed
        if self._target_units is None or self._target_units == self._source_units:
            return self._values

        # Check if we have a valid cached conversion
        if self._converted_values is not None:
            return self._converted_values

        # Perform conversion and cache
        if self._source_units is None:
            # Can't convert without source units
            return self._values

        try:
            from earthkit.plots.metadata import units as metadata_units
            self._converted_values = metadata_units.convert(
                self._values, self._source_units, self._target_units
            )
            return self._converted_values
        except Exception as e:
            # If conversion fails, warn and return original values
            import warnings
            warnings.warn(
                f"Unit conversion failed: {self._source_units} -> {self._target_units}. "
                f"Error: {e}. Returning original values.",
                UserWarning
            )
            return self._values

    def set_target_units(self, target_units: Optional[str]) -> None:
        """
        Set the target units for this dimension.

        This sets the units that the .values property will convert to.
        Calling this clears any cached converted values if the target changes.

        Parameters
        ----------
        target_units : str or None
            Target units for conversion, or None to clear.

        Examples
        --------
        >>> dim.set_target_units("celsius")
        >>> converted = dim.values  # Automatically converts from K to celsius
        """
        if target_units != self._target_units:
            self._target_units = target_units
            self._converted_values = None  # Clear cache

    @property
    def units(self) -> Optional[str]:
        """
        Get the current units for this dimension.

        Returns target units if conversion was requested, otherwise source units.

        Returns
        -------
        str or None
            The units string, or None if no units are defined.
        """
        if self._target_units is not None:
            return self._target_units
        return self._source_units

    @property
    def source_units(self) -> Optional[str]:
        """
        Get the original source units before any conversion.

        Returns
        -------
        str or None
            The original units string, or None if no units are defined.
        """
        return self._source_units

    @property
    def size(self) -> int:
        """Return the size of the dimension."""
        return self._values.size

    @property
    def shape(self) -> tuple:
        """Return the shape of the dimension."""
        return self._values.shape
    
    def metadata(self, key: str) -> Any:
        """
        Get metadata value with fallback to extractor.

        Special handling for "units" key: returns converted units if conversion occurred.

        Precedence:
        1. Special handling for "units" key (returns .units property)
        2. Local _metadata dict (dimension-specific attrs)
        3. Extractor's extract_metadata() method (for data-type-specific lookups)
        4. None if not found

        Args:
            key: Metadata key to look up

        Returns:
            Metadata value or None if not found
        """
        # Special handling for units - return converted units if available
        if key == "units":
            return self.units

        # Check local metadata first
        if key in self._metadata:
            return self._metadata[key]

        # Fall back to extractor if available
        if self._extractor and self._original_data is not None:
            return self._extractor.extract_metadata(
                self._original_data, key, dimension_name=self.name
            )

        return None
    
    def __repr__(self) -> str:
        """Readable representation."""
        return (
            f"DimensionInfo(name='{self.name}', "
            f"source={self.source.value}, "
            f"shape={self.shape}, "
            f"units={self.units})"
        )


@dataclass
class PlotContext:
    plot_type: PlotType
    crs: Optional[str] = None
    
    @property
    def is_geographic(self) -> bool:
        """Check if the plot type is geographic."""
        return self.plot_type in {PlotType.GEOGRAPHIC_1D, PlotType.GEOGRAPHIC_2D}

    @property
    def is_cartesian(self) -> bool:
        """Check if the plot type is cartesian."""
        return self.plot_type in {PlotType.CARTESIAN_1D, PlotType.CARTESIAN_2D}

    @property
    def is_1d(self) -> bool:
        """Check if the plot type is 1D."""
        return self.plot_type in {PlotType.CARTESIAN_1D, PlotType.GEOGRAPHIC_1D}
    
    @property
    def is_2d(self) -> bool:
        """Check if the plot type is 2D."""
        return self.plot_type in {PlotType.CARTESIAN_2D, PlotType.GEOGRAPHIC_2D}
    
    @property
    def requires_z(self) -> bool:
        """Check if the plot type requires a Z dimension."""
        return self.is_2d

@dataclass
class DimensionSet:
    """
    Container for a complete set of dimensions for plotting.

    This represents a validated set of x, y, and optionally z dimensions
    that are ready to be used for visualization.

    Attributes:
        x: The x-axis dimension
        y: The y-axis dimension
        z: The z-axis dimension (optional, for 2D plots)
        plot_context: The plot context this set was created for
        crs: Coordinate Reference System (cartopy CRS) for geographic data, None for Cartesian
        grid: Grid identifier for specialized grids (HEALPix, Octahedral, etc.), None for regular grids
        _metadata: Global metadata (use .metadata() method to access)
        _original_data: Reference to original data object
        _extractor: Reference to extractor for data-type-specific metadata extraction
        _regridded: Flag indicating whether the data was regridded (True only if regridding occurred)
        _has_cyclic_point: Flag indicating whether a cyclic point has been added (True only if cyclic point was added)
    """
    x: DimensionInfo
    y: DimensionInfo
    z: Optional[DimensionInfo] = None
    plot_context: Optional[PlotContext] = None
    crs: Optional[Any] = None  # cartopy.crs.CRS or None
    grid: Optional[Any] = None  # GridIdentifier or None
    _metadata: dict = field(default_factory=dict, repr=False)
    _original_data: Any = field(default=None, repr=False)
    _extractor: Optional['DataExtractor'] = field(default=None, repr=False)
    _regridded: bool = field(default=False, repr=False)
    _has_cyclic_point: bool = field(default=False, repr=False)
    
    def validate(self) -> None:
        """
        Validate that this dimension set is internally consistent.
        
        Raises:
            ValueError: If dimensions are incompatible or missing required dimensions
        """
        # Check that we have required dimensions
        if self.plot_context and self.plot_context.requires_z and self.z is None:
            raise ValueError(
                f"Plot type {self.plot_context.plot_type.value} requires a z dimension"
            )
    
    def __post_init__(self):
        """Automatically validate after initialization."""
        self.validate()
    
    def metadata(self, key: str) -> Any:
        """
        Get global metadata value with fallback to extractor.
        
        Precedence:
        1. User-provided _metadata dict (highest priority)
        2. Extractor's extract_metadata() method (for data-type-specific lookups)
        3. None if not found
        
        Args:
            key: Metadata key to look up
        
        Returns:
            Metadata value or None if not found
        """
        # Check local metadata first (user-provided has precedence)
        if key in self._metadata:
            return self._metadata[key]
        
        # Fall back to extractor if available
        if self._extractor and self._original_data is not None:
            return self._extractor.extract_metadata(self._original_data, key)
        
        return None
    
    def to_dict(self) -> dict[str, np.ndarray]:
        """
        Convert to a simple dictionary of arrays.
        
        Useful for passing to matplotlib or other plotting libraries
        that just need the raw data.
        
        Returns:
            Dictionary with keys 'x', 'y', and optionally 'z'
        """
        result = {'x': self.x.values, 'y': self.y.values}
        if self.z is not None:
            result['z'] = self.z.values
        return result
    
    def get_labels(self) -> dict[str, str]:
        """
        Get suggested axis labels based on metadata.
        
        Returns:
            Dictionary with keys 'x', 'y', and optionally 'z' containing
            formatted label strings including units if available.
        """
        labels = {}
        
        for axis_name, dim_info in [('x', self.x), ('y', self.y), ('z', self.z)]:
            if dim_info is None:
                continue
            
            # Prefer long_name, fall back to name
            label = dim_info.long_name or dim_info.name
            
            # Add units if available
            if dim_info.units:
                label = f"{label} [{dim_info.units}]"
            
            labels[axis_name] = label
        
        return labels
    
    @property
    def primary_dimension(self) -> DimensionInfo:
        """
        Get the primary dimension for plotting.
        
        For 1D plots, this is the dimension corresponding to the variable being plotted.
        For 2D plots, this is the z dimension.
        
        Returns:
            The primary DimensionInfo object
        """
        if self.plot_context and self.plot_context.is_1d:
            if self.x.source == DimensionSource.VARIABLE:
                return self.x
            return self.y
        elif self.plot_context and self.plot_context.is_2d:
            return self.z
        else:
            raise ValueError("Plot context is not defined or invalid")
    
    def datetime(self) -> dict:
        """
        Get datetime information from the data.

        Returns a dictionary with 'base_time' and 'valid_time' keys.
        Delegates to the extractor if available, otherwise tries to
        extract from metadata.

        Returns:
            dict: Dictionary with datetime information
        """
        if self._extractor and self._original_data is not None:
            return self._extractor.extract_datetime(self._original_data)

        # Fallback: try to get time from metadata
        time = self.metadata("time")
        if time is not None:
            return {"base_time": time, "valid_time": time}

        return {"base_time": None, "valid_time": None}

    def __repr__(self) -> str:
        """Readable representation."""
        parts = [f"DimensionSet(x={self.x.name}, y={self.y.name}"]
        if self.z is not None:
            parts.append(f", z={self.z.name}")
        return "".join(parts) + ")"

# Convenience function for creating index dimensions
def create_index_dimension(
    size: int,
    name: str = "index",
    axis: Optional[str] = None,
    original_data: Any = None,
    extractor: Optional['DataExtractor'] = None,
) -> DimensionInfo:
    """
    Create a generated index dimension (0, 1, 2, ..., size-1).
    
    Args:
        size: The size of the index array
        name: Name for the dimension (default: 'index')
        axis: Axis type ('X' or 'Y') if applicable
        original_data: Reference to original data object
        extractor: Reference to extractor
    
    Returns:
        DimensionInfo representing the index array
    """
    return DimensionInfo(
        name=name,
        _values=np.arange(size),
        source=DimensionSource.GENERATED,
        axis=axis,
        _original_data=original_data,
        _extractor=extractor,
    )