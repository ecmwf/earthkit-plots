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

from earthkit.plots.temporal.timeseries import TimeSeries

CLASS_KWARGS = {
    "size",
}


def timeseries(
    data,
    *args,
    title="{variable_name}",
    xticks=None,
    yticks=None,
    xlabel=None,
    ylabel=None,
    plot="line",
    **kwargs
):
    """
    Create a time series plot with automatic configuration.

    This is a convenience function that creates a TimeSeries subplot with
    sensible defaults for time series visualization. It automatically handles
    time axis detection and applies appropriate formatting.

    .. warning::
        This function uses the experimental TimeSeries class. We welcome feedback
        and bug reports on GitHub issues: https://github.com/ecmwf/earthkit-plots/issues

    Parameters
    ----------
    data : array-like or earthkit data source
        The time series data to plot. Can be a numpy array, xarray DataArray,
        or any earthkit data source with time dimensions.
    *args : tuple
        Additional positional arguments passed to the plotting method.
    title : str, optional
        Title for the plot. Can include format strings like {variable_name},
        {base_time}, {valid_time}, etc. Default is "{variable_name}".
    xticks : str or dict, optional
        Configuration for x-axis ticks. If a string, treated as frequency
        (e.g., "Y", "M6", "D7", "h"). If a dict, passed as kwargs to xticks().
        Valid options are:
        - frequency : str, Major tick frequency (e.g., "Y", "M6", "D7", "h").
        - minor_frequency : str, Minor tick frequency. If None, uses frequency.
        - format : str, Format string for major tick labels.
        - minor_format : str, Format string for minor tick labels. If None and format is specified, uses format.
        - period : bool, If True, centers labels between ticks for better visual balance.
        - labels : str, Which tick labels to show: "major", "minor", "both", or None.
        - **kwargs : Additional keyword arguments to pass to the tick locators.
        Default is None (automatic).
    yticks : str or dict, optional
        Configuration for y-axis ticks. If a string, treated as frequency.
        If a dict, passed as kwargs to yticks(). Valid options are:
        - frequency : str, Major tick frequency (e.g., "Y", "M6", "D7", "h").
        - minor_frequency : str, Minor tick frequency. If None, uses frequency.
        - format : str, Format string for major tick labels.
        - minor_format : str, Format string for minor tick labels. If None and format is specified, uses format.
        - period : bool, If True, centers labels between ticks for better visual balance.
        - labels : str, Which tick labels to show: "major", "minor", "both", or None.
        - **kwargs : Additional keyword arguments to pass to the tick locators.
        Default is None (automatic).
    xlabel : str, optional
        Label for the x-axis. Default is None (automatic based on data).
    ylabel : str, optional
        Label for the y-axis. Default is None (automatic based on data).
    units : str, optional
        Units for the primary axis. Default is None (automatic based on data).
        The primary axis is guessed based on the structure of the data; if you
        want to specify the units for a specific axis, you can do so with the
        xunits and yunits parameters.
    xunits : str, optional
        Units for the x-axis. Default is None (automatic based on data).
    yunits : str, optional
        Units for the y-axis. Default is None (automatic based on data).
    plot : str, optional
        Plotting method to use. Options include "line", "scatter", "bar", etc.
        Default is "line".
    **kwargs : dict
        Additional keyword arguments passed to the plotting method and
        TimeSeries constructor. Special kwargs:
        - size : tuple, Figure size as (width, height). Default is (8, 4).

    Returns
    -------
    TimeSeries
        A configured TimeSeries subplot object.

    Examples
    --------
    Basic time series plot:
    >>> import numpy as np
    >>> import pandas as pd
    >>> times = pd.date_range("2020-01-01", periods=100, freq="D")
    >>> values = np.random.randn(100).cumsum()
    >>> ts = timeseries(values, x=times)
    >>> ts.show()

    With custom title and axis labels:
    >>> ts = timeseries(
    ...     data,
    ...     title="Temperature over time",
    ...     xlabel="Date",
    ...     ylabel="Temperature (°C)",
    ... )

    With custom tick formatting:
    >>> ts = timeseries(data, xticks="M3", yticks="auto")

    Scatter plot instead of line:
    >>> ts = timeseries(data, plot="scatter", s=20)

    Custom figure size:
    >>> ts = timeseries(data, size=(12, 6))
    """
    class_kwargs = {
        kwarg: kwargs.pop(kwarg) for kwarg in CLASS_KWARGS if kwarg in kwargs
    }
    ts = TimeSeries(**class_kwargs)

    getattr(ts, plot)(data, *args, **kwargs)
    ts.xlabel(xlabel)
    ts.ylabel(ylabel)

    if xticks is not None:
        if isinstance(xticks, str):
            ts.xticks(frequency=xticks)
        else:
            ts.xticks(**xticks)

    if yticks is not None:
        if isinstance(yticks, str):
            ts.yticks(frequency=yticks)
        else:
            ts.yticks(**yticks)

    ts.title(title)
    return ts
