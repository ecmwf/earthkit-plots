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

import warnings

import numpy as np

from earthkit.plots.metadata.formatters import TimeFormatter, format_month


class LocationInfo:
    """Container for location information with formatting support."""

    def __init__(self, city=None, country=None, lat=None, lon=None):
        self.city = city
        self.country = country
        self.lat = lat
        self.lon = lon

    def __str__(self):
        """Default string representation - city name or coordinates."""
        if self.city:
            return self.city
        elif self.lat is not None and self.lon is not None:
            return f"{self.lat:.2f}°{'N' if self.lat >= 0 else 'S'}, {abs(self.lon):.2f}°{'E' if self.lon >= 0 else 'W'}"
        else:
            return "Unknown location"


def get_location(data):
    """
    Get the nearest city name using reverse geocoding with fallback logic.

    Tries to find the nearest city with decreasing population thresholds:
    1. min_population=10000, distance <= 0.1 degrees
    2. min_population=5000, distance <= 0.1 degrees
    3. no min_population, distance <= 0.1 degrees
    4. If still > 0.1 degrees away, return lat/lon coordinates

    Parameters
    ----------
    data : earthkit.plots.sources.Source
        The data source containing coordinate information.

    Returns
    -------
    LocationInfo
        Location information with city, country, and coordinates.
    """
    try:
        import reverse_geocode
    except ImportError:
        raise ImportError(
            "The reverse-geocode package is required to get the location."
        )

    # Extract coordinates from the data source
    # Try different ways to get lat/lon based on data source type
    lat, lon = None, None

    # Method 1: Try metadata access
    try:
        lat = data.metadata("latitude")
        lon = data.metadata("longitude")
    except (AttributeError, KeyError, ValueError, TypeError):
        pass

    # Method 2: Try coordinate values (take first/mean if arrays)
    if lat is None or lon is None:
        try:
            if hasattr(data, "y_values") and hasattr(data, "x_values"):
                y_vals = data.y_values
                x_vals = data.x_values
                if isinstance(y_vals, np.ndarray):
                    lat = (
                        float(np.mean(y_vals))
                        if y_vals.size > 1
                        else float(y_vals.flat[0])
                    )
                else:
                    lat = float(y_vals)
                if isinstance(x_vals, np.ndarray):
                    lon = (
                        float(np.mean(x_vals))
                        if x_vals.size > 1
                        else float(x_vals.flat[0])
                    )
                else:
                    lon = float(x_vals)
        except (AttributeError, ValueError, TypeError, IndexError):
            pass

    if lat is None or lon is None:
        return LocationInfo(lat=lat, lon=lon)

    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance in degrees between two points."""
        return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

    # Try with different population thresholds
    for min_pop in [10000, 5000, None]:
        try:
            if min_pop is not None:
                result = reverse_geocode.get((lat, lon), min_population=min_pop)
            else:
                result = reverse_geocode.get((lat, lon))

            if result:
                result_lat = float(result.get("lat", lat))
                result_lon = float(result.get("lon", lon))
                distance = calculate_distance(lat, lon, result_lat, result_lon)

                if distance <= 0.1:
                    return LocationInfo(
                        city=result.get("city", "Unknown city"),
                        country=result.get("country", "Unknown country"),
                        lat=lat,
                        lon=lon,
                    )
        except (ImportError, AttributeError, KeyError, ValueError, TypeError):
            continue

    # If no city found within 0.1 degrees, return coordinates
    return LocationInfo(lat=lat, lon=lon)


#: Default title for forecast plots.
DEFAULT_FORECAST_TITLE = (
    "{variable_name}\n"
    "Base time: {base_time:%H:%M} on {base_time:%Y-%m-%d}   "
    "Valid time: {valid_time:%H:%M} on {valid_time:%Y-%m-%d} (T+{lead_time})"
)

#: Default title for analysis plots.
DEFAULT_ANALYSIS_TITLE = (
    "{variable_name} at {valid_time:%H:%M} on {valid_time:%Y-%m-%d}"
)

#: Keys that are related to time.
TIME_KEYS = ["base_time", "valid_time", "lead_time", "time", "utc_offset"]

#: Magic keys that can be used to extract metadata.
MAGIC_KEYS = {
    "variable_name": {
        "preference": ["long_name", "standard_name", "name", "short_name"],
        "remove_underscores": True,
    },
    "short_name": {
        "preference": ["short_name", "name", "standard_name", "long_name"],
    },
    "location": {
        "function": get_location,
    },
    "ensemble_member": {
        "preference": [
            "ensemble_member",
            "realization",
            "number",
            "ensemble",
            "member",
        ],
    },
    "month": {
        "function": format_month,
    },
    "values": {
        "function": lambda data: data.values,
    },
}

#: Nice names for coordinate reference systems.
CRS_NAMES = {
    "PlateCarree": "Plate Carrée",
    "NorthPolarStereo": "North Polar Stereographic",
    "SouthPolarStereo": "South Polar Stereographic",
}


def default_label(data):
    """
    Get the default label type for a given data object (analysis or forecast).

    Parameters
    ----------
    data : earthkit.plots.sources.Source
        The data source to get the label for.
    """
    if data.metadata("type") == "an":
        format_string = DEFAULT_ANALYSIS_TITLE
    else:
        format_string = DEFAULT_FORECAST_TITLE
    return format_string


def extract(data, attr, default=None, issue_warnings=True, axis=None):
    """
    Extract an attribute from a data object.

    Parameters
    ----------
    data : earthkit.plots.sources.Source
        The data source to extract the label from.
    attr : str
        The attribute to extract.
    default : str, optional
        The default label to use if the attribute is not found.
    axis : str, optional
        The axis to extract the label from. If None, the label will be extracted
        from the general metadata of the data.
    """
    if attr in TIME_KEYS:
        handler = TimeFormatter(data.datetime())
        label = getattr(handler, attr)
        if len(label) == 1:
            label = label[0]

    else:
        if axis is not None:
            metadata = getattr(data, f"{axis}_metadata")

            def search(x, default):
                return metadata.get(x, default)

        elif hasattr(data, "metadata"):
            search = data.metadata
        else:
            data_key = [
                key
                for key in data.attrs["reduce_attrs"]
                if "reduce_dims" in data.attrs["reduce_attrs"][key]
            ][0]

            def search(x, default):
                return data.attrs["reduce_attrs"][data_key].get(x, default)

        candidates = [attr]
        remove_underscores = False
        if attr in MAGIC_KEYS:
            if "function" in MAGIC_KEYS[attr]:
                return MAGIC_KEYS[attr]["function"](data)
            else:
                candidates = MAGIC_KEYS[attr]["preference"] + candidates
                remove_underscores = MAGIC_KEYS[attr].get("remove_underscores", False)

        for item in candidates:
            label = search(item, default=None)
            if label is not None:
                break
        else:
            if issue_warnings:
                warnings.warn(f'No key "{attr}" found in layer metadata.')

        if remove_underscores:
            if isinstance(label, (list, tuple)):
                label = [
                    lab.replace("_", " ") if isinstance(lab, str) else lab
                    for lab in label
                ]
            elif isinstance(label, str):
                label = label.replace("_", " ")

    if label is None:
        label = default
    return label
