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

from datetime import datetime, timedelta
import warnings

from dateutil.relativedelta import relativedelta

from ..schema import schema


SEASON_INITIALS = "JFMAMJJASOND"


DUMMY_YEAR = 2


MONTH_MIDPOINTS = {
    1: {"day": 16, "hour": 12},   # January
    2: {"day": 14, "hour": 0},    # February
    3: {"day": 16, "hour": 12},   # March
    4: {"day": 16, "hour": 0},    # April
    5: {"day": 16, "hour": 12},   # May
    6: {"day": 16, "hour": 0},    # June
    7: {"day": 16, "hour": 0},    # July
    8: {"day": 16, "hour": 12},   # August
    9: {"day": 16, "hour": 0},    # September
    10: {"day": 16, "hour": 12},  # October
    11: {"day": 16, "hour": 0},   # November
    12: {"day": 16, "hour": 12},  # December
}


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def str_to_datetime(string, format=DATETIME_FORMAT):
    return datetime.strptime(string, format)


def datetime_to_str(dt, format=DATETIME_FORMAT):
    return dt.strftime(format)


def season_to_datetime(season, year=DUMMY_YEAR):
    superstring = SEASON_INITIALS*2
    if season not in superstring:
        raise ValueError(f"invalid season '{season}'")
    
    month = (superstring.index(season)+len(season)//2)%12+1
    kwargs = {"day": 1, "hour": 0}
    if len(season)%2:
        kwargs = MONTH_MIDPOINTS[month]

    return datetime(year, month, **kwargs)


def update_layout(self, axis):
    calendar_layout = {
        f"{axis}axis": {
            "showgrid": True,
            "gridwidth": 1,
            "gridcolor": "#EEEEEE",
            "fixedrange": True,
            "ticklabelmode": "period",
            "tickformat": "%B",
            "dtick": "M1",
            "range": ["0002-01-01 00:00:00", "0003-01-01 00:00:00"],
            "title": "",
        },
        "hoverdistance": -1,
    }
    self.update_layout(**calendar_layout)


def dayofyear(array, cyclic=False):
    array = [
        datetime(DUMMY_YEAR, 1, 1) + timedelta(days=int(day)) for day in array
    ]
    if cyclic:
        if len(array) in (365, 366):
            offset = timedelta(days=1)
            array = [array[0]-offset] + array + [array[-1]+offset]
        else:
            warnings.warn(
                f"cyclic dayofyear axis must have length 365 or 366 but got "
                f"{len(array)}; plotting raw data without cyclic extensions"
            )
    return array


def weekofyear(array, cyclic=False):
    array = [
        datetime(2, 1, 1)+timedelta(days=int(week)*7-3.5) for week in array
    ]
    if cyclic:
        if len(array) in (52, 53):
            offset = timedelta(days=7)
            array = [array[0]-offset] + array + [array[-1]+offset]
        else:
            warnings.warn(
                f"cyclic weekofyear axis must have length 52 or 53 but got "
                f"{len(array)}; plotting raw data without cyclic extensions"
            )
    return array


def month(array, cyclic=False):
    array = [
        datetime(DUMMY_YEAR, month, **MONTH_MIDPOINTS[month]) for month in array
    ]
    if cyclic:
        if len(array)==12:
            offset = timedelta(days=31)
            array = [array[0]-offset] + array + [array[-1]+offset]
        else:
            warnings.warn(
                f"cyclic month axis must have length 12 but got "
                f"{len(array)}; plotting raw data without cyclic extensions"
            )
    return array


def season(array, cyclic=False):
    array = [season_to_datetime(season) for season in array]
    if cyclic:
        if len(array) == 4:
            offset = relativedelta(months=3)
            array = [array[0]-offset] + array + [array[-1]+offset]
        else:
            warnings.warn(
                f"cyclic season axis must have length 4 but got "
                f"{len(array)}; plotting raw data without cyclic extensions"
            )
    return array


def default_axis(key, kwargs):
    if key not in DEFAULT_AXES:
        raise ValueError(f"unable to generate axis type calendar.{key}")
    return DEFAULT_AXES[key]


def format_hovertemplate(hovertemplate):
    if "%Y" in hovertemplate:
        warnings.warn(
            "attempting %Y date format over calendar axis, where there is no "
            "'year' value to parse; the %Y in your format string has been "
            "replaced with '????'"
        )
    return hovertemplate.replace("%Y", "????")


HOVERTEMPLATES =  {
    "month": {
        "extra": "%{{{axis}|%B}}",
    },
    "dayofyear": {
        "extra": "%{{{axis}|%-d %B}}",
    },
    "weekofyear": {
        "customdata": lambda dates: [date-timedelta(days=3.5) for date in dates],
        "extra": "w/c %{customdata|%-d %B}",
    },
    "season": {
        "customdata": lambda *args, **kwargs: [
            "Autumn (SON)",
            "Winter (DJF)",
            "Spring (MAM)",
            "Summer (JJA)",
            "Autumn (SON)",
            "Winter (DJF)",
        ],
        "extra": "%{customdata}",
    },
}


def update_hovertemplate(name, axis, kwargs):
    hovertemplate = kwargs.get("hovertemplate")
    if hovertemplate is None:
        hovertemplate = schema.calendar.hovertemplate
    
    if "{axis}" in hovertemplate:
        hovertemplate = hovertemplate.format(axis={"x": "y", "y": "x"}[axis])

    if "<extra>" not in hovertemplate:
        template = HOVERTEMPLATES[name]

        extra = template.get("extra", "")
        if "{axis}" in extra:
            extra = extra.format(axis=axis)
        kwargs["hovertemplate"] = f"{hovertemplate}<extra>{extra}</extra>"

        customdata = template.get("customdata")
        if customdata is not None:
            kwargs["customdata"] = customdata(kwargs[axis])
    return kwargs

    


DEFAULT_AXES = {
    "dayofyear": list(range(1, 367)),
    "weekofyear": list(range(1, 54)),
    "month": list(range(1, 13)),
    "season": list(range(1, 5)),
}


TRANSFORMERS = {
    "dayofyear": dayofyear,
    "weekofyear": weekofyear,
    "month": month,
    "season": season,
}


def calendar(self, name, axis, kwargs):
    if name not in TRANSFORMERS:
        raise ValueError(
            f"invalid axis transformer 'calendar.{name}'; must be one of "
            f"{list(TRANSFORMERS)}"
        )
    transformer = TRANSFORMERS[name]
    candidate = kwargs.get(axis)
    cyclic = kwargs.get("cyclic", False)
    if isinstance(candidate, str):
        candidate = default_axis(name, kwargs)
    kwargs[axis] = transformer(candidate, cyclic=cyclic)

    kwargs = update_hovertemplate(name, axis, kwargs)
    update_layout(self, axis)

    return kwargs