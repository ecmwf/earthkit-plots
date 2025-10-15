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

import logging
from string import Formatter
from zoneinfo import ZoneInfo

import dateutil
import numpy as np

from earthkit.plots import metadata
from earthkit.plots.schemas import schema
from earthkit.plots.utils import iter_utils, string_utils

logger = logging.getLogger(__name__)


def parse_time(time):
    return [dateutil.parser.parse(str(t)) for t in time]


SPECIAL_METHODS = {
    "parse_time": parse_time,
}


class BaseFormatter(Formatter):
    """
    Base formatter class for earthkit-plots metadata.

    This class provides basic formatting capabilities for metadata values,
    including support for coordinate formatting with degree symbols and directions.

    Format Specifiers:
    - %Lt: Format as latitude with degree symbol and N/S direction
           Example: 45.0 -> "45.00°N", -30.5 -> "30.50°S"
    - %Lt.1f: Format as latitude with custom precision (1 decimal place)
           Example: 45.0 -> "45.0°N", -30.5 -> "30.5°S"
    - %Ln: Format as longitude with degree symbol and E/W direction
           Example: 15.2 -> "15.20°E", -45.8 -> "45.80°W"
    - %Ln.1f: Format as longitude with custom precision (1 decimal place)
           Example: 15.2 -> "15.2°E", -45.8 -> "45.8°W"
    - %c: Format location as city name only
           Example: LocationInfo(city="London", country="United Kingdom") -> "London"
    - %C: Format location as country name only
           Example: LocationInfo(city="London", country="United Kingdom") -> "United Kingdom"
    - __units__: Format units using the metadata.units module
    """

    #: Attributes of subplots which can be extracted by format strings
    SUBPLOT_ATTRIBUTES = {
        "domain": "domain_name",
        "crs": "crs_name",
    }

    #: Attributes of styles which can be extracted by format strings
    STYLE_ATTRIBUTES = {
        "units": "units",
    }

    def convert_field(self, value, conversion):
        """
        Convert a field value according to the conversion type.

        Parameters
        ----------
        value : object
            The value to be converted.
        conversion : str
            The conversion type.
        """
        if conversion == "u":
            return str(value).upper()
        elif conversion == "l":
            return str(value).lower()
        elif conversion == "c":
            return str(value).capitalize()
        elif conversion == "t":
            return str(value).title()
        return super().convert_field(value, conversion)

    def format_keys(self, format_string, kwargs):
        """
        Format keys in a format string.

        Parameters
        ----------
        format_string : str
            The format string.
        kwargs : dict
            The keyword arguments to be formatted.
        """
        keys = (i[1] for i in self.parse(format_string) if i[1] is not None)
        for key in keys:
            main_key, *methods = key.split(".")
            result = self.format_key(main_key)
            for method in methods:
                if method in SPECIAL_METHODS:
                    result = SPECIAL_METHODS[method](result)
                else:
                    result = getattr(np, method)(result)
                if not isinstance(result, (list, tuple, np.ndarray)):
                    result = [result]
            kwargs[key] = result
        return kwargs

    def format_key(self, key):
        return key

    def format(self, format_string, /, *args, **kwargs):
        kwargs = self.format_keys(format_string, kwargs)
        keys = list(kwargs)
        for key in keys:
            if "." in key:
                replacement_key = key.replace(".", "_")
                kwargs[replacement_key] = kwargs.pop(key)
                format_string = format_string.replace(key, replacement_key)
        return super().format(format_string, *args, **kwargs)

    def format_field(self, value, format_spec):
        """
        Format a field value according to the format specification.

        Parameters
        ----------
        value : object
            The value to be formatted.
        format_spec : str
            The format specification.
        """
        if isinstance(value, str) and value.startswith("__units__"):
            return metadata.units.format_units(
                value.replace("__units__", ""), format_spec
            )

        # Handle coordinate format specifiers
        if format_spec.startswith("%Lt"):
            # Format as latitude with degree symbol and N/S direction
            precision = self._extract_precision(format_spec, default=2)
            return self._format_latitude(value, precision)
        elif format_spec.startswith("%Ln"):
            # Format as longitude with degree symbol and E/W direction
            precision = self._extract_precision(format_spec, default=2)
            return self._format_longitude(value, precision)
        elif format_spec == "%c":
            # Format location as city
            return self._format_location_city(value)
        elif format_spec == "%C":
            # Format location as country
            return self._format_location_country(value)

        return super().format_field(value, format_spec)

    def _extract_precision(self, format_spec, default=2):
        """Extract precision from format specification like %Lt.1f or %Ln.3f."""
        import re

        # Match patterns like %Lt.1f, %Ln.3f, etc.
        match = re.match(r"%L[tn]\.(\d+)f?", format_spec)
        if match:
            return int(match.group(1))
        return default

    def _format_latitude(self, value, precision=2):
        """Format a latitude value with degree symbol and N/S direction."""
        try:
            lat = float(value)
            direction = "N" if lat >= 0 else "S" if lat < 0 else ""
            abs_lat = abs(lat)
            return f"{abs_lat:.{precision}f}°{direction}"
        except (ValueError, TypeError):
            return str(value)

    def _format_longitude(self, value, precision=2):
        """Format a longitude value with degree symbol and E/W direction."""
        try:
            lon = float(value)
            direction = "E" if lon >= 0 else "W"
            abs_lon = abs(lon)
            return f"{abs_lon:.{precision}f}°{direction}"
        except (ValueError, TypeError):
            return str(value)

    def _format_location_city(self, value):
        """Format a location value to show only the city."""
        # Import here to avoid circular imports
        from earthkit.plots.metadata.labels import LocationInfo

        if isinstance(value, LocationInfo):
            return value.city or str(value)
        else:
            return str(value)

    def _format_location_country(self, value):
        """Format a location value to show only the country."""
        # Import here to avoid circular imports
        from earthkit.plots.metadata.labels import LocationInfo

        if isinstance(value, LocationInfo):
            return value.country or str(value)
        else:
            return str(value)


