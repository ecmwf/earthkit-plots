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

import calendar
import functools
import re

import numpy as np
import pandas as pd

from earthkit.plots.components.subplots import Subplot
from earthkit.plots.identifiers import find_time

_OFFSET_RE = re.compile(r"^(-?)(\d+)([A-Za-z]+)$")


def _coerce_year_dim_to_datetime(data):
    """
    If *data* has an integer-valued ``year`` dimension, replace it with a
    ``datetime64[ns]`` coordinate set to Jan 1 of each year.

    This allows matplotlib's date locators (e.g. ``YearLocator``) to work
    correctly when the user's data is indexed by plain year integers.
    """
    import xarray as xr

    if not isinstance(data, (xr.DataArray, xr.Dataset)):
        return data

    dims = list(data.dims)
    time_dim = find_time(dims)
    if time_dim is None:
        return data

    coord = data[time_dim]
    if np.issubdtype(coord.dtype, np.datetime64):
        return data  # already datetime, nothing to do

    if np.issubdtype(coord.dtype, np.integer):
        years = coord.values.astype(int)
        dt = np.array([f"{y}-01-01" for y in years], dtype="datetime64[ns]")
        return data.assign_coords({time_dim: dt})

    return data


_VALID_RESAMPLE_METHODS = ("mean", "median", "min", "max", "sum", "std")


def _parse_time_offset(s):
    """
    Parse a time-offset string into a :class:`pandas.Timedelta` or
    :class:`pandas.DateOffset`.

    Supported suffixes (case-insensitive):

    * ``H``, ``min``, ``s``, ``D``, ``W`` → :class:`pandas.Timedelta`
    * ``M`` (months), ``Y`` (years) → :class:`pandas.DateOffset`

    A leading ``-`` negates the offset.

    Examples: ``"12H"``, ``"-6H"``, ``"1D"``, ``"3M"``, ``"-1Y"``

    Raises
    ------
    ValueError
        If the string cannot be parsed or the unit is not recognised.
    """
    m = _OFFSET_RE.match(s.strip())
    if not m:
        raise ValueError(
            f"Cannot parse time_offset {s!r}. "
            "Expected a string like '12H', '-6H', '1D', '2W', '3M', '-1Y'."
        )
    sign_str, n_str, unit = m.groups()
    n = int(n_str)
    if sign_str == "-":
        n = -n

    unit_up = unit.upper()
    _td_units = {"H": "h", "MIN": "min", "S": "s", "D": "D", "W": "W"}
    if unit_up in _td_units:
        return pd.Timedelta(n, unit=_td_units[unit_up])
    elif unit_up == "M":
        return pd.DateOffset(months=n)
    elif unit_up == "Y":
        return pd.DateOffset(years=n)
    else:
        raise ValueError(
            f"Unrecognised time_offset unit {unit!r} in {s!r}. "
            "Supported units: H, min, s, D, W, M, Y."
        )


def _resample(da, freq, method="mean", time_dim=None):
    """
    Resample a DataArray along its time dimension.

    Parameters
    ----------
    da : xarray.DataArray
        Data to resample.  Non-DataArray inputs are returned unchanged.
    freq : str
        Pandas-compatible resampling frequency (e.g. ``"6h"``, ``"D"``).
    method : str, optional
        Aggregation method.  One of ``"mean"``, ``"median"``, ``"min"``,
        ``"max"``, ``"sum"``, ``"std"``.  Default ``"mean"``.
    time_dim : str, optional
        Name of the time dimension.  Auto-detected if ``None``.

    Returns
    -------
    xarray.DataArray
        Resampled data, or *da* unchanged if it has no time dimension.
    """
    import xarray as xr

    if not isinstance(da, xr.DataArray):
        return da

    if method not in _VALID_RESAMPLE_METHODS:
        raise ValueError(
            f"Invalid resample_method {method!r}. "
            f"Choose from: {_VALID_RESAMPLE_METHODS}"
        )

    if time_dim is None:
        for d in da.dims:
            if np.issubdtype(da[d].dtype, np.datetime64):
                time_dim = d
                break
        if time_dim is None:
            time_dim = find_time(list(da.dims))

    if time_dim is None:
        return da  # no time dim found — pass through unchanged

    return getattr(da.resample({time_dim: freq}), method)()


