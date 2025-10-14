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

import math
from datetime import date, datetime, timedelta

import matplotlib.dates as mdates


class AnchoredYearLocator(mdates.DateLocator):
    """
    Yearly ticks every `base` years, aligned so that `anchor_year` is included.
    Ticks are placed at Jan 1 00:00 plus an optional relativedelta `offset`.
    """

    def __init__(self, base=1, anchor_year=2000, offset=None, tz=None):
        super().__init__()
        if base < 1:
            raise ValueError("base must be >= 1")
        self.base = int(base)
        self.anchor_year = int(anchor_year)
        self.offset = offset  # relativedelta or None
        self.tz = tz

    def tick_values(self, vmin, vmax):
        if vmax < vmin:
            vmin, vmax = vmax, vmin

        dt_min = mdates.num2date(vmin, tz=self.tz)
        dt_max = mdates.num2date(vmax, tz=self.tz)
        y_min, y_max = dt_min.year, dt_max.year

        # First aligned year >= y_min
        k0 = math.ceil((y_min - self.anchor_year) / self.base)
        y = self.anchor_year + k0 * self.base

        ticks = []
        while y <= y_max + 1:
            dt = datetime(y, 1, 1, tzinfo=self.tz)
            if self.offset:
                dt = dt + self.offset
            n = mdates.date2num(dt)
            if vmin <= n <= vmax:
                ticks.append(n)
            elif n > vmax:
                break
            y += self.base
        return ticks

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)


class AnchoredMonthLocator(mdates.DateLocator):
    """
    Monthly ticks every `base` months, aligned so that `anchor_month` is included.
    i.e. all datetimes whose month index i = year*12 + (month-1) satisfies
    (i - (anchor_month-1)) % base == 0.
    """

    def __init__(self, base=1, anchor_month=1, tz=None, offset=None):
        """
        Parameters
        ----------
        base : int           # step in months (>=1)
        anchor_month : int   # 1..12 (Jan=1)
        tz : tzinfo | None   # timezone for conversions (optional)
        offset : relativedelta | None
            Optional extra shift applied after placing at the 1st of the month.
            (Kept for parity with yearly; you can pass None now.)
        """
        super().__init__()
        if base < 1:
            raise ValueError("base must be >= 1")
        if not 1 <= int(anchor_month) <= 12:
            raise ValueError("anchor_month must be 1..12")
        self.base = int(base)
        self.anchor_month = int(anchor_month)
        self.tz = tz
        self.offset = offset  # optional (e.g., relativedelta(days=15))

    def tick_values(self, vmin, vmax):
        if vmax < vmin:
            vmin, vmax = vmax, vmin

        dt_min = mdates.num2date(vmin, tz=self.tz)

        # Month indices from "epoch": i = year*12 + (month-1)
        i_min = dt_min.year * 12 + (dt_min.month - 1)
        i_anchor = self.anchor_month - 1

        # First aligned index >= i_min
        k0 = math.ceil((i_min - i_anchor) / self.base)
        i = i_anchor + k0 * self.base

        ticks = []
        while True:
            y = i // 12
            m = (i % 12) + 1
            dt = datetime(y, m, 1, tzinfo=self.tz)
            if self.offset:
                dt = dt + self.offset
            n = mdates.date2num(dt)
            if n > vmax:
                break
            if n >= vmin:
                ticks.append(n)
            i += self.base
        return ticks

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)


class AnchoredDayLocator(mdates.DateLocator):
    """
    Daily ticks every `base` days, aligned so that `anchor_date` is included.
    Ticks are placed at 00:00 of each selected day, plus optional `offset`
    (a dateutil.relativedelta).
    """

    def __init__(self, base=1, anchor_date=None, offset=None, tz=None):
        super().__init__()
        if base < 1:
            raise ValueError("base must be >= 1")
        self.base = int(base)
        # default anchor: 1970-01-01 if none provided
        self.anchor_date = anchor_date or date(1970, 1, 1)
        self.offset = offset  # relativedelta or None
        self.tz = tz

    def tick_values(self, vmin, vmax):
        if vmax < vmin:
            vmin, vmax = vmax, vmin

        dt_min = mdates.num2date(vmin, tz=self.tz)
        dt_max = mdates.num2date(vmax, tz=self.tz)

        dmin = dt_min.date()
        dmax = dt_max.date()

        # days since anchor
        delta_days = (dmin - self.anchor_date).days
        k0 = math.ceil(delta_days / self.base)
        cur = self.anchor_date + timedelta(days=k0 * self.base)

        ticks = []
        while cur <= dmax:
            dt = datetime(cur.year, cur.month, cur.day, tzinfo=self.tz)
            if self.offset:
                dt = dt + self.offset
            n = mdates.date2num(dt)
            if n >= vmin and n <= vmax:
                ticks.append(n)
            cur += timedelta(days=self.base)
        return ticks

    def __call__(self):
        # forward current view limits to tick_values
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)
