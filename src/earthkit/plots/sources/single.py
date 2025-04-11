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

from earthkit.plots.sources import gridspec

_NO_EARTHKIT_REGRID = False
try:
    import earthkit.regrid
except ImportError:
    _NO_EARTHKIT_REGRID = True


class SingleSource:
    """
    A basic source class for plotting, providing a structure for defining x, y, z coordinates,
    optional metadata, and optional coordinate reference system (CRS).

    Parameters
    ----------
    *args : array-like
        Positional arguments representing the data to be plotted.
    x : array-like, optional
        The x-coordinates of the data.
    y : array-like, optional
        The y-coordinates of the data.
    z : array-like, optional
        The z-coordinates or values of the data.
    u : array-like, optional
        The u-component of the data.
    v : array-like, optional
        The v-component of the data.
    crs : object, optional
        The coordinate reference system of the data.
    metadata : dict, optional
        Metadata associated with the source, e.g., units or description.
    **kwargs : dict
        Additional keyword arguments to be attached as metadata.
    """

    def __init__(
        self,
        *args,
        x=None,
        y=None,
        z=None,
        u=None,
        v=None,
        crs=None,
        regrid=True,
        metadata=None,
        **kwargs,
    ):
        # Handle metadata and additional attributes
        self._x = x
        self._y = y
        self._z = z
        self._u = u
        self._v = v
        self._crs = crs
        self._metadata = metadata or {}
        self._metadata.update(kwargs)

        self._earthkit_data = None

        self._gridspec = None
        self.regrid = regrid

        # Automatically interpret *args based on length
        if len(args) > 3:
            raise ValueError(
                f"{self.__class__.__name__} accepts at most three positional arguments (got {len(args)})."
            )

        # Interpret args as data components
        self._data = None
        if len(args) == 1:
            # Single positional argument can be x or y data
            self._data = args[0]
            if isinstance(args[0], (np.ndarray, list)):
                self._data = np.asarray(self._data)
        elif len(args) == 2:
            # Two positional arguments: interpret as x and y
            self._x, self._y = map(np.asarray, args)
        elif len(args) == 3:
            # Three positional arguments: interpret as x, y, and z
            self._x, self._y, self._z = map(np.asarray, args)
            self._data = self._z

        # Infer x, y, z values from provided args and attributes
        self._x_values, self._y_values, self._z_values = self._infer_xyz()

    @property
    def gridspec(self):
        """
        The gridspec of the data.

        The gridspec is used to determine the grid type of the data, which is
        required for regridding more complex grid types like reduced Gaussian
        grids.
        """
        if self._gridspec is None:
            self._gridspec = gridspec.GridSpec.from_data(self.data)
        return self._gridspec

    def _infer_xyz(self):
        """Infers x, y, and z values based on args and provided x, y, and z attributes."""
        if self._data is not None:
            if self._data.ndim == 1:
                # 1D data interpreted as y_values, infer x_values if not provided
                y_values = self._data
                if self._x is not None:
                    x_values = np.asarray(self._x)
                elif self._y is not None:
                    # Interpret positional data as x_values if y is given
                    x_values = self._data
                    y_values = np.asarray(self._y)
                else:
                    x_values = np.arange(len(self._data))
                z_values = None
            elif self._data.ndim == 2:
                # 2D data interpreted as z_values, infer x and y if not provided
                x_values = (
                    np.arange(self._data.shape[1])
                    if self._x is None
                    else np.asarray(self._x)
                )
                y_values = (
                    np.arange(self._data.shape[0])
                    if self._y is None
                    else np.asarray(self._y)
                )
                z_values = self._data
            else:
                raise ValueError("Positional data must be 1D or 2D.")
        else:
            # Handle cases with no data and only x, y, or z provided
            if self._x is not None and self._y is not None:
                x_values, y_values = np.asarray(self._x), np.asarray(self._y)
                z_values = np.asarray(self._z) if self._z is not None else None
            elif self._x is not None:
                x_values = np.asarray(self._x)
                y_values = (
                    np.arange(len(x_values)) if self._y is None else np.asarray(self._y)
                )
                z_values = None
            elif self._y is not None:
                y_values = np.asarray(self._y)
                x_values = (
                    np.arange(len(y_values)) if self._x is None else np.asarray(self._x)
                )
                z_values = None
            else:
                raise ValueError("Insufficient arguments to infer x and y.")

        return x_values, y_values, z_values

    @property
    def data(self):
        """Returns the data, if present."""
        return self._data

    @property
    def x_values(self):
        """Returns the inferred or specified x values."""
        return self._x_values

    @property
    def y_values(self):
        """Returns the inferred or specified y values."""
        return self._y_values

    @property
    def z_values(self):
        """Returns the inferred or specified z values."""
        return self._z_values

    @property
    def u_values(self):
        """Returns the u values."""
        return self._u

    @property
    def v_values(self):
        """Returns the v values."""
        return self._v

    @property
    def magnitude(self):
        return (self.u_values**2 + self.v_values**2) ** 0.5

    @property
    def crs(self):
        """Returns the coordinate reference system (CRS) of the data."""
        return self._crs

    def metadata(self, key, default=None):
        """
        Retrieve a metadata value associated with the source.

        Parameters
        ----------
        key : str
            The key for the metadata to retrieve.
        default : any, optional
            The default value if the metadata key is not present.

        Returns
        -------
        any
            The value of the metadata or the default if not found.
        """
        return self._metadata.get(key, default)

    @property
    def units(self):
        """Returns the units of the data, if specified in metadata."""
        result = self.metadata("units")
        if isinstance(result, list):
            result = result[0]
        return result

    def to_earthkit(self):
        """Convert the data to an earthkit.data.core.Base object."""
        if self._earthkit_data is None:
            if not isinstance(self.data, (earthkit.data.core.Base)):
                self._earthkit_data = earthkit.data.from_object(self.data)
        return self._earthkit_data

    def datetime(self):
        """Returns the datetime values of the data."""
        return self.metadata("time")

    def mutate(self):
        return self
