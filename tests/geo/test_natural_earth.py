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

import cartopy.crs as ccrs
import pytest

from earthkit.plots.geo import natural_earth


def test_NaturalEarthDomain_name_France():
    ne_domain = natural_earth.NaturalEarthDomain(domain_name="France")
    assert ne_domain.domain_name == "France"


def test_NaturalEarthDomain_record_France():
    ne_domain = natural_earth.NaturalEarthDomain(domain_name="France")
    assert ne_domain.record.attributes["NAME_EN"] == "France"


def test_NaturalEarthDomain_crs_France():
    ne_domain = natural_earth.NaturalEarthDomain(domain_name="France")
    assert isinstance(ne_domain.crs, ccrs.AlbersEqualArea)


def test_NaturalEarthDomain_crs_India():
    ne_domain = natural_earth.NaturalEarthDomain(domain_name="India")
    assert isinstance(ne_domain.crs, ccrs.PlateCarree)


def test_NaturalEarthDomain_bounds_France():
    ne_domain = natural_earth.NaturalEarthDomain(domain_name="France")
    assert ne_domain.bounds == pytest.approx([-626161, 690812, -625183, 649633])
