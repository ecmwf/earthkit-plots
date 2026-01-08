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

import sys
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from earthkit.plots.geo import gisco


def test_invalid_geometry_type_raises():
    with pytest.raises(ValueError, match="Invalid geometry type"):
        gisco._download_and_cache_gisco(
            name="CNTR",
            category="countries",
            geometry_type="banana",
            resolution="60M",
            year=2024,
        )


def test_invalid_year_raises():
    with pytest.raises(ValueError, match="Year 1999 is not available"):
        gisco._download_and_cache_gisco(
            name="CNTR",
            category="countries",
            geometry_type="polygons",
            resolution="60M",
            year=1999,
        )


def test_valid_geometry_type():
    with patch("requests.get"):
        with patch.object(Path, "exists", return_value=True):
            # geometry_type 'polygons' is 'RG'
            path = gisco._download_and_cache_gisco(
                name="NUTS",
                category="nuts",
                geometry_type="polygons",
                resolution="01M",
                year=2024,
            )
            assert "NUTS_RG_01M_2024_4326.shp" in path


def test_filename_construction_with_suffix():
    with patch("requests.get"):
        with patch.object(Path, "exists", return_value=True):
            # geometry_type 'polygons' is 'RG'
            path = gisco._download_and_cache_gisco(
                name="NUTS",
                category="nuts",
                geometry_type="polygons",
                resolution="01M",
                year=2024,
                suffix="_LEVL_2",
            )
            assert "NUTS_RG_01M_2024_4326_LEVL_2.shp" in path


def test_filename_construction_countries():
    with patch("requests.get"):
        with patch.object(Path, "exists", return_value=True):
            # geometry_type 'polygons' is 'RG'
            path = gisco._download_and_cache_gisco(
                name="CNTR",
                category="countries",
                geometry_type="polygons",
                resolution="01M",
                year=2024,
            )
            assert "CNTR_RG_01M_2024_4326.shp" in path


def test_load_with_earthkit_data_warns(monkeypatch):
    monkeypatch.setitem(sys.modules, "earthkit.data", None)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = gisco._load_with_earthkit_data("dummy_path")
        assert any("not installed" in str(wi.message) for wi in w)
        assert result == "dummy_path"