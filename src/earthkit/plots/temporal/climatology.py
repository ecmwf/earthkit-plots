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

import pandas as pd

from earthkit.plots.temporal.timeseries import (
    TimeSeries,
    _apply_time_offset,
    _parse_time_offset,
)

# Reference year — a leap year so Feb 29 data can be represented.
_LEAP_REF_YEAR = 2000

# Full-year x-axis bounds used when multi-year data is split by year.
_XMIN = pd.Timestamp(f"{_LEAP_REF_YEAR}-01-01")
_XMAX = pd.Timestamp(f"{_LEAP_REF_YEAR}-12-31 23:59:59")


def _remap_year(da, ref_year, time_dim):
    """Replace the year component of all timestamps in *da* with *ref_year*."""
    old_times = pd.DatetimeIndex(da[time_dim].values)
    new_times = [t.replace(year=ref_year) for t in old_times]
    return da.assign_coords({time_dim: new_times})


def _split_by_year(da, time_dim="time"):
    """
    Yield ``(year, remapped_da)`` for each calendar year present in *da*.

    All years are remapped onto :data:`_LEAP_REF_YEAR` (2000) so that the
    entire plot shares a single Jan–Dec x-axis.  Non-leap years simply have
    no Feb 29 data point.
    """
    for year, group in da.groupby(da[time_dim].dt.year):
        yield int(year), _remap_year(group, _LEAP_REF_YEAR, time_dim)


def _month_center(year, month):
    """
    Return the timestamp at the exact centre of *month* in *year*.

    For months with an odd number of days the centre falls at midnight on the
    middle day (e.g. January: day 16 00:00).  For months with an even number
    of days it falls at noon on the lower-middle day (e.g. April: day 15
    12:00), giving a true half-day offset.
    """
    n = calendar.monthrange(year, month)[1]
    half = (n + 1) / 2  # e.g. 31→16.0, 30→15.5, 29→15.0, 28→14.5
    day = int(half)
    extra_hours = 12 if half != day else 0
    return pd.Timestamp(year, month, day, extra_hours)


def _clim_dim_to_datetimes(da, dim, month_day=None):
    """
    Convert a DataArray with a climatology integer dimension to one with
    datetime coordinates on the reference year (:data:`_LEAP_REF_YEAR`).

    - ``month`` (1–12): each value is placed at the centre of its month by
      default (``month_day=None``).  Pass an integer day (1–28) to fix the
      day, or ``-1`` to use the last day of each month.
    - ``dayofyear`` (1–366): each value is placed at Jan 1 + (doy - 1) days.
    """
    import xarray as xr

    vals = da[dim].values.astype(int)
    ref = pd.Timestamp(f"{_LEAP_REF_YEAR}-01-01")
    if dim == "month":
        dates = []
        for m in vals:
            if month_day is None:
                dates.append(_month_center(_LEAP_REF_YEAR, int(m)))
            elif month_day == -1:
                n = calendar.monthrange(_LEAP_REF_YEAR, int(m))[1]
                dates.append(pd.Timestamp(_LEAP_REF_YEAR, int(m), n))
            else:
                dates.append(pd.Timestamp(_LEAP_REF_YEAR, int(m), month_day))
    else:  # dayofyear
        dates = [ref + pd.Timedelta(days=int(d) - 1) for d in vals]

    # Preserve scalar (0-d) coordinates so metadata like latitude/longitude
    # remains accessible to the metadata/label system downstream.
    scalar_coords = {
        name: da.coords[name]
        for name in da.coords
        if name != dim and da.coords[name].ndim == 0
    }
    scalar_coords["time"] = dates

    return xr.DataArray(
        da.values,
        coords=scalar_coords,
        dims=["time"],
        attrs=da.attrs,
    )


