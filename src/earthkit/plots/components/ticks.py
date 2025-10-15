# Copyright 2024-, European Centre for Medium Range Weather Forecasts.
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

"""
Tick management utilities for earthkit-plots.

This module provides functionality for setting and formatting axis ticks,
including support for datetime axes with period mode for centered labels.
"""

import re
from calendar import month_abbr, month_name
from datetime import date

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from dateutil.relativedelta import relativedelta

from earthkit.plots.temporal.anchors import (
    AnchoredDayLocator,
    AnchoredMonthLocator,
    AnchoredYearLocator,
)

# Default datetime formats for different tick levels
DEFAULT_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]
ZERO_FORMATS = ["%Y", "%b", "%-d", "%H:%M", "%H:%M", "%S.%f"]

TIME_PREFIX_YEAR = "Y"  # Yearly frequency
TIME_PREFIX_WY = "WY"  # Water year frequency
TIME_PREFIX_QUARTER = "Q"  # Quarterly frequency
TIME_PREFIX_SEASON = "SEAS"  # Seasonal frequency
TIME_PREFIX_MONTH = "M"  # Monthly frequency
TIME_PREFIX_WEEK = "W"  # Weekly frequency
TIME_PREFIX_DAY = "D"  # Daily frequency
TIME_PREFIX_HOUR = "H"  # Hourly frequency
TIME_PREFIX_MINUTE = "m"  # Minutely frequency
TIME_PREFIX_SECOND = "S"  # Secondly frequency

TIME_PREFIXES = (
    TIME_PREFIX_YEAR,
    TIME_PREFIX_WY,
    TIME_PREFIX_QUARTER,
    TIME_PREFIX_SEASON,
    TIME_PREFIX_MONTH,
    TIME_PREFIX_WEEK,
    TIME_PREFIX_DAY,
    TIME_PREFIX_HOUR,
    TIME_PREFIX_MINUTE,
    TIME_PREFIX_SECOND,
)

SEASON_ANCHOR_MONTH = 12  # DJF anchor (Dec). Can be overridden via kwargs.
SEASON_NAME_HEMI = "north"  # or "south"
SEASON_MONTH_SEP = ", "  # used for %b / %B lists

