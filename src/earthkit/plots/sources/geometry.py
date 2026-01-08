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

import warnings
from typing import Any, Optional

import numpy as np


class GeometrySource:
    """
    Data source for geometry-based plotting (GeoDataFrames).

    Unlike the coordinate-based Source class, GeometrySource wraps shapely
    geometry objects with associated data values. Used for choropleth maps
    and other geometry-based visualizations.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        The GeoDataFrame containing geometries and data
    column : str, optional
        Name of the column containing data values for coloring.
        If None, auto-detects first numeric column.
    units : str, optional
        Target units for data values (e.g., "celsius", "kilometers")
    metadata : dict, optional
        Additional metadata

    Attributes
    ----------
    geometries : list
        List of shapely geometry objects
    values : np.ndarray or None
        Data values associated with each geometry (for coloring)
    value_name : str
        Name of the data column
    crs : cartopy.crs.CRS or None
        Coordinate reference system
    """

    def __init__(
        self,
        data,
        *,
        z: Optional[str] = None,
        units: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """
        Initialize GeometrySource from a GeoDataFrame.

        Parameters
        ----------
        data : geopandas.GeoDataFrame
            The GeoDataFrame to wrap
        column : str, optional
            Column name for data values
        units : str, optional
            Target units for data values
        metadata : dict, optional
            Additional metadata
        """
        self._check_geopandas(data)
        self._data = data
        self._column = z
        self._target_units = units
        self._user_metadata = metadata or {}

        # Lazy evaluation flags
        self._extracted = False
        self._geometries = None
        self._values = None
        self._value_name = None
        self._source_units = None
        self._applied_units = None
        self._value_metadata = {}

    def _check_geopandas(self, data):
        """Verify this is a GeoDataFrame."""
        if data.__class__.__name__ != "GeoDataFrame":
            raise TypeError(
                f"GeometrySource requires a GeoDataFrame, got {type(data)}"
            )

        if not hasattr(data, "geometry"):
            raise ValueError("GeoDataFrame must have a geometry column")

    def _extract(self):
        """Extract geometries and data values."""
        if self._extracted:
            return

        # Extract geometries
        self._geometries = list(self._data.geometry)

        # Extract data values
        if self._column is None:
            # Auto-detect: find first numeric column (excluding geometry and coordinate-like columns)
            numeric_cols = self._data.select_dtypes(include=[np.number]).columns
            candidate_cols = [
                col
                for col in numeric_cols
                if col not in ["x", "y", "X", "Y", "geometry"]
            ]

            if candidate_cols:
                self._column = candidate_cols[0]

        if self._column is not None:
            if self._column not in self._data.columns:
                raise ValueError(
                    f"Column '{self._column}' not found in GeoDataFrame"
                )

            self._value_name = self._column
            self._values = self._data[self._column].values

            # Extract metadata from column if available
            if hasattr(self._data[self._column], "attrs"):
                self._value_metadata = dict(self._data[self._column].attrs)
                self._source_units = self._value_metadata.get("units")

            # Apply unit conversion if requested
            if self._target_units is not None and self._values is not None:
                self._values, self._applied_units = self._convert_units(
                    self._values, self._source_units, self._target_units
                )
            else:
                self._applied_units = self._source_units

        self._extracted = True

    def _convert_units(self, values, source_units, target_units):
        """
        Convert data values to target units.

        Parameters
        ----------
        values : np.ndarray
            Values to convert
        source_units : str or None
            Source units
        target_units : str
            Target units

        Returns
        -------
        tuple[np.ndarray, str or None]
            (converted_values, applied_units)
        """
        if source_units is None:
            import warnings

            warnings.warn(
                f"Cannot convert data values to {target_units}: "
                f"source units not available. Returning original values.",
                UserWarning,
            )
            return values, source_units

        if source_units == target_units:
            return values, target_units

        try:
            from earthkit.plots.metadata import units as metadata_units

            converted = metadata_units.convert(values, source_units, target_units)
            return converted, target_units
        except Exception as e:
            import warnings

            warnings.warn(
                f"Unit conversion failed: {source_units} -> {target_units}. "
                f"Error: {e}. Returning original values.",
                UserWarning,
            )
            return values, source_units

    @property
    def data(self):
        """Get the underlying GeoDataFrame."""
        return self._data

    @property
    def geometries(self):
        """
        Get list of shapely geometry objects.

        Returns
        -------
        list
            List of shapely geometries (Polygon, Point, LineString, etc.)
        """
        self._extract()
        return self._geometries

    @property
    def values(self):
        """
        Get data values associated with each geometry.

        Returns
        -------
        np.ndarray or None
            Data values (one per geometry), or None if no data column
        """
        self._extract()
        return self._values

    @property
    def value_name(self):
        """
        Get name of the data value column.

        Returns
        -------
        str or None
            Column name, or None if no data
        """
        self._extract()
        return self._value_name

    @property
    def units(self):
        """
        Get units for the data values.

        Returns applied units if conversion occurred, otherwise source units.

        Returns
        -------
        str or None
            Units string or None
        """
        self._extract()
        return self._applied_units

    @property
    def source_units(self):
        """
        Get original source units before conversion.

        Returns
        -------
        str or None
            Original units or None
        """
        self._extract()
        return self._source_units

    @property
    def crs(self):
        """
        Get coordinate reference system.

        Returns
        -------
        cartopy.crs.CRS or None
            The CRS, or None if not available
        """
        if self._data.crs is None:
            return None

        import cartopy.crs as ccrs
        
        try:
            # Get the proj4 string from pyproj CRS
            with warnings.catch_warnings():
                # pyproj always warns when converting to proj4
                warnings.simplefilter("ignore")
                proj4_string = self._data.crs.to_proj4()

            # Try to match to common cartopy projections
            if "longlat" in proj4_string or "latlong" in proj4_string:
                return ccrs.PlateCarree()
            elif "merc" in proj4_string:
                return ccrs.Mercator()
            else:
                # For other projections, use the proj4 string
                return ccrs.CRS(proj4_string)
        except Exception:
            # If conversion fails, default to PlateCarree
            return ccrs.PlateCarree()

    def metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value.

        Checks:
        1. User-provided metadata (from constructor)
        2. GeoDataFrame attrs
        3. Column values (if constant across all rows)

        Parameters
        ----------
        key : str
            Metadata key
        default : Any
            Default value if not found

        Returns
        -------
        Any
            Metadata value or default
        """
        # Check user metadata first
        if key in self._user_metadata:
            return self._user_metadata[key]

        # Check GeoDataFrame attrs
        if hasattr(self._data, "attrs") and key in self._data.attrs:
            return self._data.attrs[key]

        # Check if key is a column with constant value
        if key in self._data.columns:
            col = self._data[key]
            if col.nunique() == 1:
                return col.iloc[0]

        # Check value-specific metadata
        self._extract()
        if key in self._value_metadata:
            return self._value_metadata[key]
        
        if key in ["name", "long_name", "standard_name", "variable_name"]:
            if isinstance(self._column, str):
                return self._column

        return default

    def is_vector(self) -> bool:
        """
        Check if this is vector data (u/v components).

        Always False for GeometrySource - geometries don't have vector components.

        Returns
        -------
        bool
            False
        """
        return False

    def __repr__(self):
        """String representation for debugging."""
        self._extract()
        n_geoms = len(self._geometries) if self._geometries else 0
        value_str = f", values='{self._value_name}'" if self._value_name else ""
        units_str = f" ({self.units})" if self.units else ""
        return f"GeometrySource({n_geoms} geometries{value_str}{units_str})"


def get_geometry_source(
    data,
    column=None,
    units=None,
    metadata=None,
    **kwargs,
):
    """
    Create a GeometrySource from a GeoDataFrame.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        The GeoDataFrame containing geometries and data
    column : str, optional
        Name of the column containing data values for coloring.
        If None, auto-detects first numeric column.
    units : str, optional
        Target units for data values
    metadata : dict, optional
        Additional metadata
    **kwargs
        Additional metadata to merge

    Returns
    -------
    GeometrySource
        GeometrySource wrapping the GeoDataFrame
    """
    # Merge kwargs into metadata
    if metadata is None:
        metadata = {}
    metadata.update(kwargs)

    return GeometrySource(
        data,
        z=column,
        units=units,
        metadata=metadata,
    )
