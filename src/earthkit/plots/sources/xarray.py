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

import earthkit.data
import numpy as np
import xarray as xr

from earthkit.plots.identifiers import find_time, find_u, find_v, find_x, find_y
from earthkit.plots.sources.single import SingleSource
from earthkit.plots.utils import time_utils


class XarraySource(SingleSource):
    """
    A data source for xarray-like inputs, extending Source with additional support
    for identifying x, y, and z dimensions within an xarray Dataset or DataArray.

    Parameters
    ----------
    dataarray : xarray.Dataset or xarray.DataArray
        The xarray data to use as the source.
    x : str or array-like, optional
        The x-coordinate name or values of the data.
    y : str or array-like, optional
        The y-coordinate name or values of the data.
    z : str or array-like, optional
        The z-coordinate name or values of the data.
    u : array-like, optional
        The u-component of the data.
    v : array-like, optional
        The v-component of the data.
    crs : cartopy.crs.CRS, optional
        The CRS of the data.
    style : str, optional
        The style to use when plotting the data.
    metadata : dict, optional
        Metadata to attach to this Source.
    **kwargs
        Additional metadata keys and values to attach to this Source.
    """

    def __init__(self, dataarray, x=None, y=None, z=None, **kwargs):
        dataarray = dataarray.squeeze()
        self._xarray_source = dataarray
        if isinstance(dataarray, xr.Dataset):
            if z is not None:
                dataarray = dataarray[z]
            elif len(dataarray.data_vars) == 1:
                dataarray = dataarray[list(dataarray.data_vars)[0]]
            else:
                # Find the variable with coordinate dimensions
                key_var = self._find_key_variable(dataarray)
                if key_var is not None:
                    dataarray = dataarray[key_var]
                else:
                    raise ValueError(
                        "Multiple variables found in the xarray Dataset. Please specify a variable name with the 'z' parameter."
                    )
        super().__init__(dataarray, x=x, y=y, z=z, **kwargs)
        self._data = dataarray

        self._x_values, self._y_values, self._z_values = self._infer_xyz()

    def _find_key_variable(self, dataset):
        """
        Find the variable that has coordinate dimensions (the main data variable).

        Parameters
        ----------
        dataset : xr.Dataset
            The xarray Dataset to analyze

        Returns
        -------
        str or None
            The name of the key variable, or None if multiple variables have coordinate dimensions
        """
        variables_with_coords = []

        for var_name, var in dataset.data_vars.items():
            # Check if this variable has any coordinate dimensions
            if any(dim in dataset.coords for dim in var.dims):
                variables_with_coords.append(var_name)

        # If exactly one variable has coordinate dimensions, that's our key variable
        if len(variables_with_coords) == 1:
            return variables_with_coords[0]

        # If multiple variables have coordinate dimensions, we can't auto-select
        # If no variables have coordinate dimensions, we also can't auto-select
        return None

    def _infer_xyz(self):
        """Infers x, y, and z values based on xarray input dimensions and provided names."""
        if self._x is not None or self._y is not None or self._z is not None:
            return self._explicit_xyz()
        else:
            return self._implicit_xyz()

    def _implicit_xyz(self):
        """Default identification of x, y and z when self._x, self._y and self._z are all None."""
        data_shape = self._data.shape
        data_dims = list(self._data.dims)

        # Case 1: Single 1D array of dimensionless data
        if len(data_shape) == 1 and len(data_dims) == 0:
            # Data is dimensionless 1D array - use as y_values with index as x_values
            x_values = np.arange(data_shape[0])
            y_values = self._data.values
            z_values = None
            self._x = None
            self._y = self._data.name if hasattr(self._data, "name") else None
            self._z = None
            return x_values, y_values, z_values

        # Case 2: 1D data with one dimension (e.g., time series)
        elif len(data_shape) == 1 and len(data_dims) == 1:
            dim_name = data_dims[0]
            # The dimension's values become x_values, variable values become y_values
            x_values = self._data[dim_name].values
            y_values = self._data.values
            z_values = None
            self._x = dim_name
            self._y = self._data.name if hasattr(self._data, "name") else None
            self._z = None
            return x_values, y_values, z_values

        # Case 3: 2D data
        elif len(data_shape) == 2:
            # Try to identify x and y dimensions using find_x and find_y
            x_dim = find_x(self._data.dims)
            y_dim = find_y(self._data.dims)

            # If identification fails, assume first dimension is x and second is y
            if x_dim is None:
                x_dim = data_dims[0]
            if y_dim is None:
                y_dim = data_dims[1]

            x_values = self._data[x_dim].values
            y_values = self._data[y_dim].values
            z_values = self._data.values

            self._x = x_dim
            self._y = y_dim
            self._z = self._data.name if hasattr(self._data, "name") else None
            return x_values, y_values, z_values

        # Case 4: Higher dimensional data (3D+)
        else:
            x_dim = find_x(self._data.dims)
            x_values = (
                self._data[x_dim].values if x_dim else np.arange(self._data.shape[-1])
            )

            y_dim = find_y(self._data.dims)
            y_values = (
                self._data[y_dim].values if y_dim else np.arange(self._data.shape[0])
            )

            # Handle z values - for DataArray use the data values, for Dataset this should not happen
            # since we select a single variable in __init__
            if isinstance(self._data, xr.DataArray):
                z_values = self._data.values
            else:
                raise ValueError(
                    "Cannot determine z values for Dataset without explicit variable selection."
                )

            self._x = x_dim
            self._y = y_dim
            self._z = self._data.name if hasattr(self._data, "name") else None
            return x_values, y_values, z_values

    def _explicit_xyz(self):
        """Handle explicit x, y, z values when any of self._x, self._y, self._z are not None."""
        data_shape = self._data.shape

        if len(data_shape) == 1:
            return self._explicit_xyz_1d()

        elif len(data_shape) == 2:
            return self._explicit_xyz_2d()

        else:
            return self._explicit_xyz_nd()

    def _explicit_xyz_1d(self):
        """Handle explicit x, y arguments for 1D data."""
        data_dims = list(self._data.dims)

        # Case 1: Both x and y are provided
        if self._x is not None and self._y is not None:
            x_values = self._get_coordinate_or_variable_values(self._x)
            y_values = self._get_coordinate_or_variable_values(self._y)
            z_values = None

        # Case 2: Only x is provided
        elif self._x is not None:
            x_values = self._get_coordinate_or_variable_values(self._x)
            if self._x in data_dims:
                # x is a dimension name, so y should be the variable values
                y_values = self._data.values
                # Set y to the variable name (DataArray name or None)
                y_name = self._data.name if hasattr(self._data, "name") else None
            else:
                # x is a variable name, so y should be the dimension values
                # Find the dimension that's not x
                remaining_dims = [dim for dim in data_dims if dim != self._x]
                if remaining_dims:
                    y_values = self._data[remaining_dims[0]].values
                    y_name = remaining_dims[0]
                else:
                    # No other dimensions, use index array
                    y_values = np.arange(len(x_values))
                    y_name = None
            z_values = None

            # Set the y attribute for the implicitly identified coordinate
            if y_name is not None:
                self._y = y_name

        # Case 3: Only y is provided
        elif self._y is not None:
            y_values = self._get_coordinate_or_variable_values(self._y)
            if self._y in data_dims:
                # y is a dimension name, so x should be the variable values
                x_values = self._data.values
                # Set x to the variable name (DataArray name or None)
                x_name = self._data.name if hasattr(self._data, "name") else None
            else:
                # y is a variable name, so x should be the dimension values
                # Find the dimension that's not y
                remaining_dims = [dim for dim in data_dims if dim != self._y]
                if remaining_dims:
                    x_values = self._data[remaining_dims[0]].values
                    x_name = remaining_dims[0]
                else:
                    # No other dimensions, use index array
                    x_values = np.arange(len(y_values))
                    x_name = None
            z_values = None

            # Set the x attribute for the implicitly identified coordinate
            if x_name is not None:
                self._x = x_name

        # Case 4: Only z is provided (unusual for 1D, but handle gracefully)
        elif self._z is not None:
            z_values = self._get_coordinate_or_variable_values(self._z)
            # For 1D data, if only z is provided, we need to infer x and y
            if len(data_dims) == 1:
                x_values = self._data[data_dims[0]].values
                y_values = np.arange(len(x_values))
            else:
                x_values = np.arange(len(z_values))
                y_values = np.arange(len(z_values))
        else:
            # This shouldn't happen given the calling logic, but handle gracefully
            raise ValueError("No explicit x, y, or z values provided")

        return x_values, y_values, z_values

    def _explicit_xyz_2d(self):
        """Handle explicit x, y arguments for 2D data."""
        data_dims = list(self._data.dims)

        # Case 1: All three (x, y, z) are provided
        if self._x is not None and self._y is not None and self._z is not None:
            x_values = self._get_coordinate_or_variable_values(self._x)
            y_values = self._get_coordinate_or_variable_values(self._y)
            z_values = self._get_coordinate_or_variable_values(self._z)

        # Case 2: x and y are provided, z is not
        elif self._x is not None and self._y is not None:
            x_values = self._get_coordinate_or_variable_values(self._x)
            y_values = self._get_coordinate_or_variable_values(self._y)
            # For 2D data, z values are the data values
            z_values = self._data.values

        # Case 3: Only x is provided
        elif self._x is not None:
            x_values = self._get_coordinate_or_variable_values(self._x)
            # Find y from remaining dimensions using identifiers
            remaining_dims = [dim for dim in data_dims if dim != self._x]
            y_dim = find_y(remaining_dims) if remaining_dims else None

            if y_dim is None and remaining_dims:
                # If no y dimension found, use the first remaining dimension
                y_dim = remaining_dims[0]

            if y_dim:
                y_values = self._data[y_dim].values
            else:
                # No other dimensions, use index array
                y_values = np.arange(self._data.shape[0])

            z_values = self._data.values

            # Set the y attribute for the implicitly identified coordinate
            if y_dim:
                self._y = y_dim

        # Case 4: Only y is provided
        elif self._y is not None:
            y_values = self._get_coordinate_or_variable_values(self._y)
            # Find x from remaining dimensions using identifiers
            remaining_dims = [dim for dim in data_dims if dim != self._y]
            x_dim = find_x(remaining_dims) if remaining_dims else None

            if x_dim is None and remaining_dims:
                # If no x dimension found, use the first remaining dimension
                x_dim = remaining_dims[0]

            if x_dim:
                x_values = self._data[x_dim].values
            else:
                # No other dimensions, use index array
                x_values = np.arange(self._data.shape[1])

            z_values = self._data.values

            # Set the x attribute for the implicitly identified coordinate
            if x_dim:
                self._x = x_dim

        # Case 5: Only z is provided
        elif self._z is not None:
            z_values = self._get_coordinate_or_variable_values(self._z)
            # Find x and y from dimensions using identifiers
            x_dim = find_x(data_dims)
            y_dim = find_y(data_dims)

            # If identifiers fail, assume first dimension is x and second is y
            if x_dim is None:
                x_dim = data_dims[0] if data_dims else None
            if y_dim is None:
                y_dim = data_dims[1] if len(data_dims) > 1 else None

            if x_dim and y_dim:
                x_values = self._data[x_dim].values
                y_values = self._data[y_dim].values
            elif x_dim:
                x_values = self._data[x_dim].values
                y_values = np.arange(self._data.shape[0])
            elif y_dim:
                x_values = np.arange(self._data.shape[1])
                y_values = self._data[y_dim].values
            else:
                # No dimensions found, use index arrays
                x_values = np.arange(self._data.shape[1])
                y_values = np.arange(self._data.shape[0])

            # Set the x and y attributes for the implicitly identified coordinates
            if x_dim:
                self._x = x_dim
            if y_dim:
                self._y = y_dim

        else:
            # This shouldn't happen given the calling logic, but handle gracefully
            raise ValueError("No explicit x, y, or z values provided for 2D data")

        return x_values, y_values, z_values

    def _explicit_xyz_nd(self):
        """Handle explicit x, y arguments for higher dimensional data."""
        # TODO: Implement higher dimensional explicit xyz handling
        # This method should handle cases where x, y, or z are explicitly provided
        # for 3D+ data
        pass

    def _get_coordinate_or_variable_values(self, name):
        """Get values for a coordinate or variable name."""
        if isinstance(name, str):
            # Check if it's a dimension name
            if name in self._data.dims:
                return self._data[name].values
            # Check if it's a variable name (for datasets)
            elif hasattr(self._data, "data_vars") and name in self._data.data_vars:
                return self._data[name].values
            # Check if it's a coordinate name
            elif name in self._data.coords:
                return self._data[name].values
            # Check if it matches the DataArray name attribute
            elif hasattr(self._data, "name") and self._data.name == name:
                return self._data.values
            else:
                raise ValueError(
                    f"'{name}' not found in dimensions, data variables, coordinates, or DataArray name"
                )
        else:
            # If not a string, assume it's already an array-like value
            return np.asarray(name)

    @property
    def data(self):
        """Return the original xarray data, if provided."""
        return self._data

    @staticmethod
    def extract_u(data, u=None):
        """Return the u-component values of the data, if found."""
        u_data = None
        if u is not None:
            u_data = data[u]
        else:
            u_var = find_u(data.data_vars)
            if u_var:
                u_data = data[u_var]
        return u_data

    @staticmethod
    def extract_v(data, v=None):
        """Return the v-component values of the data, if found."""
        v_data = None
        if v is not None:
            v_data = data[v]
        else:
            v_var = find_v(data.data_vars)
            if v_var:
                v_data = data[v_var]
        return v_data

    @property
    def z_values(self):
        """Returns the inferred or provided z values (or color values)."""
        return self._z_values

    def metadata(self, key, default=None):
        """
        Extract metadata from the data.

        Parameters
        ----------
        key : str
            The metadata key to extract.
        default : any, optional
            The default value to return if the key is not found.
        """
        value = super().metadata(key, default)
        if value == default:
            if key in self.data.attrs:
                value = self.data.attrs[key]
            elif hasattr(self.data, key):
                value = getattr(self.data, key)
            elif hasattr(self._xarray_source, key):
                value = getattr(self._xarray_source, key)
            if hasattr(value, "values"):
                value = value.values
        return value

    @property
    def crs(self):
        """The CRS of the data."""
        if self._crs is None:
            earthkit_data = self.to_earthkit()
            try:
                self._crs = earthkit_data.projection().to_cartopy_crs()
            except ValueError:
                try:
                    self._crs = earthkit_data[0].projection().to_cartopy_crs()
                except (AttributeError, NotImplementedError):
                    self._crs = None
            except (AttributeError, NotImplementedError):
                self._crs = None
        return self._crs

    def to_earthkit(self):
        """Convert the data to an earthkit.data.core.Base object."""
        if self._earthkit_data is None:
            self._earthkit_data = earthkit.data.from_object(self._xarray_source)
        return self._earthkit_data

    def datetime(self):
        """Get the datetime of the data."""
        from datetime import datetime

        datetimes = None
        time_coord = find_time(self.data)
        if time_coord is not None:
            datetimes = [
                time_utils.to_pydatetime(dt)
                for dt in np.atleast_1d(self.data[time_coord])
            ]
        else:
            if all(key in self._xarray_source.attrs for key in ("date", "time")):
                date = self._xarray_source.attrs["date"]
                time = self._xarray_source.attrs["time"]
                datetimes = [datetime.strptime(f"{date}{time:04d}", "%Y%m%d%H%M")]
        return {
            "base_time": datetimes,
            "valid_time": datetimes,
        }

    def _axis_metadata(self, name):
        """Get metadata for a coordinate or variable name."""
        if isinstance(name, str):
            if name in self._data.dims:
                attrs = self._data[name].attrs
            elif hasattr(self._data, "data_vars") and name in self._data.data_vars:
                attrs = self._data[name].attrs
            elif name in self._data.coords:
                attrs = self._data[name].attrs
            elif hasattr(self._data, "name") and self._data.name == name:
                attrs = self._data.attrs
            else:
                attrs = {}
            if not attrs:
                attrs = {
                    "long_name": name,
                }
            return attrs

    @property
    def x_metadata(self):
        """Returns metadata for the x coordinate."""
        return self._axis_metadata(self._x)

    @property
    def y_metadata(self):
        """Returns metadata for the y coordinate."""
        return self._axis_metadata(self._y)

    @property
    def z_metadata(self):
        """Returns metadata for the z coordinate."""
        return self._axis_metadata(self._z)
