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
import pytest

import earthkit.plots as ekp
from earthkit.plots import schema
from earthkit.plots.geography import domains


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_builtin_domains_figure():
    fig = ekp.Figure(rows=2, columns=3)
    for domain in ["Brazil", "North Atlantic", "Antarctica", "Africa", "Greenland", "Australia"]:
        fig.add_map(domain=domain)
    fig.land()
    fig.borders()
    fig.coastlines()
    fig.gridlines()
    fig.subplot_titles("{domain}")
    return fig.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_custom_domain():
    central_europe = domains.Domain.from_bbox(
        bbox=[2, 24, 45, 55],
        name="Central Europe",
    )
    chart = ekp.Map(domain=central_europe)
    chart.land()
    chart.borders()
    chart.coastlines()
    chart.gridlines()
    chart.title("{domain}")
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_override_crs():
    chart = ekp.Map(
        domain="Europe",
        crs=ccrs.NorthPolarStereo(central_longitude=10),
    )
    chart.coastlines()
    chart.borders()
    chart.land()
    chart.gridlines()
    chart.title("{domain} on a {crs} projection")
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_domain_union():
    EU_COUNTRIES = [
        "Austria",
        "Belgium",
        "Bulgaria",
        "Croatia",
        "Cyprus",
        "Czech Republic",
        "Denmark",
        "Estonia",
        "Finland",
        "France",
        "Germany",
        "Greece",
        "Hungary",
        "Ireland",
        "Italy",
        "Latvia",
        "Lithuania",
        "Luxembourg",
        "Netherlands",
        "Poland",
        "Portugal",
        "Romania",
        "Slovakia",
        "Slovenia",
        "Spain",
        "Sweden",
    ]
    EU = domains.union(EU_COUNTRIES, name="European Union")
    eu_map = ekp.Map(domain=EU)
    eu_map.countries(edgecolor="white")
    eu_map.countries(include=EU_COUNTRIES, facecolor="cornflowerblue", edgecolor="white", labels=True)
    eu_map.gridlines()
    eu_map.title("{domain}")
    eu_map.legend(
        ekp.styles.Categorical(
            categories=["Non-EU countries", "EU countries"],
            colors=["lightgrey", "cornflowerblue"],
        )
    )
    return eu_map.fig
