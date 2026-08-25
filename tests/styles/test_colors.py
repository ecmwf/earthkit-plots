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

from earthkit.plots.styles.colors import cmap_and_norm

LEVELS = [0, 1, 2, 3]

EPS = 1e-9


def color_at(cmap, norm, value):
    """The RGBA colour which `value` is rendered with."""
    return tuple(np.asarray(cmap(norm(value)), dtype=float))


@pytest.mark.parametrize("extend", [None, "min"])
@pytest.mark.parametrize("colors", ["viridis", ["red", "green", "blue", "yellow"]])
def test_top_level_matches_final_bin(colors, extend):
    """Values equal to `levels[-1]` take the colour of the final bin.

    `BoundaryNorm` assigns `levels[-1]` the over-range index, so a colormap
    which is not extended at the top must fall back to its final colour rather
    than rendering the value transparent (see GH #243).
    """
    cmap, norm = cmap_and_norm(colors, LEVELS, True, extend, extend_levels=False)

    assert color_at(cmap, norm, LEVELS[-1]) == color_at(cmap, norm, LEVELS[-1] - EPS)


@pytest.mark.parametrize("extend", ["max", "both"])
@pytest.mark.parametrize("colors", ["viridis", ["red", "green", "blue", "yellow"]])
def test_top_level_takes_extend_color(colors, extend):
    """Where the colormap is extended at the top, `levels[-1]` takes the over colour."""
    cmap, norm = cmap_and_norm(colors, LEVELS, True, extend, extend_levels=False)

    assert color_at(cmap, norm, LEVELS[-1]) == tuple(np.asarray(cmap.get_over(), dtype=float))


@pytest.mark.parametrize("extend", [None, "min", "max", "both"])
@pytest.mark.parametrize("colors", ["viridis", ["red", "green", "blue", "yellow"]])
def test_bottom_level_matches_first_bin(colors, extend):
    """Values equal to `levels[0]` take the colour of the first bin."""
    cmap, norm = cmap_and_norm(colors, LEVELS, True, extend, extend_levels=False)

    assert color_at(cmap, norm, LEVELS[0]) == color_at(cmap, norm, LEVELS[0] + EPS)


@pytest.mark.parametrize("extend", [None, "min", "max", "both"])
@pytest.mark.parametrize("colors", ["viridis", ["red", "green", "blue", "yellow"]])
def test_out_of_range_values_are_opaque(colors, extend):
    """Out-of-range values are never rendered transparent.

    Transparency is reserved for masked/NaN data; values which merely fall
    outside the levels take the colour of the nearest end of the colormap.
    """
    cmap, norm = cmap_and_norm(colors, LEVELS, True, extend, extend_levels=False)

    assert color_at(cmap, norm, LEVELS[-1] + 1)[3] == 1.0
    assert color_at(cmap, norm, LEVELS[0] - 1)[3] == 1.0


@pytest.mark.parametrize("colors", ["viridis", ["red", "green", "blue", "yellow"]])
def test_unextended_endpoints_match_matplotlib(colors):
    """With `extend=None`, endpoints behave as an ordinary matplotlib Colormap.

    Matplotlib defaults `over`/`under` to the terminal colours of the colormap,
    so both ends of the levels render opaquely.
    """
    cmap, norm = cmap_and_norm(colors, LEVELS, True, None, extend_levels=False)

    assert tuple(np.asarray(cmap.get_over(), dtype=float)) == color_at(cmap, norm, LEVELS[-1] - EPS)
    assert tuple(np.asarray(cmap.get_under(), dtype=float)) == color_at(cmap, norm, LEVELS[0])


@pytest.mark.parametrize("extend", [None, "min", "max", "both"])
def test_extend_colors_are_not_reused_as_bins(extend):
    """Colours reserved for the extend arrows are not also used as in-range bins."""
    colors = ["red", "green", "blue", "yellow"]
    cmap, norm = cmap_and_norm(colors, LEVELS, True, extend, extend_levels=False)

    in_range = [color_at(cmap, norm, level + 0.5) for level in LEVELS[:-1]]

    if extend in ("both", "max"):
        assert tuple(np.asarray(cmap.get_over(), dtype=float)) not in in_range
    if extend in ("both", "min"):
        assert tuple(np.asarray(cmap.get_under(), dtype=float)) not in in_range
