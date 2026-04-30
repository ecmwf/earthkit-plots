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

import earthkit.data as ekd
import pytest

import earthkit.plots as ekp
import matplotlib.pyplot as plt
from earthkit.plots import schema


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_subplot_layout():
    joachim = ekd.from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/metview/gallery/fc_msl_wg_joachim.grib",
    ).to_fieldlist()
    figure = ekp.Figure(domain=[-5, 23, 40, 58], figsize=(9, 7), rows=3, columns=4)

    gust_style = ekp.styles.Style(
        colors=["#85AAEE", "#208EFC", "#6CA632", "#FFB000", "#FF0000", "#7A11B1"],
        levels=[12, 15, 20, 25, 30, 35, 50],
        units="m s-1",
    )

    # Start at the top-right cell, leaving a gap for the colour bar
    figure.add_map(0, 3)
    for i in range(8):
        figure.add_map(1 + i // 4, i % 4)

    figure.contourf(joachim.sel({"parameter.variable": "10fg6"}), style=gust_style)
    figure.contour(joachim.sel({"parameter.variable": "msl"}), units="hPa", style="auto")

    figure.land()
    figure.coastlines()
    figure.borders()

    # Place the colourbar on a custom matplotlib axes
    ax = plt.axes((0.05, 0.8, 0.65, 0.025))
    figure.legend(ax=ax)

    figure.subplot_titles("{time.valid_datetime:%Y-%m-%d %H} UTC (+{time.step}h)")
    figure.title(
        "ECMWF HRES Run: {time.base_datetime:%Y-%m-%d %H} UTC\n{variable_name}",
        fontsize=13,
        horizontalalignment="left",
        x=0,
        y=0.96,
    )

    return figure.fig