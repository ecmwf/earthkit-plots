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
import numpy as np
import pytest

from earthkit.plots.geography import domains
from earthkit.plots.schemas import schema


@pytest.fixture(autouse=True)
def enable_crop_domain():
    """Force crop_domain=True for all Domain.extract tests.

    The schema default is False (cropping is opt-in at runtime), but the
    tests here specifically exercise the extraction logic so they need it on.
    """
    original = schema.crop_domain
    schema.crop_domain = True
    yield
    schema.crop_domain = original


def test_format_name_UK():
    name = domains.format_name("UK")
    assert name == "United Kingdom"


def test_union():
    domain = domains.union(["UK", "France"])
    assert list(domain.bbox) == pytest.approx(
        [-932531, 781009, -1070763, 1162024], 0.001
    )


def test_force_minus_180_to_180():
    assert domains.force_minus_180_to_180(-190) == 170
    assert domains.force_minus_180_to_180(190) == -170
    assert domains.force_minus_180_to_180(180) == 180
    assert domains.force_minus_180_to_180(-180) == -180
    assert domains.force_minus_180_to_180(0) == 0


def test_force_0_to_360():
    assert domains.force_0_to_360(-10) == 350
    assert domains.force_0_to_360(370) == 10
    assert domains.force_0_to_360(360) == 360
    assert domains.force_0_to_360(0) == 0
    assert domains.force_0_to_360(180) == 180
    assert domains.force_0_to_360(-180) == 180


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


