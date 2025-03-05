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

import yaml

import earthkit.plots
from earthkit.plots.geo.coordinate_reference_systems import parse_crs


def parse_yaml(file):
    with open(file) as f:
        config = yaml.safe_load(f)

    chart = None
    if "tile" in config:
        if "crs" in config["tile"]:
            config["tile"]["crs"] = parse_crs(config["tile"]["crs"])
        chart = earthkit.plots.Tile(**config["tile"])
        figure = chart.figure
    else:
        figure = earthkit.plots.Figure(**config.get("figure", {}))

    for item in config.get("workflow", []):
        if "subplot" in item:
            if chart is None:
                subplot_type = item["subplot"].pop("type", "map")
                subplot = getattr(figure, f"add_{subplot_type}")(
                    **{
                        key: value
                        for key, value in item["subplot"].items()
                        if key != "layers"
                    }
                )
            else:
                subplot = chart
            for layer in item["subplot"].get("layers", []):
                if isinstance(layer, dict):
                    method = list(layer.keys())[0]
                    kwargs = layer[method]
                    if "source" in kwargs:
                        kwargs["data"] = earthkit.data.from_source(
                            kwargs["source"]["type"],
                            kwargs["source"]["path"],
                        )
                        del kwargs["source"]
                else:
                    method = layer
                    kwargs = {}
                getattr(subplot, method)(**kwargs)

    if "save" in config:
        figure.save(**config["save"])
