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
