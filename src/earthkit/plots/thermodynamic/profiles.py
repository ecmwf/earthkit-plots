# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

"""Helpers to extract vertical profiles (soundings) for thermodynamic diagrams."""

import numpy as np

from earthkit.plots.thermodynamic.transforms import T_C2K

#: Names of pressure coordinates recognised in xarray objects.
PRESSURE_NAMES = ("pressure_level", "isobaricInhPa", "isobaricInPa", "plev", "pressure", "level", "lev", "pres")

_PRESSURE_FACTORS = {"hpa": 1.0, "mbar": 1.0, "mb": 1.0, "millibar": 1.0, "pa": 0.01, "kpa": 10.0}
_TEMPERATURE_OFFSETS = {
    "k": -T_C2K,
    "kelvin": -T_C2K,
    "degc": 0.0,
    "celsius": 0.0,
    "degree_celsius": 0.0,
    "degrees_celsius": 0.0,
    "°c": 0.0,
    "c": 0.0,
}


def _is_xarray(data):
    return hasattr(data, "dims") and hasattr(data, "coords")


def is_pandas(data):
    """Whether ``data`` is a pandas DataFrame or Series."""
    from earthkit.plots.sources.extractors.pandas import is_pandas as _is_pandas

    return _is_pandas(data)


def _pandas_units(data, name):
    """Units of the column ``name`` from pandas ``attrs`` (a string, or a mapping from column names)."""
    from earthkit.plots.sources.extractors.pandas import _units_from_attrs

    return _units_from_attrs(data.attrs, name)


#: Name of the pressure column added to a profile when the pressure is given as an array.
PRESSURE_COLUMN = "pressure"


def pandas_profile(data, column=None, p=None, kind="temperature", units=None, p_units="hPa"):
    """
    Prepare a profile from a pandas object for plotting through the standard pipeline.

    The returned DataFrame keeps all the columns of ``data``, so that its
    metadata (e.g. the constant latitude and longitude columns of a station)
    remain available to titles. The plotted values are converted to diagram
    units, the levels with missing values are dropped, and the frame is
    indexed by pressure (hPa), ordered from the bottom up.

    Parameters
    ----------
    data : pandas.DataFrame or pandas.Series
        The profile. For a DataFrame, ``column`` names the plotted column
        (it may be omitted when there is a single column besides the pressure).
    column : str, optional
        The column of ``data`` holding the profile values.
    p : str, pandas.Series or array-like, optional
        The pressure: the name of a column, or the values. Defaults to the
        index of ``data`` when it is named.
    kind : {"temperature", "raw"}
        How the values are converted: temperatures to °C.
    units : str, optional
        Units of the values. Read from ``attrs["units"]`` when not given;
        temperatures default to °C.
    p_units : str
        Units of the pressure when ``attrs["units"]`` does not give them. Default hPa.

    Returns
    -------
    frame : pandas.DataFrame
        The profile, indexed by pressure.
    column : str
        The name of the plotted column.
    p_name : str
        The name of the pressure index.
    """
    # Units of the columns, from attrs["units"]
    units_map = _units_mapping(data)
    if type(data).__name__ == "Series":
        column = data.name if data.name is not None else "values"
        frame = data.to_frame(name=column)
    else:
        frame = data.copy()

    # The pressure
    if isinstance(p, str):
        if p in frame.columns:
            p_name = p
        elif p == frame.index.name:
            frame = frame.reset_index()
            p_name = p
        else:
            raise ValueError(f"Pressure column {p!r} not found; available columns are {list(frame.columns)}")
    elif p is not None:
        p_name = getattr(p, "name", None) or PRESSURE_COLUMN
        if p_name == column:
            p_name = "__pressure__"
        values = p.to_numpy() if is_pandas(p) else np.asarray(p, dtype=float)
        if len(values) != len(frame):
            raise ValueError(f"p has {len(values)} values but the profile has {len(frame)}")
        frame[p_name] = values
        units_map[p_name] = (_pandas_units(p, p.name) if is_pandas(p) else None) or p_units
    elif frame.index.name is not None:
        p_name = frame.index.name
        frame = frame.reset_index()
    else:
        raise ValueError("Give the pressure with p=: the name of a column, or the values")

    # The plotted column
    if column is None:
        others = [c for c in frame.columns if c != p_name]
        if len(others) != 1:
            raise ValueError(f"The DataFrame has several columns {others}; name the plotted one with column=...")
        column = others[0]
    elif column not in frame.columns:
        raise ValueError(f"Column {column!r} not found; available columns are {list(frame.columns)}")

    values = frame[column].to_numpy(dtype=float)
    pressure = pressure_to_hpa(frame[p_name].to_numpy(dtype=float), units_map.get(p_name) or p_units)
    value_units = units or units_map.get(column)
    if kind == "temperature":
        values = temperature_to_celsius(values, value_units or "celsius")
        value_units = "celsius"

    frame[column] = values
    frame[p_name] = pressure
    frame = frame[np.isfinite(values) & np.isfinite(pressure)]
    frame = frame.sort_values(p_name, ascending=False, kind="stable").set_index(p_name)
    units_map.update({column: value_units, p_name: "hPa"})
    frame.attrs = {**data.attrs, "units": {k: v for k, v in units_map.items() if v is not None}}
    return frame, column, p_name