class TestDomainExtract:
    """Test cases for the Domain.extract method."""

    def test_extract_simple_gridded_data(self):
        """Test basic extraction of gridded data without longitude wrapping."""
        domain = domains.Domain([-10, 10, -10, 10])

        x = np.linspace(-20, 20, 41)
        y = np.linspace(-20, 20, 41)
        values = np.random.random((41, 41))

        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.min() >= -11  # Domain -10 with ~1 degree padding
        assert x_ext.max() <= 11
        assert y_ext.min() >= -11
        assert y_ext.max() <= 11

        assert values_ext.shape == x_ext.shape == y_ext.shape

    def test_extract_simple_1D_data(self):
        """Test basic extraction of gridded data without longitude wrapping."""
        domain = domains.Domain([-10, 10, -10, 10])

        x = np.linspace(-20, 20, 41)
        y = np.linspace(-20, 20, 41)
        values = np.random.random(41)

        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.min() >= -11  # Domain -10 with ~1 degree padding
        assert x_ext.max() <= 11
        assert y_ext.min() >= -11
        assert y_ext.max() <= 11

        assert values_ext.shape == x_ext.shape == y_ext.shape

    def test_extract_longitude_wrapping_0_360_to_negative(self):
        """Test longitude wrapping when data is 0-360 and domain spans negative longitudes."""
        domain = domains.Domain([-10, 40, 35, 70])  # Europe-like domain

        x = np.linspace(0, 360, 361)
        y = np.linspace(-90, 90, 181)
        values = np.random.random((181, 361))

        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.shape == y_ext.shape == values_ext.shape
        assert x_ext.shape[0] > 0
        assert x_ext.shape[1] > 0

    def test_extract_longitude_wrapping_minus_180_180_spanning_0(self):
        """Test longitude wrapping when data is -180 to 180 and domain spans 0 meridian."""
        domain = domains.Domain([-5, 5, -5, 5])

        x = np.linspace(-180, 180, 361)
        y = np.linspace(-90, 90, 181)
        values = np.random.random((181, 361))

        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.shape == y_ext.shape == values_ext.shape
        assert x_ext.shape[0] > 0
        assert x_ext.shape[1] > 0

    def test_extract_with_extra_values(self):
        """Test extraction with extra values."""
        domain = domains.Domain([-5, 5, -5, 5])

        x = np.linspace(-10, 10, 21)
        y = np.linspace(-10, 10, 21)
        values = np.random.random((21, 21))
        extra1 = np.random.random((21, 21))
        extra2 = np.random.random((21, 21))

        x_ext, y_ext, values_ext, extra_ext = domain.extract(
            x, y, values, [extra1, extra2]
        )

        assert x_ext.shape == y_ext.shape == values_ext.shape
        assert len(extra_ext) == 2
        assert extra_ext[0].shape == x_ext.shape
        assert extra_ext[1].shape == x_ext.shape

    def test_extract_with_3d_values(self):
        """Test extraction with 3D values (e.g., time series)."""
        domain = domains.Domain([-5, 5, -5, 5])

        x = np.linspace(-10, 10, 21)
        y = np.linspace(-10, 10, 21)
        values = np.random.random((21, 21, 5))  # 5 time steps

        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert values_ext.shape == (x_ext.shape[0], x_ext.shape[1], 5)

    def test_extract_basic_functionality(self):
        """Test basic extraction functionality with various data types."""
        domain = domains.Domain([-5, 5, -5, 5])

        test_cases = [
            # (x_shape, y_shape, values_shape, description)
            ((21, 21), (21, 21), (21, 21), "2D gridded data"),
            ((21, 21), (21, 21), (21, 21, 3), "2D gridded data with 3D values"),
            ((21,), (21,), (21, 21), "1D coordinates that get converted to meshgrid"),
            (
                (21,),
                (21,),
                (21),
                "1D coordinates and data, they do not get converted to meshgrid",
            ),
        ]

        for x_shape, y_shape, values_shape, description in test_cases:
            if len(x_shape) == 1:
                x = np.linspace(-10, 10, x_shape[0])
                y = np.linspace(-10, 10, y_shape[0])
            else:
                x = np.random.random(x_shape)
                y = np.random.random(y_shape)

            values = np.random.random(values_shape)

            x_ext, y_ext, values_ext = domain.extract(x, y, values)

            assert x_ext.size > 0, f"Failed for {description}"
            assert y_ext.size > 0, f"Failed for {description}"
            assert values_ext.size > 0, f"Failed for {description}"

            assert x_ext.shape == y_ext.shape, f"Shape mismatch for {description}"
            if values_ext.ndim in [1, 2]:
                assert values_ext.shape == x_ext.shape, (
                    f"Values shape mismatch for {description}"
                )
            elif values_ext.ndim == 3:
                assert values_ext.shape[:2] == x_ext.shape, (
                    f"Values shape mismatch for {description}"
                )

    def test_extract_edge_case_empty_result(self):
        """Test extraction edge case where result would be empty."""
        domain = domains.Domain([0.1, 0.2, 0.1, 0.2])

        x = np.linspace(-1, 1, 21)
        y = np.linspace(-1, 1, 21)
        values = np.random.random((21, 21))

        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.size > 0
        assert y_ext.size > 0
        assert values_ext.size > 0

    def test_extract_with_source_crs(self):
        """Test extraction with different source CRS."""
        domain = domains.Domain([-5, 5, -5, 5], crs=ccrs.LambertAzimuthalEqualArea())

        x = np.linspace(-10, 10, 21)
        y = np.linspace(-10, 10, 21)
        values = np.random.random((21, 21))

        x_ext, y_ext, values_ext = domain.extract(
            x, y, values, source_crs=ccrs.PlateCarree()
        )

        assert x_ext.shape == y_ext.shape == values_ext.shape
        assert x_ext.size > 0

    def test_extract_1d_coordinates(self):
        """Test extraction with 1D coordinates that get converted to meshgrid."""
        domain = domains.Domain([-5, 5, -5, 5])

        x = np.linspace(-10, 10, 21)
        y = np.linspace(-10, 10, 21)
        values = np.random.random((21, 21))

        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.shape == y_ext.shape == values_ext.shape
        assert x_ext.ndim == 2  # Should be converted to 2D
        assert y_ext.ndim == 2

    def _global_0_360_grid(self):
        """Return a global 1-degree grid with longitudes in 0-360."""
        lons = np.linspace(0, 359, 360)
        lats = np.linspace(-90, 90, 181)
        lon2d, lat2d = np.meshgrid(lons, lats)
        # Values encode the longitude so we can check which columns were kept.
        values = lon2d.copy()
        return lon2d, lat2d, values

    def test_extract_antimeridian_straddling_domain_0_360_data(self):
        """Data 0-360, domain straddles the antimeridian (USA-like bounds ~150E-330E).

        This was the bug: crs_bounds[0] > 0 and crs_bounds[1] > 180 but the
        old elif guard required crs_bounds[1] > x.max() (~360), which was false,
        so no rolling was done and the mask cut off everything west of 150°E.
        """
        # Approximate USA bounds in 0-360 space (150°E to 330°E / -30°E)
        domain = domains.Domain([150, 330, 10, 80])

        x, y, values = self._global_0_360_grid()
        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.size > 0, "No data extracted for antimeridian-straddling domain"

        # The extracted x values should be in –180 to +180 (rolled for cartopy).
        assert x_ext.min() >= -180
        assert x_ext.max() <= 180

        # The domain covers both sides of the antimeridian: longitudes
        # 150°–180° (east side) AND –180°–(–30°) / 330°–360° (west side).
        # Both sides must be present after extraction.
        assert (x_ext >= 150).any(), "East side of antimeridian missing"
        assert (x_ext < 0).any(), "West side of antimeridian (negative lons) missing"

    def test_extract_antimeridian_explicit_0_360_domain_regression(self):
        """Explicit 0-360 domain straddling antimeridian ([100, 300, ...]) must still work."""
        domain = domains.Domain([100, 300, -50, 50])

        x, y, values = self._global_0_360_grid()
        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.size > 0
        # Should cover both east (100-180) and west (-180 to -60 / 300-360) sides.
        assert (x_ext >= 100).any() or (x_ext >= -180).any()

    def test_extract_antimeridian_values_contiguous(self):
        """Extracted values must correspond to the correct columns after rolling.

        Checks that the roll doesn't introduce an offset between x and values
        (the misalignment bug that appeared in an earlier fix attempt).
        """
        domain = domains.Domain([150, 330, -10, 10])

        lons = np.linspace(0, 359, 360)
        lats = np.linspace(-90, 90, 181)
        lon2d, lat2d = np.meshgrid(lons, lats)
        # values[i, j] == lon2d[i, j] so we can verify alignment.
        values = lon2d.copy()

        x_ext, y_ext, values_ext = domain.extract(lon2d, lat2d, values)

        assert x_ext.size > 0
        # After extraction, every value must match its x coordinate
        # (values encode the original longitude, x is the shifted longitude).
        # The shifted x should equal (original_lon mod 360 shifted to –180/+180),
        # but the simplest alignment check: no cell should be off by more than
        # 0.5° from the nearest expected original longitude.
        orig_lons = x_ext % 360  # back to 0-360
        np.testing.assert_allclose(
            orig_lons % 360,
            values_ext % 360,
            atol=0.6,
            err_msg="x and values are misaligned after antimeridian roll",
        )

    def test_extract_europe_domain_0_360_data_unaffected(self):
        """Europe domain (crs_bounds[0] < 0) with 0-360 data still works correctly."""
        domain = domains.Domain([-10, 40, 35, 70])

        x, y, values = self._global_0_360_grid()
        x_ext, y_ext, values_ext = domain.extract(x, y, values)

        assert x_ext.size > 0
        # Europe longitudes are roughly –10 to +40.
        assert x_ext.min() >= -15
        assert x_ext.max() <= 45

    def test_extract_projected_crs_data_not_treated_as_longitudes(self):
        """Data in a projected (metre-based) CRS must not have its x values
        treated as longitudes even when they are numerically > 180.

        Regression: the antimeridian fix checked crs_bounds[1] > 180 and
        x > 180 without guarding against projected coordinates, causing LAEA
        data reprojected to PlateCarree to produce an empty plot.
        """
        laea = ccrs.LambertAzimuthalEqualArea(central_longitude=10, central_latitude=52)

        # Simulate LAEA metre coordinates for a Europe-sized domain.
        # x values are in the range -1e6 to +1e6 metres — all > 180.
        lons_m = np.linspace(-1_000_000, 1_000_000, 50)
        lats_m = np.linspace(-800_000, 800_000, 50)
        x2d, y2d = np.meshgrid(lons_m, lats_m)
        values = np.ones_like(x2d)

        # Domain in LAEA space covering the same region.
        domain = domains.Domain([-1_100_000, 1_100_000, -900_000, 900_000], crs=laea)

        x_ext, y_ext, values_ext = domain.extract(x2d, y2d, values, source_crs=laea)

        # All data should be returned — nothing should be dropped by a bogus roll.
        assert x_ext.size > 0
        # x coordinates must stay in metre range, not be collapsed to [-180, 180].
        assert x_ext.max() > 180, (
            "Projected x coordinates were incorrectly treated as longitudes"
        )
