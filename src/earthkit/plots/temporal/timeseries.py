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

from earthkit.plots.components.subplots import Subplot
from earthkit.plots.identifiers import find_time


class TimeSeries(Subplot):
    """
    A specialized Subplot class for time series plots.

    .. warning::
        This is an experimental new feature. We welcome feedback and bug reports
        on GitHub issues: https://github.com/ecmwf/earthkit-plots/issues

    This class inherits from Subplot and provides specialized functionality
    for plotting time series data, including automatic time axis detection
    and appropriate default sizing.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a TimeSeries subplot.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to Subplot constructor.
        **kwargs : dict
            Keyword arguments to pass to Subplot constructor.
            If 'size' is not provided, defaults to (8, 4).
        """
        warnings.warn(
            "TimeSeries is an experimental new feature in earthkit-plots. "
            "We welcome feedback and bug reports on GitHub issues: "
            "https://github.com/ecmwf/earthkit-plots/issues",
            UserWarning,
            stacklevel=2,
        )

        # Set default size if not provided
        if "size" not in kwargs:
            kwargs["size"] = (8, 4)

        super().__init__(*args, **kwargs)

    @property
    def _time_axis(self):
        """
        Determine which axis contains time data.

        Returns
        -------
        str
            'x' if time is on the x-axis, 'y' if time is on the y-axis.
            Returns 'x' as default if no time dimension is found.
        """
        if not self.layers:
            return "x"  # Default to x-axis if no layers

        # Check the first layer's source for time dimensions
        source = self.layers[0].sources[0]

        # Get the dimensions from the source
        if hasattr(source, "_data") and hasattr(source._data, "dims"):
            dims = list(source._data.dims)

            # Check if time dimension exists
            time_dim = find_time(dims)
            if time_dim:
                # Determine which axis this dimension corresponds to
                if hasattr(source, "_x") and source._x == time_dim:
                    return "x"
                elif hasattr(source, "_y") and source._y == time_dim:
                    return "y"
                else:
                    # If time dimension exists but isn't explicitly mapped,
                    # assume it's on the x-axis (common convention)
                    return "x"

        # Default to x-axis if no time dimension is found
        return "x"

    def show(self, *args, **kwargs):
        getattr(self.ax, f"set_{self._time_axis}margin")(0)
        super().show(*args, **kwargs)

    def save(self, *args, **kwargs):
        getattr(self.ax, f"set_{self._time_axis}margin")(0)
        super().save(*args, **kwargs)