def _units_mapping(data):
    """The ``attrs["units"]`` of a pandas object as a mapping from column names."""
    units = data.attrs.get("units")
    if isinstance(units, dict):
        return dict(units)
    if isinstance(units, str) and type(data).__name__ == "Series":
        return {data.name: units}
    return {}


def _units(obj):
    return str(getattr(obj, "attrs", {}).get("units", "")).strip()


def pressure_to_hpa(p, units="hPa"):
    """Convert pressure values in ``units`` to hPa."""
    key = str(units).replace(" ", "").lower()
    if key not in _PRESSURE_FACTORS:
        raise ValueError(f"Unsupported pressure units {units!r}; expected one of hPa, Pa, kPa")
    return np.asarray(p, dtype=float) * _PRESSURE_FACTORS[key]


def temperature_to_celsius(t, units="celsius"):
    """Convert temperature values in ``units`` to °C."""
    key = str(units).replace(" ", "").lower()
    if key not in _TEMPERATURE_OFFSETS:
        raise ValueError(f"Unsupported temperature units {units!r}; expected K or celsius")
    return np.asarray(t, dtype=float) + _TEMPERATURE_OFFSETS[key]


def find_pressure_coord(data):
    """
    Find the name of the pressure coordinate of an xarray object.

    A coordinate is recognised by its units (Pa, hPa, ...) or by its name.

    Raises
    ------
    ValueError
        If no pressure coordinate is found.
    """
    candidates = list(data.dims) + [c for c in data.coords if c not in data.dims]
    for name in candidates:
        if name in data.coords and _units(data.coords[name]).replace(" ", "").lower() in _PRESSURE_FACTORS:
            return name
    for name in PRESSURE_NAMES:
        if name in data.coords:
            return name
    raise ValueError(
        f"Could not find a pressure coordinate in {list(data.coords)}; pass the pressure explicitly with p=..."
    )


def pressure_units(data, name):
    """Units of the pressure coordinate ``name``, defaulting to hPa when not set."""
    units = _units(data.coords[name])
    if units:
        return units
    # GRIB-style names imply the units
    return "Pa" if name == "isobaricInPa" else "hPa"