class SourceFormatter(BaseFormatter):
    """
    Formatter of earthkit-plots `Layers`, enabling convient titles and labels.
    """

    def __init__(self, source, axis=None):
        self.source = source
        self._axis = axis

    def format_key(self, key):
        return [metadata.labels.extract(self.source, key, axis=self._axis)[0]]


class LayerFormatter(BaseFormatter):
    """
    Formatter of earthkit-plots `Layers`, enabling convient titles and labels.
    """

    def __init__(self, layer, default=None, issue_warnings=True, axis=None):
        self.layer = layer
        self._default = default
        self._issue_warnings = issue_warnings
        self._axis = axis

    def format_key(self, key):
        if key in self.SUBPLOT_ATTRIBUTES:
            value = getattr(self.layer.subplot, self.SUBPLOT_ATTRIBUTES[key])
        elif key in self.STYLE_ATTRIBUTES and self.layer.style is not None:
            value = getattr(self.layer.style, self.STYLE_ATTRIBUTES[key])
            if value is None:
                value = [
                    metadata.labels.extract(
                        source,
                        key,
                        default=self._default,
                        issue_warnings=self._issue_warnings,
                        axis=self._axis,
                    )
                    for source in self.layer.sources
                ]
            if key == "units":
                # Check if we have axis-specific units defined
                axis_specific_units = None
                if (
                    hasattr(self.layer, "axis_units")
                    and self.layer.axis_units
                    and self._axis in self.layer.axis_units
                ):
                    axis_specific_units = self.layer.axis_units[self._axis]

                # Use axis-specific units if available
                if axis_specific_units is not None:
                    value = [f"__units__{axis_specific_units}"]
                else:
                    # For legend formatting (when axis is None) or primary axis, prioritize style units
                    is_primary_axis = (
                        hasattr(self.layer, "primary_axis")
                        and self.layer.primary_axis == self._axis
                    )
                    is_legend_formatting = self._axis is None

                    if (is_primary_axis or is_legend_formatting) and value is not None:
                        # This is the primary data axis or legend formatting - use style units
                        if isinstance(value, list):
                            value = [
                                f"__units__{v}" if v is not None else "" for v in value
                            ]
                        else:
                            value = [f"__units__{value}" if value is not None else ""]
                    else:
                        # This is a coordinate axis or no style units available - use source units
                        value = [
                            metadata.labels.extract(
                                source,
                                key,
                                default=self._default,
                                issue_warnings=self._issue_warnings,
                                axis=self._axis,
                            )
                            for source in self.layer.sources
                        ]
        else:
            value = [
                metadata.labels.extract(
                    source,
                    key,
                    default=self._default,
                    issue_warnings=self._issue_warnings,
                    axis=self._axis,
                )
                for source in self.layer.sources
            ]
        if isinstance(value, list):
            if len(value) == 1 or iter_utils.all_equal(value):
                value = value[0]
            else:
                value = string_utils.list_to_human(value)
        return value

    def format_field(self, _value, format_spec):
        value = str(_value)
        return super().format_field(value, format_spec)


class SubplotFormatter(BaseFormatter):
    """
    Formatter of earthkit-plots `Subplots`, enabling convient titles and labels.
    """

    def __init__(self, subplot, unique=True, axis=None):
        self.subplot = subplot
        self.unique = unique
        self._layer_index = None
        self._axis = axis

    def convert_field(self, value, conversion):
        f = super().convert_field
        if isinstance(value, list):
            if isinstance(conversion, str) and conversion.isnumeric():
                try:
                    return str(value[int(conversion)])
                except IndexError as err:
                    error_message = (
                        f"Layer index {conversion} in title is out of range. "
                        f"This subplot contains {len(value)} layer{'s' if len(value) != 1 else ''}."
                    )
                    raise IndexError(error_message) from err
            return [f(v, conversion) for v in value]
        else:
            return f(value, conversion)

    def format_key(self, key):
        if key in self.SUBPLOT_ATTRIBUTES:
            values = [getattr(self.subplot, self.SUBPLOT_ATTRIBUTES[key])]
        else:
            values = [
                LayerFormatter(layer, axis=self._axis).format_key(key)
                for layer in self.subplot.layers
            ]
        return values

    def format_field(self, value, format_spec):
        f = super().format_field
        if isinstance(value, list):
            values = [f(v, format_spec) for v in value]
            if self._layer_index is not None:
                value = values[self._layer_index]
                self._layer_index = None
            else:
                if self.unique:
                    values = list(dict.fromkeys(values))
                value = string_utils.list_to_human(values)
        return value