def _with_resampling(func):
    """
    Decorator that injects ``resample`` / ``resample_method`` keyword
    arguments into any :class:`TimeSeries` plotting method.

    When ``resample`` is supplied the decorator auto-detects every
    :class:`xarray.DataArray` in the positional arguments and resamples
    each one before the method body runs.  The ``resample`` and
    ``resample_method`` keys are consumed and never forwarded.
    """

    @functools.wraps(func)
    def wrapper(self, *args, resample=None, resample_method="mean", **kwargs):
        if resample is not None:
            args = tuple(_resample(a, resample, resample_method) for a in args)
        return func(self, *args, **kwargs)

    return wrapper


def _apply_time_offset(da, offset, time_dim=None):
    """
    Return a copy of *da* with its time coordinate shifted by *offset*.

    *offset* should be a :class:`pandas.Timedelta` (vectorised) or a
    :class:`pandas.DateOffset` (applied element-wise, needed for months/years).

    If no time coordinate can be found the DataArray is returned unchanged.
    Non-DataArray inputs are returned unchanged (silent no-op).

    Parameters
    ----------
    da : xarray.DataArray or any
        Data to shift.  Non-DataArray inputs pass through unmodified.
    offset : pandas.Timedelta or pandas.DateOffset
        Amount to shift the time coordinate.
    time_dim : str, optional
        Name of the time dimension.  Auto-detected if ``None``.
    """
    import xarray as xr

    if not isinstance(da, xr.DataArray):
        return da

    if time_dim is None:
        time_dim = find_time(list(da.dims))

    if time_dim is None or time_dim not in da.coords:
        return da

    old_times = pd.DatetimeIndex(da[time_dim].values)
    if isinstance(offset, pd.Timedelta):
        new_times = old_times + offset
    else:
        # DateOffset (months / years) — must be applied per element
        new_times = pd.DatetimeIndex([t + offset for t in old_times])

    return da.assign_coords({time_dim: new_times})


