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
                raise ValueError(
                    "Multiple variables found in the xarray Dataset. Please specify a variable name with the 'z' parameter."
                )
        super().__init__(dataarray, x=x, y=y, z=z, **kwargs)
        self._data = dataarray

        self._x_values, self._y_values, self._z_values = self._infer_xyz()

    def _infer_xyz(self):
        """Infers x, y, and z values based on xarray input dimensions and provided names."""
        if isinstance(self._data, (xr.DataArray, xr.Dataset)):
            # If `x` and `y` are strings, interpret them as dimension names in the xarray object
            if isinstance(self._x, str):
                x_values = self._data[self._x].values
            else:
                x_dim = find_x(self._data.dims)
                x_values = (
                    self._data[x_dim].values
                    if x_dim
                    else np.arange(self._data.shape[-1])
                )

            if isinstance(self._y, str):
                y_values = self._data[self._y].values
            else:
                y_dim = find_y(self._data.dims)
                y_values = (
                    self._data[y_dim].values
                    if y_dim
                    else np.arange(self._data.shape[0])
                )

            # Handle z as a specified variable name within the xarray dataset or default to main data values
            if (
                isinstance(self._data, xr.Dataset)
                and isinstance(self._z, str)
                and self._z in list(self._data.variables)
            ):
                z_values = self._data[self._z].values
            elif isinstance(self._data, xr.DataArray):
                z_values = self._data.values
            else:
                raise ValueError(
                    f"Variable '{self._z}' not found in the xarray dataset."
                )

        else:
            # Fall back to base Source handling if not xarray input
            return super()._infer_xyz()

        return x_values, y_values, z_values

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
