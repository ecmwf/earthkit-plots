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


TEMPERATURE_ANOM_UNITS = [
    "kelvin",
    "celsius",
]


PRETTY_UNITS = {
    "celsius": "°C",
    "fahrenheit": "°F",
}


def are_equal(unit_1, unit_2):
    if _NO_CF_UNITS:
        raise ImportError("cf-units is required for checking unit equivalence")
    return cf_units.Unit(unit_1) == cf_units.Unit(unit_2)


def anomaly_equivalence(units):
    return any(are_equal(units, t_units) for t_units in TEMPERATURE_ANOM_UNITS)


def convert(data, source_units, target_units):
    if _NO_CF_UNITS:
        raise ImportError("cf-units is required for unit conversion")
    return cf_units.Unit(source_units).convert(data, target_units)


def format_units(units):
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
