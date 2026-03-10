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

from earthkit.plots.temporal.timeseries import TimeSeries

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
    for year, group in da.groupby(f"{time_dim}.year"):
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

    Each call to :meth:`line` or :meth:`fill_between` either:

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._climatology_formatter_applied = False
        # Set to True when multi-year data is split, indicating the x-axis
        # should be clamped to exactly one full calendar year at render time.
        self._needs_xclamp = False

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

    def _plot_clim_data(self, method, data, *args, month_day=None, **kwargs):
        """
        Shared helper: detect clim dim, convert to datetimes, and call *method*.

        Returns True if a clim dim was detected and handled, False otherwise.

        If ``drawstyle='steps-period'`` is passed, each value is placed at the
        start of its calendar period (1st of the month for monthly data, start
        of the day for daily data) with an extra trailing point so that
        ``drawstyle='steps-post'`` spans each full period.
        """
        clim_dim = _detect_clim_dim(data)
        if clim_dim is None:
            return False

        steps_period = kwargs.pop("drawstyle", None) == "steps-period"
        if steps_period:
            mapped = _expand_steps_period(data, dim=clim_dim)
            kwargs["drawstyle"] = "steps-post"
        else:
            mapped = _clim_dim_to_datetimes(data, dim=clim_dim, month_day=month_day)

        label = kwargs.pop("label", None)
        method(mapped, *args, label=label, **kwargs)
        if not self._climatology_formatter_applied:
            self._apply_climatology_formatter()
            self._climatology_formatter_applied = True
        return True

    def line(self, data, *args, time_dim=None, month_day=None, **kwargs):
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
        **kwargs :
            Forwarded to the underlying
            :meth:`~earthkit.plots.components.subplots.Subplot.line` method.
        """
        import xarray as xr

        from earthkit.plots.identifiers import find_time

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

        if self._plot_clim_data(
            super().line, data, *args, month_day=month_day, **kwargs
        ):
            return

        # --- multi-year datetime path ---
        if time_dim is None:
            found = find_time(list(data.dims))
            time_dim = found if found else "time"

        label = kwargs.pop("label", None)
        for i, (_year, remapped) in enumerate(_split_by_year(data, time_dim=time_dim)):
            line_label = (
                (label if i == 0 else "_nolegend_") if label is not None else None
            )
            super().line(remapped, *args, label=line_label, **kwargs)

        if not self._climatology_formatter_applied:
            self._apply_climatology_formatter()
            self._climatology_formatter_applied = True
        self._needs_xclamp = True

    def fill_between(self, y1, y2=0, *args, month_day=None, **kwargs):
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
        drawstyle : str, optional
            Step style for the filled region. Accepts ``'steps-pre'``,
            ``'steps-mid'``, ``'steps-post'`` (translated to the ``step``
            kwarg of ``ax.fill_between``), or ``'steps-period'`` (spans each
            full calendar period).
        **kwargs :
            Forwarded to :meth:`~earthkit.plots.components.subplots.Subplot.fill_between`.
        """
        import xarray as xr

        def _to_dataarray(obj):
            """Extract a single-variable Dataset to DataArray, passthrough otherwise."""
            if isinstance(obj, xr.Dataset):
                data_vars = list(obj.data_vars)
                if len(data_vars) != 1:
                    raise TypeError(
                        "Climatology.fill_between() requires xarray DataArrays or "
                        f"single-variable Datasets, but got {len(data_vars)} variables."
                    )
                return obj[data_vars[0]]
            return obj

        y1 = _to_dataarray(y1)
        y2 = _to_dataarray(y2)

        _drawstyle_to_step = {
            "steps-pre": "pre",
            "steps-mid": "mid",
            "steps-post": "post",
        }
        drawstyle = kwargs.pop("drawstyle", None)

        clim_dim = _detect_clim_dim(y1) if isinstance(y1, xr.DataArray) else None
        if clim_dim is not None:
            if drawstyle == "steps-period":
                y1 = _expand_steps_period(y1, dim=clim_dim)
                if isinstance(y2, xr.DataArray):
                    y2 = _expand_steps_period(y2, dim=clim_dim)
                kwargs["step"] = "post"
            else:
                y1 = _clim_dim_to_datetimes(y1, dim=clim_dim, month_day=month_day)
                if isinstance(y2, xr.DataArray):
                    y2 = _clim_dim_to_datetimes(y2, dim=clim_dim, month_day=month_day)
                if drawstyle in _drawstyle_to_step:
                    kwargs["step"] = _drawstyle_to_step[drawstyle]
            if not self._climatology_formatter_applied:
                self._apply_climatology_formatter()
                self._climatology_formatter_applied = True

        super().fill_between(y1, y2, *args, **kwargs)
