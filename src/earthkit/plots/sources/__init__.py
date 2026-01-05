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

import earthkit.data as ek_data
import numpy as np

from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.coordinates import CoordinateInfo
from earthkit.plots.sources.dimensions import DimensionInfo

# New architecture imports
from earthkit.plots.sources.extractors import (
    EarthkitExtractor,
    NumpyExtractor,
    XarrayExtractor,
)
from earthkit.plots.sources.metadata import MetadataResolver
from earthkit.plots.sources.protocols import DataExtractor


class Source:
    """
    Unified data source for plotting.

    Wraps different data types via extractors and provides a consistent
    interface for coordinate extraction, metadata access, and regridding.

    Parameters
    ----------
    data : Any
        The data object (numpy array, xarray DataArray/Dataset, earthkit data).
    x : str, np.ndarray, or None, optional
        X coordinate specification.
    y : str, np.ndarray, or None, optional
        Y coordinate specification.
    z : str, np.ndarray, or None, optional
        Z values specification.
    context : PlotContext, optional
        Plot context to guide coordinate inference.
        Defaults to CARTESIAN_2D.
    regrid : bool, optional
        Whether to apply regridding if data has special grid structure.
        Defaults to True.
    metadata : dict, optional
        User-provided metadata.
    units : str, optional
        Target units for data values. Behavior depends on context:
        - 1D cartesian: Tries to convert both x and y. If both fail, raises error.
        - 2D/geographic: Converts z (the data field).
        Dimension-specific units (x_units, y_units, z_units) take precedence.
    x_units : str, optional
        Target units for x dimension. Overrides 'units' for x.
    y_units : str, optional
        Target units for y dimension. Overrides 'units' for y.
    z_units : str, optional
        Target units for z dimension. Overrides 'units' for z.
    """

    def __init__(
        self,
        data: Any,
        *,
        x: Optional[Union[str, np.ndarray]] = None,
        y: Optional[Union[str, np.ndarray]] = None,
        z: Optional[Union[str, np.ndarray]] = None,
        context: PlotContext = PlotContext.CARTESIAN_2D,
        regrid: bool = True,
        metadata: Optional[dict] = None,
        units: Optional[str] = None,
        x_units: Optional[str] = None,
        y_units: Optional[str] = None,
        z_units: Optional[str] = None,
    ):
        self._extractor = _get_extractor(data, metadata)
        self._x_spec = x
        self._y_spec = y
        self._z_spec = z
        self._context = context
        self._should_regrid = regrid
        self._metadata_resolver = MetadataResolver(self._extractor, metadata)

        # Unit conversion tracking
        self._generic_units = (
            units  # Generic units - applied intelligently based on context
        )
        self._target_x_units = x_units  # Explicit x units
        self._target_y_units = y_units  # Explicit y units
        self._target_z_units = z_units  # Explicit z units

        # Track which conversions actually succeeded (populated during conversion)
        self._applied_x_units: Optional[str] = None
        self._applied_y_units: Optional[str] = None
        self._applied_z_units: Optional[str] = None

        # Lazy extraction flags
        self._coords_extracted = False
        self._x_coord_info: Optional[CoordinateInfo] = None
        self._y_coord_info: Optional[CoordinateInfo] = None
        self._z_coord_info: Optional[CoordinateInfo] = None

        # Cached DimensionInfo objects (created lazily)
        self._x_dimension: Optional[DimensionInfo] = None
        self._y_dimension: Optional[DimensionInfo] = None
        self._z_dimension: Optional[DimensionInfo] = None

        # Backward compatibility properties
        self._data = data  # For backward compatibility
        self.regrid = regrid  # For backward compatibility

    def _extract(self):
        """Lazy coordinate extraction with optional regridding."""
        if self._coords_extracted:
            return

        # Clear dimension cache
        self._x_dimension = None
        self._y_dimension = None
        self._z_dimension = None

        # Extract coordinates using extractor
        extracted = self._extractor.extract_coordinates(
            self._x_spec, self._y_spec, self._z_spec, self._context
        )

        # Store CoordinateInfo objects
        self._x_coord_info = extracted.x
        self._y_coord_info = extracted.y
        self._z_coord_info = extracted.z

        # Apply regridding if needed
        if self._should_regrid and self._z_coord_info is not None:
            gridspec = self._extractor.get_gridspec()
            if gridspec is not None:
                from earthkit.plots.sources.regrid import apply_regrid

                x, y, z = apply_regrid(
                    self._x_coord_info.values,
                    self._y_coord_info.values,
                    self._z_coord_info.values,
                    gridspec,
                    self._context,
                )
                # Update coordinate info with regridded values
                self._x_coord_info = CoordinateInfo(
                    values=x,
                    name=self._x_coord_info.name,
                    source_units=self._x_coord_info.source_units,
                    metadata=self._x_coord_info.metadata,
                )
                self._y_coord_info = CoordinateInfo(
                    values=y,
                    name=self._y_coord_info.name,
                    source_units=self._y_coord_info.source_units,
                    metadata=self._y_coord_info.metadata,
                )
                self._z_coord_info = CoordinateInfo(
                    values=z,
                    name=self._z_coord_info.name,
                    source_units=self._z_coord_info.source_units,
                    metadata=self._z_coord_info.metadata,
                )

        self._coords_extracted = True

    def _convert_values(
        self,
        values: np.ndarray,
        source_units: Optional[str],
        target_units: str,
        coord_name: str,
        silent: bool = False,
    ) -> tuple[np.ndarray, bool]:
        """
        Convert values from source units to target units.

        Parameters
        ----------
        values : np.ndarray
            Values to convert
        source_units : str or None
            Source units
        target_units : str
            Target units
        coord_name : str
            Name of coordinate for error messages ('x', 'y', or 'z')
        silent : bool, optional
            If True, don't emit warnings on failure (for smart unit detection).
            Defaults to False.

        Returns
        -------
        tuple[np.ndarray, bool]
            (converted_values, success) - Returns converted values and whether conversion succeeded.
            If conversion fails, returns original values with success=False.
        """
        if source_units is None:
            if not silent:
                import warnings

                warnings.warn(
                    f"Cannot convert {coord_name} values to {target_units}: "
                    f"source units not available. Returning original values.",
                    UserWarning,
                )
            return values, False

        if source_units == target_units:
            # No conversion needed - count as success
            return values, True

        try:
            from earthkit.plots.metadata import units as metadata_units

            converted = metadata_units.convert(values, source_units, target_units)
            return converted, True
        except Exception as e:
            if not silent:
                import warnings

                warnings.warn(
                    f"Unit conversion failed for {coord_name}: {source_units} -> {target_units}. "
                    f"Error: {e}. Returning original values.",
                    UserWarning,
                )
            return values, False

    @property
    def data(self):
        """Get the underlying data object (for backward compatibility)."""
        return self._data

    def _build_dimension(
        self,
        coord_name: str,
        coord_info: CoordinateInfo,
        target_units: Optional[str],
        cache_attr: str,
        silent: bool = True,
    ) -> DimensionInfo:
        """
        Build a DimensionInfo object with optional unit conversion.

        Parameters
        ----------
        coord_name : str
            Name of the coordinate ('x', 'y', or 'z').
        coord_info : CoordinateInfo
            The coordinate info to build from.
        target_units : str or None
            Target units for conversion.
        cache_attr : str
            Name of the cache attribute (e.g., '_x_dimension').
        silent : bool
            Whether to silently skip failed conversions.

        Returns
        -------
        DimensionInfo
            Built dimension with values, units, and metadata.
        """
        # Start with source values and units
        values = coord_info.values
        applied_units = coord_info.source_units

        # Attempt unit conversion if target_units specified
        if target_units is not None:
            # First try with source_units from coordinate
            source_units = coord_info.source_units
            # Fallback to generic source.units if coord source_units is None
            if source_units is None:
                source_units = self.source_units

            if source_units is not None:
                converted, success = self._convert_values(
                    values, source_units, target_units, coord_name, silent=silent
                )
                if success:
                    values = converted
                    applied_units = target_units

        # Build and cache DimensionInfo
        dimension = DimensionInfo(
            name=coord_info.name,
            values=values,
            source_units=coord_info.source_units,
            applied_units=applied_units,
            metadata_dict=coord_info.metadata,
        )
        setattr(self, cache_attr, dimension)
        return dimension

    @property
    def x(self) -> DimensionInfo:
        """
        Get x dimension information with metadata.

        Returns
        -------
        DimensionInfo
            X dimension with values, units, name, and metadata.
        """
        if self._x_dimension is not None:
            return self._x_dimension

        self._extract()

        # Determine target units with fallback
        target_units = self._target_x_units
        if target_units is None and self._generic_units is not None:
            # In 1D cartesian context, generic units applies to x (and y)
            if self._context == PlotContext.CARTESIAN_1D:
                target_units = self._generic_units

        return self._build_dimension(
            "x", self._x_coord_info, target_units, "_x_dimension", silent=True
        )

    @property
    def y(self) -> DimensionInfo:
        """
        Get y dimension information with metadata.

        Returns
        -------
        DimensionInfo
            Y dimension with values, units, name, and metadata.
        """
        if self._y_dimension is not None:
            return self._y_dimension

        self._extract()

        # Determine target units with fallback
        target_units = self._target_y_units
        if target_units is None and self._generic_units is not None:
            # In 1D cartesian context, generic units applies to y
            if self._context == PlotContext.CARTESIAN_1D:
                target_units = self._generic_units

        return self._build_dimension(
            "y", self._y_coord_info, target_units, "_y_dimension", silent=False
        )

    @property
    def z(self) -> Optional[DimensionInfo]:
        """
        Get z dimension information with metadata.

        Returns
        -------
        DimensionInfo or None
            Z dimension with values, units, name, and metadata.
            None for 1D plots.
        """
        if self._z_dimension is not None:
            return self._z_dimension

        self._extract()

        if self._z_coord_info is None:
            return None

        # Determine target units with fallback
        target_units = self._target_z_units
        if target_units is None and self._generic_units is not None:
            # In 2D and geographic contexts, z is the data field
            if self._context.is_2d:
                target_units = self._generic_units

        return self._build_dimension(
            "z", self._z_coord_info, target_units, "_z_dimension", silent=False
        )

    @property
    def u_values(self):
        """Get u-component values (for vector plots)."""
        # Not implemented in new architecture yet - return None for now
        return None

    @property
    def v_values(self):
        """Get v-component values (for vector plots)."""
        # Not implemented in new architecture yet - return None for now
        return None

    @property
    def magnitude(self):
        """Get magnitude of vector field (for backward compatibility)."""
        if self.u_values is not None and self.v_values is not None:
            return (self.u_values**2 + self.v_values**2) ** 0.5
        return None

    @property
    def crs(self):
        """Get coordinate reference system."""
        return self._extractor.get_crs()

    @property
    def gridspec(self):
        """Get grid specification."""
        return self._extractor.get_gridspec()

    def metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value.

        For xarray data, if key is a scalar coordinate name (like 'latitude' or 'longitude'),
        returns the scalar value instead of the attrs dict.

        Parameters
        ----------
        key : str
            Metadata key or coordinate name.
        default : Any
            Default value if not found.

        Returns
        -------
        Any
            Metadata value, scalar coordinate value, or default.
        """
        # For xarray, check if key is a scalar coordinate and return its value
        if self._extractor.__class__.__name__ == "XarrayExtractor":
            selected_da = getattr(self._extractor, "_selected_dataarray", None)
            da = selected_da if selected_da is not None else self._extractor.data

            if hasattr(da, "coords") and key in da.coords:
                coord = da.coords[key]
                # If coordinate is scalar (0-dimensional), return its value
                if coord.ndim == 0:
                    return coord.item()  # Extract scalar value

        # Otherwise, use metadata resolver
        return self._metadata_resolver.get(key, default)

    @property
    def units(self) -> Optional[str]:
        """
        Get units for the primary data dimension (context-dependent).

        For 1D cartesian: returns y units
        For 2D/geographic: returns z units

        Returns applied units if conversion occurred, otherwise source units.
        """
        if self._context == PlotContext.CARTESIAN_1D:
            return self.y.units
        else:
            if self.z is not None:
                return self.z.units
            return None

    @property
    def source_units(self) -> Optional[str]:
        """
        Get original source units before any conversion.

        Always returns units from the underlying data, regardless of target units.
        """
        return self._metadata_resolver.get_units()

    def datetime(self) -> dict:
        """
        Get datetime information from the data.

        Returns a dictionary with 'base_time' and 'valid_time' keys.
        Tries to extract time information from the underlying data object.

        Returns
        -------
        dict
            Dictionary with datetime information. Keys are 'base_time' and 'valid_time'.
            Values are datetime objects or None if not available.
        """
        # Try to get datetime from the underlying data if it's earthkit-data
        if hasattr(self._data, "datetime") and callable(self._data.datetime):
            return self._data.datetime()

        # Fallback: try to get time from metadata
        time = self.metadata("time")
        if time is not None:
            return {"base_time": time, "valid_time": time}

        return {"base_time": None, "valid_time": None}


def _get_extractor(data: Any, metadata: Optional[dict] = None) -> DataExtractor:
    """
    Factory to create appropriate extractor for data type.

    Parameters
    ----------
    data : Any
        Data object.
    metadata : dict, optional
        Metadata to pass to extractor.

    Returns
    -------
    DataExtractor
        Appropriate extractor for the data type.
    """
    # Check for xarray types
    if data.__class__.__name__ in ("DataArray", "Dataset"):
        return XarrayExtractor(data)

    # Check for earthkit types
    if isinstance(data, ek_data.core.Base):
        return EarthkitExtractor(data)

    # Default to numpy extractor (handles arrays, lists, etc.)
    return NumpyExtractor(data, metadata=metadata)


def get_source(
    *args,
    data=None,
    x=None,
    y=None,
    z=None,
    context=None,
    regrid=True,
    metadata=None,
    units=None,
    x_units=None,
    y_units=None,
    z_units=None,
    **kwargs,
):
    """
    Get a Source object from the given data.

    Parameters
    ----------
    *args
        Positional arguments. If provided, first arg is treated as data.
    data : numpy.ndarray, xarray.DataArray, earthkit.data.core.Base, optional
        The data to be plotted.
    x : numpy.ndarray or str, optional
        The x-coordinates of the data. If a string, it is assumed to be the name
        of the x-coordinate variable in data.
    y : numpy.ndarray or str, optional
        The y-coordinates of the data. If a string, it is assumed to be the name
        of the y-coordinate variable in data.
    z : numpy.ndarray or str, optional
        The z-coordinates of the data. If a string, it is assumed to be the name
        of the z-coordinate variable in data.
    context : PlotContext, optional
        Plot context to guide coordinate inference. If None, defaults to
        CARTESIAN_2D.
    regrid : bool, optional
        Whether to apply regridding if data has special grid structure.
        Defaults to True.
    metadata : dict, optional
        User-provided metadata.
    units : str, optional
        Target units for data values. Behavior depends on context:
        - 1D cartesian: Tries to convert both x and y. If both fail, raises error.
        - 2D/geographic: Converts z (the data field).
        Dimension-specific units (x_units, y_units, z_units) take precedence.
    x_units : str, optional
        Target units for x dimension. Overrides 'units' for x.
    y_units : str, optional
        Target units for y dimension. Overrides 'units' for y.
    z_units : str, optional
        Target units for z dimension. Overrides 'units' for z.
    **kwargs
        Additional metadata to merge with metadata dict.

    Returns
    -------
    Source
        Unified source object for plotting.
    """
    # Determine data object
    data_obj = data if data is not None else (args[0] if args else None)
    if isinstance(data_obj, ek_data.core.Base):
        if hasattr(data_obj, "__len__") and len(data_obj) == 1:
            data_obj = data_obj[0]

    if data_obj is None:
        # Check for 'c' parameter (matplotlib convention for color/data)
        c = kwargs.pop("c", None)
        if c is not None:
            data_obj = c
        elif isinstance(z, (np.ndarray, list)):
            data_obj = z
        else:
            raise ValueError("No data provided to get_source()")

    # Merge kwargs into metadata
    if metadata is None:
        metadata = {}
    metadata.update(kwargs)

    # Default context
    if context is None:
        context = PlotContext.CARTESIAN_2D

    # Create new unified Source
    return Source(
        data_obj,
        x=x,
        y=y,
        z=z,
        context=context,
        regrid=regrid,
        metadata=metadata,
        units=units,
        x_units=x_units,
        y_units=y_units,
        z_units=z_units,
    )
