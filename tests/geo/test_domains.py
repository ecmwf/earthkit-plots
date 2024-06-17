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

import pytest

from earthkit.plots.geo import domains


def test_format_name_UK():
    name = domains.format_name("UK")
    assert name == "United Kingdom"


def test_union():
    domain = domains.union(["UK", "France"])
    assert list(domain.bbox) == pytest.approx(
        [-932531, 781009, -1070763, 1162024], 0.001
    )


def test_Domain_from_string():
    domain = domains.Domain.from_string("United Kingdom")
    assert list(domain.bbox) == pytest.approx([-363797, 373425, -541558, 545791], 0.001)


def test_Domain_from_bbox():
    domain = domains.Domain.from_bbox([-10, 20, -10, 20])
    assert list(domain.bbox) == pytest.approx([-15, 15, -10, 20])


def test_Domain_name_single():
    domain = domains.Domain([-180, 180, -90, 90], name="foo")
    assert domain.name == "foo"


def test_Domain_name_multiple():
    domain = domains.Domain([-180, 180, -90, 90], name=["foo", "bar", "baz"])
    assert domain.name == "foo, bar and baz"


def test_Domain_title_with_name():
    domain = domains.Domain([-180, 180, -90, 90], name="foo")
    assert domain.title == "foo"


def test_Domain_title_without_name():
    domain = domains.Domain([-180, 180, -90, 90])
    assert domain.title == "-180°W, 180°E, -90°S, 90°N"


def test_Domain_title_without_name_zero():
    domain = domains.Domain([-180, 180, 0, 90])
    assert domain.title == "-180°W, 180°E, 0°, 90°N"
