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

from earthkit.plots.components import subplots


def test_subplots_figure_size():
    # Test that the figure size is set correctly when creating a subplot
    subplot = subplots.Subplot(figsize=[10, 5])
    assert subplot.figure._figsize == [10, 5]


def test_subplots_figure_size_deprecated():
    with pytest.warns(DeprecationWarning, match="figsize"):
        subplot = subplots.Subplot(size=[10, 5])
    assert subplot.figure._figsize == [10, 5]


class _DummyStyle:
    """Minimal stand-in for a Style exposing only ``_preferred_method``."""

    def __init__(self, preferred_method="contourf"):
        self._preferred_method = preferred_method


def test_resolve_style_method_with_style_object():
    # An explicit Style object resolves to its preferred method and is passed
    # through unchanged as the style argument.
    subplot = subplots.Subplot()
    style = _DummyStyle("contourf")
    method, style_arg = subplot._resolve_style_method(None, style, None)
    assert method == subplot.contourf
    assert style_arg is style


def test_resolve_style_method_none_skips_detection():
    # ``None`` skips style detection and falls back to the cell renderer
    # (pcolormesh on a base Subplot).
    subplot = subplots.Subplot()
    method, style_arg = subplot._resolve_style_method(None, None, None)
    assert method == subplot.pcolormesh
    assert style_arg is None


def test_resolve_style_method_auto_without_match(monkeypatch):
    # "auto" with no matching style falls back to the cell renderer but still
    # forwards the "auto" sentinel.
    subplot = subplots.Subplot()
    monkeypatch.setattr(subplots.auto, "guess_style", lambda source, units=None, **kwargs: None)
    method, style_arg = subplot._resolve_style_method("source", "auto", None)
    assert method == subplot.pcolormesh
    assert style_arg == "auto"
