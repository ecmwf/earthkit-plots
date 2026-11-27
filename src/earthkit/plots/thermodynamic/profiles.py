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


def extract(data, p=None, kind="temperature", units=None, p_units="hPa"):
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

    Returns
    -------
    values, p : numpy.ndarray
        The values and the pressure (hPa), ordered from the bottom up.
    """
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
