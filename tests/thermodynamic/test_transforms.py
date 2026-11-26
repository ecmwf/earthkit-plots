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

import numpy as np
import pytest

pytest.importorskip("earthkit.meteo")

from earthkit.plots.thermodynamic.transforms import (  # noqa: E402
    EmagramGeometry,
    SkewTGeometry,
    TephigramGeometry,
    ThermoTransform,
    potential_temperature,
)

GEOMETRIES = [EmagramGeometry(), SkewTGeometry(), SkewTGeometry(skew=30), TephigramGeometry()]
IDS = ["emagram", "skewt", "skewt30", "tephigram"]

T = np.array([-90.0, -60.0, -20.0, 0.0, 25.0, 45.0])
P = np.array([1050.0, 850.0, 500.0, 200.0, 50.0, 10.0])


def _angle(geometry, t, p):
    """Angle (degrees) of the segment between two (T, p) points in diagram coordinates."""
    x, y = geometry.forward(np.asarray(t, dtype=float), np.asarray(p, dtype=float))
    return np.degrees(np.arctan2(y[1] - y[0], x[1] - x[0]))


@pytest.mark.parametrize("geometry", GEOMETRIES, ids=IDS)
def test_roundtrip(geometry):
    x, y = geometry.forward(T, P)
    t, p = geometry.inverse(x, y)
    np.testing.assert_allclose(t, T, atol=1e-9)
    np.testing.assert_allclose(p, P, rtol=1e-12)


@pytest.mark.parametrize("geometry", GEOMETRIES, ids=IDS)
def test_pressure_decreases_upwards(geometry):
    _, y = geometry.forward(np.zeros(4), np.array([1000.0, 700.0, 300.0, 100.0]))
    assert np.all(np.diff(y) > 0)


def test_emagram_isotherms_vertical():
    assert _angle(EmagramGeometry(), [10, 10], [1000, 300]) == pytest.approx(90.0)


@pytest.mark.parametrize("skew", [30.0, 45.0, 60.0])
def test_skewt_isotherm_angle(skew):
    assert _angle(SkewTGeometry(skew=skew), [-20, -20], [1000, 300]) == pytest.approx(skew)


def test_skewt_invalid_skew():
    with pytest.raises(ValueError):
        SkewTGeometry(skew=90)


def test_tephigram_isotherms_and_dry_adiabats_are_perpendicular():
    g = TephigramGeometry()
    # isotherm at 45 degrees
    assert _angle(g, [0, 0], [1000, 400]) == pytest.approx(45.0)
    # dry adiabat theta = 300 K at -45 degrees
    t = np.array([20.0, -30.0])
    p = 1000.0 * ((t + 273.15) / 300.0) ** (1 / 0.285691)
    np.testing.assert_allclose(potential_temperature(t, p), 300.0, rtol=1e-6)
    assert _angle(g, t[::-1], p[::-1]) == pytest.approx(-45.0)


def test_tephigram_isobars_horizontal_near_reference():
    # Along an isobar dY/dX = a / T, so with a = 273.15 K isobars are horizontal at 0 C
    assert _angle(TephigramGeometry(), [-0.5, 0.5], [1000, 1000]) == pytest.approx(0.0, abs=0.1)


@pytest.mark.parametrize("geometry", GEOMETRIES, ids=IDS)
def test_isotherm_x(geometry):
    y = np.array([0.0, 30.0, 80.0])
    x = geometry.isotherm_x(15.0, y)
    t, _ = geometry.inverse(x, y)
    np.testing.assert_allclose(t, 15.0, atol=1e-9)


@pytest.mark.parametrize("geometry", GEOMETRIES, ids=IDS)
def test_isobar_y(geometry):
    x = np.array([-40.0, 0.0, 30.0])
    y = geometry.isobar_y(500.0, x)
    _, p = geometry.inverse(x, y)
    np.testing.assert_allclose(p, 500.0, rtol=1e-4)


@pytest.mark.parametrize("geometry", GEOMETRIES, ids=IDS)
def test_extent_bottom_corners(geometry):
    x0, x1, y0, y1 = geometry.extent((-40.0, 50.0), (1050.0, 100.0))
    assert x0 < x1 and y0 < y1
    # The bottom isobar runs between the minimum and maximum temperature
    xb, yb = geometry.forward(np.array([-40.0, 50.0]), 1050.0)
    np.testing.assert_allclose(xb, [x0, x1])
    assert np.all(yb >= y0 - 1e-9)


@pytest.mark.parametrize("geometry", GEOMETRIES, ids=IDS)
def test_extent_top(geometry):
    x0, x1, _, y1 = geometry.extent((-40.0, 50.0), (1050.0, 100.0))
    _, p = geometry.inverse(0.5 * (x0 + x1), y1)
    assert p == pytest.approx(100.0, rel=1e-4)


@pytest.mark.parametrize("geometry", GEOMETRIES, ids=IDS)
def test_matplotlib_transform(geometry):
    tr = ThermoTransform(geometry)
    pts = np.column_stack([T, P])
    out = tr.transform(pts)
    x, y = geometry.forward(T, P)
    np.testing.assert_allclose(out, np.column_stack([x, y]))
    np.testing.assert_allclose(tr.inverted().transform(out), pts, rtol=1e-10, atol=1e-9)