def _tile_clim_to_years(da, years, month_day=15, extend=False):
    """
    Tile a climatology DataArray with a ``month`` (1–12) or ``dayofyear``
    (1–366) dimension across a sequence of real calendar years.

    Returns a new DataArray with a real ``time`` coordinate spanning all
    requested years, suitable for plotting on a :class:`TimeSeries` subplot
    alongside actual observational data.

    Parameters
    ----------
    da : xarray.DataArray
        A 1-D DataArray with either a ``month`` (1–12) or ``dayofyear``
        (1–366) integer dimension.  Extra dimensions (e.g. latitude,
        longitude) are preserved.
    years : iterable of int
        Calendar years to tile the climatology over (e.g. ``range(2015, 2018)``
        produces 2015, 2016, 2017).
    month_day : int, optional
        Day of month on which to place each monthly value.  Default is ``15``.
        Only relevant for ``month``-dimensioned data.
    extend : bool, optional
        If ``True``, prepend one extra year before the first requested year
        and append one extra year after the last, so that the tiled data
        extends smoothly past the plot edges without changing the x-axis
        range.  Default ``False``.

    Returns
    -------
    xarray.DataArray
        A new DataArray whose time dimension contains real calendar
        timestamps (one per (year, month) or (year, dayofyear) pair),
        ordered chronologically.

    Raises
    ------
    ValueError
        If *da* has neither a ``month`` nor a ``dayofyear`` dimension.
    """
    import xarray as xr

    if "month" in da.dims:
        clim_dim = "month"
    elif "dayofyear" in da.dims:
        clim_dim = "dayofyear"
    else:
        raise ValueError(
            "_tile_clim_to_years() requires a DataArray with a 'month' or "
            "'dayofyear' dimension."
        )

    years = list(years)
    if extend:
        years = [years[0] - 1] + years + [years[-1] + 1]

    pieces = []
    for year in years:
        vals = da[clim_dim].values.astype(int)
        if clim_dim == "month":
            dates = []
            for m in vals:
                # Clamp month_day to the actual number of days in the month.
                n_days = calendar.monthrange(year, int(m))[1]
                day = min(int(month_day), n_days)
                dates.append(pd.Timestamp(year, int(m), day))
        else:  # dayofyear
            ref = pd.Timestamp(year, 1, 1)
            dates = [ref + pd.Timedelta(days=int(d) - 1) for d in vals]

        # Build a copy of da with clim_dim replaced by the real time coord.
        scalar_coords = {
            name: da.coords[name]
            for name in da.coords
            if name != clim_dim and da.coords[name].ndim == 0
        }
        scalar_coords["time"] = dates

        other_dims = [d for d in da.dims if d != clim_dim]
        if other_dims:
            # Multi-dimensional: clim_dim is not the only dim.
            # We need to reassign coords including the new time.
            new_coords = {
                name: da.coords[name] for name in da.coords if name != clim_dim
            }
            new_coords["time"] = dates
            piece = da.assign_coords({clim_dim: dates}).rename({clim_dim: "time"})
        else:
            piece = xr.DataArray(
                da.values,
                coords=scalar_coords,
                dims=["time"],
                attrs=da.attrs,
            )
        pieces.append(piece)

    result = xr.concat(pieces, dim="time")
    result.attrs.update(da.attrs)
    return result


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
                if hasattr(source, "_x_spec") and source._x_spec == time_dim:
                    return "x"
                elif hasattr(source, "_y_spec") and source._y_spec == time_dim:
                    return "y"
                else:
                    # If time dimension exists but isn't explicitly mapped,
                    # assume it's on the x-axis (common convention)
                    return "x"

        # Default to x-axis if no time dimension is found
        return "x"

    def _apply_tight_time_axis(self):
        """Set zero margin on the time axis so the plot extent is tight."""
        getattr(self.ax, f"set_{self._time_axis}margin")(0)

    @_with_resampling
    def line(
        self,
        data,
        *args,
        time_offset=None,
        repeat_years=None,
        month_day=15,
        extend_years=False,
        **kwargs,
    ):
        """
        Plot a line on the TimeSeries subplot.

        Extends :meth:`~earthkit.plots.components.subplots.Subplot.line` with
        the ``time_offset``, ``resample`` / ``resample_method``, and
        ``repeat_years`` parameters.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            Data to plot.  If *data* has a ``month`` or ``dayofyear``
            dimension and *repeat_years* is given, the climatology is tiled
            across those years automatically.
        time_offset : str, optional
            Shift the time coordinate by this amount before plotting.
            Accepts strings such as ``"12H"``, ``"-6H"``, ``"1D"``,
            ``"3M"``, ``"-1Y"``.  See :func:`_parse_time_offset` for the
            full list of supported units.
        repeat_years : iterable of int, optional
            If supplied, a DataArray with a ``month`` or ``dayofyear``
            dimension is tiled across these calendar years before plotting.
            Example: ``repeat_years=range(2015, 2018)``.
        month_day : int, optional
            Day of month on which to place monthly values when tiling.
            Default is ``15``.  Only used when *repeat_years* is given and
            *data* has a ``month`` dimension.
        resample : str, optional
            Pandas-compatible resampling frequency (e.g. ``"6h"``, ``"D"``)
            applied to all DataArray arguments before plotting.
        resample_method : str, optional
            Aggregation method for ``resample``.  One of ``"mean"``,
            ``"median"``, ``"min"``, ``"max"``, ``"sum"``, ``"std"``.
            Default ``"mean"``.
        **kwargs
            Forwarded to :meth:`~earthkit.plots.components.subplots.Subplot.line`.
        """
        if repeat_years is not None:
            import xarray as xr

            if isinstance(data, xr.Dataset):
                dvars = list(data.data_vars)
                data = data[dvars[0]] if len(dvars) == 1 else data
            data = _tile_clim_to_years(
                data, repeat_years, month_day=month_day, extend=extend_years
            )
        if time_offset is not None:
            data = _apply_time_offset(data, _parse_time_offset(time_offset))
        return super().line(data, *args, **kwargs)

    @_with_resampling
    def scatter(
        self,
        data,
        *args,
        time_offset=None,
        repeat_years=None,
        month_day=15,
        extend_years=False,
        **kwargs,
    ):
        """
        Plot a scatter on the TimeSeries subplot.

        Extends :meth:`~earthkit.plots.components.subplots.Subplot.scatter`
        with the ``time_offset``, ``resample`` / ``resample_method``, and
        ``repeat_years`` parameters.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            Data to plot.  If *data* has a ``month`` or ``dayofyear``
            dimension and *repeat_years* is given, the climatology is tiled
            across those years automatically.
        time_offset : str, optional
            Shift the time coordinate before plotting.
            See :func:`_parse_time_offset` for supported formats.
        repeat_years : iterable of int, optional
            If supplied, a DataArray with a ``month`` or ``dayofyear``
            dimension is tiled across these calendar years before plotting.
        month_day : int, optional
            Day of month on which to place monthly values when tiling.
            Default is ``15``.
        resample : str, optional
            Pandas-compatible resampling frequency applied before plotting.
        resample_method : str, optional
            Aggregation method for ``resample``.  Default ``"mean"``.
        **kwargs
            Forwarded to :meth:`~earthkit.plots.components.subplots.Subplot.scatter`.
        """
        if repeat_years is not None:
            data = _tile_clim_to_years(
                data, repeat_years, month_day=month_day, extend=extend_years
            )
        if time_offset is not None:
            data = _apply_time_offset(data, _parse_time_offset(time_offset))
        return super().scatter(data, *args, **kwargs)

    @_with_resampling
    def bar(self, data, *args, time_offset=None, **kwargs):
        """
        Plot bars on the TimeSeries subplot.

        Extends :meth:`~earthkit.plots.components.subplots.Subplot.bar`
        with the ``time_offset`` and ``resample`` / ``resample_method``
        parameters.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            Data to plot.
        time_offset : str, optional
            Shift the time coordinate before plotting.
            See :func:`_parse_time_offset` for supported formats.
        resample : str, optional
            Pandas-compatible resampling frequency applied before plotting.
        resample_method : str, optional
            Aggregation method for ``resample``.  Default ``"mean"``.
        **kwargs
            Forwarded to :meth:`~earthkit.plots.components.subplots.Subplot.bar`.
        """
        if time_offset is not None:
            data = _apply_time_offset(data, _parse_time_offset(time_offset))
        return super().bar(data, *args, **kwargs)

    def fill_between(
        self,
        y1,
        y2=0,
        *args,
        resample=None,
        resample_method="mean",
        time_offset=None,
        repeat_years=None,
        month_day=15,
        extend_years=False,
        **kwargs,
    ):
        """
        Fill the area between two curves.

        Extends :meth:`~earthkit.plots.components.subplots.Subplot.fill_between`
        with support for ``drawstyle`` step keywords, ``resample`` /
        ``resample_method``, and the ``time_offset`` parameter.

        Step keywords are translated to the ``step`` parameter expected by
        ``ax.fill_between``:

        - ``'steps-pre'``  → ``step='pre'``
        - ``'steps-mid'``  → ``step='mid'``
        - ``'steps-post'`` → ``step='post'``

        Parameters
        ----------
        repeat_years : iterable of int, optional
            If supplied, *y1* (and *y2* if a DataArray) must have a ``month``
            or ``dayofyear`` dimension.  The climatology is tiled across these
            calendar years before plotting.  Example:
            ``repeat_years=range(2015, 2018)``.
        month_day : int, optional
            Day of month on which to place monthly values when tiling.
            Default is ``15``.
        resample : str, optional
            Pandas-compatible resampling frequency (e.g. ``"6h"``, ``"D"``)
            applied to *y1* and *y2* (when a DataArray) before plotting.
        resample_method : str, optional
            Aggregation method for ``resample``.  Default ``"mean"``.
        time_offset : str, optional
            Shift the time coordinate of *y1* (and *y2* if it is a DataArray)
            before plotting.  See :func:`_parse_time_offset` for supported
            formats.
        """
        if repeat_years is not None:
            import xarray as xr

            def _unwrap(obj):
                if isinstance(obj, xr.Dataset):
                    dvars = list(obj.data_vars)
                    if len(dvars) != 1:
                        raise TypeError(
                            "repeat_years requires a DataArray or a single-variable "
                            f"Dataset; got {len(dvars)} variables."
                        )
                    return obj[dvars[0]]
                return obj

            y1 = _tile_clim_to_years(
                _unwrap(y1), repeat_years, month_day=month_day, extend=extend_years
            )
            if not isinstance(y2, (int, float)):
                y2 = _tile_clim_to_years(
                    _unwrap(y2), repeat_years, month_day=month_day, extend=extend_years
                )

        if resample is not None:
            y1 = _resample(y1, resample, resample_method)
            if not isinstance(y2, (int, float)):
                y2 = _resample(y2, resample, resample_method)

        if time_offset is not None:
            offset = _parse_time_offset(time_offset)
            y1 = _apply_time_offset(y1, offset)
            if not isinstance(y2, (int, float)):
                y2 = _apply_time_offset(y2, offset)

        _drawstyle_to_step = {
            "steps-pre": "pre",
            "steps-mid": "mid",
            "steps-post": "post",
        }
        drawstyle = kwargs.pop("drawstyle", None)
        if drawstyle in _drawstyle_to_step:
            kwargs["step"] = _drawstyle_to_step[drawstyle]
        elif drawstyle is not None:
            kwargs["drawstyle"] = drawstyle
        super().fill_between(y1, y2, *args, **kwargs)
        return self

    @_with_resampling
    def multiboxplot(
        self,
        data,
        dim=None,
        time_dim=None,
        time_offset=None,
        **kwargs,
    ):
        """
        Plot a multiboxplot on the TimeSeries subplot.

        Extends :meth:`~earthkit.plots.components.subplots.Subplot.multiboxplot`
        with automatic detection of the time axis: quantiles are computed along
        the *non-time* dimension by default, so that each time step becomes a
        column of boxes showing the ensemble spread.

        Parameters
        ----------
        data : xarray.DataArray
            The data to plot.
        dim : str, optional
            Dimension along which to compute quantiles.  If ``None``,
            auto-detects as the non-time dimension.
        time_dim : str, optional
            Name of the time dimension.  Auto-detected if ``None``.
        time_offset : str, optional
            Shift the time coordinate by this amount before plotting.
            See :func:`_parse_time_offset` for supported formats.
        resample : str, optional
            Pandas-compatible resampling frequency (e.g. ``"6h"``, ``"D"``)
            applied before computing quantiles.  Injected by the
            ``@_with_resampling`` decorator.
        resample_method : str, optional
            Aggregation method for ``resample``.  Default ``"mean"``.
        **kwargs
            Remaining keyword arguments forwarded to
            :meth:`~earthkit.plots.components.subplots.Subplot.multiboxplot`.
        """
        data = data.squeeze()

        # Auto-detect time dimension
        detected_time_dim = None
        for d in data.dims:
            if np.issubdtype(data[d].dtype, np.datetime64):
                detected_time_dim = d
                break
        if detected_time_dim is None:
            detected_time_dim = find_time(list(data.dims))
        if time_dim is None:
            time_dim = detected_time_dim

        # Auto-detect quantile dimension as the non-time dimension
        if dim is None and time_dim is not None and len(data.dims) >= 2:
            for d in data.dims:
                if d != time_dim:
                    dim = d
                    break

        if time_offset is not None:
            data = _apply_time_offset(
                data, _parse_time_offset(time_offset), time_dim=time_dim
            )

        return super().multiboxplot(data, dim=dim, **kwargs)

    @_with_resampling
    def stripes(self, data, *args, time_offset=None, **kwargs):
        """
        Plot climate stripes on the TimeSeries subplot.

        Extends :meth:`~earthkit.plots.components.subplots.Subplot.stripes`
        with the ``time_offset`` and ``resample`` / ``resample_method``
        parameters.

        Parameters
        ----------
        data : xarray.DataArray or array-like
            Data to plot.
        time_offset : str, optional
            Shift the time coordinate before plotting.
            See :func:`_parse_time_offset` for supported formats.
        resample : str, optional
            Pandas-compatible resampling frequency applied before plotting.
        resample_method : str, optional
            Aggregation method for ``resample``.  Default ``"mean"``.
        ymin : float, optional
            Bottom of the stripes in axes-fraction coordinates (default ``0``).
        ymax : float, optional
            Top of the stripes in axes-fraction coordinates (default ``1``).
        **kwargs
            Forwarded to :meth:`~earthkit.plots.components.subplots.Subplot.stripes`.
        """
        data = _coerce_year_dim_to_datetime(data)
        if time_offset is not None:
            data = _apply_time_offset(data, _parse_time_offset(time_offset))
        result = super().stripes(data, *args, **kwargs)
        self.ax.set_yticks([])
        self.ax.grid(False)
        return result
