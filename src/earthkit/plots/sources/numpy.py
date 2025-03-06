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

from functools import cached_property

import numpy as np

from earthkit.plots.sources.single import SingleSource


class NumpySource(SingleSource):
    """
    A single source of data for a plot, capable of interpreting input as x, y, and z (or color) values.
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
        metadata=None,
        **kwargs,
    ):
        # Initialize attributes using BaseSource constructor
        super().__init__(*args, x=x, y=y, z=z, crs=crs, metadata=metadata, **kwargs)

        # Handle positional arguments for _data and coordinates
        if len(args) > 3:
            raise ValueError(
                f"{self.__class__.__name__} accepts at most three positional arguments (got {len(args)})."
            )

        if len(args) == 1:
            # Single positional argument: 1D or 2D data
            self._data = np.asarray(args[0])
        elif len(args) == 2:
            # Two positional arguments: interpret as x and y
            self._x, self._y = np.asarray(args[0]), np.asarray(args[1])
        elif len(args) == 3:
            # Three positional arguments: interpret as x, y, and z
            self._x, self._y, self._z = map(np.asarray, args)
            self._data = self._z

        # Infer x, y, z values from inputs
        self._x_values, self._y_values, self._z_values = self._infer_xyz()

    @cached_property
    def data(self):
        """Returns the data as a NumPy array."""
        return self._data

    def _infer_xyz(self):
        """Infers x, y, and z values based on inputs."""
        # Case 1: If _data is provided as a single positional argument
        if self._data is not None:
            if self._data.ndim == 1:
                # 1D data interpreted as y_values; x_values inferred or provided by keyword
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
                # 2D data interpreted as z_values; x and y inferred or provided by keyword
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
            # Case 2: Keyword arguments only
            if self._x is not None and self._y is not None:
                # Both x and y are provided explicitly
                x_values, y_values = np.asarray(self._x), np.asarray(self._y)
                z_values = np.asarray(self._z) if self._z is not None else None
            elif self._x is not None:
                # Only x provided; infer y as index range if not set
                x_values = np.asarray(self._x)
                y_values = (
                    np.arange(len(x_values)) if self._y is None else np.asarray(self._y)
                )
                z_values = None
            elif self._y is not None:
                # Only y provided; infer x as index range if not set
                y_values = np.asarray(self._y)
                x_values = (
                    np.arange(len(y_values)) if self._x is None else np.asarray(self._x)
                )
                z_values = None
            else:
                raise ValueError("Insufficient arguments to infer x and y.")

        # Ensure x and y values are 2D arrays
        # if x_values.ndim == 1:
        #     x_values, y_values = np.meshgrid(x_values, y_values)

        return x_values, y_values, z_values

    @property
    def x_values(self):
        """Returns the x values."""
        return self._x_values

    @property
    def y_values(self):
        """Returns the y values."""
        return self._y_values

    @property
    def z_values(self):
        """Returns the z values (or color values)."""
        return self._z_values

    @cached_property
    def units(self):
        """The units of the data, if specified in metadata."""
        result = self.metadata("units")
        if isinstance(result, list):
            result = result[0]
        return result
