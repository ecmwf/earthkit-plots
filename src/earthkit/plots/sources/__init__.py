# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

from typing import Any

import numpy as np

from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.coordinates import CoordinateInfo
from earthkit.plots.sources.dimensions import DimensionInfo
from earthkit.plots.sources.extractors.numpy import NumpyExtractor
from earthkit.plots.sources.metadata import MetadataResolver
from earthkit.plots.sources.protocols import DataExtractor


def _parse_date_time_ints(date_val, time_val=None):
    """
    Parse ECMWF-style integer date and time into a datetime object.

    date_val : int or str like 20150101
    time_val : int or str like 0, 600, 1200 (HHMM or H)
    """
    import datetime

    try:
        date_str = str(int(date_val))
        if len(date_str) != 8:
            return None
        year, month, day = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
        hour, minute = 0, 0
        if time_val is not None:
            # time is HHMM (e.g. 1200) or just H (e.g. 0, 6, 12)
            t = int(time_val)
            if t < 100:
                # treat as whole hours
                hour = t
            else:
                hour, minute = t // 100, t % 100
        return datetime.datetime(year, month, day, hour, minute)
    except (ValueError, TypeError):
        return None


def _parse_time_value(value):
    """
    Try to parse an arbitrary time value into a datetime object.

    Handles numpy datetime64, Python datetime, and dateutil-parseable strings.
    Returns None if parsing fails.
    """
    import datetime

    import numpy as np

    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, np.datetime64):
        # Convert to Python datetime via pandas or direct cast
        try:
            import pandas as pd

            return pd.Timestamp(value).to_pydatetime()
        except ImportError:
            return value.astype("datetime64[ms]").astype(datetime.datetime)
    try:
        import dateutil.parser

        return dateutil.parser.parse(str(value))
    except (ValueError, TypeError, OverflowError):
        return None


