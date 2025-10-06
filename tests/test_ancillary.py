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

from earthkit.plots import ancillary


def test_load_geo_domains():
    result = ancillary.load("geo/domains")
    assert isinstance(result, dict) and "domains" in result


def test_find_logo_ecmwf():
    result = ancillary.find_logo("ecmwf")
    assert result.endswith("ecmwf.png")


def test_find_logo_not_found():
    with pytest.raises(ancillary.DataNotFoundError):
        ancillary.find_logo("nonexistent")
