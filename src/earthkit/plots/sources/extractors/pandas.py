# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

"""
Extraction of coordinates and metadata from pandas DataFrames and Series.

The metadata lookup mirrors that of xarray objects:

=====================================  =====================================
xarray                                 pandas
=====================================  =====================================
attrs of the plotted variable          ``attrs`` of the plotted Series
scalar (0-d or size-1) coordinates     constant columns, e.g. the latitude
                                       and longitude of a station
variable name                          column name
Dataset attrs                          ``DataFrame.attrs``
=====================================  =====================================

pandas has no standard place for the units of a column. They are read from
``attrs["units"]``, which is either a string (the units of a Series) or a
mapping from column names to units (for the columns of a DataFrame)::

    df.attrs["units"] = {"airTemperature": "K", "pressure": "Pa"}
"""

import datetime
from typing import Any

import numpy as np

from earthkit.plots.sources.context import PlotContext
from earthkit.plots.sources.coordinates import CoordinateInfo, ExtractedCoordinates
from earthkit.plots.sources.extractors.numpy import NumpyExtractor

#: Names of columns holding the valid time, in order of preference.
VALID_TIME_COLUMNS = ("valid_time", "time", "data_datetime", "datetime", "date_time")

#: Names of columns holding the base (reference) time, in order of preference.
BASE_TIME_COLUMNS = ("forecast_reference_time", "base_time", "initial_time")

#: Names of columns holding the lead time, in order of preference.
LEAD_TIME_COLUMNS = ("step", "lead_time")


def is_pandas(data: Any) -> bool:
    """Whether ``data`` is a pandas DataFrame or Series (without importing pandas)."""
    module = type(data).__module__ or ""
    return module.startswith("pandas") and type(data).__name__ in ("DataFrame", "Series")


def _is_series(data: Any) -> bool:
    return is_pandas(data) and type(data).__name__ == "Series"


