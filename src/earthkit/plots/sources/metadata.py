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

from earthkit.plots.sources.protocols import DataExtractor


class MetadataResolver:
    """
    Resolves metadata from multiple sources with priority order.

    Priority:
    1. User-provided metadata (highest priority)
    2. Extractor-extracted metadata
    3. Defaults (lowest priority)
    """

    def __init__(self, extractor: DataExtractor, user_metadata: dict | None = None):
        """
        Initialize metadata resolver.

        Parameters
        ----------
        extractor : DataExtractor
            Extractor to extract metadata from.
        user_metadata : dict, optional
            User-provided metadata with highest priority.
        """
        self.extractor = extractor
        self.user_metadata = user_metadata or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value with priority resolution.

        For list values, if all elements are equal, returns the first element.
        This handles cases like earthkit FieldLists where metadata returns
        [850, 850] for a vector field with u and v at the same level.

        Parameters
        ----------
        key : str
            Metadata key.
        default : Any
            Default value if key not found.

        Returns
        -------
        Any
            Metadata value or default.
        """
        # Priority 1: User metadata
        if key in self.user_metadata:
            value = self.user_metadata[key]
        # Priority 2: Extractor metadata
        elif (extractor_value := self.extractor.get_metadata(key)) is not None:
            value = extractor_value
        else:
            # Priority 3: Default
            return default

        # Normalize list values: if all elements are equal, return just one
        if isinstance(value, list) and len(value) > 0:
            # Check if all elements are equal
            if all(v == value[0] for v in value):
                return value[0]

        return value

    def get_units(self) -> str | None:
        """
        Get units with special handling.

        Returns
        -------
        str or None
            Units string.
        """
        units = self.get("units")
        if isinstance(units, list) and len(units) > 0:
            return units[0]
        return units

    def get_long_name(self) -> str | None:
        """
        Get long name for labeling.

        Returns
        -------
        str or None
            Long name or None.
        """
        for key in ["long_name", "standard_name", "name", "short_name"]:
            value = self.get(key)
            if value:
                return value
        return None
