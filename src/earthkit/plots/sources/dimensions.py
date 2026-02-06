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

from typing import Any

import numpy as np


class DimensionInfo:
    """
    Information about a plot dimension (x, y, or z).

    Provides access to dimension values, units, metadata, and name.
    Supports template string formatting like "{x.units}" or "{y.metadata('long_name')}".

    Parameters
    ----------
    name : str
        Name of the dimension (e.g., "valid_time", "t2m"). Empty string for auto-generated.
    values : np.ndarray
        Dimension values (with unit conversion already applied).
    source_units : str or None
        Original units from the data source.
    applied_units : str or None
        Units after conversion (what's shown on the plot).
    metadata_dict : dict
        Dimension-specific metadata from coordinate/variable attributes.

    Attributes
    ----------
    name : str
        Dimension name ("" for auto-generated coordinates).
    values : np.ndarray
        Dimension values with unit conversion applied.
    source_units : str or None
        Original units before conversion.
    units : str or None
        Units as shown on plot (after conversion).
    """

    def __init__(
        self,
        name: str,
        values: np.ndarray,
        source_units: str | None,
        applied_units: str | None,
        metadata_dict: dict,
    ):
        self.name = name
        self.values = values
        self.source_units = source_units
        self.units = applied_units
        self._metadata_dict = metadata_dict

    def metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata for this dimension.

        Checks dimension-specific metadata only (e.g. in the case of xarray,
        from coordinate/variable attributes).

        Special case: If key is "name" and not found in metadata, returns
        self.name.

        Parameters
        ----------
        key : str
            Metadata key to retrieve.
        default : Any, optional
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value or default.

        Examples
        --------
        >>> source.x.metadata("long_name")
        'valid_time'
        >>> source.y.metadata("units")
        'celsius'
        >>> source.z.metadata("standard_name", "unknown")
        'air_temperature'
        >>> source.y.metadata("name")  # Falls back to self.name if not in metadata
        't2m'
        """
        # Check dimension-specific metadata first
        if key in self._metadata_dict:
            return self._metadata_dict[key]

        # Special fallback for "name" - use dimension's name attribute
        if key == "name":
            # Return self.name if it's not empty, otherwise return default
            return self.name if self.name else default

        # No fallback to source-level metadata - return default
        return default

    def __repr__(self):
        """String representation for debugging."""
        units_str = f", units={self.units!r}" if self.units else ""
        name_str = f"name={self.name!r}" if self.name else "auto-generated"
        return f"DimensionInfo({name_str}, shape={self.values.shape}{units_str})"
