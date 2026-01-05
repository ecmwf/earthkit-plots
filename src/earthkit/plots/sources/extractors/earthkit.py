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

import cartopy.crs as ccrs
import numpy as np

from earthkit.plots.sources.extractors.base import BaseExtractor
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.coordinates import CoordinateInfo, ExtractedCoordinates


class EarthkitExtractor(BaseExtractor):
    """
    Extractor for earthkit.data objects (Field, FieldList, etc.).

    Handles geographic data with built-in coordinate extraction
    and metadata access.
    """

    def extract_coordinates(
        self,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        context: PlotContext,
    ) -> ExtractedCoordinates:
        """
        Extract coordinates from earthkit data with metadata.

        Parameters
        ----------
        x : str, np.ndarray, or None
            X coordinate specification.
        y : str, np.ndarray, or None
            Y coordinate specification.
        z : str, np.ndarray, or None
            Z variable name or array.
        context : PlotContext
            Plot context to guide inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata for each dimension.
        """
        # Extract z values (the field data)
        z_name = ""
        if isinstance(z, str):
            # Select specific variable by name
            z_values = self.data.sel(short_name=z).to_numpy(flatten=False)
            z_name = z
        elif isinstance(z, np.ndarray):
            z_values = z
        else:
            # Use all data
            z_values = self.data.to_numpy(flatten=False)

        # Extract x, y coordinates
        if isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
            # Explicit coordinates provided
            x_values = x
            y_values = y
        else:
            # Extract from earthkit data
            x_values, y_values = self._extract_coordinates_from_data()

        # Infer coordinate names based on grid type
        x_name, y_name = self._infer_coordinate_names()

        # Build CoordinateInfo objects
        # For earthkit data, extract all metadata and pass it to z dimension
        # since earthkit objects are 2D fields with global metadata (not data cubes)
        z_metadata = self._extract_all_metadata()
        units = z_metadata.get("units")

        x_info = CoordinateInfo(
            values=x_values,
            name=x_name,
            source_units=None,
            metadata={},
        )
        y_info = CoordinateInfo(
            values=y_values,
            name=y_name,
            source_units=None,
            metadata={},
        )
        z_info = None
        if z_values is not None:
            z_info = CoordinateInfo(
                values=z_values,
                name=z_name,
                source_units=units,
                metadata=z_metadata,  # Pass all global metadata to z dimension
            )

        return ExtractedCoordinates(x=x_info, y=y_info, z=z_info)

    def _extract_coordinates_from_data(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract coordinates from earthkit data object in native CRS.

        Strategy:
        1. Try to_points() first - returns native coordinates (x/y for projected, lon/lat for geographic)
        2. Fall back to to_latlon() if to_points() not implemented
        3. Generate indices as last resort

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (x, y) arrays in the data's native CRS.
        """
        # Try to_points method first - gives native coordinates
        if hasattr(self.data, "to_points"):
            try:
                points = self.data.to_points(flatten=False)
                # Check for x/y (projected coordinates) first
                if "x" in points and "y" in points:
                    return points["x"], points["y"]
                # Then check for lon/lat (geographic coordinates)
                elif "lon" in points and "lat" in points:
                    return points["lon"], points["lat"]
            except (AttributeError, NotImplementedError):
                pass

        # Fallback to to_latlon if to_points not available
        if hasattr(self.data, "to_latlon"):
            try:
                coords = self.data.to_latlon(flatten=False)
                if isinstance(coords, dict):
                    return coords.get("lon"), coords.get("lat")
                elif isinstance(coords, tuple) and len(coords) == 2:
                    lat, lon = coords
                    return lon, lat
            except (AttributeError, NotImplementedError):
                pass

        # Last resort: generate index arrays
        z_values = self.data.to_numpy(flatten=False)
        if z_values.ndim == 2:
            ny, nx = z_values.shape
            x_values = np.arange(nx)
            y_values = np.arange(ny)
            return x_values, y_values
        elif z_values.ndim == 1:
            x_values = np.arange(len(z_values))
            y_values = np.zeros(len(z_values))
            return x_values, y_values

        raise ValueError("Could not extract coordinates from earthkit data")

    def _infer_coordinate_names(self) -> tuple[str, str]:
        """
        Infer coordinate names based on earthkit data grid type.

        For regular_ll grids: returns ("longitude", "latitude")
        For other grids: returns ("x", "y")

        Returns
        -------
        tuple[str, str]
            (x_name, y_name) coordinate names.
        """
        # Try to get grid_type metadata
        grid_type = self.get_metadata("gridType")

        # For regular lat-lon grids, use geographic names
        if grid_type == "regular_ll":
            return ("longitude", "latitude")

        # For other grid types (projected, reduced, etc.), use generic x/y
        return ("x", "y")

    def _extract_all_metadata(self) -> dict:
        """
        Extract all available metadata from earthkit data as a dictionary.

        This allows z.metadata() to access any field metadata without
        needing to know the keys in advance.

        Returns
        -------
        dict
            Dictionary of all available metadata from the earthkit field.
        """
        metadata_dict = {}

        if not hasattr(self.data, "metadata"):
            return metadata_dict

        # Common GRIB keys to extract
        # These are the most commonly used metadata keys
        common_keys = [
            "units",
            "long_name",
            "short_name",
            "name",
            "standard_name",
            "param",
            "paramId",
            "centre",
            "centreDescription",
            "dataDate",
            "dataTime",
            "validityDate",
            "validityTime",
            "stepRange",
            "level",
            "levelType",
            "gridType",
            "Nx",
            "Ny",
            "numberOfPoints",
        ]

        for key in common_keys:
            try:
                value = self.data.metadata(key)
                if value is not None:
                    metadata_dict[key] = value
            except (AttributeError, KeyError, NotImplementedError):
                pass

        return metadata_dict

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from earthkit data.

        Parameters
        ----------
        key : str
            Metadata key.
        default : Any
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value or default.
        """
        if hasattr(self.data, "metadata"):
            try:
                value = self.data.metadata(key)
                if value is not None:
                    return value
            except (AttributeError, KeyError, NotImplementedError):
                pass

        return default

    def get_crs(self) -> Optional[Any]:
        """
        Extract CRS from earthkit data.

        Returns
        -------
        CRS or None
            Coordinate reference system.
        """
        if hasattr(self.data, "projection"):
            try:
                proj = self.data.projection()
                if hasattr(proj, "to_cartopy_crs"):
                    return proj.to_cartopy_crs()
                return proj
            except (AttributeError, NotImplementedError):
                pass

        # Default to PlateCarree for geographic data
        return ccrs.PlateCarree()

    def get_gridspec(self) -> Optional[Any]:
        """
        Extract gridspec from earthkit data.

        Returns
        -------
        GridSpec or None
            Grid specification for regridding.
        """
        # Import gridspec utilities
        from earthkit.plots.sources.gridspec import get_grid_spec

        try:
            return get_grid_spec(self.data)
        except (AttributeError, ImportError):
            return None