def _expand_steps_period(da, dim):
    """
    Expand a clim-dim DataArray so that plotting with ``drawstyle='steps-post'``
    spans each full calendar period.

    - For ``month``: x-values are placed on the 1st of each month; an extra
      point is appended at the 1st of the month *after* the last data month so
      that the final step closes correctly.
    - For ``dayofyear``: x-values are placed at the start of each day; an extra
      point is appended one day after the last.

    Returns ``(expanded_da, 'steps-post')`` — the caller should pass
    ``drawstyle='steps-post'`` to matplotlib.
    """
    import numpy as np
    import xarray as xr

    vals = da[dim].values.astype(int)
    ref = pd.Timestamp(f"{_LEAP_REF_YEAR}-01-01")

    if dim == "month":
        dates = [pd.Timestamp(_LEAP_REF_YEAR, int(m), 1) for m in vals]
        last_m = int(vals[-1])
        if last_m == 12:
            next_date = pd.Timestamp(_LEAP_REF_YEAR + 1, 1, 1)
        else:
            next_date = pd.Timestamp(_LEAP_REF_YEAR, last_m + 1, 1)
    else:  # dayofyear
        dates = [ref + pd.Timedelta(days=int(d) - 1) for d in vals]
        next_date = ref + pd.Timedelta(days=int(vals[-1]))

    all_dates = dates + [next_date]
    all_values = np.append(da.values, da.values[-1])

    scalar_coords = {
        name: da.coords[name]
        for name in da.coords
        if name != dim and da.coords[name].ndim == 0
    }
    scalar_coords["time"] = all_dates

    return xr.DataArray(
        all_values,
        coords=scalar_coords,
        dims=["time"],
        attrs=da.attrs,
    )


def _expand_steps_period_datetime(da, time_dim):
    """
    Expand a real-datetime DataArray for ``drawstyle='steps-post'`` so that
    each value spans its full day.

    Each timestamp is floored to midnight (start of day) and a trailing point
    is appended one day after the last value so the final step closes.
    """
    import numpy as np
    import xarray as xr

    times = pd.DatetimeIndex(da[time_dim].values)
    floored = pd.DatetimeIndex([t.floor("D") for t in times])
    next_day = floored[-1] + pd.Timedelta(days=1)
    all_times = floored.append(pd.DatetimeIndex([next_day]))
    all_values = np.append(da.values, da.values[-1])

    scalar_coords = {
        name: da.coords[name]
        for name in da.coords
        if name != time_dim and da.coords[name].ndim == 0
    }
    scalar_coords[time_dim] = all_times

    return xr.DataArray(
        all_values,
        coords=scalar_coords,
        dims=[time_dim],
        attrs=da.attrs,
    )


def _safe_replace_year(t, year):
    try:
        return t.replace(year=year)
    except ValueError:
        # Feb 29 in a leap year shifted to a non-leap year — use Feb 28.
        return t.replace(year=year, day=28)


def _wrap_clim_da(da, time_dim):
    """
    Wrap a clim-dim-converted (single-year) DataArray around the year boundary
    by replicating the data shifted ±1 year.

    Used for climatology data (``month``/``dayofyear`` dims) where the same
    values logically repeat every year.  Since the x-axis is clamped to one
    calendar year, only the boundary-adjacent points are visible.
    """
    import numpy as np
    import xarray as xr

    times = pd.DatetimeIndex(da[time_dim].values)
    prev_times = pd.DatetimeIndex([_safe_replace_year(t, t.year - 1) for t in times])
    next_times = pd.DatetimeIndex([_safe_replace_year(t, t.year + 1) for t in times])

    all_times = prev_times.append(times).append(next_times)
    all_values = np.concatenate([da.values, da.values, da.values])

    scalar_coords = {
        name: da.coords[name]
        for name in da.coords
        if name != time_dim and da.coords[name].ndim == 0
    }
    scalar_coords[time_dim] = all_times

    return xr.DataArray(
        all_values,
        coords=scalar_coords,
        dims=[time_dim],
        attrs=da.attrs,
    )


