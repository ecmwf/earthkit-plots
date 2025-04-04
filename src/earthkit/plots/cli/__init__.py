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

import argparse

import earthkit.data

import earthkit.plots.quickmap as qmap
from earthkit.plots.cli.parsers import parse_yaml

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("file", type=str, help="File to plot")


def cli():
    args = parser.parse_args()

    if any(args.file.endswith(ext) for ext in [".yml", ".yaml"]):
        return parse_yaml(args.file)
    data = earthkit.data.from_source("file", args.file)
    qmap.block(data, units=args.units).show()