def _scalar(value):
    """Convert a numpy scalar to a Python scalar, keeping timestamps as pandas Timestamps."""
    if isinstance(value, np.datetime64):
        import pandas as pd

        return pd.Timestamp(value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def _parse_time(value):
    """Parse a timestamp, datetime64, datetime or string into a datetime, or ``None``."""
    if value is None:
        return None
    import pandas as pd

    try:
        timestamp = pd.Timestamp(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if pd.isna(timestamp):
        return None
    return timestamp.to_pydatetime()


def _units_from_attrs(attrs: dict, name) -> str | None:
    units = attrs.get("units")
    if isinstance(units, dict):
        return units.get(name)
    if isinstance(units, str):
        return units
    return None


class PandasExtractor(NumpyExtractor):
    """
    Strategy for extracting coordinates and metadata from pandas objects.

    Coordinates may be given as column names (``x="time", y="t2m"``), the
    name of the index, or Series. Data plotted without an x coordinate are
    plotted against the index when it is meaningful (named, or of datetimes),
    and otherwise against the position of the values, like a numpy array.

    The index plays the role of the coordinates of xarray objects: when y
    names the index, the values are on x (e.g. a vertical profile indexed by
    pressure). The plotted column provides the ``name`` and ``units`` metadata.

    Parameters
    ----------
    data : pandas.DataFrame or pandas.Series
        The data.
    metadata : dict, optional
        User-provided metadata.
    """

    def __init__(self, data: Any, metadata: dict | None = None):
        super().__init__(data, metadata=metadata)
        #: Name of the column holding the plotted values, set by extract_coordinates
        self._primary = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _frame(self):
        """The data as a DataFrame (a Series becomes a single-column DataFrame)."""
        if _is_series(self.data):
            name = self.data.name if self.data.name is not None else "values"
            return self.data.to_frame(name=name)
        return self.data

    def _default_column(self):
        """The column plotted when none is named, or ``None`` if it is ambiguous."""
        if _is_series(self.data):
            return self.data.name if self.data.name is not None else "values"
        columns = list(self.data.columns)
        if len(columns) == 1:
            return columns[0]
        return None

    def _column_units(self, name) -> str | None:
        """Units of a column: from the column's own attrs, then from the attrs of the data."""
        frame = self._frame
        if name in frame.columns:
            units = _units_from_attrs(frame[name].attrs, name)
            if units is not None:
                return units
        return _units_from_attrs(self.data.attrs, name)

    def _resolve(self, spec, role: str):
        """
        Resolve a coordinate specification into ``(values, name, units)``.

        ``spec`` is a column name, the name of the index, a Series or an array.
        """
        if spec is None:
            return None
        if isinstance(spec, str):
            frame = self._frame
            if spec in frame.columns:
                return frame[spec].to_numpy(), spec, self._column_units(spec)
            if spec == frame.index.name:
                return frame.index.to_numpy(), spec, _units_from_attrs(self.data.attrs, spec)
            raise ValueError(
                f"Column {spec!r} given for '{role}' not found; available columns are {list(frame.columns)}"
            )
        if _is_series(spec):
            name = spec.name if spec.name is not None else ""
            return spec.to_numpy(), name, _units_from_attrs(spec.attrs, spec.name)
        return np.atleast_1d(spec), "", None

    def _is_index(self, spec) -> bool:
        """Whether ``spec`` names the index of the data (rather than a column)."""
        frame = self._frame
        return isinstance(spec, str) and spec == frame.index.name and spec not in frame.columns

    def _default_x(self):
        """The index of the data, when it is meaningful as an x coordinate."""
        index = self.data.index
        if index.name is not None or np.issubdtype(index.dtype, np.datetime64):
            return index.to_numpy(), index.name or "", _units_from_attrs(self.data.attrs, index.name)
        return None

    # ------------------------------------------------------------------
    # Coordinates
    # ------------------------------------------------------------------

    def extract_coordinates(
        self,
        x: str | np.ndarray | None,
        y: str | np.ndarray | None,
        z: str | np.ndarray | None,
        u: str | np.ndarray | None,
        v: str | np.ndarray | None,
        context: PlotContext,
    ) -> ExtractedCoordinates:
        """
        Extract coordinates from a DataFrame or Series.

        Column names are resolved into arrays, and the column of the plotted
        values defaults to the only column of the data (or the Series itself).
        The arrays are then handled as for numpy data, with the names and
        units of the columns attached.
        """
        resolved = {role: self._resolve(spec, role) for role, spec in zip("xyzuv", (x, y, z, u, v))}

        # The column of the plotted values: z for maps and 2-D plots; for lines
        # y, or x when y names the index. As the coordinates of xarray objects,
        # the index is the independent variable, so e.g. a vertical profile is
        # plotted with ``x="temperature", y="pressure"`` from a frame indexed by
        # pressure. The values default to the only column of the data.
        if context.is_2d or (context.is_geographic and resolved["x"] and resolved["y"]):
            value_role = "z"
        else:
            value_role = "x" if self._is_index(y) else "y"
        if resolved[value_role] is None and resolved["u"] is None:
            column = self._default_column()
            if column is None:
                raise ValueError(
                    f"The DataFrame has several columns {list(self.data.columns)}; name the column to plot "
                    f"with {value_role}=..."
                )
            if _is_series(self.data):
                resolved[value_role] = (self.data.to_numpy(), column, _units_from_attrs(self.data.attrs, column))
            else:
                resolved[value_role] = self._resolve(column, value_role)
        if value_role == "y" and resolved["x"] is None:
            resolved["x"] = self._default_x()
        primary = resolved[value_role] or resolved["u"]
        self._primary = primary[1] if primary is not None else None

        arrays = {role: (r[0] if r is not None else None) for role, r in resolved.items()}
        inner = NumpyExtractor(None, metadata=self._metadata)
        coords = inner.extract_coordinates(arrays["x"], arrays["y"], arrays["z"], arrays["u"], arrays["v"], context)

        def _annotate(info, role):
            if info is None or resolved[role] is None:
                return info
            _, name, units = resolved[role]
            metadata = {"units": units} if units is not None else {}
            return CoordinateInfo(
                values=info.values,
                name=name,
                source_units=units if units is not None else info.source_units,
                metadata=metadata,
            )

        return ExtractedCoordinates(
            x=_annotate(coords.x, "x"),
            y=_annotate(coords.y, "y"),
            z=_annotate(coords.z, "z"),
            u=_annotate(coords.u, "u"),
            v=_annotate(coords.v, "v"),
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _constant(self, name):
        """The value of a column whose non-missing values are all equal, or ``None``."""
        frame = self._frame
        if name not in frame.columns:
            return None
        values = frame[name].dropna()
        if len(values) == 0:
            return None
        first = values.iloc[0]
        try:
            if not (values == first).all():
                return None
        except (TypeError, ValueError):
            return None
        return _scalar(first)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from the pandas object.

        Lookup order:

        1. User-provided metadata
        2. ``attrs`` of the plotted Series (for ``units``, of the plotted column)
        3. A constant column named ``key`` (e.g. the latitude of a station)
        4. The name of the plotted column, for the ``name`` key
        5. ``attrs`` of the DataFrame
        """
        if key in self._metadata:
            return self._metadata[key]

        primary = self._primary if self._primary is not None else self._default_column()

        if key == "units" and primary is not None:
            units = self._column_units(primary)
            if units is not None:
                return units

        if _is_series(self.data):
            value = self.data.attrs.get(key)
            if value is not None and not isinstance(value, dict):
                return value

        value = self._constant(key)
        if value is not None:
            return value

        if key == "name" and primary not in (None, "", "values"):
            return primary

        value = self.data.attrs.get(key)
        if value is not None and not (key == "units" and isinstance(value, dict)):
            return value
        return default

    def get_datetime(self) -> dict | None:
        """
        Extract the time from constant time columns.

        The valid time is read from the first constant column of
        :data:`VALID_TIME_COLUMNS`, the base time from
        :data:`BASE_TIME_COLUMNS` and the lead time from :data:`LEAD_TIME_COLUMNS`.
        A DatetimeIndex with a single value is also used as the valid time.
        """

        def _first(names):
            for name in names:
                parsed = _parse_time(self._constant(name))
                if parsed is not None:
                    return parsed
            return None

        valid = _first(VALID_TIME_COLUMNS)
        if valid is None:
            index = self.data.index
            if np.issubdtype(index.dtype, np.datetime64) and index.nunique() == 1:
                valid = _parse_time(index[0])
        base = _first(BASE_TIME_COLUMNS)
        lead = None
        for name in LEAD_TIME_COLUMNS:
            value = self._constant(name)
            if value is not None:
                if hasattr(value, "to_pytimedelta"):
                    lead = value.to_pytimedelta()
                elif isinstance(value, datetime.timedelta):
                    lead = value
                if lead is not None:
                    break

        if valid is None and base is None and lead is None:
            return None
        result = {}
        if base is not None:
            result["base_time"] = base
        if valid is not None:
            result["valid_time"] = valid
        elif base is not None and lead is not None:
            result["valid_time"] = base + lead
        if lead is not None:
            result["lead_time"] = lead
        elif base is not None and valid is not None:
            result["lead_time"] = valid - base
        if "base_time" not in result and "valid_time" in result:
            result["base_time"] = result["valid_time"]
        return result
