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

import numpy as np

from earthkit.plots.core.subplots import Subplot
from earthkit.plots.sources.identifiers import find_time


class TimeSeries(Subplot):
    """
    A specialised Subplot class for time series plots.

    This class inherits from Subplot and provides specialised functionality
    for plotting time series data, including automatic time axis detection,
    time-based resampling, and appropriate default sizing.
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
        # Set default size if not provided
        if "size" not in kwargs:
            kwargs["size"] = (8, 4)

        super().__init__(*args, **kwargs)

    def _resample_data(self, data, time_frequency, time_agg="mean", time_dim=None):
        """
        Resample time series data to a specified frequency.

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to resample. Must be xarray with a time dimension.
        time_frequency : str
            The resampling frequency string (e.g., "6H" for 6-hourly, "D" for daily,
            "M" for monthly, "10D" for 10-day). Uses pandas frequency notation.
        time_agg : str, optional
            The aggregation method to use. Options: "mean", "median", "min", "max",
            "sum", "std". Default is "mean".
        time_dim : str, optional
            The name of the time dimension. If None, will auto-detect using
            datetime dtype or common time dimension names.

        Returns
        -------
        xarray.DataArray or xarray.Dataset
            The resampled data.

        Raises
        ------
        TypeError
            If data is not an xarray DataArray or Dataset.
        ValueError
            If no time dimension can be found or if aggregation method is invalid.
        """
        import xarray as xr

        # Validate input type
        if not isinstance(data, (xr.DataArray, xr.Dataset)):
            raise TypeError(
                f"time_frequency parameter requires xarray data. "
                f"Got {type(data).__name__} instead. "
                f"Please provide xarray.DataArray or xarray.Dataset."
            )

        # Find time dimension if not specified
        if time_dim is None:
            # First, try to find dimension with datetime dtype
            for dim in data.dims:
                if np.issubdtype(data[dim].dtype, np.datetime64):
                    time_dim = dim
                    break

            # If not found, use find_time utility
            if time_dim is None:
                time_dim = find_time(list(data.dims))

            if time_dim is None:
                raise ValueError(
                    f"Could not auto-detect time dimension in data. "
                    f"Available dimensions: {list(data.dims)}. "
                    f"Please specify time_dim parameter explicitly."
                )

        # Validate time dimension exists
        if time_dim not in data.dims:
            raise ValueError(
                f"Time dimension '{time_dim}' not found in data. "
                f"Available dimensions: {list(data.dims)}"
            )

        # Validate aggregation method
        valid_agg_methods = ["mean", "median", "min", "max", "sum", "std"]
        if time_agg not in valid_agg_methods:
            raise ValueError(
                f"Invalid aggregation method '{time_agg}'. "
                f"Valid options: {valid_agg_methods}"
            )

        # Perform resampling
        try:
            resampler = data.resample({time_dim: time_frequency})
            resampled_data = getattr(resampler, time_agg)()
            return resampled_data
        except Exception as e:
            raise ValueError(
                f"Failed to resample data with frequency '{time_frequency}' "
                f"and aggregation '{time_agg}': {str(e)}"
            )

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

        # Check the first layer's dimension_set for time dimensions
        layer = self.layers[0]
        if not hasattr(layer, "dimension_set") or layer.dimension_set is None:
            return "x"  # Default if no dimension_set

        dimension_set = layer.dimension_set

        # Check if x dimension is a time dimension
        if hasattr(dimension_set.x, "axis") and dimension_set.x.axis == "T":
            return "x"

        # Check if y dimension is a time dimension
        if hasattr(dimension_set.y, "axis") and dimension_set.y.axis == "T":
            return "y"

        # Fallback: check dimension names for time-like names
        time_dim_name = find_time([dimension_set.x.name, dimension_set.y.name])
        if time_dim_name:
            if dimension_set.x.name == time_dim_name:
                return "x"
            elif dimension_set.y.name == time_dim_name:
                return "y"

        # Default to x-axis if no time dimension is found
        return "x"

    def line(self, *args, time_frequency=None, time_agg="mean", time_dim=None, **kwargs):
        """
        Plot a line on the TimeSeries subplot with optional time resampling.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to parent line method.
        time_frequency : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled before plotting. Requires xarray data.
        time_agg : str, optional
            Aggregation method for resampling. Options: "mean", "median", "min",
            "max", "sum", "std". Default is "mean".
        time_dim : str, optional
            Name of time dimension for resampling. If None, auto-detects.
        **kwargs : dict
            Additional keyword arguments to pass to parent line method.

        Returns
        -------
        matplotlib artist
            The line plot artist.
        """
        # Resample data if time_frequency is provided
        if time_frequency is not None and len(args) > 0:
            args = list(args)
            args[0] = self._resample_data(args[0], time_frequency, time_agg, time_dim)
            args = tuple(args)

        return super().line(*args, **kwargs)

    def scatter(self, *args, time_frequency=None, time_agg="mean", time_dim=None, **kwargs):
        """
        Plot a scatter plot on the TimeSeries subplot with optional time resampling.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to parent scatter method.
        time_frequency : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled before plotting. Requires xarray data.
        time_agg : str, optional
            Aggregation method for resampling. Options: "mean", "median", "min",
            "max", "sum", "std". Default is "mean".
        time_dim : str, optional
            Name of time dimension for resampling. If None, auto-detects.
        **kwargs : dict
            Additional keyword arguments to pass to parent scatter method.

        Returns
        -------
        matplotlib artist
            The scatter plot artist.
        """
        # Resample data if time_frequency is provided
        if time_frequency is not None and len(args) > 0:
            args = list(args)
            args[0] = self._resample_data(args[0], time_frequency, time_agg, time_dim)
            args = tuple(args)

        return super().scatter(*args, **kwargs)

    def bar(self, *args, time_frequency=None, time_agg="mean", time_dim=None, **kwargs):
        """
        Plot a bar chart on the TimeSeries subplot with optional time resampling.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to parent bar method.
        time_frequency : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled before plotting. Requires xarray data.
        time_agg : str, optional
            Aggregation method for resampling. Options: "mean", "median", "min",
            "max", "sum", "std". Default is "mean".
        time_dim : str, optional
            Name of time dimension for resampling. If None, auto-detects.
        **kwargs : dict
            Additional keyword arguments to pass to parent bar method.

        Returns
        -------
        matplotlib artist
            The bar chart artist.
        """
        # Resample data if time_frequency is provided
        if time_frequency is not None and len(args) > 0:
            args = list(args)
            args[0] = self._resample_data(args[0], time_frequency, time_agg, time_dim)
            args = tuple(args)

        return super().bar(*args, **kwargs)

    def boxenplot(self, data, time_frequency=None, time_agg="mean", time_dim=None, dim=None, units=None, xunits=None, yunits=None, color=None, **kwargs):
        """
        Plot a boxenplot on the TimeSeries subplot with optional time resampling.

        For TimeSeries plots, this method automatically detects the time dimension and
        computes quantiles along the non-time dimension by default. This is useful for
        plotting ensemble forecasts or uncertainty bands where quantiles should be
        computed across ensemble members (not across time).

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to plot.
        time_frequency : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled along the time dimension before computing quantiles.
            This reduces the number of boxes/time points displayed. Requires xarray data.
        time_agg : str, optional
            Aggregation method for resampling. Options: "mean", "median", "min",
            "max", "sum", "std". Default is "mean".
        time_dim : str, optional
            Name of time dimension for resampling. If None, auto-detects.
        dim : str, optional
            Name of dimension along which to compute quantiles. If None, auto-detects
            as the non-time dimension (or falls back to left-most dimension if no time
            dimension is found).
        units : str, optional
            Target units for the data values (y-axis). If specified, data will be
            automatically converted from source units to target units.
        xunits : str, optional
            Target units for the x-axis values.
        yunits : str, optional
            Target units for the y-axis values. Takes precedence over `units`.
        color : str or tuple, optional
            Color for the darkest (innermost) box. If None, uses matplotlib's color cycle
            to automatically assign colors.
        **kwargs : dict
            Additional keyword arguments to pass to parent boxenplot method.

        Returns
        -------
        list of matplotlib artists
            The boxenplot artists.
        """
        # Resample data if time_frequency is provided
        # For boxenplot, we resample along the TIME dimension while preserving
        # the ensemble/quantile dimension
        data = data.squeeze()

        # Determine quantile dimension from original squeezed data
        # For TimeSeries, default to the non-time dimension
        if dim is None:
            # Find the time dimension
            detected_time_dim = None

            # First, try to find dimension with datetime dtype
            for d in data.dims:
                if np.issubdtype(data[d].dtype, np.datetime64):
                    detected_time_dim = d
                    break

            # If not found, use find_time utility
            if detected_time_dim is None:
                detected_time_dim = find_time(list(data.dims))

            # If we found a time dimension, use the OTHER dimension for quantiles
            if detected_time_dim is not None and len(data.dims) >= 2:
                for d in data.dims:
                    if d != detected_time_dim:
                        dim = d
                        break
            # Otherwise, fall back to default behavior (left-most dimension)
            # by leaving dim as None - parent class will handle it

            # Store the detected time dimension for resampling if not explicitly provided
            if time_dim is None:
                time_dim = detected_time_dim

        # Resample the data
        if time_frequency is not None:
            data = self._resample_data(data, time_frequency, time_agg, time_dim)

        # Pass the explicitly determined quantile dimension and units to parent
        return super().boxenplot(data, dim=dim, units=units, xunits=xunits, yunits=yunits, color=color, **kwargs)

    def envelopes(self, data, time_frequency=None, time_agg="mean", time_dim=None, dim=None, units=None, xunits=None, yunits=None, **kwargs):
        """
        Plot quantile envelopes on the TimeSeries subplot with optional time resampling.

        For TimeSeries plots, this method automatically detects the time dimension and
        computes quantiles along the non-time dimension by default. This is useful for
        plotting ensemble forecasts or uncertainty bands where quantiles should be
        computed across ensemble members (not across time).

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to plot.
        time_frequency : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled along the time dimension before computing quantiles.
            This reduces the number of envelope bands displayed. Requires xarray data.
        time_agg : str, optional
            Aggregation method for resampling. Options: "mean", "median", "min",
            "max", "sum", "std". Default is "mean".
        time_dim : str, optional
            Name of time dimension for resampling. If None, auto-detects.
        dim : str, optional
            Name of dimension along which to compute quantiles. If None, auto-detects
            as the non-time dimension (or falls back to left-most dimension if no time
            dimension is found).
        units : str, optional
            Target units for the data values (y-axis). If specified, data will be
            automatically converted from source units to target units.
        xunits : str, optional
            Target units for the x-axis values.
        yunits : str, optional
            Target units for the y-axis values. Takes precedence over `units`.
        **kwargs : dict
            Additional keyword arguments to pass to parent envelopes method.

        Returns
        -------
        list of matplotlib artists
            The envelope band artists.
        """
        # Resample data if time_frequency is provided
        # For envelopes, we resample along the TIME dimension while preserving
        # the ensemble/quantile dimension
        data = data.squeeze()

        # Determine quantile dimension from original squeezed data
        # For TimeSeries, default to the non-time dimension
        if dim is None:
            # Find the time dimension
            detected_time_dim = None

            # First, try to find dimension with datetime dtype
            for d in data.dims:
                if np.issubdtype(data[d].dtype, np.datetime64):
                    detected_time_dim = d
                    break

            # If not found, use find_time utility
            if detected_time_dim is None:
                detected_time_dim = find_time(list(data.dims))

            # If we found a time dimension, use the OTHER dimension for quantiles
            if detected_time_dim is not None and len(data.dims) >= 2:
                for d in data.dims:
                    if d != detected_time_dim:
                        dim = d
                        break
            # Otherwise, fall back to default behavior (left-most dimension)
            # by leaving dim as None - parent class will handle it

            # Store the detected time dimension for resampling if not explicitly provided
            if time_dim is None:
                time_dim = detected_time_dim

        # Resample the data
        if time_frequency is not None:
            data = self._resample_data(data, time_frequency, time_agg, time_dim)

        # Pass the explicitly determined quantile dimension and units to parent
        return super().envelopes(data, dim=dim, units=units, xunits=xunits, yunits=yunits, **kwargs)

    def show(self, *args, **kwargs):
        getattr(self.ax, f"set_{self._time_axis}margin")(0)
        super().show(*args, **kwargs)

    def save(self, *args, **kwargs):
        getattr(self.ax, f"set_{self._time_axis}margin")(0)
        super().save(*args, **kwargs)
