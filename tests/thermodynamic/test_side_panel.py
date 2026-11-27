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

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

pytest.importorskip("earthkit.meteo")

from earthkit.plots.thermodynamic import Emagram, SidePanel, SkewT, Tephigram  # noqa: E402

P = np.array([1000.0, 850.0, 700.0, 500.0, 300.0, 200.0])
DDEP = np.array([2.0, 5.0, 8.0, 12.0, 20.0, 25.0])


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("cls", [Tephigram, SkewT, Emagram])
def test_pressure_follows_right_edge(cls):
    d = cls()
    panel = d.side_panel()
    assert isinstance(panel, SidePanel)
    x0, x1, y0, y1 = d.extent
    # each level is where its isobar meets the right edge of the diagram
    _, p = d.geometry.inverse(np.full(P.shape, x1), panel.pressure_to_y(P))
    np.testing.assert_allclose(p, P, rtol=1e-3)
    assert panel.ax.get_ylim() == pytest.approx((y0, y1))


def test_tephigram_panel_differs_from_left_edge():
    # On a tephigram the isobars are curved, so the height of a level at the
    # right edge is not its height at the left edge
    d = Tephigram(temperature_range=(-20, 60), pressure_range=(1015, 30))
    panel = d.side_panel()
    x0 = d.extent[0]
    assert not np.allclose(panel.pressure_to_y(P), d.geometry.isobar_y(P, x0))


def test_pressure_labels():
    d = SkewT()
    panel = d.side_panel()
    labels = panel.ax.yaxis.get_major_formatter().seq
    assert "1000" in labels and "500" in labels and "100" in labels
    assert len(d.side_panel(pressure_labels=False).ax.get_yticks()) == 0


def test_isobars_follow_grid():
    d = SkewT()
    n = len(d.side_panel().ax.lines)
    assert n > 5
    assert len(d.side_panel(isobars=False).ax.lines) == 0
    d.grid(isobars=False)
    assert all(len(p.ax.lines) == 0 for p in d._side_panels)


def test_line_and_envelope():
    d = Tephigram()
    panel = d.side_panel(xlim=(0, 30), xlabel="T - Td (K)")
    line = panel.line(DDEP[::-1], p=P[::-1], color="blue")
    # ordered from the bottom up, plotted in the units of the data
    np.testing.assert_allclose(line.get_xdata(), DDEP)
    np.testing.assert_allclose(line.get_ydata(), panel.pressure_to_y(P))
    band = panel.envelope(DDEP - 1, DDEP + 1, p=P)
    verts = np.concatenate([path.vertices for path in band.get_paths()])
    assert verts[:, 0].min() == pytest.approx(1.0) and verts[:, 0].max() == pytest.approx(26.0)
    assert panel.ax.get_xlim() == (0, 30)
    assert panel.ax.get_xlabel() == "T - Td (K)"


def test_envelope_levels_must_match():
    xr = pytest.importorskip("xarray")
    lower = xr.DataArray(DDEP, coords={"level": P}, dims="level")
    upper = xr.DataArray(DDEP[:-1], coords={"level": P[:-1]}, dims="level")
    with pytest.raises(ValueError, match="same pressure levels"):
        SkewT().side_panel().envelope(lower, upper)


def test_wind_in_centre():
    panel = SkewT().side_panel(xlim=(0, 20))
    u = np.full(P.shape, 10.0)
    barbs = panel.wind(u, -u, p=P)
    offsets = barbs.get_offsets()
    np.testing.assert_allclose(offsets[:, 0], 10.0)
    np.testing.assert_allclose(offsets[:, 1], panel.pressure_to_y(P))
    # converted to knots by default
    np.testing.assert_allclose(barbs.u, 10.0 * 3600.0 / 1852.0)


def test_wind_outside_diagram_dropped():
    d = SkewT(pressure_range=(1050, 400))
    barbs = d.side_panel().wind(np.ones(P.shape), np.ones(P.shape), p=P, x=5)
    assert len(barbs.get_offsets()) == 4  # 1000, 850, 700, 500


def test_set_extent_updates_panel():
    d = SkewT()
    panel = d.side_panel()
    d.set_extent(pressure_range=(1000, 500))
    assert panel.ax.get_ylim() == pytest.approx(d.extent[2:])


def test_xaxis_off():
    panel = SkewT().side_panel(xaxis=False)
    assert len(panel.ax.get_xticks()) == 0


def test_diagram_wind_in_new_panel():
    d = Tephigram()
    u = np.full(P.shape, 10.0)
    barbs = d.wind(u, u, p=P, panel=True)
    (panel,) = d._side_panels
    assert barbs.axes is panel.ax
    assert len(panel.ax.get_xticks()) == 0
    np.testing.assert_allclose(barbs.get_offsets()[:, 1], panel.pressure_to_y(P))


def test_diagram_wind_in_existing_panel():
    d = SkewT()
    panel = d.side_panel(xlim=(0, 30))
    barbs = d.wind(np.ones(P.shape), np.ones(P.shape), p=P, panel=panel)
    assert barbs.axes is panel.ax and len(d._side_panels) == 1
    np.testing.assert_allclose(barbs.get_offsets()[:, 0], 15.0)


def test_diagram_wind_on_diagram_by_default():
    d = SkewT()
    barbs = d.wind(np.ones(P.shape), np.ones(P.shape), p=P)
    assert barbs.axes is d.ax and d._side_panels == []