class FigureFormatter(BaseFormatter):
    """
    Formatter of earthkit-plots `Charts`, enabling convient titles and labels.
    """

    def __init__(self, subplots, unique=True):
        self.subplots = subplots
        self.unique = unique
        self._layer_index = None

    def convert_field(self, value, conversion):
        f = super().convert_field
        if isinstance(value, list):
            if isinstance(conversion, str) and conversion.isnumeric():
                return str(value[int(conversion)])
            return [f(v, conversion) for v in value]
        else:
            return f(value, conversion)

    def format_key(self, key):
        values = [
            SubplotFormatter(subplot).format_key(key) for subplot in self.subplots
        ]
        values = [item for sublist in values for item in sublist]
        return values

    def format_field(self, value, format_spec):
        f = super().format_field
        if isinstance(value, list):
            values = [f(v, format_spec) for v in value]
            if self._layer_index is not None:
                value = values[self._layer_index]
                self._layer_index = None
            else:
                if self.unique:
                    values = list(dict.fromkeys(values))
                value = string_utils.list_to_human(values)
        return value


class TimeFormatter:
    """
    Formatter of time data, enabling convient time labels.

    Parameters
    ----------
    times : list
        The times to be formatted.
    time_zone : str, optional
        The time zone to be used for the times.
    """

    def __init__(self, times, time_zone=None):
        if not isinstance(times, (list, tuple)):
            times = [times]
        for i, time in enumerate(times):
            if not isinstance(time, dict):
                times[i] = {"time": time}
        self.times = times
        time_zone = time_zone or schema.time_zone
        self._time_zone = time_zone if time_zone is None else ZoneInfo(time_zone)

    def _extract_time(method):
        def wrapper(self):
            attr = method.__name__
            times = [self._named_time(time, attr) for time in self.times]
            if len(np.array(times).shape) > 1 and np.array(times).shape[0] == 1:
                times = times[0]
            _, indices = np.unique(times, return_index=True)
            result = [times[i] for i in sorted(indices)]
            if self._time_zone is not None:
                if None in [t.tzinfo for t in result]:
                    logger.warning(
                        "Attempting time zone conversion, but some data has no "
                        "time zone metadata; assuming UTC"
                    )
                    result = [
                        t if t.tzinfo is not None else t.replace(tzinfo=ZoneInfo("UTC"))
                        for t in result
                    ]
                result = [t.astimezone(tz=self._time_zone) for t in result]
            return result

        return property(wrapper)

    @staticmethod
    def _named_time(time, attr):
        return time.get(attr, time.get("time"))

    @property
    def time(self):
        """The most basic representation of time."""
        return self.valid_time

    @property
    def utc_offset(self):
        """The offset in hours from UTC."""
        valid_times = self.valid_time
        if None in [vt.tzinfo for vt in valid_times]:
            logger.warning(
                "Some of the data is missing time zone metadata; assuming UTC"
            )
            valid_times = [
                t if t.tzinfo is not None else t.replace(tzinfo=ZoneInfo("UTC"))
                for t in valid_times
            ]
        offsets = [vt.utcoffset().seconds // 3600 for vt in valid_times]
        time_zones = [f"UTC{offset:+d}" for offset in offsets]
        return time_zones

    @_extract_time
    def base_time(self):
        """The base time of the data, i.e. the time of the forecast."""
        pass

    @_extract_time
    def valid_time(self):
        """The valid time of the data, i.e. the time the forecast is for."""
        pass

    @property
    def lead_time(self):
        """The lead time of the data, i.e. the time between the base and valid times."""
        lead_times = []
        for time in self.times:
            btime = self._named_time(time, "base_time")
            vtime = self._named_time(time, "valid_time")
            if btime is not None and vtime is not None:
                lead_time_hours = int((vtime - btime).total_seconds() / 3600)
                lead_times.append(lead_time_hours)
            else:
                lead_times.append(None)

        if len(lead_times) > 1:
            non_none_values = [x for x in lead_times if x is not None]

            if non_none_values:
                # Create result list preserving None values and unique non-None values
                result = []
                seen_values = set()
                for _, value in enumerate(lead_times):
                    if value is None:
                        result.append(None)
                    elif value not in seen_values:
                        result.append(value)
                        seen_values.add(value)
            else:
                # All values are None
                result = lead_times
        else:
            result = lead_times

        return result


def format_month(data):
    """
    Extract the month of the data time.

    Parameters
    ----------
    data : earthkit.maps.sources.Source
        The data source.
    """
    import calendar

    month = data.metadata("month", default=None)
    if month is not None:
        month = calendar.month_name[month]
    else:
        time = data.datetime()
        if "valid_time" in time:
            time = time["valid_time"]
        else:
            time = time["base_time"]
        month = f"{time:%B}"
    return month