_MONTH_INITIAL = ["", "J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


_SEASON_TOKEN_RE = re.compile(r"\{season(?::\s*(%[bBcCsSN]))?\}")

# D<step>[@YYYY-MM-DD][+offset...], offsets like +7h-30m etc.
_DAY_SPEC_RE = re.compile(
    r"""
    ^D(?P<step>\d+)?                           # D, D2, D10
    (?:@(?P<anchor>\d{4}-\d{2}-\d{2}))?        # @YYYY-MM-DD (optional)
    (?P<offset>(?:[+\-]\d+(?:\.\d+)?[Wdhms])*) # +2d+12h-30m etc. (optional)
    $""",
    re.VERBOSE | re.IGNORECASE,
)


def _parse_daily_with_anchor_and_offset(spec: str):
    """
    Returns (step:int, anchor_date:datetime.date|None, offset:relativedelta|None).
    """
    m = _DAY_SPEC_RE.match(spec)
    if not m:
        raise ValueError(f"Bad daily spec '{spec}'")

    step = int(m.group("step") or "1")
    anc = m.group("anchor")
    off = m.group("offset") or ""

    anchor_date = None
    if anc:
        try:
            y, mo, d = map(int, anc.split("-"))
            anchor_date = date(y, mo, d)
        except Exception:
            raise ValueError(f"Bad daily anchor '{anc}' in '{spec}'. Use YYYY-MM-DD.")

    # Parse +... tokens → relativedelta
    rd = relativedelta()
    if off:
        token_re = re.compile(r"([+\-]\d+(?:\.\d+)?)([Wdhms])")
        for num, unit in token_re.findall(off):
            val = float(num)
            sign = 1 if val >= 0 else -1
            mag = abs(val)
            # weeks/d/h/m/s – allow fractional for sub-day precision
            if unit == "W":
                rd += relativedelta(weeks=sign * mag)
            elif unit == "d":
                rd += relativedelta(days=sign * mag)
            elif unit == "h":
                rd += relativedelta(hours=sign * mag)
            elif unit == "m":
                rd += relativedelta(minutes=sign * mag)
            elif unit == "s":
                rd += relativedelta(seconds=sign * mag)

    if rd == relativedelta():
        rd = None
    return step, anchor_date, rd


def _enable_minor_grid(ax, axis: str, alpha_scale: float = 0.5):
    """
    Turn on the minor grid using the same color/linestyle/linewidth as the
    major grid, but with alpha reduced by `alpha_scale` (default 50%).
    """
    # Pick the axis and current grid line artists (if any are already drawn)
    if axis == "x":
        major_lines = ax.get_xgridlines()
    else:
        major_lines = ax.get_ygridlines()

    # Defaults from rcParams
    color = mpl.rcParams.get("grid.color", "0.8")
    ls = mpl.rcParams.get("grid.linestyle", "-")
    lw = mpl.rcParams.get("grid.linewidth", 0.8)
    a = mpl.rcParams.get("grid.alpha", 1.0)

    # If major gridlines exist and were styled explicitly, copy from one
    for ln in major_lines:
        if ln.get_visible():
            color = ln.get_color() or color
            ls = ln.get_linestyle() or ls
            lw = ln.get_linewidth() or lw
            a = ln.get_alpha() if ln.get_alpha() is not None else a
            break

    minor_alpha = (a or 1.0) * alpha_scale

    # Enable minor grid with copied style but reduced alpha
    ax.grid(
        True,
        which="minor",
        axis=axis,
        color=color,
        linestyle=ls,
        linewidth=lw,
        alpha=minor_alpha,
    )


def _season_triad_months(dt, anchor_month=SEASON_ANCHOR_MONTH):
    """Return the 3 month numbers [m1, m2, m3] of the season containing dt,
    with seasons starting at anchor, anchor+3, anchor+6, anchor+9."""
    m = dt.month
    offset = (m - anchor_month) % 12
    start_month = ((anchor_month - 1) + 3 * (offset // 3)) % 12 + 1
    return [((start_month - 1 + i) % 12) + 1 for i in range(3)]


def _season_code(months):
    return "".join(_MONTH_INITIAL[m] for m in months)


def _season_name(dt, hemi=SEASON_NAME_HEMI):
    """Season names are tied to standard met seasons: DJF, MAM, JJA, SON."""
    # Use the fixed Dec/Mar/Jun/Sep anchor for naming
    start = _season_triad_months(dt, anchor_month=12)[0]
    index = {12: 0, 3: 1, 6: 2, 9: 3}[start]
    north = ["Winter", "Spring", "Summer", "Autumn"]
    south = ["Summer", "Autumn", "Winter", "Spring"]
    return (north if hemi == "north" else south)[index]


def _expand_season_placeholders(
    dt,
    fmt,
    *,
    code_anchor=SEASON_ANCHOR_MONTH,
    hemi=SEASON_NAME_HEMI,
    sep=SEASON_MONTH_SEP,
):
    """Replace {season} or {season:%x} with the correct string for dt, then return new fmt."""
    months = _season_triad_months(dt, anchor_month=code_anchor)

    def repl(match):
        spec = match.group(1)
        if spec is None:
            # No format specifier provided, default to %c (season code)
            return _season_code(months)
        if spec == "%b":
            return sep.join(month_abbr[m] for m in months)
        if spec == "%B":
            return sep.join(month_name[m] for m in months)
        if spec == "%c":
            return _season_code(months)
        if spec == "%s":
            return _season_name(dt, hemi=hemi)
        if spec == "%N":
            return _season_name(dt, hemi="north")
        if spec == "%S":
            return _season_name(dt, hemi="south")
        return match.group(0)  # shouldn't happen

    return _SEASON_TOKEN_RE.sub(repl, fmt)


class SeasonStrftimeFormatter(ticker.Formatter):
    def __init__(
        self,
        fmt,
        *,
        season_anchor=SEASON_ANCHOR_MONTH,
        season_hemi=SEASON_NAME_HEMI,
        season_sep=SEASON_MONTH_SEP,
        tz=None,
    ):
        self.fmt = fmt
        self.season_anchor = season_anchor
        self.season_hemi = season_hemi
        self.season_sep = season_sep
        self.tz = tz

    def __call__(self, x, pos=None):
        dt = mdates.num2date(x, tz=self.tz)
        # Expand {season:%x}, then run the rest through strftime for %Y etc.
        expanded = _expand_season_placeholders(
            dt,
            self.fmt,
            code_anchor=self.season_anchor,
            hemi=self.season_hemi,
            sep=self.season_sep,
        )
        return dt.strftime(expanded)


def set_ticks(
    ax,
    axis,
    frequency=None,
    minor_frequency=None,
    format=None,
    minor_format=None,
    period=False,
    labels="major",
    **kwargs,
):
    """
    Set axis tick locations and formatting for either x or y axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The matplotlib axes to configure.
    axis : str
        Which axis to configure: "x" or "y".
    frequency : str, optional
        Major tick frequency. For time axes: "Y", "M6", "D7", "H".
        For numeric axes: numeric string like "5" for every 5 units.
        Default is None (auto).
    minor_frequency : str, optional
        Minor tick frequency. If None, uses frequency.
        Default is None.
    format : str, optional
        Format string for major tick labels.
        Default is None (auto).
    minor_format : str, optional
        Format string for minor tick labels. If None and format is specified, uses format.
        Default is None.
    period : bool, optional
        If True, centers labels between ticks for better visual balance.
        Only applicable for time axes.
        Default is False.
    labels : str, optional
        Which tick labels to show: "major", "minor", "both", or None.
        Default is "major".
    **kwargs
        Additional keyword arguments to pass to the tick locators.
    """
    if axis not in ["x", "y"]:
        raise ValueError("axis must be 'x' or 'y'")

    # Get the appropriate axis object
    axis_obj = ax.xaxis if axis == "x" else ax.yaxis

    # Check if this is a time axis by looking at the data type
    is_time_axis = False
    if axis == "x":
        # Check if x-axis has datetime data
        try:
            if hasattr(ax, "get_xdata") and len(ax.get_xdata()) > 0:
                ax.get_xdata()  # Check if data exists
            # Simple heuristic: if frequency looks like time format, treat as time
            if frequency and any(
                frequency.upper().startswith(p) for p in TIME_PREFIXES
            ):
                is_time_axis = True
        except (AttributeError, TypeError, ValueError):
            pass
    else:  # y-axis
        # Check if y-axis has datetime data
        try:
            ax.get_ylim()
            if hasattr(ax, "get_ydata") and len(ax.get_ydata()) > 0:
                ax.get_ydata()
            # Simple heuristic: if frequency looks like time format, treat as time
            if frequency and any(
                frequency.upper().startswith(p) for p in TIME_PREFIXES
            ):
                is_time_axis = True
        except (AttributeError, TypeError, ValueError):
            pass

    if is_time_axis:
        # Handle time axis
        _set_time_ticks(
            ax,
            axis_obj,
            frequency,
            minor_frequency,
            format,
            minor_format,
            period,
            labels,
            **kwargs,
        )
    else:
        # Handle numeric axis
        _set_numeric_ticks(
            ax,
            axis_obj,
            frequency,
            minor_frequency,
            format,
            minor_format,
            labels,
            **kwargs,
        )


def _set_time_ticks(
    ax,
    axis_obj,
    frequency,
    minor_frequency,
    format,
    minor_format,
    period,
    labels,
    **kwargs,
):
    """Helper function to set time-based ticks."""

    season_anchor = kwargs.pop("season_anchor", SEASON_ANCHOR_MONTH)
    season_hemi = kwargs.pop("season_hemi", SEASON_NAME_HEMI)
    season_sep = kwargs.pop("season_sep", SEASON_MONTH_SEP)

    # Set major ticks
    if frequency is None:
        # Default to auto locator
        locator = mdates.AutoDateLocator(maxticks=30)
    else:
        locator = _get_time_locator(frequency)

    # Set major tick format
    if format:
        major_formats = [format] * 6
    else:
        major_formats = DEFAULT_FORMATS

    # Handle period behavior (centered labels)
    if period:
        axis_obj.set_major_locator(locator)
        axis_obj.set_major_formatter(ticker.NullFormatter())

        minor_locator = _get_period_minor_locator(frequency)

        if format and _SEASON_TOKEN_RE.search(format):
            axis_obj.set_minor_locator(minor_locator)
            axis_obj.set_minor_formatter(
                SeasonStrftimeFormatter(
                    format,
                    season_anchor=season_anchor,
                    season_hemi=season_hemi,
                    season_sep=season_sep,
                )
            )
        else:
            minor_formatter = mdates.ConciseDateFormatter(
                minor_locator,
                formats=[format] * 6 if format else DEFAULT_FORMATS,
                zero_formats=ZERO_FORMATS,
                show_offset=False,
            )
            axis_obj.set_minor_locator(minor_locator)
            axis_obj.set_minor_formatter(minor_formatter)
        labels = "minor"

    else:
        if labels in ["major", "both"]:
            if format and _SEASON_TOKEN_RE.search(format):
                # NEW: use our season-aware formatter
                axis_obj.set_major_locator(locator)
                axis_obj.set_major_formatter(
                    SeasonStrftimeFormatter(
                        format,
                        season_anchor=season_anchor,
                        season_hemi=season_hemi,
                        season_sep=season_sep,
                    )
                )
            else:
                formatter = mdates.ConciseDateFormatter(
                    locator,
                    formats=[format] * 6 if format else DEFAULT_FORMATS,
                    zero_formats=ZERO_FORMATS,
                    show_offset=False,
                )
                axis_obj.set_major_locator(locator)
                axis_obj.set_major_formatter(formatter)
        else:
            axis_obj.set_major_locator(locator)
            axis_obj.set_major_formatter(ticker.NullFormatter())
    # Set minor ticks if specified
    if minor_frequency is not None:
        minor_locator = _get_time_locator(minor_frequency)
        _enable_minor_grid(
            ax, axis="x" if axis_obj is ax.xaxis else "y", alpha_scale=0.25
        )

        # Set minor tick format - use format if minor_format is None
        if minor_format is not None:
            minor_formats = [minor_format] * 6
        elif format is not None:
            minor_formats = [format] * 6
        else:
            minor_formats = major_formats

        # Only set minor ticks if not in period mode (to avoid conflicts)
        if not period:
            # Only set minor formatter if we want to show minor labels
            if labels in ["minor", "both"]:
                minor_formatter = mdates.ConciseDateFormatter(
                    minor_locator,
                    formats=minor_formats,
                    zero_formats=ZERO_FORMATS,
                    show_offset=False,
                )
                axis_obj.set_minor_locator(minor_locator)
                axis_obj.set_minor_formatter(minor_formatter)
            else:
                # Hide minor labels by setting null formatter
                axis_obj.set_minor_locator(minor_locator)
                axis_obj.set_minor_formatter(ticker.NullFormatter())


_YEAR_SPEC_RE = re.compile(
    r"""
    ^Y(?P<step>\d+)?                  # step: Y, Y2, Y10
    (?:@(?P<anchor>\d{4})             # @YYYY (required if @ present)
       (?:-(?P<mm>\d{2})              # optional -MM sugar (month-of-year)
          (?:-(?P<dd>\d{2}))?         # optional -DD (rare; becomes extra offset)
       )?
    )?
    (?P<offset>(?:[+\-]\d+(?:\.\d+)?[YMWdhms])*)$   # +5M-12h etc.
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _parse_yearly_with_anchor_and_offset(spec: str):
    """
    Returns (step:int, anchor_year:int|None, offset:relativedelta|None).
    - '-MM' sugar becomes months=(MM-1).
    - '-DD' sugar becomes days=(DD-1).
    """
    m = _YEAR_SPEC_RE.match(spec)
    if not m:
        raise ValueError(f"Bad yearly spec '{spec}'")

    step = int(m.group("step") or "1")
    anchor = m.group("anchor")
    mm = m.group("mm")
    dd = m.group("dd")
    off_str = m.group("offset") or ""

    # Base offset from -MM / -DD sugar (from Jan 1 boundary)
    base_rd = relativedelta()
    if mm:
        base_rd += relativedelta(months=int(mm) - 1)  # Jan→+0M, Jun→+5M
    if dd:
        base_rd += relativedelta(days=int(dd) - 1)  # Day-of-month (1-based)

    # Parse +... tokens
    token_re = re.compile(r"([+\-]\d+(?:\.\d+)?)([YMWdhms])")
    rd = base_rd
    for num, unit in token_re.findall(off_str):
        val = float(num)
        sign = 1 if val >= 0 else -1
        mag = abs(val)
        # relativedelta supports fractional hours/min/sec but not fractional months/years cleanly.
        # We’ll keep months/years integral by rounding; document this.
        if unit in "YM":
            mag = int(round(mag))
        delta = {
            "Y": relativedelta(years=sign * int(mag)),
            "M": relativedelta(months=sign * int(mag)),
            "W": relativedelta(weeks=sign * mag),
            "d": relativedelta(days=sign * mag),
            "h": relativedelta(hours=sign * mag),
            "m": relativedelta(minutes=sign * mag),
            "s": relativedelta(seconds=sign * mag),
        }[unit]
        rd += delta

    anchor_year = int(anchor) if anchor else None
    return step, anchor_year, (rd if (rd != relativedelta()) else None)


def _parse_month_anchor_token(token: str) -> int:
    """Accept 'Jan', 'January', '1', '01', case-insensitive. Also 'Sept'."""
    t = token.strip().lower()
    # Numeric 1..12
    if re.fullmatch(r"\d{1,2}", t):
        n = int(t)
        if 1 <= n <= 12:
            return n
        raise ValueError(f"Month out of range in anchor '{token}'")
    # Names
    names = {month_name[i].lower(): i for i in range(1, 13)}
    abbrs = {month_abbr[i].lower(): i for i in range(1, 13)}
    names.update(abbrs)
    names["sept"] = 9  # common alias
    if t in names:
        return names[t]
    raise ValueError(f"Unrecognised month anchor '{token}'. Try Jan/January/1/01.")


def _get_time_locator(frequency):
    f = frequency
    F = f.upper()

    if F.startswith("D"):
        step, adate, rd = _parse_daily_with_anchor_and_offset(f.strip())
        if adate is None and rd is None:
            return mdates.DayLocator(interval=step)
        else:
            return AnchoredDayLocator(base=step, anchor_date=adate, offset=rd)

    elif F.startswith("M"):
        s = f.strip()
        at = s.find("@")
        main = s if at == -1 else s[:at]
        anchor = None if at == -1 else s[at + 1 :].strip()

        interval = int(main[1:] or "1")

        if not anchor:
            return mdates.MonthLocator(interval=interval)
        else:
            anchor_month = _parse_month_anchor_token(anchor)
            return AnchoredMonthLocator(base=interval, anchor_month=anchor_month)

    elif F.startswith("Y"):
        step, anchor_year, rd = _parse_yearly_with_anchor_and_offset(f.strip())
        if anchor_year is None and rd is None:
            return mdates.YearLocator(base=step)
        else:
            return AnchoredYearLocator(
                base=step, anchor_year=anchor_year or 2000, offset=rd
            )

    elif F.startswith("W"):
        interval = int(f[1:] or "1")
        return mdates.WeekdayLocator(
            byweekday=mdates.MO, interval=interval
        )  # or expose start day

    elif F.startswith("H"):
        interval = int(f[1:] or "1")
        return mdates.HourLocator(interval=interval)

    elif f.startswith("m"):  # minutes (lower-case)
        interval = int(f[1:] or "1")
        return mdates.MinuteLocator(interval=interval)

    elif F.startswith("SEAS"):
        interval = int(f[4:] or "1")
        return mdates.MonthLocator(bymonth=[12, 3, 6, 9], interval=interval)

    elif F.startswith("S"):  # seconds
        interval = int(f[1:] or "1")
        return mdates.SecondLocator(interval=interval)

    else:
        return mdates.AutoDateLocator(maxticks=30)


def _get_period_minor_locator(frequency):
    """Get the appropriate minor locator for period mode (centered labels)."""
    f = frequency
    F = f.upper()

    if F.startswith("D"):
        interval = int(f[1:] or "1")
        return mdates.HourLocator(interval=1, byhour=12)

    elif F.startswith("M"):
        interval = int(f[1:] or "1")
        return mdates.MonthLocator(interval=interval, bymonthday=16)

    elif F.startswith("Y"):
        interval = int(f[1:] or "1")
        return mdates.YearLocator(base=interval, month=7, day=1)

    elif F.startswith("W"):
        interval = int(f[1:] or "1")
        return mdates.WeekdayLocator(
            byweekday=mdates.TH, interval=interval
        )  # or expose start day

    elif F.startswith("SEAS"):
        interval = int(f[4:] or "1")
        return mdates.MonthLocator(
            bymonth=[1, 4, 7, 10], interval=interval, bymonthday=16
        )

    elif F.startswith("S"):  # seconds
        interval = int(f[1:] or "1")
        return mdates.SecondLocator(interval=interval)
    else:
        # For other frequencies, use the same locator but with adjusted parameters
        # This will create minor ticks that are offset from major ticks
        return _get_time_locator(frequency)


def _set_numeric_ticks(
    ax, axis_obj, frequency, minor_frequency, format, minor_format, labels, **kwargs
):
    """Helper function to set numeric ticks."""
    # For numeric axis, we'll use numeric tickers
    if frequency is not None:
        # Parse frequency for numeric ticks (e.g., "5" for every 5 units)
        try:
            interval = float(frequency)
            major_locator = ticker.MultipleLocator(interval)
        except ValueError:
            # If not a number, fall back to auto locator
            major_locator = ticker.AutoLocator()
    else:
        major_locator = ticker.AutoLocator()

    # Set major ticks
    axis_obj.set_major_locator(major_locator)

    # Only set major tick format if we want to show major labels
    if labels in ["major", "both"] and format:
        axis_obj.set_major_formatter(ticker.FormatStrFormatter(format))
    elif labels not in ["major", "both"]:
        # Hide major labels by setting null formatter
        axis_obj.set_major_formatter(ticker.NullFormatter())

    # Set minor ticks if specified
    if minor_frequency is not None:
        try:
            interval = float(minor_frequency)
            minor_locator = ticker.MultipleLocator(interval)
        except ValueError:
            # Default to auto minor locator
            minor_locator = ticker.AutoMinorLocator()

        axis_obj.set_minor_locator(minor_locator)
        _enable_minor_grid(
            ax, axis="x" if axis_obj is ax.xaxis else "y", alpha_scale=0.25
        )

        # Only set minor tick format if we want to show minor labels
        if labels in ["minor", "both"]:
            # Set minor tick format - use format if minor_format is None
            if minor_format is not None:
                minor_format_str = minor_format
            elif format is not None:
                minor_format_str = format
            else:
                minor_format_str = None

            if minor_format_str:
                axis_obj.set_minor_formatter(
                    ticker.FormatStrFormatter(minor_format_str)
                )
        else:
            # Hide minor labels by setting null formatter
            axis_obj.set_minor_formatter(ticker.NullFormatter())


def set_xticks(
    ax,
    frequency=None,
    minor_frequency=None,
    format=None,
    minor_format=None,
    period=False,
    labels="major",
    **kwargs,
):
    """
    Set x-axis tick locations and formatting.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The matplotlib axes to configure.
    frequency : str, optional
        Major tick frequency (e.g., "Y", "M6", "D7", "H" for time, "5" for numeric).
        Default is None (auto).
    minor_frequency : str, optional
        Minor tick frequency. If None, uses frequency.
        Default is None.
    format : str, optional
        Format string for major tick labels.
        Default is None (auto).
    minor_format : str, optional
        Format string for minor tick labels. If None and format is specified, uses format.
        Default is None.
    period : bool, optional
        If True, centers labels between ticks for better visual balance.
        Only applicable for time axes.
        Default is False.
    labels : str, optional
        Which tick labels to show: "major", "minor", "both", or None.
        Default is "major".
    **kwargs
        Additional keyword arguments to pass to the tick locators.
    """
    set_ticks(
        ax,
        "x",
        frequency,
        minor_frequency,
        format,
        minor_format,
        period,
        labels,
        **kwargs,
    )


def set_yticks(
    ax,
    frequency=None,
    minor_frequency=None,
    format=None,
    minor_format=None,
    labels="major",
    **kwargs,
):
    """
    Set y-axis tick locations and formatting.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The matplotlib axes to configure.
    frequency : str, optional
        Major tick frequency (e.g., "Y", "M6", "D7", "H" for time, "5" for numeric).
        Default is None (auto).
    minor_frequency : str, optional
        Minor tick frequency. If None, uses frequency.
        Default is None.
    format : str, optional
        Format string for major tick labels.
        Default is None (auto).
    minor_format : str, optional
        Format string for minor tick labels. If None and format is specified, uses format.
        Default is None.
    labels : str, optional
        Which tick labels to show: "major", "minor", "both", or None.
        Default is "major".
    **kwargs
        Additional keyword arguments to pass to the tick locators.
    """
    set_ticks(
        ax,
        "y",
        frequency,
        minor_frequency,
        format,
        minor_format,
        labels=labels,
        **kwargs,
    )
