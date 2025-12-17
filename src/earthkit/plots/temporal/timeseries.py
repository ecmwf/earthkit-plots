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
        self.ax.set_axisbelow(True)

    def _resample_data(self, data, resample_time, resample_method="mean", time_dim=None):
        """
        Resample time series data to a specified frequency.

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to resample. Must be xarray with a time dimension.
        resample_time : str
            The resampling frequency string (e.g., "6H" for 6-hourly, "D" for daily,
            "M" for monthly, "10D" for 10-day). Uses pandas frequency notation.
        resample_method : str, optional
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
                f"resample_time parameter requires xarray data. "
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
        if resample_method not in valid_agg_methods:
            raise ValueError(
                f"Invalid aggregation method '{resample_method}'. "
                f"Valid options: {valid_agg_methods}"
            )

        # Perform resampling
        try:
            resampler = data.resample({time_dim: resample_time})
            resampled_data = getattr(resampler, resample_method)()
            return resampled_data
        except Exception as e:
            raise ValueError(
                f"Failed to resample data with frequency '{resample_time}' "
                f"and aggregation '{resample_method}': {str(e)}"
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

    def line(self, *args, resample_time=None, resample_method="mean", time_dim=None, **kwargs):
        """
        Plot a line on the TimeSeries subplot with optional time resampling.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to parent line method.
        resample_time : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled before plotting. Requires xarray data.
        resample_method : str, optional
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
        # Resample data if resample_time is provided
        if resample_time is not None and len(args) > 0:
            args = list(args)
            args[0] = self._resample_data(args[0], resample_time, resample_method, time_dim)
            args = tuple(args)

        return super().line(*args, **kwargs)

    def scatter(self, *args, resample_time=None, resample_method="mean", time_dim=None, **kwargs):
        """
        Plot a scatter plot on the TimeSeries subplot with optional time resampling.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to parent scatter method.
        resample_time : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled before plotting. Requires xarray data.
        resample_method : str, optional
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
        # Resample data if resample_time is provided
        if resample_time is not None and len(args) > 0:
            args = list(args)
            args[0] = self._resample_data(args[0], resample_time, resample_method, time_dim)
            args = tuple(args)

        return super().scatter(*args, **kwargs)

    def bar(self, *args, resample_time=None, resample_method="mean", time_dim=None, **kwargs):
        """
        Plot a bar chart on the TimeSeries subplot with optional time resampling.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to parent bar method.
        resample_time : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled before plotting. Requires xarray data.
        resample_method : str, optional
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
        # Resample data if resample_time is provided
        if resample_time is not None and len(args) > 0:
            args = list(args)
            args[0] = self._resample_data(args[0], resample_time, resample_method, time_dim)
            args = tuple(args)

        return super().bar(*args, **kwargs)

    def multiboxplot(self, data, resample_time=None, resample_method="mean", time_dim=None, dim=None, units=None, xunits=None, yunits=None, color=None, **kwargs):
        """
        Plot a multiboxplot on the TimeSeries subplot with optional time resampling.

        For TimeSeries plots, this method automatically detects the time dimension and
        computes quantiles along the non-time dimension by default. This is useful for
        plotting ensemble forecasts or uncertainty bands where quantiles should be
        computed across ensemble members (not across time).

        Parameters
        ----------
        data : xarray.DataArray or xarray.Dataset
            The data to plot.
        resample_time : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled along the time dimension before computing quantiles.
            This reduces the number of boxes/time points displayed. Requires xarray data.
        resample_method : str, optional
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
            Additional keyword arguments to pass to parent multiboxplot method.

        Returns
        -------
        list of matplotlib artists
            The multiboxplot artists.
        """
        # Resample data if time_frequency is provided
        # For multiboxplot, we resample along the TIME dimension while preserving
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
        if resample_time is not None:
            data = self._resample_data(data, resample_time, resample_method, time_dim)

        # Pass the explicitly determined quantile dimension and units to parent
        return super().multiboxplot(data, dim=dim, units=units, xunits=xunits, yunits=yunits, color=color, **kwargs)

    def envelopes(self, data, resample_time=None, resample_method="mean", time_dim=None, dim=None, units=None, xunits=None, yunits=None, **kwargs):
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
        resample_time : str, optional
            Resampling frequency (e.g., "6H", "D", "M", "10D"). If provided,
            data will be resampled along the time dimension before computing quantiles.
            This reduces the number of envelope bands displayed. Requires xarray data.
        resample_method : str, optional
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
        if resample_time is not None:
            data = self._resample_data(data, resample_time, resample_method, time_dim)

        # Pass the explicitly determined quantile dimension and units to parent
        return super().envelopes(data, dim=dim, units=units, xunits=xunits, yunits=yunits, **kwargs)

    def xticks(
        self,
        frequency=None,
        minor_frequency=None,
        format=None,
        minor_format=None,
        period=False,
        labels="major",
        highlight_frequency=None,
        highlight_color='red',
        highlight_weight='bold',
        highlight_style='normal',
        boundary_format="auto",
        **kwargs
    ):
        """
        Set x-axis tick locations and formatting with time-aware enhancements.

        This method extends the parent xticks() with additional features for time series:
        - Highlighting ticks at specific frequencies (e.g., midnight, Sundays)
        - Automatic boundary labels when crossing month/year thresholds

        Parameters
        ----------
        frequency : str, optional
            Major tick frequency (e.g., "Y", "M6", "D7", "H").
            Default is None (auto).
        minor_frequency : str, optional
            Minor tick frequency. If None, uses frequency.
            Default is None.
        format : str, optional
            Format string for major tick labels (e.g., "%a %-d" for "Wed 31").
            Default is None (auto).
        minor_format : str, optional
            Format string for minor tick labels. If None and format is specified, uses format.
            Default is None.
        period : bool, optional
            If True, centers labels between ticks for better visual balance.
            Default is False.
        labels : str, optional
            Which tick labels to show: "major", "minor", "both", or None.
            Default is "major".
        highlight_frequency : str, optional
            Frequency at which to highlight ticks using pandas notation.
            Examples: 'D' for daily highlights on hourly data (midnight),
                     'W' for weekly highlights on daily data (Sundays).
            Default is None (no highlighting).
        highlight_color : str or tuple, optional
            Color for highlighted tick labels.
            Default is 'red'.
        highlight_weight : str, optional
            Font weight for highlighted labels: 'normal', 'bold', etc.
            Default is 'bold'.
        highlight_style : str, optional
            Font style for highlighted labels: 'normal', 'italic', etc.
            Default is 'normal'.
        boundary_format : dict, str, or None, optional
            Formatting for labels at boundary crossings (month/year changes).
            - If "auto" (default): adds month name ('%b') and year ('%Y') when boundaries
              are crossed
            - If dict: keys specify which boundaries to detect ('month', 'year', 'week', 'day'),
              values specify the format strings that appear on a newline below the base label
              e.g., {'month': '%Y'} shows the year when month changes
            - If None: no boundary formatting
        **kwargs
            Additional keyword arguments to pass to tick locators.

        Examples
        --------
        >>> # Daily data with day-of-week and date, month name when month changes
        >>> chart = TimeSeries()
        >>> chart.line(daily_data)
        >>> chart.xticks(frequency='D', format='%a %-d')
        >>> # Labels: "Wed 31", "Thu 1\nDec", "Fri 2", ...

        >>> # Hourly data with daily (midnight) highlights in red
        >>> chart.xticks(frequency='6H', format='%H:%M',
        ...              highlight_frequency='D', highlight_color='red')

        >>> # Daily data with weekly highlights and custom boundary format
        >>> chart.xticks(frequency='D', format='%-d',
        ...              highlight_frequency='W', highlight_color='blue',
        ...              boundary_format={'month': '%b', 'year': '%b %Y'})

        >>> # Disable boundary formatting
        >>> chart.xticks(frequency='D', format='%a %-d', boundary_format=None)
        """
        # First, call parent method to set up basic ticks
        super().xticks(
            frequency=frequency,
            minor_frequency=minor_frequency,
            format=format,
            minor_format=minor_format,
            period=period,
            labels=labels,
            **kwargs
        )

        # Only apply our enhancements if we have highlighting or boundary formatting to do
        has_highlighting = (highlight_frequency is not None)
        has_boundary_formatting = (boundary_format is not None and format is not None)

        if not has_highlighting and not has_boundary_formatting:
            return  # Nothing to do

        # In period mode, labels are on minor ticks; otherwise on major ticks
        if period:
            tick_locs = self.ax.get_xticks(minor=True)
            tick_labels = self.ax.get_xticklabels(minor=True)
        else:
            tick_locs = self.ax.get_xticks(minor=False)
            tick_labels = self.ax.get_xticklabels(minor=False)

        if len(tick_locs) == 0:
            return  # No ticks to process

        # Convert tick locations to datetime
        import matplotlib.dates as mdates
        import pandas as pd

        tick_times = [mdates.num2date(loc) for loc in tick_locs]
        tick_index = pd.DatetimeIndex(tick_times)

        # Process boundary labels FIRST
        # This must come before highlighting because set_xticklabels creates new label objects
        if boundary_format is not None and format is not None:
            new_labels = self._format_labels_with_boundaries(
                tick_index,
                format,
                boundary_format
            )
            # Set labels on the appropriate ticks (minor if period mode, major otherwise)
            if period:
                self.ax.set_xticklabels(new_labels, minor=True)
                # Refresh tick_labels after setting new labels
                tick_labels = self.ax.get_xticklabels(minor=True)
            else:
                self.ax.set_xticklabels(new_labels, minor=False)
                # Refresh tick_labels after setting new labels
                tick_labels = self.ax.get_xticklabels(minor=False)

        # Process highlights SECOND (can be done even in period mode)
        # This must come after boundary formatting so we highlight the final labels
        if highlight_frequency is not None:
            highlight_mask = self._get_highlight_mask(tick_index, highlight_frequency)
            self._apply_tick_highlights(
                tick_labels,
                highlight_mask,
                highlight_color,
                highlight_weight,
                highlight_style
            )

    def _get_highlight_mask(self, tick_index, highlight_frequency):
        """
        Determine which ticks should be highlighted based on frequency.

        Parameters
        ----------
        tick_index : pd.DatetimeIndex
            The tick times as a pandas DatetimeIndex.
        highlight_frequency : str
            Pandas frequency string for highlighting.

        Returns
        -------
        np.ndarray
            Boolean mask indicating which ticks to highlight.
        """
        import pandas as pd

        # Handle different frequency types
        # For fixed frequencies (D, H, T, S), we can use floor()
        # For non-fixed frequencies (W, M, Y), we need a different approach

        try:
            # Try using floor for fixed frequencies
            rounded = tick_index.floor(highlight_frequency)
            mask = (tick_index == rounded)
        except (ValueError, TypeError):
            # For non-fixed frequencies like 'W' (weekly), use a different approach
            # Check if each tick is at the start of the period for that frequency
            mask = np.zeros(len(tick_index), dtype=bool)

            if highlight_frequency.upper().startswith('W'):
                # Weekly: highlight Sundays (or Monday if that's the week start)
                # Default pandas week starts on Sunday (weekday=6)
                for i, dt in enumerate(tick_index):
                    # Check if this is a Sunday (weekday() returns 6 for Sunday)
                    mask[i] = (dt.weekday() == 6)
            elif highlight_frequency.upper().startswith('M'):
                # Monthly: highlight first day of month
                for i, dt in enumerate(tick_index):
                    mask[i] = (dt.day == 1)
            elif highlight_frequency.upper().startswith('Y'):
                # Yearly: highlight Jan 1
                for i, dt in enumerate(tick_index):
                    mask[i] = (dt.month == 1 and dt.day == 1)
            else:
                # Unknown frequency, return all False
                mask = np.zeros(len(tick_index), dtype=bool)

        return mask if isinstance(mask, np.ndarray) else mask.to_numpy()

    def _detect_boundaries(self, tick_index, boundary_levels):
        """
        Detect where time boundaries are crossed (month/year changes).

        Parameters
        ----------
        tick_index : pd.DatetimeIndex
            The tick times as a pandas DatetimeIndex.
        boundary_levels : list of str
            Which boundaries to check (e.g., ['month', 'year']).

        Returns
        -------
        dict
            Dictionary mapping boundary types ('year', 'month', etc.) to boolean masks.
        """
        if len(tick_index) < 2:
            return {}

        boundaries = {}

        for level in boundary_levels:
            mask = np.zeros(len(tick_index), dtype=bool)

            for i in range(1, len(tick_index)):
                curr = tick_index[i]
                prev = tick_index[i-1]

                if level == 'year':
                    mask[i] = (curr.year != prev.year)
                elif level == 'month':
                    mask[i] = (curr.month != prev.month)
                elif level == 'week':
                    mask[i] = (curr.isocalendar()[1] != prev.isocalendar()[1])
                elif level == 'day':
                    mask[i] = (curr.day != prev.day)

            boundaries[level] = mask

        return boundaries

    def _format_labels_with_boundaries(self, tick_index, base_format, boundary_format):
        """
        Generate tick labels with boundary-aware formatting.

        Boundary information is added on a newline below the base format.

        Parameters
        ----------
        tick_index : pd.DatetimeIndex
            The tick times.
        base_format : str
            Base format string for all labels.
        boundary_format : dict or str
            Boundary format specification. If "auto", uses default month/year formats.
            If dict, keys determine which boundaries to detect.

        Returns
        -------
        list of str
            Formatted tick labels with boundary information.
        """
        labels = []

        # Set up default boundary formats if using "auto"
        if boundary_format == "auto":
            boundary_format = {
                'year': '%Y',
                'month': '%b',
            }

        # Derive boundary levels from the keys in boundary_format
        boundary_levels = list(boundary_format.keys())

        # Detect boundaries
        boundaries = self._detect_boundaries(tick_index, boundary_levels)

        for i, tick_time in enumerate(tick_index):
            # Start with base format
            label = tick_time.strftime(base_format)

            # Check if we're at a boundary (skip first tick)
            if i > 0:
                # Determine highest priority boundary crossed
                # Priority order: year > month > week > day
                crossed_boundary = None
                for level in ['year', 'month', 'week', 'day']:
                    if level in boundaries and boundaries[level][i]:
                        crossed_boundary = level
                        break  # Take first (highest priority) match

                if crossed_boundary and isinstance(boundary_format, dict):
                    # Build boundary label parts
                    boundary_parts = []

                    if crossed_boundary == 'year':
                        # Year boundary: show both month and year
                        if 'month' in boundary_format:
                            boundary_parts.append(tick_time.strftime(boundary_format['month']))
                        if 'year' in boundary_format:
                            boundary_parts.append(tick_time.strftime(boundary_format['year']))
                    elif crossed_boundary == 'month':
                        # Month boundary: show only month
                        if 'month' in boundary_format:
                            boundary_parts.append(tick_time.strftime(boundary_format['month']))

                    # Add boundary info on newline if we have any
                    if boundary_parts:
                        label = f"{label}\n{' '.join(boundary_parts)}"

            labels.append(label)

        return labels

    def _apply_tick_highlights(self, tick_labels, highlight_mask, highlight_color, highlight_weight, highlight_style):
        """
        Apply visual highlighting to specific tick labels.

        Parameters
        ----------
        tick_labels : list
            The tick labels to potentially highlight.
        highlight_mask : np.ndarray
            Boolean mask indicating which ticks to highlight.
        highlight_color : str or tuple
            Color for highlighted labels.
        highlight_weight : str
            Font weight for highlighted labels.
        highlight_style : str
            Font style for highlighted labels.
        """
        for tick_label, should_highlight in zip(tick_labels, highlight_mask):
            if should_highlight:
                tick_label.set_color(highlight_color)
                tick_label.set_fontweight(highlight_weight)
                tick_label.set_fontstyle(highlight_style)

    def show(self, *args, **kwargs):
        getattr(self.ax, f"set_{self._time_axis}margin")(0)
        super().show(*args, **kwargs)

    def save(self, *args, **kwargs):
        getattr(self.ax, f"set_{self._time_axis}margin")(0)
        super().save(*args, **kwargs)
