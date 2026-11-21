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

import json
from pathlib import Path

import pytest

from earthkit.plots.styles import Style
from earthkit.plots.styles.magics import from_magics


class MagicsFixtures:
    def __init__(self, fname):
        p = Path(__file__).parent / fname
        with p.open("rt") as f:
            fixtures = sorted((name, data) for (name, data) in json.load(f).items())
            self.ids = [n for (n, _) in fixtures]
            self.data = [d for (_, d) in fixtures]


_contour_fixtures = MagicsFixtures("eccharts-magics-contour-styles.json")


@pytest.fixture(scope="session", params=_contour_fixtures.data, ids=_contour_fixtures.ids)
def magics_contour_style(request):
    return request.param


def test_magics_contour_style_conversion(magics_contour_style):
    """Magics countour styles used in eccharts can be converted to earthkit-plots styles."""
    style = from_magics(**magics_contour_style)
    assert style


def test_contour_style_serialise_deserialise(magics_contour_style):
    """Contour style definitions can be serialised to JSON, and deserialised back from JSON."""
    style = from_magics(**magics_contour_style)
    ser = json.dumps(style.to_dict())
    des = Style.from_dict(json.loads(ser))
    assert des == style
