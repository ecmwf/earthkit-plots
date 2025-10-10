# Copyright 2024, European Centre for Medium Range Weather Forecasts.
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

from functools import cached_property

import numpy as np

from earthkit.plots import identifiers
from earthkit.plots.sources.single import SingleSource


class TabularSource(SingleSource):
    """
    Source class for tabular data.

    Parameters
    ----------
    data : xarray.Dataset
        The data to be plotted.
    x : str, optional
        The x-coordinate variable in data.
    y : str, optional
        The y-coordinate variable in data.
    z : str, optional
        The z-coordinate variable in data.
    u : str, optional
        The u-component variable in data.
    v : str, optional
        The v-component variable in data.
    crs : cartopy.crs.CRS, optional
        The CRS of the data.
    **kwargs
        Metadata keys and values to attach to this Source.
    """

    @cached_property
    def data(self):
        """The underlying xarray data."""
        # Promote a column (e.g., pandas or polars Series) to a DataFrame
        if len(self._data.shape) == 1:
            return self._data.to_frame()
        return self._data

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
        if key == "variable_name":
            # 2D data: use label of z column
            if isinstance(self._z, str):
                return self._z
            # 1D data: use label of y column
            if isinstance(self._y, str):
                return self._y
        return super().metadata(key, default)

    @property
    def _nrows(self):
        return self.data.shape[0]

    @property
    def _ncols(self):
        return self.data.shape[1]

    def _column_values(self, name):
        return self.data[name].to_numpy().squeeze()

    @cached_property
    def x_values(self):
        # Column name specified explicitly or identified from standard set. Note
        # that this means that identified columns take precedence over the index
        # of a pandas DataFrame or Series.
        if self._x is None:
            self._x = identifiers.find_x(self.data.columns)
        if self._x is not None:
            return self._column_values(self._x)
        # Table has an index (e.g., pandas.DataFrame)
        if hasattr(self.data, "index"):
            x = self.data.index
            self._x = x.name
            return x.to_numpy()
        # Fallback: count upwards from 0
        return np.arange(self._nrows)

    @cached_property
    def y_values(self):
        # Column name specified explicitly or identified from standard set
        if self._y is None:
            self._y = identifiers.find_y(self.data.columns)
        if self._y is not None:
            return self._column_values(self._y)
        # Single-column dataset
        if self._ncols == 1:
            self._y = self.data.columns[0]
            return self.data.to_numpy().squeeze()
        return None

    @cached_property
    def z_values(self):
        if isinstance(self._z, str):
            return self._column_values(self._z)
        return None