def _wrap_datetime_year(current_da, prev_da, next_da, time_dim):
    """
    Wrap a single year's remapped DataArray using actual data from neighbouring
    years.

    - Prepends the **last day** of *prev_da* (shifted forward one year) so the
      line continues smoothly from Dec into Jan.
    - Appends the **first day** of *next_da* (shifted back one year) so the
      line continues smoothly from Dec into Jan of the next year.

    Either *prev_da* or *next_da* may be ``None``, in which case that side is
    not wrapped.  All timestamps are already remapped to :data:`_LEAP_REF_YEAR`.
    """
    import numpy as np
    import xarray as xr

    times = pd.DatetimeIndex(current_da[time_dim].values)
    values = current_da.values

    scalar_coords = {
        name: current_da.coords[name]
        for name in current_da.coords
        if name != time_dim and current_da.coords[name].ndim == 0
    }

    prefix_times, prefix_vals = [], []
    suffix_times, suffix_vals = [], []

    if prev_da is not None:
        # prev_da is already remapped to _LEAP_REF_YEAR.
        # Take its last calendar day and place it at _LEAP_REF_YEAR - 1 so it
        # sits just before Jan 1 of the ref year on the x-axis.
        prev_times = pd.DatetimeIndex(prev_da[time_dim].values)
        last_date = prev_times.normalize()[-1]
        mask = prev_times.normalize() == last_date
        p_times = prev_times[mask]
        p_vals = prev_da.values[mask]
        prefix_times = pd.DatetimeIndex(
            [_safe_replace_year(t, _LEAP_REF_YEAR - 1) for t in p_times]
        )
        prefix_vals = p_vals

    if next_da is not None:
        # next_da is already remapped to _LEAP_REF_YEAR.
        # Take its first calendar day and place it at _LEAP_REF_YEAR + 1 so it
        # sits just after Dec 31 of the ref year on the x-axis.
        next_times = pd.DatetimeIndex(next_da[time_dim].values)
        first_date = next_times.normalize()[0]
        mask = next_times.normalize() == first_date
        n_times = next_times[mask]
        n_vals = next_da.values[mask]
        suffix_times = pd.DatetimeIndex(
            [_safe_replace_year(t, _LEAP_REF_YEAR + 1) for t in n_times]
        )
        suffix_vals = n_vals

    all_times = (
        (pd.DatetimeIndex(prefix_times) if len(prefix_times) else pd.DatetimeIndex([]))
        .append(times)
        .append(
            pd.DatetimeIndex(suffix_times)
            if len(suffix_times)
            else pd.DatetimeIndex([])
        )
    )
    all_values = np.concatenate(
        [v for v in [prefix_vals, values, suffix_vals] if len(v)]
    )

    scalar_coords[time_dim] = all_times
    return xr.DataArray(
        all_values,
        coords=scalar_coords,
        dims=[time_dim],
        attrs=current_da.attrs,
    )


def _should_auto_wrap(da, dim):
    """
    Return True if *da* covers both ends of the annual cycle.

    - ``month`` dim: must contain both month 1 and month 12.
    - ``dayofyear`` dim: must contain day 1 and day >= 365.
    - datetime dim: first point in Jan, last point in Dec.
    """

    if dim == "month":
        vals = da[dim].values.astype(int)
        return 1 in vals and 12 in vals
    elif dim == "dayofyear":
        vals = da[dim].values.astype(int)
        return 1 in vals and vals.max() >= 365
    else:
        # real datetime dimension
        times = pd.DatetimeIndex(da[dim].values)
        return times[0].month == 1 and times[-1].month == 12


def _detect_clim_dim(da):
    """
    Return the name of a climatology dimension if one is present, else None.

    Recognises dims named ``"month"`` (values 1–12) and ``"dayofyear"``
    (values 1–366).
    """
    import numpy as np

    for dim in da.dims:
        if dim == "month":
            vals = da[dim].values
            if (
                np.issubdtype(vals.dtype, np.integer)
                and vals.min() >= 1
                and vals.max() <= 12
            ):
                return "month"
        elif dim == "dayofyear":
            vals = da[dim].values
            if (
                np.issubdtype(vals.dtype, np.integer)
                and vals.min() >= 1
                and vals.max() <= 366
            ):
                return "dayofyear"
    return None


