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

import matplotlib
import matplotlib.pyplot as plt
import pytest

from earthkit.plots.components import figures


def test_add_attribution():
    fig = figures.Figure()
    fig.add_attribution("© Copyright message")
    assert fig.attributions == ["© Copyright message"]


def test_add_attribution_duplicate():
    fig = figures.Figure()
    fig.add_attribution("© Copyright message")
    fig.add_attribution("© Copyright message")
    assert fig.attributions == ["© Copyright message"]


def test_add_attribution_multiple():
    fig = figures.Figure()
    fig.add_attribution("© Copyright message 1")
    fig.add_attribution("© Copyright message 2")
    assert fig.attributions == ["© Copyright message 1", "© Copyright message 2"]


def test_add_logo():
    fig = figures.Figure()
    fig.add_logo("ecmwf")
    assert fig.logos == ["ecmwf"]


def test_add_logo_duplicate():
    fig = figures.Figure()
    fig.add_logo("ecmwf")
    fig.add_logo("ecmwf")
    assert fig.logos == ["ecmwf"]


def test_add_logo_multiple():
    fig = figures.Figure()
    fig.add_logo("ecmwf")
    fig.add_logo("copernicus")
    assert fig.logos == ["ecmwf", "copernicus"]


@pytest.fixture(autouse=True)
def close_figures():
    """Close all matplotlib figures after each test."""
    yield
    plt.close("all")


class TestRcParamsIsolation:
    """earthkit Figure must not permanently pollute matplotlib's global rcParams.

    Tests use a sentinel value injected into the schema so they are independent
    of whether earthkit's default styles happen to match matplotlib's defaults.
    """

    SENTINEL = "#010203"  # an unlikely matplotlib default

    def test_rcparams_restored_after_save(self, tmp_path):
        """RcParams must be restored to their pre-figure values after save()."""
        from earthkit.plots.schemas import schema

        before = matplotlib.rcParams["axes.edgecolor"]

        with schema.set(axes={"edgecolor": self.SENTINEL}):
            fig = figures.Figure(rows=1, columns=1)
            assert matplotlib.rcParams["axes.edgecolor"] == self.SENTINEL
            fig.save(tmp_path / "test.png")

        assert matplotlib.rcParams["axes.edgecolor"] == before

    def test_rcparams_restored_after_show(self, monkeypatch):
        """RcParams must be restored to their pre-figure values after show()."""
        from earthkit.plots.schemas import schema

        monkeypatch.setattr(plt, "show", lambda *a, **kw: None)
        before = matplotlib.rcParams["axes.edgecolor"]

        with schema.set(axes={"edgecolor": self.SENTINEL}):
            fig = figures.Figure(rows=1, columns=1)
            assert matplotlib.rcParams["axes.edgecolor"] == self.SENTINEL
            fig.show()

        assert matplotlib.rcParams["axes.edgecolor"] == before

    def test_style_context_active_during_figure_lifetime(self):
        """Earthkit styles must be active between Figure creation and show/save."""
        from earthkit.plots.schemas import schema

        with schema.set(axes={"edgecolor": self.SENTINEL}):
            fig = figures.Figure(rows=1, columns=1)

            assert fig._style_context is not None
            assert matplotlib.rcParams["axes.edgecolor"] == self.SENTINEL

    def test_exit_style_context_is_idempotent(self, monkeypatch):
        """Calling _exit_style_context multiple times must not raise."""
        monkeypatch.setattr(plt, "show", lambda *a, **kw: None)

        fig = figures.Figure(rows=1, columns=1)
        fig._exit_style_context()
        fig._exit_style_context()  # second call must be a no-op
