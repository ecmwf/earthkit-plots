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

from typing import Any, Optional

from earthkit.plots.sources.protocols import DataAdaptor


class MetadataResolver:
    """
    Resolves metadata from multiple sources with priority order.

    Priority:
    1. User-provided metadata (highest priority)
    2. Adaptor-extracted metadata
    3. Defaults (lowest priority)
    """

    def __init__(self, adaptor: DataAdaptor, user_metadata: Optional[dict] = None):
        """
        Initialize metadata resolver.

        Parameters
        ----------
        adaptor : DataAdaptor
            Adaptor to extract metadata from.
        user_metadata : dict, optional
            User-provided metadata with highest priority.
        """
        self.adaptor = adaptor
        self.user_metadata = user_metadata or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value with priority resolution.

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
            return self.user_metadata[key]

        # Priority 2: Adaptor metadata
        value = self.adaptor.get_metadata(key)
        if value is not None:
            return value

        # Priority 3: Default
        return default

    def get_units(self) -> Optional[str]:
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

    def get_long_name(self) -> Optional[str]:
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
