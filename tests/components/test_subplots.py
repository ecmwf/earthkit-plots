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

from earthkit.plots.components import subplots


def test_subplots_figure_size():
    # Test that the figure size is set correctly when creating a subplot
    subplot = subplots.Subplot(figsize=[10, 5])
    assert subplot.figure._figsize == [10, 5]


def test_subplots_figure_size_deprecated():
    import pytest

    with pytest.warns(DeprecationWarning, match="figsize"):
        subplot = subplots.Subplot(size=[10, 5])
    assert subplot.figure._figsize == [10, 5]


def test_pcolormesh_interpolate_kwarg_with_style_does_not_leak():
    """The deprecated ``interpolate`` kwarg must not leak to matplotlib.

    Regression test for #183: supplying both a ``style`` and the legacy
    ``interpolate`` kwarg raised ``AttributeError: QuadMesh.set() got an
    unexpected keyword argument 'interpolate'`` because the kwarg was passed
    straight through to ``Axes.pcolormesh`` instead of being translated into a
    resample step.
    """
    import numpy as np
    import pytest
    import xarray as xr

    from earthkit.plots.styles import Style

    data = xr.DataArray(
        np.random.rand(10, 10) * 50 + 250,
        dims=["lat", "lon"],
        coords={"lat": np.linspace(-89, 89, 10), "lon": np.linspace(-179, 179, 10)},
        attrs={"units": "K"},
    )
    style = Style(colors="viridis", levels=[250, 270, 290, 310])
    subplot = subplots.Subplot()
    with pytest.warns(DeprecationWarning, match="interpolate"):
        subplot.pcolormesh(data, style=style, interpolate={"distance_threshold": "auto"})
    assert len(subplot.layers) == 1
