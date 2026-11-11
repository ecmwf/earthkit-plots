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

import pytest

from earthkit.plots.metadata import units


@pytest.mark.parametrize(
    "unit_str, expected",
    [
        ("K days", "day * kelvin"),
        ("mm d-1", "millimeter / day"),
        ("kg m-2", "kilogram / meter ** 2"),
        ("m s-1", "meter / second"),
        ("mm / day", "millimeter / day"),
    ],
)
def test_pintify_compound_units_with_spaces(unit_str, expected):
    ureg = units._get_ureg()
    assert units._pintify(unit_str) == ureg(expected).units


def test_format_units_compound_units_with_spaces():
    assert units.format_units("K days", format="~L") == r"$\mathrm{d} \cdot \mathrm{K}$"
