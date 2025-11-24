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

"""
Identity matcher - matches data metadata against identity criteria to find appropriate styles.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

from earthkit.plots._plugins import PLUGINS
from earthkit.plots.styles.loader import get_optimal


class IdentityMatcher:
    """
    Matches data objects against identity criteria to find appropriate styles.

    Identity files define criteria for recognizing specific variables
    (e.g., temperature, pressure) based on metadata attributes.
    """

    def __init__(self):
        self._identities_cache: Dict[str, dict] = {}
        self._loaded = False

    def _get_identity_directories(self) -> List[Path]:
        """Get all directories containing identity files, in priority order."""
        directories = []

        # 1. User config directory (highest priority)
        user_config = Path.home() / ".config" / "earthkit-plots" / "identities"
        if user_config.exists():
            directories.append(user_config)

        # 2. Plugin directories
        for plugin_name, plugin_info in PLUGINS.items():
            if plugin_info.get("identities") is not None:
                directories.append(plugin_info["identities"])

        # 3. Built-in defaults (lowest priority)
        default_identities = Path(__file__).parent.parent / "_defaults" / "identities"
        if default_identities.exists():
            directories.append(default_identities)

        return directories

    def _load_identity_file(self, filepath: Path) -> dict:
        """Load a YAML identity file and return its contents."""
        with open(filepath, "r") as f:
            return yaml.safe_load(f)

    def _load_all_identities(self):
        """Load all identity files from all directories."""
        if self._loaded:
            return

        directories = self._get_identity_directories()

        # Load identities in reverse priority order so higher priority overwrites
        for directory in reversed(directories):
            for yaml_file in directory.glob("*.yml"):
                try:
                    content = self._load_identity_file(yaml_file)

                    if "id" not in content or "criteria" not in content:
                        continue

                    identity_id = content["id"]
                    self._identities_cache[identity_id] = content

                except Exception as e:
                    # Log warning but continue loading other identities
                    print(f"Warning: Failed to load identity from {yaml_file}: {e}")

        self._loaded = True

    def _extract_metadata(self, data) -> Dict[str, Any]:
        """
        Extract metadata from a data object.

        Parameters
        ----------
        data : object
            The data object to extract metadata from.

        Returns
        -------
        dict
            Dictionary of metadata attributes.
        """
        metadata = {}

        # Try to extract common metadata attributes
        # These are typical attributes from earthkit-data, xarray, etc.
        attrs_to_check = [
            "paramId",
            "shortName",
            "standard_name",
            "long_name",
            "name",
            "units",
            "level",
            "typeOfLevel",
        ]

        for attr in attrs_to_check:
            # Try multiple access patterns
            value = None

            # Direct attribute access
            if hasattr(data, attr):
                value = getattr(data, attr)

            # Dictionary-like access
            elif hasattr(data, "metadata") and isinstance(data.metadata, dict):
                value = data.metadata.get(attr)

            # xarray attrs
            elif hasattr(data, "attrs") and isinstance(data.attrs, dict):
                value = data.attrs.get(attr)

            # earthkit-data metadata method
            elif hasattr(data, "metadata") and callable(data.metadata):
                try:
                    value = data.metadata(attr)
                except:
                    pass

            if value is not None:
                metadata[attr] = value

        return metadata

    def _matches_criterion(self, metadata: dict, criterion: dict) -> bool:
        """
        Check if metadata matches a single criterion.

        A criterion is a dict like {paramId: 151, shortName: "msl"}.
        All key-value pairs must match for the criterion to match.

        Parameters
        ----------
        metadata : dict
            Metadata extracted from data object.
        criterion : dict
            Criterion to check.

        Returns
        -------
        bool
            True if all criterion keys match metadata values.
        """
        for key, expected_value in criterion.items():
            if key not in metadata:
                return False

            actual_value = metadata[key]

            # Handle different comparison types
            if isinstance(expected_value, (list, tuple)):
                # Expected value is a list - check if actual is in list
                if actual_value not in expected_value:
                    return False
            else:
                # Direct comparison
                if actual_value != expected_value:
                    return False

        return True

    def _matches_identity(self, metadata: dict, identity: dict) -> bool:
        """
        Check if metadata matches an identity's criteria.

        An identity matches if ANY of its criteria match.

        Parameters
        ----------
        metadata : dict
            Metadata extracted from data object.
        identity : dict
            Identity definition with "criteria" list.

        Returns
        -------
        bool
            True if any criterion matches.
        """
        criteria = identity.get("criteria", [])

        for criterion in criteria:
            if self._matches_criterion(metadata, criterion):
                return True

        return False

    def match(self, data) -> List[str]:
        """
        Find all identity IDs that match the given data.

        Parameters
        ----------
        data : object
            Data object to match (earthkit-data field, xarray DataArray, etc.)

        Returns
        -------
        list of str
            List of identity IDs (e.g., ["mean-sea-level-pressure"]) that match,
            or empty list if no matches found.

        Examples
        --------
        >>> from earthkit.plots.styles import matcher
        >>> identity_ids = matcher.match(data)
        >>> print(identity_ids)
        ['mean-sea-level-pressure']
        """
        self._load_all_identities()

        # Extract metadata from data
        metadata = self._extract_metadata(data)

        if not metadata:
            return []

        # Try to match against all identities and return all matches
        matches = []
        for identity_id, identity in self._identities_cache.items():
            if self._matches_identity(metadata, identity):
                matches.append(identity_id)

        return matches

    def get_style(self, data) -> Optional:
        """
        Get the optimal style for the given data by matching its metadata.

        This is a convenience method that combines identity matching
        with style lookup. Returns the first matching style.

        Parameters
        ----------
        data : object
            Data object to match.

        Returns
        -------
        Style or None
            The optimal style for this data, or None if no match found.

        Examples
        --------
        >>> from earthkit.plots.styles import matcher
        >>> style = matcher.get_style(data)
        >>> print(style.plot_type)
        contour
        """
        identity_ids = self.match(data)

        if not identity_ids:
            return None

        # Get the optimal style for the first matching identity
        return get_optimal(identity_ids[0])


# Global identity matcher instance
_matcher = IdentityMatcher()


def match(data) -> List[str]:
    """
    Find all identity IDs that match the given data.

    Parameters
    ----------
    data : object
        Data object to match (earthkit-data field, xarray DataArray, etc.)

    Returns
    -------
    list of str
        List of identity IDs (e.g., ["mean-sea-level-pressure"]) that match,
        or empty list if no matches found.

    Examples
    --------
    >>> from earthkit.plots.styles import matcher
    >>> identity_ids = matcher.match(data)
    >>> print(identity_ids)
    ['mean-sea-level-pressure']
    """
    return _matcher.match(data)


def get_style(data) -> Optional:
    """
    Get the optimal style for the given data by matching its metadata.

    This is a convenience method that combines identity matching
    with style lookup.

    Parameters
    ----------
    data : object
        Data object to match.

    Returns
    -------
    Style or None
        The optimal style for this data, or None if no match found.

    Examples
    --------
    >>> from earthkit.plots.styles import matcher
    >>> style = matcher.get_style(data)
    >>> print(style.plot_type)
    contour
    """
    return _matcher.get_style(data)
