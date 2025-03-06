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

from datetime import datetime

import cftime
import numpy as np
import pandas as pd

from earthkit.plots.utils import time_utils


def test_python_datetime_to_pydatetime():
    dt = datetime(1991, 10, 12, 12, 30, 20)
    assert time_utils.to_pydatetime(dt) == dt


def test_numpy_datetime64_to_pydatetime():
    dt = np.datetime64("2023-12-15T12:34:56")
    expected = datetime.strptime("2023-12-15T12:34:56", "%Y-%m-%dT%H:%M:%S")
    assert time_utils.to_pydatetime(dt) == expected


def test_pandas_timestamp_to_pydatetime():
    dt = pd.Timestamp("2023-12-15 12:34:56")
    expected = datetime(2023, 12, 15, 12, 34, 56)
    assert time_utils.to_pydatetime(dt) == expected


def test_cftime_to_pydatetime():
    dt = cftime.DatetimeGregorian(2023, 12, 15, 12, 0, 0)
    expected = datetime(2023, 12, 15, 12, 0, 0)
    assert time_utils.to_pydatetime(dt) == expected
