# Copyright 2023, European Centre for Medium Range Weather Forecasts.
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

LABEL_PREFERENCE = [
    "long_name",
    "name",
    "standard_name",
    "short_name",
    "var_name",
]


def get_axis_title(data, attr=None):
    title = get_label(data, attr) or str()
    units = get_units(data, attr)
    if units is not None:
        title = f"{title} ({units})"
    return title


def get_label(data, attr=None):
    if attr is not None:
        data = data[attr]
    for item in LABEL_PREFERENCE:
        try:
            label = getattr(data, item)
            break
        except AttributeError:
            continue
    else:
        label = attr
    return label


def get_units(data, attr=None):
    units = None
    if attr is not None:
        data = data[attr]
    try:
        units = data.units
    except AttributeError:
        pass
    return units


def split_dim(dataarray, dim):
    dataarray = [dataarray.isel(**{dim: i}) for i in range(len(dataarray[dim]))]
    return dataarray


def dim_labels(dataarray, dim):
    labels = [f"{dim}={value}" for value in dataarray[dim].values()]
    return labels