# Copyright 2024, European Centre for Medium Range Weather Forecasts.
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


_NO_CF_UNITS = False
try:
    import cf_units
except ImportError:
    _NO_CF_UNITS = True

#: Units for temperature anomalies.
TEMPERATURE_ANOM_UNITS = [
    "kelvin",
    "celsius",
]

#: Pretty units for temperature.
PRETTY_UNITS = {
    "celsius": "°C",
    "fahrenheit": "°F",
}

#: Unit equivalences.
UNIT_EQUIVALENCE = {
    "kg m-2": "mm",
}


def are_equal(unit_1, unit_2):
    """
    Check if two units are equivalent.

    Parameters
    ----------
    unit_1 : str
        The first unit.
    unit_2 : str
        The second unit.
    """
    if _NO_CF_UNITS:
        raise ImportError("cf-units is required for checking unit equivalence")
    return cf_units.Unit(unit_1) == cf_units.Unit(unit_2)


def anomaly_equivalence(units):
    """
    Check if units are equivalent for temperature anomalies.

    This is a special case for temperature anomalies, for which Kelvin and
    Celsius are considered equivalent.

    Parameters
    ----------
    units : str
        The units to check for equivalence.
    """
    return any(are_equal(units, t_units) for t_units in TEMPERATURE_ANOM_UNITS)


def convert(data, source_units, target_units):
    """
    Convert data from one set of units to another.

    Parameters
    ----------
    data : numpy.ndarray
        The data to convert.
    source_units : str
        The units of the data.
    target_units : str
        The units to convert to.
    """
    if _NO_CF_UNITS:
        raise ImportError("cf-units is required for unit conversion")
    try:
        result = cf_units.Unit(source_units).convert(data, target_units)
    except ValueError as err:
        for units in UNIT_EQUIVALENCE:
            if cf_units.Unit(source_units) == cf_units.Unit(units):
                try:
                    equal_units = UNIT_EQUIVALENCE[units]
                    result = cf_units.Unit(equal_units).convert(data, target_units)
                except ValueError:
                    raise err
                else:
                    break
    return result


def format_units(units):
    """
    Format units for display in LaTeX.

    Parameters
    ----------
    units : str
        The units to format.

    Example
    -------
    >>> format_units("kg m-2")
    "$kg m^{-2}$"
    """
    if _NO_CF_UNITS:
        return f"${PRETTY_UNITS.get(units, units)}$"

    from cf_units.tex import tex

    for name, formatted_units in PRETTY_UNITS.items():
        try:
            if are_equal(units, name):
                units = formatted_units
                break
        except ValueError:
            continue
    else:
        try:
            units = str(cf_units.Unit(units))
        except ValueError:
            pass

    try:
        formatted_units = f"${tex(units)}$"
    except SyntaxError:
        formatted_units = units

    return formatted_units
