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

import re

import pint
from pint import UnitRegistry

from earthkit.plots.schemas import schema

ureg = UnitRegistry()
Q_ = ureg.Quantity


def _convert_whole_numbers(strings):
    """
    Converts strings that are whole numbers with decimals into strings of integers.

    Args:
    strings (list of str): List of strings to process.

    Returns:
    list of str: List with converted whole numbers.
    """
    converted = []
    for item in strings:
        try:
            # Try to convert the string to a float
            float_value = float(item)
            # Check if the float is a whole number
            if float_value.is_integer():
                # Convert it to an integer and then back to a string
                converted.append(str(int(float_value)))
            else:
                # If it's not a whole number, keep the original string
                converted.append(item)
        except ValueError:
            # If the string cannot be converted to a float, keep it as is
            converted.append(item)
    return converted


@pint.register_unit_format("E")
def format_unit_simple(unit, registry, **options):
    # Generating unit string with powers
    unit_str = " * ".join(f"{u} ** {p}" for u, p in unit.items())
    # Split the unit string correctly handling spaces and asterisks
    units = unit_str.replace(" ", "").split("*")
    units = _convert_whole_numbers(units)
    formatted_units = []

    # Iterate through the split units to format correctly
    i = 0
    while i < len(units):
        if i + 1 < len(units) and units[i + 1] == "":
            base = units[i]
            exponent = units[i + 2]
            if exponent != "1":
                formatted_units.append(f"{base}^{{{exponent}}}")
            else:
                formatted_units.append(base)
            i += 3  # move past the base, '**', and exponent
        else:
            formatted_units.append(units[i])
            i += 1

    # Join all formatted units with LaTeX multiplication, avoiding empty elements
    latex_string = " \\cdot ".join(filter(None, formatted_units))
    return latex_string


def _pintify(unit_str):
    if unit_str is None:
        unit_str = "dimensionless"

    # Replace spaces with dots
    unit_str = unit_str.replace(" ", ".")

    # Insert ^ between characters and numbers (including negative numbers)
    unit_str = re.sub(r"([a-zA-Z])(-?\d+)", r"\1^\2", unit_str)

    try:
        result = ureg(unit_str).units
    except pint.errors.UndefinedUnitError:
        result = unit_str
    return result


#: Units for temperature anomalies.
TEMPERATURE_ANOM_UNITS = [
    "kelvin",
    "celsius",
]


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
    return _pintify(unit_1) == _pintify(unit_2)


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
    source_units = _pintify(source_units)
    target_units = _pintify(target_units)
    try:
        result = (data * source_units).to(target_units).magnitude
    except ValueError as err:
        for units in UNIT_EQUIVALENCE:
            if source_units == _pintify(units):
                try:
                    equal_units = _pintify(UNIT_EQUIVALENCE[units])
                    result = (data * equal_units).to(target_units)
                except ValueError:
                    raise err
                else:
                    break
    return result


def format_units(units, format=None):
    """
    Format units for display in LaTeX.

    Parameters
    ----------
    units : str
        The units to format.
    format : str, optional
        The format to use. If not provided, the default format from the schema is used.

    Example
    -------
    >>> format_units("kg m-2")
    "$kg m^{-2}$"
    """
    format = format or schema.units_format
    if format == "R":
        return units
    if format == "~R":
        raise ValueError("Format '~R' is not supported.")
    units = _pintify(units)
    if isinstance(units, str):
        return units
    if units.dimensionless:
        return "dimensionless"
    else:
        latex_str = "{0:{1}}".format(units, format)
    return f"${latex_str}$"