class Climatology(TimeSeries):
    """
    A :class:`~earthkit.plots.temporal.timeseries.TimeSeries` subplot for
    climatology / annual-cycle plots.

    Each call to :meth:`line`, :meth:`scatter`, :meth:`bar`, or
    :meth:`fill_between` either:

    - Splits a multi-year DataArray (with a real datetime coordinate) by
      calendar year and remaps every year onto a common Jan–Dec reference
      axis (all years → 2000), or
    - Accepts a DataArray with a ``month`` (1–12) or ``dayofyear`` (1–366)
      dimension and maps it directly onto the reference year axis.

    When multi-year data is split, the x-axis is clamped to exactly one
    calendar year.  When only clim-dim data is provided the x-axis autoscales
    to the data extent (useful for partial-year climatologies).

    .. warning::
        This is an experimental new feature. We welcome feedback and bug
        reports on GitHub issues:
        https://github.com/ecmwf/earthkit-plots/issues

    Examples
    --------
    >>> import earthkit.plots as ekp
    >>> ekp.climatology(da).show()

    >>> ts = ekp.Climatology()
    >>> ts.line(da)
    >>> ts.show()
    """

    def __init__(self, *args, wrap_time="auto", **kwargs):
        super().__init__(*args, **kwargs)
        self._climatology_formatter_applied = False
        # Set to True when multi-year data is split, indicating the x-axis
        # should be clamped to exactly one full calendar year at render time.
        self._needs_xclamp = False
        #: Default wrap_time setting for all plotting methods on this subplot.
        self.wrap_time = wrap_time

    def _extract_ref_year_x(self, data):
        """
        Return ``(x_for_plot, time_dim_name)`` for *data*, where *x_for_plot*
        is an array of timestamps remapped to :data:`_LEAP_REF_YEAR` suitable
        for passing as ``x=`` to matplotlib.

        The original DataArray is left **unchanged** so that its datetime
        coordinates are still accessible via metadata / format strings.

        Returns ``(None, None)`` if no time coordinate can be found.
        """
        import xarray as xr

        from earthkit.plots.identifiers import find_time

        if not isinstance(data, xr.DataArray):
            return None, None

        # 0-d scalar DataArray — remap the single scalar time coordinate
        if data.ndim == 0:
            for coord_name, coord in data.coords.items():
                if coord.ndim == 0:
                    try:
                        ts = pd.Timestamp(coord.values)
                        remapped = ts.replace(year=_LEAP_REF_YEAR)
                        return pd.DatetimeIndex([remapped]), coord_name
                    except Exception:
                        pass
            return None, None

        # 1-D (or higher) DataArray — find the time dimension and remap
        time_dim = find_time(list(data.dims))
        if time_dim is None:
            return None, None

        old_times = pd.DatetimeIndex(data[time_dim].values)
        remapped = pd.DatetimeIndex([t.replace(year=_LEAP_REF_YEAR) for t in old_times])
        return remapped, time_dim

    def _apply_climatology_formatter(self):
        """Set the x-axis to monthly ticks labelled by month name only (no year)."""
        import matplotlib.dates as mdates

        self.ax.xaxis.set_major_locator(mdates.MonthLocator())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    def _clamp_xaxis(self):
        """Restrict x-axis to exactly one calendar year and re-autoscale y."""
        import matplotlib.dates as mdates

        self.ax.set_xlim(mdates.date2num(_XMIN), mdates.date2num(_XMAX))
        self.ax.autoscale(axis="y")

    def show(self, *args, **kwargs):
        if self._needs_xclamp:
            self._clamp_xaxis()
        super().show(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self._needs_xclamp:
            self._clamp_xaxis()
        super().save(*args, **kwargs)

    def _resolve_wrap_time(self, wrap_time):
        """Return the effective wrap_time, falling back to the instance default."""
        if wrap_time is None:
            return self.wrap_time
        return wrap_time

    def _prepare_clim_data(
        self, data, wrap_time=None, time_dim=None, month_day=None, steps_period=False
    ):
        """
        Convert *data* to a list of datetime-coord DataArrays ready for plotting.

        Handles both paths:

        - **Clim-dim** (``month``/``dayofyear`` integer dimension): returns a
          single-element list with the converted DataArray.
        - **Multi-year datetime**: splits by year and returns one DataArray per
          year, all remapped to :data:`_LEAP_REF_YEAR`.

        In both cases ``wrap_time`` controls year-boundary wrapping and
        ``steps_period`` places values at period starts with a trailing duplicate.

        Returns ``(mapped_list, clim_dim_or_time_dim, is_datetime_path)``.
        ``mapped_list`` is ``None`` if *data* is not a recognised type.
        """
        import xarray as xr

        from earthkit.plots.identifiers import find_time

        wrap_time = self._resolve_wrap_time(wrap_time)

        clim_dim = _detect_clim_dim(data) if isinstance(data, xr.DataArray) else None

        if clim_dim is not None:
            # --- clim-dim path ---
            if steps_period:
                mapped = _expand_steps_period(data, dim=clim_dim)
            else:
                mapped = _clim_dim_to_datetimes(data, dim=clim_dim, month_day=month_day)

            do_wrap = (
                _should_auto_wrap(data, clim_dim) if wrap_time == "auto" else wrap_time
            )
            if do_wrap:
                mapped = _wrap_clim_da(mapped, "time")
                self._needs_xclamp = True

            return [mapped], clim_dim, False

        if isinstance(data, xr.DataArray) and data.ndim > 0:
            # --- multi-year datetime path ---
            if time_dim is None:
                found = find_time(list(data.dims))
                time_dim = found if found else "time"

            # Split into per-year remapped DataArrays and build a lookup by year.
            years_data = {}
            for year, remapped in _split_by_year(data, time_dim=time_dim):
                if steps_period:
                    remapped = _expand_steps_period_datetime(remapped, time_dim)
                years_data[year] = remapped

            sorted_years = sorted(years_data)
            result = []
            for year in sorted_years:
                remapped = years_data[year]
                do_wrap = (
                    _should_auto_wrap(remapped, time_dim)
                    if wrap_time == "auto"
                    else wrap_time
                )
                if do_wrap:
                    prev_da = years_data.get(year - 1)
                    next_da = years_data.get(year + 1)
                    # Only wrap a side if the neighbouring year's data exists.
                    remapped = _wrap_datetime_year(remapped, prev_da, next_da, time_dim)
                result.append(remapped)
            self._needs_xclamp = True
            return result, time_dim, True

        return None, None, False

    def line(
        self,
        data,
        *args,
        time_dim=None,
        month_day=None,
        wrap_time=None,
        time_offset=None,
        **kwargs,
    ):
        """
        Plot data on the climatology x-axis.

        Accepts either:

        - A multi-year DataArray with a real datetime coordinate — split by
          year and remapped onto the Jan–Dec reference axis.  When a
          ``label=`` is supplied it is applied only to the **first** year's
          line; all subsequent lines are suppressed from the legend.
        - A DataArray with a ``month`` (1–12) or ``dayofyear`` (1–366)
          dimension — mapped directly onto the reference year axis.

        Parameters
        ----------
        data : xarray.DataArray
            Timeseries or climatology data.
        time_dim : str, optional
            Name of the datetime dimension.  Detected automatically if omitted.
        month_day : int or None, optional
            Day of month on which to place each monthly value. Default is
            ``None``, which uses the true centre of each month (e.g. Jan 16
            00:00, Apr 15 12:00). Pass an integer (1–28) to fix the day, or
            ``-1`` to use the last day of each month.
        wrap_time : bool, "auto", or None, optional
            Whether to wrap data around year boundaries so the line continues
            smoothly past Jan and Dec. ``True`` always wraps; ``False`` never
            wraps; ``"auto"`` wraps only when the data spans a full year (Jan
            through Dec). ``None`` (default) uses the subplot's
            :attr:`wrap_time` setting.
        **kwargs :
            Forwarded to the underlying
            :meth:`~earthkit.plots.components.subplots.Subplot.line` method.
        """
        import xarray as xr

        if isinstance(data, xr.Dataset):
            data_vars = list(data.data_vars)
            if len(data_vars) != 1:
                raise TypeError(
                    "Climatology.line() requires an xarray DataArray or a Dataset "
                    f"with exactly one variable, but got {len(data_vars)} variables."
                )
            data = data[data_vars[0]]
        elif not isinstance(data, xr.DataArray):
            raise TypeError(
                "Climatology.line() requires an xarray DataArray. "
                f"Got {type(data).__name__!r}."
            )

        # Intercept steps-period before passing to _prepare_clim_data.
        drawstyle = kwargs.pop("drawstyle", None)
        steps_period = drawstyle == "steps-period"
        if not steps_period and drawstyle is not None:
            kwargs["drawstyle"] = drawstyle
        if steps_period:
            kwargs["drawstyle"] = "steps-post"

        mapped_list, _, _ = self._prepare_clim_data(
            data,
            wrap_time=wrap_time,
            time_dim=time_dim,
            month_day=month_day,
            steps_period=steps_period,
        )
        if mapped_list is None:
            # Not a recognised type — pass through unchanged.
            if time_offset is not None:
                data = _apply_time_offset(data, _parse_time_offset(time_offset))
            super().line(data, *args, **kwargs)
            return

        if time_offset is not None:
            offset = _parse_time_offset(time_offset)
            mapped_list = [_apply_time_offset(m, offset) for m in mapped_list]

        label = kwargs.pop("label", None)
        for i, mapped in enumerate(mapped_list):
            line_label = (
                (label if i == 0 else "_nolegend_") if label is not None else None
            )
            super().line(mapped, *args, label=line_label, **kwargs)

        if not self._climatology_formatter_applied:
            self._apply_climatology_formatter()
            self._climatology_formatter_applied = True

    def fill_between(
        self,
        y1,
        y2=0,
        *args,
        month_day=None,
        wrap_time=None,
        time_offset=None,
        **kwargs,
    ):
        """
        Fill the area between two curves on the climatology x-axis.

        If *y1* has a ``month`` or ``dayofyear`` dimension, both *y1* and
        *y2* are converted to datetime coordinates on the reference year
        before plotting.

        Parameters
        ----------
        y1 : xarray.DataArray
            Lower (or upper) bound.
        y2 : xarray.DataArray, array-like, or scalar
            Upper (or lower) bound.
        month_day : int or None, optional
            Day of month on which to place each monthly value. Default is
            ``None``, which uses the true centre of each month (e.g. Jan 16
            00:00, Apr 15 12:00). Pass an integer (1–28) to fix the day, or
            ``-1`` to use the last day of each month.
        wrap_time : bool, "auto", or None, optional
            Whether to wrap around year boundaries. Defaults to the subplot's
            :attr:`wrap_time` setting.
        drawstyle : str, optional
            Step style. ``'steps-period'`` spans each full calendar period.
            ``'steps-pre'``, ``'steps-mid'``, and ``'steps-post'`` are also
            accepted and translated by the parent class.
        **kwargs :
            Forwarded to :meth:`~earthkit.plots.temporal.timeseries.TimeSeries.fill_between`.
        """
        import xarray as xr

        def _to_da(obj):
            if isinstance(obj, xr.Dataset):
                data_vars = list(obj.data_vars)
                if len(data_vars) != 1:
                    raise TypeError(
                        "Climatology.fill_between() requires xarray DataArrays or "
                        f"single-variable Datasets, but got {len(data_vars)} variables."
                    )
                return obj[data_vars[0]]
            return obj

        y1 = _to_da(y1)
        y2 = _to_da(y2)

        drawstyle = kwargs.pop("drawstyle", None)
        steps_period = drawstyle == "steps-period"
        if not steps_period and drawstyle is not None:
            kwargs["drawstyle"] = drawstyle
        if steps_period:
            kwargs["drawstyle"] = "steps-post"

        # Map y1 through _prepare_clim_data for conversion + wrapping.
        mapped_y1_list, _, _ = self._prepare_clim_data(
            y1,
            wrap_time=wrap_time,
            month_day=month_day,
            steps_period=steps_period,
        )
        if mapped_y1_list is not None:
            if time_offset is not None:
                offset = _parse_time_offset(time_offset)
                mapped_y1_list = [_apply_time_offset(m, offset) for m in mapped_y1_list]
            # Apply the same conversion to y2 if it's a DataArray.
            if isinstance(y2, xr.DataArray):
                mapped_y2_list, _, _ = self._prepare_clim_data(
                    y2,
                    wrap_time=wrap_time,
                    month_day=month_day,
                    steps_period=steps_period,
                )
                if mapped_y2_list and time_offset is not None:
                    mapped_y2_list = [
                        _apply_time_offset(m, offset) for m in mapped_y2_list
                    ]
                y2 = mapped_y2_list[0] if mapped_y2_list else y2
            y1 = mapped_y1_list[0]
            if not self._climatology_formatter_applied:
                self._apply_climatology_formatter()
                self._climatology_formatter_applied = True

        super().fill_between(y1, y2, *args, **kwargs)

    def text(self, x, y=None, s="", time_offset=None, **kwargs):
        """
        Add text at position (*x*, *y*) on the climatology x-axis.

        Accepts the same calling conventions as
        :meth:`~earthkit.plots.components.subplots.Subplot.text`: either
        explicit ``(x, y, s)`` coordinates, or a DataArray whose x/y are
        extracted automatically.  Any datetime x value is remapped to the
        reference year (:data:`_LEAP_REF_YEAR`) for plotting, while the
        original DataArray (if supplied) is used for metadata / format strings.
        """
        import xarray as xr

        from earthkit.plots.metadata.formatters import SourceFormatter
        from earthkit.plots.sources import get_source
        from earthkit.plots.sources.context import PlotContext

        if not self._climatology_formatter_applied:
            self._apply_climatology_formatter()
            self._climatology_formatter_applied = True

        if isinstance(x, xr.DataArray):
            # Build source from the *original* DataArray so format strings
            # (e.g. {time:%Y}) see the real year, not the reference year.
            source = get_source(x, context=PlotContext.CARTESIAN_1D)
            _, y_val = source.x.values, source.y.values
            y_val = y_val.flat[0]
            if y is not None:
                s = y  # text(da, "hello") calling convention
            s = SourceFormatter(source).format(s)
            # Remap x to the reference year only for the plot position.
            x_plot, _ = self._extract_ref_year_x(x)
            x_pos = x_plot[0] if x_plot is not None else 0
            if time_offset is not None and x_pos != 0:
                x_pos = x_pos + _parse_time_offset(time_offset)
            self.ax.text(x_pos, y_val, s, **kwargs)
        else:
            try:
                ts = pd.Timestamp(x)
                x = ts.replace(year=_LEAP_REF_YEAR)
                if time_offset is not None:
                    x = x + _parse_time_offset(time_offset)
            except Exception:
                pass
            s = self.format_string(s)
            self.ax.text(x, y, s, **kwargs)

    def annotate(self, s, xy, xytext=None, time_offset=None, **kwargs):
        """
        Add an annotation on the climatology x-axis.

        Like :meth:`~earthkit.plots.components.subplots.Subplot.annotate` but
        remaps any datetime *xy* point to the reference year
        (:data:`_LEAP_REF_YEAR`) so it aligns with the shared Jan–Dec x-axis.
        The original DataArray (if supplied) is used for metadata / format
        strings so that ``{time:%Y}`` reflects the true year.
        """
        import xarray as xr

        from earthkit.plots.metadata.formatters import SourceFormatter
        from earthkit.plots.sources import get_source
        from earthkit.plots.sources.context import PlotContext

        if not self._climatology_formatter_applied:
            self._apply_climatology_formatter()
            self._climatology_formatter_applied = True

        if isinstance(xy, xr.DataArray):
            source = get_source(xy, context=PlotContext.CARTESIAN_1D)
            _, y_val = source.x.values, source.y.values
            y_val = y_val.flat[0]
            s = SourceFormatter(source).format(s)
            x_plot, _ = self._extract_ref_year_x(xy)
            x_pos = x_plot[0] if x_plot is not None else 0
            if time_offset is not None and x_pos != 0:
                x_pos = x_pos + _parse_time_offset(time_offset)
            xy = (x_pos, y_val)
        else:
            s = self.format_string(s)
            try:
                x_ts = pd.Timestamp(xy[0])
                x_shifted = x_ts.replace(year=_LEAP_REF_YEAR)
                if time_offset is not None:
                    x_shifted = x_shifted + _parse_time_offset(time_offset)
                xy = (x_shifted, xy[1])
            except Exception:
                pass

        if xytext is not None:
            self.ax.annotate(s, xy=xy, xytext=xytext, **kwargs)
        else:
            self.ax.annotate(s, xy=xy, **kwargs)

    def scatter(self, data, *args, wrap_time=None, time_offset=None, **kwargs):
        """
        Plot a scatter on the climatology x-axis.

        The year of any datetime coordinate is remapped to the reference year
        (:data:`_LEAP_REF_YEAR`) so that the point aligns with the shared
        Jan–Dec x-axis.  The original DataArray is passed to the source
        unchanged so that metadata (e.g. ``{time:%Y}``) reflects the true year.

        Parameters
        ----------
        wrap_time : bool, "auto", or None, optional
            Whether to wrap around year boundaries. Defaults to the subplot's
            :attr:`wrap_time` setting.
        time_offset : str, optional
            Shift the plotted x positions by this amount after remapping to
            the reference year.  See :func:`_parse_time_offset` for supported
            formats (e.g. ``"12H"``, ``"-1M"``).
        """
        offset = _parse_time_offset(time_offset) if time_offset is not None else None
        mapped_list, _, _ = self._prepare_clim_data(data, wrap_time=wrap_time)
        if mapped_list is not None:
            for mapped in mapped_list:
                x_plot, _ = self._extract_ref_year_x(mapped)
                kw = dict(kwargs)
                if x_plot is not None:
                    if offset is not None:
                        x_plot = x_plot + offset
                    kw.setdefault("x", x_plot)
                if not self._climatology_formatter_applied:
                    self._apply_climatology_formatter()
                    self._climatology_formatter_applied = True
                super().scatter(mapped, *args, **kw)
        else:
            x_plot, _ = self._extract_ref_year_x(data)
            if x_plot is not None:
                if offset is not None:
                    x_plot = x_plot + offset
                kwargs.setdefault("x", x_plot)
            if not self._climatology_formatter_applied:
                self._apply_climatology_formatter()
                self._climatology_formatter_applied = True
            super().scatter(data, *args, **kwargs)

    def bar(self, data, *args, wrap_time=None, time_offset=None, **kwargs):
        """
        Plot bars on the climatology x-axis.

        The year of any datetime coordinate is remapped to the reference year
        (:data:`_LEAP_REF_YEAR`) so that bars align with the shared Jan–Dec
        x-axis.  The original DataArray is passed to the source unchanged so
        that metadata (e.g. ``{time:%Y}``) reflects the true year.

        Parameters
        ----------
        wrap_time : bool, "auto", or None, optional
            Whether to wrap around year boundaries. Defaults to the subplot's
            :attr:`wrap_time` setting.
        time_offset : str, optional
            Shift the plotted x positions by this amount after remapping to
            the reference year.  See :func:`_parse_time_offset` for supported
            formats (e.g. ``"12H"``, ``"-1M"``).
        """
        offset = _parse_time_offset(time_offset) if time_offset is not None else None
        mapped_list, _, _ = self._prepare_clim_data(data, wrap_time=wrap_time)
        if mapped_list is not None:
            for mapped in mapped_list:
                x_plot, _ = self._extract_ref_year_x(mapped)
                kw = dict(kwargs)
                if x_plot is not None:
                    if offset is not None:
                        x_plot = x_plot + offset
                    kw.setdefault("x", x_plot)
                if not self._climatology_formatter_applied:
                    self._apply_climatology_formatter()
                    self._climatology_formatter_applied = True
                super().bar(mapped, *args, **kw)
        else:
            x_plot, _ = self._extract_ref_year_x(data)
            if x_plot is not None:
                if offset is not None:
                    x_plot = x_plot + offset
                kwargs.setdefault("x", x_plot)
            if not self._climatology_formatter_applied:
                self._apply_climatology_formatter()
                self._climatology_formatter_applied = True
            super().bar(data, *args, **kwargs)
