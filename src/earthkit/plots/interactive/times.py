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

import warnings

TIME_DIMS = ["time", "t", "month"]


def guess_time_dim(data):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dims = dict(data.squeeze().dims)
        for dim in TIME_DIMS:
            if dim in dims:
                return dim


def guess_non_time_dim(data):
    dims = list(data.squeeze().dims)
    for dim in TIME_DIMS:
        if dim in dims:
            dims.pop(dims.index(dim))
            break

    if len(dims) == 1:
        return list(dims)[0]

    else:
        raise ValueError("could not identify single dim over which to aggregate")
