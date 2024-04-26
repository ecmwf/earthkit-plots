# Copyright 2024, European Centre for Medium Range Weather Forecasts.
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

import glob
import os

import yaml

from earthkit.plots import definitions, styles
from earthkit.plots.metadata.units import are_equal


def guess_style(data, units=None):
    from earthkit.maps import schema

    if os.path.exists(schema.style_library):
        styles_path = f"{schema.style_library}/*"
    else:
        styles_path = definitions.STYLES_DIR / (
            "*" if schema.style_library == "default" else f"{schema.style_library}/*"
        )

    for fname in glob.glob(str(styles_path)):
        if os.path.isfile(fname):
            with open(fname, "r") as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
        else:
            continue

        for criteria in config["criteria"]:
            for key, value in criteria.items():
                if data.metadata(key, default=None) != value:
                    break
            else:
                break
        else:
            continue
        break
    else:
        return styles.DEFAULT_STYLE

    if units is None:
        style = config["styles"][config["preferred-style"]]
    else:
        for _, style in config["styles"].items():
            if are_equal(style.get("units"), units):
                break
        else:
            # No style matching units found; return default
            return styles.Style(units=units)

    return styles.Style.from_dict(style)