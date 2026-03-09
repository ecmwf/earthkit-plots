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


def _clim_dim_to_datetimes(da, dim):
    """
    Convert a DataArray with a climatology integer dimension to one with
    datetime coordinates on the reference year (:data:`_LEAP_REF_YEAR`).

    - ``month`` (1–12): each value is placed at the 15th of its month.
    - ``dayofyear`` (1–366): each value is placed at Jan 1 + (doy - 1) days.
    """
    import xarray as xr

    vals = da[dim].values.astype(int)
    ref = pd.Timestamp(f"{_LEAP_REF_YEAR}-01-01")
    if dim == "month":
        dates = [pd.Timestamp(_LEAP_REF_YEAR, int(m), 15) for m in vals]
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
            if np.issubdtype(vals.dtype, np.integer) and vals.min() >= 1 and vals.max() <= 12:
                return "month"
        elif dim == "dayofyear":
            vals = da[dim].values
            if np.issubdtype(vals.dtype, np.integer) and vals.min() >= 1 and vals.max() <= 366:
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

    def _plot_clim_data(self, method, data, *args, **kwargs):
        """
        Shared helper: detect clim dim, convert to datetimes, and call *method*.

        Returns True if a clim dim was detected and handled, False otherwise.
        """
        clim_dim = _detect_clim_dim(data)
        if clim_dim is None:
            return False
        mapped = _clim_dim_to_datetimes(data, dim=clim_dim)
        label = kwargs.pop("label", None)
        method(mapped, *args, label=label, **kwargs)
        if not self._climatology_formatter_applied:
            self._apply_climatology_formatter()
            self._climatology_formatter_applied = True
        return True

    def line(self, data, *args, time_dim=None, **kwargs):
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

        if self._plot_clim_data(super().line, data, *args, **kwargs):
            return

        # --- multi-year datetime path ---
        if time_dim is None:
            found = find_time(list(data.dims))
            time_dim = found if found else "time"

        label = kwargs.pop("label", None)
        for i, (_year, remapped) in enumerate(_split_by_year(data, time_dim=time_dim)):
            line_label = (label if i == 0 else "_nolegend_") if label is not None else None
            super().line(remapped, *args, label=line_label, **kwargs)

        if not self._climatology_formatter_applied:
            self._apply_climatology_formatter()
            self._climatology_formatter_applied = True
        self._needs_xclamp = True

    def fill_between(self, y1, y2=0, *args, **kwargs):
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

        clim_dim = _detect_clim_dim(y1) if isinstance(y1, xr.DataArray) else None
        if clim_dim is not None:
            y1 = _clim_dim_to_datetimes(y1, dim=clim_dim)
            if isinstance(y2, xr.DataArray):
                y2 = _clim_dim_to_datetimes(y2, dim=clim_dim)
            if not self._climatology_formatter_applied:
                self._apply_climatology_formatter()
                self._climatology_formatter_applied = True

        super().fill_between(y1, y2, *args, **kwargs)
