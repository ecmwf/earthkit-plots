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


def to_pydatetime(dt):
    """
    Convert an arbitrary datetime representation to a Python datetime object.

    Parameters
    ----------
    dt : datetime.datetime, numpy.datetime64, or pandas.Timestamp
        The datetime object to convert.

    Returns
    -------
    datetime.datetime
        The Python datetime object.
    """
    from datetime import datetime

    import pandas as pd

    if hasattr(dt, "isoformat"):
        # Handle non-numpy datetimes
        pydatetime = datetime.strptime(dt.isoformat(), "%Y-%m-%dT%H:%M:%S")
    else:
        # Handle numpy datetimes
        pydatetime = pd.to_datetime(dt).to_pydatetime()

    return pydatetime