class Source:
    """
    Unified data source for plotting.

    Wraps different data types via extractors and provides a consistent
    interface for coordinate extraction and metadata access.

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
    u : str, np.ndarray, or None, optional
        U component specification (for vector plots).
    v : str, np.ndarray, or None, optional
        V component specification (for vector plots).
    context : PlotContext, optional
        Plot context to guide coordinate inference.
        Defaults to CARTESIAN_2D.
    metadata : dict, optional
        User-provided metadata.
    units : str, optional
        Target units for data values. Behavior depends on context:
        - 1D cartesian: Tries to convert both x and y. If both fail, raises error.
        - 2D/geographic: Converts z (the data field).
        Dimension-specific units (x_units, y_units, z_units) take precedence.
        See :doc:`/examples/examples/introduction/08-unit-conversion` for
        examples.
    x_units : str, optional
        Target units for x dimension. Overrides 'units' for x.
    y_units : str, optional
        Target units for y dimension. Overrides 'units' for y.
    z_units : str, optional
        Target units for z dimension. Overrides 'units' for z.
    u_units : str, optional
        Target units for u component. Overrides 'units' for u.
    v_units : str, optional
        Target units for v component. Overrides 'units' for v.
    """

    def __init__(
        self,
        data: Any,
        *,
        x: str | np.ndarray | None = None,
        y: str | np.ndarray | None = None,
        z: str | np.ndarray | None = None,
        u: str | np.ndarray | None = None,
        v: str | np.ndarray | None = None,
        context: PlotContext = PlotContext.CARTESIAN_2D,
        metadata: dict | None = None,
        units: str | None = None,
        x_units: str | None = None,
        y_units: str | None = None,
        z_units: str | None = None,
        u_units: str | None = None,
        v_units: str | None = None,
    ):
        self._extractor = _get_extractor(data, metadata)
        self._x_spec = x
        self._y_spec = y
        self._z_spec = z
        self._u_spec = u
        self._v_spec = v
        self._context = context
        self._metadata_resolver = MetadataResolver(self._extractor, metadata)

        # Unit conversion tracking
        self._generic_units = units  # Generic units - applied intelligently based on context
        self._target_x_units = x_units  # Explicit x units
        self._target_y_units = y_units  # Explicit y units
        self._target_z_units = z_units  # Explicit z units
        self._target_u_units = u_units  # Explicit u units
        self._target_v_units = v_units  # Explicit v units

        # Track which conversions actually succeeded (populated during conversion)
        self._applied_x_units: str | None = None
        self._applied_y_units: str | None = None
        self._applied_z_units: str | None = None

        # Lazy extraction flags
        self._coords_extracted = False
        self._x_coord_info: CoordinateInfo | None = None
        self._y_coord_info: CoordinateInfo | None = None
        self._z_coord_info: CoordinateInfo | None = None
        self._u_coord_info: CoordinateInfo | None = None
        self._v_coord_info: CoordinateInfo | None = None

        # Cached DimensionInfo objects (created lazily)
        self._x_dimension: DimensionInfo | None = None
        self._y_dimension: DimensionInfo | None = None
        self._z_dimension: DimensionInfo | None = None
        self._u_dimension: DimensionInfo | None = None
        self._v_dimension: DimensionInfo | None = None

        # Backward compatibility properties
        self._data = data  # For backward compatibility

    def _extract(self):
        """Lazy coordinate extraction."""
        if self._coords_extracted:
            return

        # Clear dimension cache
        self._x_dimension = None
        self._y_dimension = None
        self._z_dimension = None
        self._u_dimension = None
        self._v_dimension = None

        # Extract coordinates using extractor
        extracted = self._extractor.extract_coordinates(
            self._x_spec,
            self._y_spec,
            self._z_spec,
            self._u_spec,
            self._v_spec,
            self._context,
        )

        # Store CoordinateInfo objects
        self._x_coord_info = extracted.x
        self._y_coord_info = extracted.y
        self._z_coord_info = extracted.z
        self._u_coord_info = extracted.u
        self._v_coord_info = extracted.v

        self._coords_extracted = True

    def _convert_values(
        self,
        values: np.ndarray,
        source_units: str | None,
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
        target_units: str | None,
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

        def _unwrap_units(u):
            """Unwrap single-element lists that earthkit metadata() can return."""
            if isinstance(u, list):
                return u[0] if u else None
            return u

        # Start with source values and units
        values = coord_info.values
        user_units = _unwrap_units(self._metadata_resolver.user_metadata.get("units"))
        applied_units = user_units or _unwrap_units(coord_info.source_units)

        # Attempt unit conversion if target_units specified
        if target_units is not None:
            # source_units priority:
            # 1. User-provided metadata (metadata={"units": "..."}) — highest priority
            # 2. Units embedded in the coordinate by the extractor
            user_units = _unwrap_units(self._metadata_resolver.user_metadata.get("units"))
            source_units = user_units or _unwrap_units(coord_info.source_units) or _unwrap_units(self.source_units)

            if source_units is not None:
                converted, success = self._convert_values(values, source_units, target_units, coord_name, silent=silent)
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

    def update_units(self, units: str) -> None:
        """
        Update the target units for this source, clearing any cached dimension
        so that unit conversion is applied on the next access.

        This is used by the pipeline when ``use_preferred_units`` selects a
        style after the source has already been constructed, to ensure the data
        values are converted to the style's units before plotting.

        Parameters
        ----------
        units :
            The new target units string (e.g. ``"celsius"``).
        """
        self._generic_units = units
        # Clear the cached z dimension so it is rebuilt with conversion applied.
        self._z_dimension = None

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

        return self._build_dimension("x", self._x_coord_info, target_units, "_x_dimension", silent=True)

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

        return self._build_dimension("y", self._y_coord_info, target_units, "_y_dimension", silent=False)

    @property
    def z(self) -> DimensionInfo | None:
        """
        Get z dimension information with metadata.

        For vector fields (when u and v are present), z represents the magnitude
        of the vector field, computed lazily as sqrt(u^2 + v^2).

        Returns
        -------
        DimensionInfo or None
            Z dimension with values, units, name, and metadata.
            For vector fields, returns magnitude.
            None for 1D plots or when no data is available.
        """
        if self._z_dimension is not None:
            return self._z_dimension

        self._extract()

        # For vector fields, compute magnitude lazily
        if self._u_coord_info is not None and self._v_coord_info is not None:
            # Compute magnitude from u and v components
            u_values = self._u_coord_info.values
            v_values = self._v_coord_info.values
            magnitude = np.sqrt(u_values**2 + v_values**2)

            # Create a CoordinateInfo for magnitude
            # Use u's metadata as a base, but update name and units
            magnitude_info = CoordinateInfo(
                values=magnitude,
                name="magnitude",
                source_units=self._u_coord_info.source_units,  # Assume same units as components
                metadata={
                    **self._u_coord_info.metadata,
                    "long_name": "Vector magnitude",
                },
            )

            # Determine target units with fallback
            target_units = self._target_z_units
            if target_units is None and self._generic_units is not None:
                if self._context.is_2d:
                    target_units = self._generic_units

            # Build and cache the dimension
            self._z_dimension = self._build_dimension("z", magnitude_info, target_units, "_z_dimension", silent=False)
            return self._z_dimension

        # Regular scalar field case
        if self._z_coord_info is None:
            return None

        # Determine target units with fallback
        target_units = self._target_z_units
        if target_units is None and self._generic_units is not None:
            # In 2D contexts, z is always the data field
            # In 1D contexts with z (scatter/point_cloud), z is the color/data field
            if self._context.is_2d or (self._context.is_1d and self._z_coord_info is not None):
                target_units = self._generic_units

        return self._build_dimension("z", self._z_coord_info, target_units, "_z_dimension", silent=False)

    @property
    def u(self) -> DimensionInfo | None:
        """
        Get u component dimension information with metadata.

        Returns
        -------
        DimensionInfo or None
            U component with values, units, name, and metadata.
            None if no vector data.
        """
        if self._u_dimension is not None:
            return self._u_dimension

        self._extract()

        if self._u_coord_info is None:
            return None

        # Determine target units
        target_units = self._target_u_units

        return self._build_dimension("u", self._u_coord_info, target_units, "_u_dimension", silent=False)

    @property
    def v(self) -> DimensionInfo | None:
        """
        Get v component dimension information with metadata.

        Returns
        -------
        DimensionInfo or None
            V component with values, units, name, and metadata.
            None if no vector data.
        """
        if self._v_dimension is not None:
            return self._v_dimension

        self._extract()

        if self._v_coord_info is None:
            return None

        # Determine target units
        target_units = self._target_v_units

        return self._build_dimension("v", self._v_coord_info, target_units, "_v_dimension", silent=False)

    @property
    def u_values(self):
        """Get u-component values (deprecated - use source.u.values instead)."""
        import warnings

        warnings.warn(
            "u_values is deprecated. Use source.u.values instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if self.u is not None:
            return self.u.values
        return None

    @property
    def v_values(self):
        """Get v-component values (deprecated - use source.v.values instead)."""
        import warnings

        warnings.warn(
            "v_values is deprecated. Use source.v.values instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if self.v is not None:
            return self.v.values
        return None

    @property
    def magnitude(self):
        """Get magnitude of vector field (for backward compatibility)."""
        if self.u is not None and self.v is not None:
            return (self.u.values**2 + self.v.values**2) ** 0.5
        return None

    def is_vector(self) -> bool:
        """
        Check if this source represents vector data.

        Returns
        -------
        bool
            True if the source has both u and v components, False otherwise.
        """
        return self.u is not None and self.v is not None

    @property
    def crs(self):
        """Get coordinate reference system."""
        return self._extractor.get_crs()

    @property
    def gridspec(self):
        """Get grid specification."""
        if hasattr(self, "_gridspec_override"):
            return self._gridspec_override
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
        # Use metadata resolver (XarrayExtractor.get_metadata handles scalar coords)
        return self._metadata_resolver.get(key, default)

    @property
    def units(self) -> str | None:
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
    def source_units(self) -> str | None:
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

        # For xarray: scan for time-like scalar coordinates or attrs
        # Common xarray time coord names: "time", "valid_time", "forecast_reference_time"
        import xarray as xr

        if isinstance(self._data, (xr.DataArray, xr.Dataset)):
            da = (
                self._data
                if isinstance(self._data, xr.DataArray)
                else next(iter(self._data.data_vars.values()), self._data)
            )
            time_coord_names = [
                "valid_time",
                "time",
                "forecast_reference_time",
                "initial_time",
            ]
            found = {}
            for name in time_coord_names:
                if name in da.coords:
                    coord = da.coords[name]
                    val = coord.values if coord.ndim == 0 else (coord.values[0] if coord.size == 1 else None)
                    if val is not None:
                        dt = _parse_time_value(val)
                        if dt is not None:
                            found[name] = dt
            if found:
                valid = found.get("valid_time") or found.get("time")
                base = found.get("forecast_reference_time") or found.get("initial_time") or valid
                return {"base_time": base, "valid_time": valid}

        # Try to build a datetime from ECMWF-style integer date/time attrs
        # e.g. date=20150101, time=0 (or time=1200)
        date_val = self.metadata("date")
        time_val = self.metadata("time")
        if date_val is not None:
            dt = _parse_date_time_ints(date_val, time_val)
            if dt is not None:
                return {"base_time": dt, "valid_time": dt}

        # Fallback: try to parse a generic "time" metadata value
        if time_val is not None:
            dt = _parse_time_value(time_val)
            if dt is not None:
                return {"base_time": dt, "valid_time": dt}

        return {"base_time": None, "valid_time": None}


def _is_xarray_backed_earthkit(data: Any) -> bool:
    """
    Return True for earthkit NetCDF objects that should be converted via to_xarray().

    Detects any earthkit Base subclass whose module contains 'netcdf' and which
    exposes a to_xarray() method, covering all known earthkit.data versions.
    """
    try:
        import earthkit.data as ek_data
    except ImportError:
        return False
    if not isinstance(data, ek_data.core.Base):
        return False
    if not hasattr(data, "to_xarray"):
        return False
    module = getattr(type(data), "__module__", "") or ""
    return "netcdf" in module


def _get_extractor(data: Any, metadata: dict | None = None) -> DataExtractor:
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
    # No data object — coordinate-only call (e.g. line(x=lons, y=lats))
    if data is None:
        return NumpyExtractor(None)

    # Check for xarray types
    if data.__class__.__name__ in ("DataArray", "Dataset"):
        from earthkit.plots.sources.extractors.xarray import XarrayExtractor

        return XarrayExtractor(data)

    # xarray-backed earthkit objects (NetCDF FieldLists, etc.) — convert first
    if _is_xarray_backed_earthkit(data):
        from earthkit.plots.sources.extractors.xarray import XarrayExtractor

        return XarrayExtractor(data.to_xarray())

    # Check for earthkit types
    try:
        import earthkit.data as ek_data

        if isinstance(data, ek_data.core.Base):
            from earthkit.plots.sources.extractors.earthkit import EarthkitExtractor

            return EarthkitExtractor(data)
    except ImportError:
        pass

    # Default to numpy extractor (handles arrays, lists, etc.)
    return NumpyExtractor(data, metadata=metadata)


def get_source(
    *args,
    data=None,
    x=None,
    y=None,
    z=None,
    u=None,
    v=None,
    context=None,
    metadata=None,
    units=None,
    x_units=None,
    y_units=None,
    z_units=None,
    u_units=None,
    v_units=None,
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
    u : numpy.ndarray or str, optional
        The u-component of the data (for vector plots). If a string, it is assumed
        to be the name of the u-component variable in data.
    v : numpy.ndarray or str, optional
        The v-component of the data (for vector plots). If a string, it is assumed
        to be the name of the v-component variable in data.
    context : PlotContext, optional
        Plot context to guide coordinate inference. If None, defaults to
        CARTESIAN_2D.
    metadata : dict, optional
        User-provided metadata.
    units : str, optional
        Target units for data values. Behavior depends on context:
        - 1D cartesian: Tries to convert both x and y. If both fail, raises error.
        - 2D/geographic: Converts z (the data field).
        Dimension-specific units (x_units, y_units, z_units) take precedence.
        See :doc:`/examples/examples/introduction/08-unit-conversion` for
        examples.
    x_units : str, optional
        Target units for x dimension. Overrides 'units' for x.
    y_units : str, optional
        Target units for y dimension. Overrides 'units' for y.
    z_units : str, optional
        Target units for z dimension. Overrides 'units' for z.
    u_units : str, optional
        Target units for u component. Overrides 'units' for u.
    v_units : str, optional
        Target units for v component. Overrides 'units' for v.
    **kwargs
        Additional metadata to merge with metadata dict.

    Returns
    -------
    Source
        Unified source object for plotting.
    """
    # Determine data object
    data_obj = data if data is not None else (args[0] if args else None)
    try:
        import earthkit.data as ek_data

        _ek_base = ek_data.core.Base
    except ImportError:
        _ek_base = type(None)
    if isinstance(data_obj, _ek_base) and not _is_xarray_backed_earthkit(data_obj):
        if hasattr(data_obj, "to_fieldlist"):
            data_obj = data_obj.to_fieldlist()
        if hasattr(data_obj, "__len__") and len(data_obj) >= 1:
            # For vector contexts, keep the full FieldList so the extractor can
            # find U/V pairs across fields. For scalar plots, collapse to [0].
            is_vector = context is not None and context.is_vector
            if not is_vector:
                data_obj = data_obj[0]

    if data_obj is None:
        # Check for 'c' parameter (matplotlib convention for color/data)
        c = kwargs.pop("c", None)
        if c is not None:
            data_obj = c
        elif isinstance(z, (np.ndarray, list)):
            data_obj = z
        elif not isinstance(x, (np.ndarray, list)) and not isinstance(y, (np.ndarray, list)):
            # No positional data and no coordinate arrays — nothing to plot.
            raise ValueError("No data provided to get_source()")

    # Merge kwargs into metadata
    if metadata is None:
        metadata = {}
    metadata.update(kwargs)

    # Default context
    if context is None:
        context = PlotContext.CARTESIAN_2D

    # Route to GeometrySource if context is geometry-based
    if context.is_geometry:
        from earthkit.plots.sources.geometry import _UNSET, GeometrySource

        return GeometrySource(
            data_obj,
            z=_UNSET if z is None else z,
            units=units,
            metadata=metadata,
        )

    # Create coordinate-based Source for non-geometry contexts
    return Source(
        data_obj,
        x=x,
        y=y,
        z=z,
        u=u,
        v=v,
        context=context,
        metadata=metadata,
        units=units,
        x_units=x_units,
        y_units=y_units,
        z_units=z_units,
        u_units=u_units,
        v_units=v_units,
    )


# Import GeometrySource for geometry-based data (GeoDataFrames)
from earthkit.plots.sources.geometry import GeometrySource  # noqa: E402

__all__ = ["Source", "get_source", "GeometrySource"]