def extract(data, p=None, kind="temperature", units=None, p_units="hPa", column=None):
    """
    Extract a profile as numpy arrays in diagram units.

    Parameters
    ----------
    data : xarray.DataArray or array-like
        The profile values.
    p : xarray.DataArray or array-like, optional
        Pressure of the profile. Taken from the pressure coordinate of ``data``
        when not given.
    kind : {"temperature", "specific_humidity", "relative_humidity", "raw"}
        How the values are converted: temperatures to °C; humidities are
        returned as they are.
    units : str, optional
        Units of ``data``. Read from the ``units`` attribute of xarray objects;
        for plain arrays temperatures default to °C.
    p_units : str
        Units of ``p`` when it is a plain array. Default hPa.
    column : str, optional
        For a pandas DataFrame, the column holding the values; ``p`` may then
        be a column name too. See :func:`pandas_profile`.

    Returns
    -------
    values, p : numpy.ndarray
        The values and the pressure (hPa), ordered from the bottom up.
    """
    if is_pandas(data) and (column is not None or isinstance(p, str) or type(data).__name__ == "DataFrame"):
        frame, column, _ = pandas_profile(
            data,
            column=column,
            p=p,
            kind="temperature" if kind == "temperature" else "raw",
            units=units,
            p_units=p_units,
        )
        return frame[column].to_numpy(dtype=float), frame.index.to_numpy(dtype=float)

    if _is_xarray(data):
        if p is None:
            name = find_pressure_coord(data)
            p_hpa = pressure_to_hpa(data.coords[name].values, pressure_units(data, name))
            values = data.transpose(name, ...).values if data.ndim > 1 else data.values
        else:
            values = data.values
            p_hpa = _pressure_values(p, p_units)
        units = units or _units(data)
    else:
        if p is None:
            raise ValueError("p must be given when the profile is not an xarray object")
        values = np.asarray(data, dtype=float)
        p_hpa = _pressure_values(p, p_units)

    values = np.asarray(values, dtype=float)
    p_hpa = np.asarray(p_hpa, dtype=float)
    if values.ndim != 1 or values.shape != p_hpa.shape:
        raise ValueError(
            f"Expected a 1-D profile with one value per pressure level; got values {values.shape}, p {p_hpa.shape}"
        )

    if kind == "temperature":
        values = temperature_to_celsius(values, units or "celsius")
    elif kind == "relative_humidity" and (units or "%").strip() not in ("%", "percent"):
        # fractions are converted to percent
        values = values * 100.0

    order = np.argsort(-p_hpa, kind="stable")
    return values[order], p_hpa[order]


def _pressure_values(p, p_units):
    if _is_xarray(p):
        return pressure_to_hpa(p.values, _units(p) or p_units)
    return pressure_to_hpa(p, p_units)


def dewpoint_from_specific_humidity(q, p):
    """Dewpoint (°C) from specific humidity (kg/kg) and pressure (hPa)."""
    from earthkit.plots.thermodynamic.transforms import thermo_backend

    with np.errstate(all="ignore"):
        return thermo_backend().dewpoint_from_specific_humidity(q, p * 100.0) - T_C2K


def dewpoint_from_relative_humidity(t, r):
    """Dewpoint (°C) from temperature (°C) and relative humidity (%)."""
    from earthkit.plots.thermodynamic.transforms import thermo_backend

    with np.errstate(all="ignore"):
        return thermo_backend().dewpoint_from_relative_humidity(t + T_C2K, r) - T_C2K


#: Conversion factor from m/s to knots.
KNOTS_PER_MS = 3600.0 / 1852.0


def wind_components(u=None, v=None, p=None, speed=None, direction=None, p_units="hPa", units="m/s", knots=True):
    """
    Extract a wind profile as ``(u, v, p)`` arrays for :meth:`matplotlib.axes.Axes.barbs`.

    Parameters
    ----------
    u, v : xarray.DataArray or array-like, optional
        Wind components.
    p : xarray.DataArray or array-like, optional
        Pressure of the profile, required for plain arrays.
    speed, direction : xarray.DataArray or array-like, optional
        Wind speed and meteorological direction (degrees, the direction the
        wind blows from), used instead of ``u`` and ``v``.
    p_units : str
        Units of ``p`` when it is a plain array. Default hPa.
    units : {"m/s", "knots"}
        Units of the wind. Default ``"m/s"``.
    knots : bool
        Return the components in knots (as usual for barbs) rather than m/s.

    Returns
    -------
    u, v, p : numpy.ndarray
        The components and the pressure (hPa), ordered from the bottom up.
    """
    if u is not None and v is not None:
        u, p_hpa = extract(u, p=p, kind="raw", p_units=p_units)
        v, p_v = extract(v, p=p, kind="raw", p_units=p_units)
    elif speed is not None and direction is not None:
        from earthkit.meteo.wind import array as wind

        speed, p_hpa = extract(speed, p=p, kind="raw", p_units=p_units)
        direction, p_v = extract(direction, p=p, kind="raw", p_units=p_units)
        u, v = wind.polar_to_xy(speed, direction)
    else:
        raise ValueError("Provide u and v, or speed and direction")
    if not np.array_equal(p_hpa, p_v):
        raise ValueError("The wind components must be on the same pressure levels")

    if units not in ("m/s", "knots"):
        raise ValueError(f"units must be 'm/s' or 'knots', got {units!r}")
    if knots and units == "m/s":
        u, v = u * KNOTS_PER_MS, v * KNOTS_PER_MS
    elif not knots and units == "knots":
        u, v = u / KNOTS_PER_MS, v / KNOTS_PER_MS
    return u, v, p_hpa
