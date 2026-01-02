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
import xarray as xr

from earthkit.plots import identifiers
from earthkit.plots.sources.adaptors import SELECTED_DATA
from earthkit.plots.sources.adaptors.base import BaseAdaptor
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.extractor import CoordinateExtractor
from earthkit.plots.sources.coordinates import CoordinateInfo, ExtractedCoordinates


class XarrayAdaptor(BaseAdaptor):
    """
    Adaptor for xarray DataArrays and Datasets.

    Handles rich metadata, coordinate systems, and multi-dimensional data.
    """

    def __init__(self, data: Union[xr.DataArray, xr.Dataset]):
        """
        Initialize xarray adaptor.

        Parameters
        ----------
        data : xr.DataArray or xr.Dataset
            Xarray data structure.
        """
        super().__init__(data)
        # Squeeze to remove size-1 dimensions
        self.data = data.squeeze()
        # Cache for selected DataArray (when data is Dataset)
        self._selected_dataarray: Optional[xr.DataArray] = None

    def extract_coordinates(
        self,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
        context: PlotContext,
    ) -> ExtractedCoordinates:
        """
        Extract coordinates from xarray data with metadata.

        Parameters
        ----------
        x : str, np.ndarray, or None
            X coordinate name or array.
        y : str, np.ndarray, or None
            Y coordinate name or array.
        z : str, np.ndarray, or None
            Z variable name or array.
        context : PlotContext
            Plot context to guide inference.

        Returns
        -------
        ExtractedCoordinates
            Extracted coordinates with metadata for each dimension.
        """
        # Convert Dataset to DataArray if needed
        # Pass x and y as well since they might refer to data variables
        da = self._get_dataarray(z, x, y)

        # Determine which coordinates refer to the selected DataArray's data values
        # When the user specifies z='temperature' for a Dataset, they want 'temperature'
        # to be treated as the z data values (not as a coordinate name)
        # We need to communicate this to the coordinate extractor
        selected_var_name = self._selected_dataarray.name if self._selected_dataarray is not None else None

        if isinstance(self.data, xr.Dataset) and selected_var_name:
            # Replace references to the selected variable with SELECTED_DATA marker
            # This tells _collect_arrays to use the DataArray's values for this dimension
            x_coord = SELECTED_DATA if (isinstance(x, str) and x == selected_var_name) else x
            y_coord = SELECTED_DATA if (isinstance(y, str) and y == selected_var_name) else y
            z_coord = SELECTED_DATA if (isinstance(z, str) and z == selected_var_name) else z
        else:
            x_coord, y_coord, z_coord = x, y, z

        # Build candidate arrays from dimensions and coordinates
        # This will extract any data variables that aren't the selected one
        # Also track which original names were used
        arrays, name_tracker = self._collect_arrays(da, x_coord, y_coord, z_coord)

        # Use coordinate extractor to infer
        coords = CoordinateExtractor.infer_from_shapes_and_context(arrays, context)

        # Build CoordinateInfo for each dimension
        x_info = self._build_coordinate_info(
            coords["x"], name_tracker, x, da, "x"
        )
        y_info = self._build_coordinate_info(
            coords["y"], name_tracker, y, da, "y"
        )
        z_info = None
        if coords.get("z") is not None:
            z_info = self._build_coordinate_info(
                coords["z"], name_tracker, z, da, "z"
            )

        return ExtractedCoordinates(x=x_info, y=y_info, z=z_info)

    def _get_dataarray(
        self,
        z: Optional[Union[str, np.ndarray]],
        x: Optional[Union[str, np.ndarray]] = None,
        y: Optional[Union[str, np.ndarray]] = None,
    ) -> xr.DataArray:
        """
        Get DataArray from Dataset if needed.

        Parameters
        ----------
        z : str, np.ndarray, or None
            Variable name to extract if data is a Dataset.
        x, y : str, np.ndarray, or None
            May refer to variable names in 1D contexts.

        Returns
        -------
        xr.DataArray
            Extracted or existing DataArray.
        """
        if not isinstance(self.data, xr.Dataset):
            self._selected_dataarray = self.data
            return self.data

        # Data is a Dataset - need to select variable
        dataset = self.data

        # Check if x, y, or z refers to a data variable
        # Priority: z > y > x (for backward compatibility)
        var_name = None
        if isinstance(z, str) and z in dataset.data_vars:
            var_name = z
        elif isinstance(y, str) and y in dataset.data_vars:
            var_name = y
        elif isinstance(x, str) and x in dataset.data_vars:
            var_name = x

        if var_name:
            self._selected_dataarray = dataset[var_name]
            return self._selected_dataarray

        # Auto-select variable
        if len(dataset.data_vars) == 1:
            var_name = list(dataset.data_vars.keys())[0]
            self._selected_dataarray = dataset[var_name]
            return self._selected_dataarray

        # Try to find the main data variable (has coordinate dimensions)
        var_name = identifiers.identify_primary(dataset)
        if var_name and var_name in dataset.data_vars:
            self._selected_dataarray = dataset[var_name]
            return self._selected_dataarray

        raise ValueError(
            f"Multiple variables in Dataset: {list(dataset.data_vars.keys())}. "
            "Please specify which variable to plot using 'x', 'y', or 'z' parameter."
        )

    def _collect_arrays(
        self,
        da: xr.DataArray,
        x: Optional[Union[str, np.ndarray]],
        y: Optional[Union[str, np.ndarray]],
        z: Optional[Union[str, np.ndarray]],
    ) -> tuple[dict[str, np.ndarray], dict]:
        """
        Collect all available arrays from the DataArray and original Dataset.

        This method builds a dictionary of all available arrays that could be used
        as coordinates or data values. It includes:
        - Dimension coordinates (e.g., latitude, longitude)
        - Non-dimension coordinates (e.g., time, auxiliary coords)
        - The selected DataArray's data values (keyed as SELECTED_DATA)
        - User-specified arrays or references to other data variables

        The SELECTED_DATA marker is used to reference the main DataArray's
        values when the user specified a variable name that matches the selected
        variable (e.g., z='temperature' for a Dataset with a temperature variable).

        Parameters
        ----------
        da : xr.DataArray
            DataArray to extract arrays from.
        x, y, z : str, np.ndarray, or None
            User-specified coordinates/variables. May be:
            - SELECTED_DATA: marker for the selected DataArray's values
            - coordinate/dimension name (str)
            - explicit numpy array

        Returns
        -------
        tuple
            - dict[str, np.ndarray]: Dictionary of available arrays
            - dict: Name tracker mapping id(array) to their original names in xarray
        """
        arrays = {}
        name_tracker = {}  # Maps id(array) -> original name in xarray

        # Add dimension coordinates
        for i, dim in enumerate(da.dims):
            if dim in da.coords:
                arr = da.coords[dim].values
                arrays[dim] = arr
                name_tracker[id(arr)] = dim
            else:
                # Dimension without coordinate - generate index
                arr = np.arange(da.sizes[dim])
                arrays[dim] = arr
                name_tracker[id(arr)] = ""  # Auto-generated

        # Add non-dimension coordinates
        for coord_name in da.coords:
            if coord_name not in da.dims:
                arr = da.coords[coord_name].values
                arrays[coord_name] = arr
                name_tracker[id(arr)] = coord_name

        # Add the selected DataArray's data values
        # Use SELECTED_DATA constant as the key
        arr = da.values
        arrays[SELECTED_DATA] = arr
        # Track the original variable name
        var_name = da.name if da.name else ""
        name_tracker[id(arr)] = var_name

        # If we have a Dataset, also track other data variables for error messages
        available_vars = []
        if isinstance(self.data, xr.Dataset):
            available_vars = list(self.data.data_vars.keys())

        # Process user-specified coordinates
        if x is not None:
            if isinstance(x, str):
                # Check if x matches the DataArray's own name (i.e., the selected data)
                if var_name and x == var_name:
                    # User wants to use the DataArray's values as x-coordinate
                    arrays["x_spec"] = arrays[SELECTED_DATA]
                # Check if x is a data variable in the original Dataset
                elif isinstance(self.data, xr.Dataset) and x in self.data.data_vars:
                    # Extract this variable directly
                    arr = self.data[x].values
                    arrays["x_spec"] = arr
                    name_tracker[id(arr)] = x
                elif x in arrays:
                    # x is a coordinate/dimension name - reuse existing array
                    arrays["x_spec"] = arrays[x]
                    # Track the dimension name for x_spec
                    name_tracker["__x_dim_name__"] = x
                else:
                    # Build helpful error message - exclude internal keys
                    available_coords = [k for k in arrays.keys() if k not in [SELECTED_DATA, "x_spec", "y_spec", "z_spec"]]
                    available = available_coords.copy()
                    if var_name:
                        available.append(f"(data variable) {var_name}")
                    if available_vars:
                        available.extend([f"(data variable) {v}" for v in available_vars])
                    raise ValueError(
                        f"Coordinate or variable '{x}' not found. "
                        f"Available: {available}"
                    )
            else:
                # x is an explicit array
                arr = np.atleast_1d(x)
                arrays["x_spec"] = arr
                name_tracker[id(arr)] = ""  # User-provided array has no name

        if y is not None:
            if isinstance(y, str):
                # Check if y matches the DataArray's own name (i.e., the selected data)
                if var_name and y == var_name:
                    # User wants to use the DataArray's values as y-coordinate
                    arrays["y_spec"] = arrays[SELECTED_DATA]
                # Check if y is a data variable in the original Dataset
                elif isinstance(self.data, xr.Dataset) and y in self.data.data_vars:
                    # Extract this variable directly
                    arr = self.data[y].values
                    arrays["y_spec"] = arr
                    name_tracker[id(arr)] = y
                elif y in arrays:
                    # y is a coordinate/dimension name - reuse existing array
                    arrays["y_spec"] = arrays[y]
                    # Track the dimension name for y_spec
                    name_tracker["__y_dim_name__"] = y
                else:
                    # Build helpful error message - exclude internal keys
                    available_coords = [k for k in arrays.keys() if k not in [SELECTED_DATA, "x_spec", "y_spec", "z_spec"]]
                    available = available_coords.copy()
                    if var_name:
                        available.append(f"(data variable) {var_name}")
                    if available_vars:
                        available.extend([f"(data variable) {v}" for v in available_vars])
                    raise ValueError(
                        f"Coordinate or variable '{y}' not found. "
                        f"Available: {available}"
                    )
            else:
                # y is an explicit array
                arr = np.atleast_1d(y)
                arrays["y_spec"] = arr
                name_tracker[id(arr)] = ""  # User-provided array has no name

        # z is handled in _get_dataarray, but if it's an explicit array:
        if z is not None:
            if isinstance(z, str):
                # Check if z matches the DataArray's own name (i.e., the selected data)
                if var_name and z == var_name:
                    # User wants to use the DataArray's values as z-coordinate
                    arrays["z_spec"] = arrays[SELECTED_DATA]
                # Check if z is a data variable in the original Dataset
                elif isinstance(self.data, xr.Dataset) and z in self.data.data_vars:
                    # Extract this variable directly
                    arr = self.data[z].values
                    arrays["z_spec"] = arr
                    name_tracker[id(arr)] = z
                elif z in arrays:
                    # z is a coordinate/dimension name - reuse existing array
                    arrays["z_spec"] = arrays[z]
                    # Track the dimension name for z_spec
                    name_tracker["__z_dim_name__"] = z
                # If z is not found, it's okay - it might be the SELECTED_DATA marker
            else:
                arr = np.atleast_1d(z)
                arrays["z_spec"] = arr
                name_tracker[id(arr)] = ""  # User-provided array has no name

        return arrays, name_tracker

    def _build_coordinate_info(
        self,
        values: np.ndarray,
        name_tracker: dict,
        user_spec: Optional[Union[str, np.ndarray]],
        da: xr.DataArray,
        role: str,
    ) -> CoordinateInfo:
        """
        Build CoordinateInfo for a dimension.

        Parameters
        ----------
        values : np.ndarray
            Extracted coordinate values.
        name_tracker : dict
            Mapping from id(array) to original xarray name.
        user_spec : str, np.ndarray, or None
            User specification for this dimension (x, y, or z param).
        da : xr.DataArray
            The DataArray we're extracting from.
        role : str
            Dimension role: "x", "y", or "z".

        Returns
        -------
        CoordinateInfo
            Coordinate information with metadata.
        """
        # Look up the coordinate name by ID first
        coord_name = name_tracker.get(id(values), "")

        # If not found by ID (e.g., array was transformed by meshgrid),
        # check if we have a dimension name marker for this role
        if not coord_name:
            if role == "x":
                coord_name = name_tracker.get("__x_dim_name__", "")
            elif role == "y":
                coord_name = name_tracker.get("__y_dim_name__", "")
            elif role == "z":
                coord_name = name_tracker.get("__z_dim_name__", "")

        # If still not found, try to infer the name from the DataArray dimensions
        if not coord_name:
            # Try to infer from dimensions based on the role and array shape
            # For 2D data with 2 dimensions, infer from position
            if len(da.dims) == 2 and role in ["x", "y"]:
                # By xarray/numpy convention: first dim is rows (y), second is columns (x)
                if role == "y":
                    coord_name = da.dims[0]
                elif role == "x":
                    coord_name = da.dims[1]
            # For 1D data with 1 dimension
            elif len(da.dims) == 1 and role == "x":
                coord_name = da.dims[0]
            # Fallback: look for common geographic dimension names
            elif role == "x":
                # Look for longitude-like dimension names
                for dim in da.dims:
                    if dim.lower() in ["longitude", "lon", "x"]:
                        coord_name = dim
                        break
            elif role == "y":
                # Look for latitude-like dimension names
                for dim in da.dims:
                    if dim.lower() in ["latitude", "lat", "y"]:
                        coord_name = dim
                        break
            elif role == "z":
                # For z, use the data variable name
                coord_name = da.name if da.name else ""

        # Extract metadata for this coordinate/variable
        source_units = None
        metadata_dict = {}

        # Check if this is the selected DataArray's data values (for z or y in 1D)
        # This happens when coord_name matches the DataArray name, or when dealing
        # with the SELECTED_DATA marker
        is_selected_data = (
            self._selected_dataarray is not None
            and (
                (coord_name and coord_name == self._selected_dataarray.name)
                or (role in ["y", "z"] and id(values) == id(self._selected_dataarray.values))
            )
        )

        if is_selected_data:
            # This is the main data variable - extract attrs from the DataArray
            metadata_dict = dict(self._selected_dataarray.attrs) if hasattr(self._selected_dataarray, "attrs") else {}
            source_units = metadata_dict.get("units")
        elif coord_name:
            # Look in coordinates first
            if coord_name in da.coords:
                coord_obj = da.coords[coord_name]
                metadata_dict = dict(coord_obj.attrs) if hasattr(coord_obj, "attrs") else {}
                source_units = metadata_dict.get("units")
            # Check if it's a data variable in the original Dataset
            elif isinstance(self.data, xr.Dataset) and coord_name in self.data.data_vars:
                var_obj = self.data[coord_name]
                metadata_dict = dict(var_obj.attrs) if hasattr(var_obj, "attrs") else {}
                source_units = metadata_dict.get("units")

        return CoordinateInfo(
            values=values,
            name=coord_name,
            source_units=source_units,
            metadata=metadata_dict,
        )

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from xarray attrs.

        For Datasets, extracts metadata from the selected variable (if available).
        For DataArrays, extracts from the DataArray attrs.

        Can also extract metadata for specific coordinates/variables when key matches
        a coordinate or variable name.

        Parameters
        ----------
        key : str
            Metadata key or variable/coordinate name.
        default : Any
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value, coordinate attrs dict, or default.
        """
        # First check if key is a coordinate or variable name
        # If so, return its attrs as a dict
        if isinstance(self.data, xr.Dataset):
            # Check in data variables
            if key in self.data.data_vars:
                return dict(self.data[key].attrs) if self.data[key].attrs else {}
            # Check in coordinates
            if key in self.data.coords:
                return dict(self.data.coords[key].attrs) if self.data.coords[key].attrs else {}
        elif isinstance(self.data, xr.DataArray):
            # Check in coordinates
            if key in self.data.coords:
                return dict(self.data.coords[key].attrs) if self.data.coords[key].attrs else {}
            # Check in dimensions
            if key in self.data.dims and key in self.data.coords:
                return dict(self.data.coords[key].attrs) if self.data.coords[key].attrs else {}

        # Not a coordinate/variable name - look for metadata key in attrs
        # Prefer selected DataArray attrs if available (for Dataset case)
        if self._selected_dataarray is not None:
            if hasattr(self._selected_dataarray, "attrs"):
                return self._selected_dataarray.attrs.get(key, default)

        # Fall back to main data attrs
        if hasattr(self.data, "attrs"):
            return self.data.attrs.get(key, default)

        return default

    def get_crs(self) -> Optional[Any]:
        """
        Extract CRS from xarray data.

        Uses earthkit-data to convert xarray and extract projection information,
        which handles CF-convention grid_mapping and other metadata.

        Returns
        -------
        CRS or None
            Coordinate reference system (cartopy CRS) if found.
        """
        # Quick check: if 'crs' is directly in attrs, return it
        if hasattr(self.data, "attrs") and "crs" in self.data.attrs:
            return self.data.attrs["crs"]

        # Try to use earthkit-data to extract projection from CF conventions
        try:
            import earthkit.data as ek_data

            # Get the data to convert (prefer selected DataArray for Datasets)
            data_to_convert = self._selected_dataarray if self._selected_dataarray is not None else self.data

            # Convert to earthkit-data object
            earthkit_data = ek_data.from_object(data_to_convert)

            # Extract projection and convert to cartopy CRS
            if hasattr(earthkit_data, "projection"):
                projection = earthkit_data.projection()
                if projection is not None and hasattr(projection, "to_cartopy_crs"):
                    return projection.to_cartopy_crs()

        except (ImportError, AttributeError, Exception):
            # If earthkit-data is not available or conversion fails, return None
            pass

        return None

    def get_gridspec(self) -> Optional[Any]:
        """
        Extract gridspec from xarray attrs.

        Returns
        -------
        GridSpec or None
            Grid specification if found in metadata.
        """
        if hasattr(self.data, "attrs"):
            if "gridSpec" in self.data.attrs:
                return self.data.attrs["gridSpec"]
            if "grid_spec" in self.data.attrs:
                return self.data.attrs["grid_spec"]

        return None
