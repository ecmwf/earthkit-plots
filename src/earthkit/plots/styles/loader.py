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
Style loader - loads style definitions from YAML files and converts them to Style objects.
"""

from pathlib import Path
from typing import Dict, Optional, List
import yaml

from earthkit.plots.styles import Style
from earthkit.plots._plugins import PLUGINS


class StyleLibrary:
    """
    Manages loading and accessing style definitions from YAML files.

    Supports styles from:
    - Built-in defaults (_defaults/styles/)
    - Plugin packages (via entry points)
    - User config directories
    """

    def __init__(self):
        self._styles_cache: Dict[str, Style] = {}
        self._style_files_cache: Dict[str, dict] = {}
        self._loaded = False

    def _get_style_directories(self) -> List[Path]:
        """Get all directories containing style files, in priority order."""
        directories = []

        # 1. User config directory (highest priority)
        user_config = Path.home() / ".config" / "earthkit-plots" / "styles"
        if user_config.exists():
            directories.append(user_config)

        # 2. Plugin directories
        for plugin_name, plugin_info in PLUGINS.items():
            if plugin_info.get("styles") is not None:
                directories.append(plugin_info["styles"])

        # 3. Built-in defaults (lowest priority)
        default_styles = Path(__file__).parent.parent / "_defaults" / "styles"
        if default_styles.exists():
            directories.append(default_styles)

        return directories

    def _load_style_file(self, filepath: Path) -> dict:
        """Load a YAML style file and return its contents."""
        if str(filepath) in self._style_files_cache:
            return self._style_files_cache[str(filepath)]

        with open(filepath, "r") as f:
            content = yaml.safe_load(f)

        self._style_files_cache[str(filepath)] = content
        return content

    def _load_all_styles(self):
        """Load all styles from all directories."""
        if self._loaded:
            return

        directories = self._get_style_directories()

        # Load styles in reverse priority order so higher priority overwrites
        for directory in reversed(directories):
            for yaml_file in directory.glob("*.yml"):
                try:
                    content = self._load_style_file(yaml_file)

                    if "styles" not in content:
                        continue

                    file_id = content.get("id", yaml_file.stem)
                    optimal_style = content.get("optimal")

                    # Load each named style in the file
                    for style_name, style_data in content["styles"].items():
                        style_obj = self._yaml_to_style(style_data)

                        # Store metadata
                        style_obj._file_id = file_id
                        style_obj._is_optimal = (style_name == optimal_style)

                        self._styles_cache[style_name] = style_obj

                except Exception as e:
                    # Log warning but continue loading other styles
                    print(f"Warning: Failed to load styles from {yaml_file}: {e}")

        self._loaded = True

    def _yaml_to_style(self, style_data):
        """
        Convert YAML style data to a Style or CompositeStyle object.

        If style_data is a list, creates a CompositeStyle with multiple component styles.
        If style_data is a dict, creates a single Style.

        Extracts known Style parameters and passes the rest as kwargs.
        Evaluates Python expressions in 'levels' field (e.g., range(-40, 41, 2)).
        """
        # Check if this is a composite style (list of styles)
        if isinstance(style_data, list):
            from earthkit.plots.styles import CompositeStyle
            component_styles = [self._dict_to_style(item) for item in style_data]
            return CompositeStyle(component_styles)
        else:
            # Single style (dict)
            return self._dict_to_style(style_data)

    def _dict_to_style(self, style_data: dict) -> Style:
        """
        Convert a single style dictionary to a Style object.

        Extracts known Style parameters and passes the rest as kwargs.
        Evaluates Python expressions in 'levels' field (e.g., range(-40, 41, 2)).
        """
        # Create a copy to avoid modifying original
        data = dict(style_data)

        # Extract plot_type and lowercase it
        plot_type = data.pop("plot_type", None)
        if plot_type:
            plot_type = plot_type.lower()

        # Extract known Style parameters
        colors = data.pop("colors", None)
        levels = data.pop("levels", None)
        units = data.pop("units", None)
        units_label = data.pop("units_label", None)
        scale_factor = data.pop("scale_factor", None)
        normalize = data.pop("normalize", True)
        anomaly = data.pop("anomaly", False)
        # For legend_type, only use "auto" default if key is not present
        # If key is present with null value, keep it as None
        legend_type = data.pop("legend_type") if "legend_type" in data else "auto"

        # Evaluate levels if it's a string (e.g., "range(-40, 41, 2)")
        if isinstance(levels, str):
            levels = self._evaluate_levels(levels)

        # Everything else goes into kwargs
        kwargs = data

        return Style(
            colors=colors,
            levels=levels,
            units=units,
            units_label=units_label,
            scale_factor=scale_factor,
            normalize=normalize,
            anomaly=anomaly,
            legend_type=legend_type,
            plot_type=plot_type,
            **kwargs
        )

    def _evaluate_levels(self, levels_str: str):
        """
        Safely evaluate a Python expression for levels.

        Supports common Python builtins like range(), list(), etc.

        Parameters
        ----------
        levels_str : str
            Python expression to evaluate (e.g., "range(-40, 41, 2)")

        Returns
        -------
        list or original value
            Evaluated result converted to list, or original if evaluation fails.
        """
        try:
            # Create a safe namespace with common functions
            safe_namespace = {
                "range": range,
                "list": list,
                "tuple": tuple,
            }
            # Evaluate the expression
            result = eval(levels_str, {"__builtins__": {}}, safe_namespace)
            # Convert range objects to list
            if isinstance(result, range):
                result = list(result)
            return result
        except Exception as e:
            # If evaluation fails, return the original string
            # This allows for error handling upstream
            print(f"Warning: Could not evaluate levels expression '{levels_str}': {e}")
            return levels_str

    def get(self, style_name: str) -> Optional[Style]:
        """
        Get a style by name.

        Parameters
        ----------
        style_name : str
            The name of the style to retrieve.

        Returns
        -------
        Style or None
            The requested style, or None if not found.
        """
        self._load_all_styles()
        return self._styles_cache.get(style_name)

    def available(self) -> List[str]:
        """
        Get a list of all available style names.

        Returns
        -------
        list of str
            Sorted list of all available style names.
        """
        self._load_all_styles()
        return sorted(self._styles_cache.keys())

    def get_optimal_for_file_id(self, file_id: str) -> Optional[Style]:
        """
        Get the optimal style for a given variable file ID.

        Parameters
        ----------
        file_id : str
            The file ID (e.g., "mean-sea-level-pressure")

        Returns
        -------
        Style or None
            The optimal style for this variable, or None if not found.
        """
        self._load_all_styles()

        for style in self._styles_cache.values():
            if hasattr(style, "_file_id") and hasattr(style, "_is_optimal"):
                if style._file_id == file_id and style._is_optimal:
                    return style

        return None


# Global style library instance
_style_library = StyleLibrary()


def get(style_name: str) -> Optional[Style]:
    """
    Get a style by name.

    Parameters
    ----------
    style_name : str
        The name of the style to retrieve.

    Returns
    -------
    Style or None
        The requested style, or None if not found.

    Examples
    --------
    >>> from earthkit.plots.styles import loader
    >>> style = loader.get("MEAN_SEA_LEVEL_PRESSURE_IN_HPA")
    >>> print(style.plot_type)
    contour
    """
    return _style_library.get(style_name)


def available() -> List[str]:
    """
    Get a list of all available style names.

    Returns
    -------
    list of str
        Sorted list of all available style names.

    Examples
    --------
    >>> from earthkit.plots.styles import loader
    >>> styles = loader.available()
    >>> print(styles[:5])
    ['MEAN_SEA_LEVEL_PRESSURE_IN_HPA', 'MEAN_SEA_LEVEL_PRESSURE_IN_PA', ...]
    """
    return _style_library.available()


def get_optimal(file_id: str) -> Optional[Style]:
    """
    Get the optimal style for a given variable file ID.

    Parameters
    ----------
    file_id : str
        The file ID (e.g., "mean-sea-level-pressure")

    Returns
    -------
    Style or None
        The optimal style for this variable, or None if not found.

    Examples
    --------
    >>> from earthkit.plots.styles import loader
    >>> style = loader.get_optimal("mean-sea-level-pressure")
    >>> print(style.units)
    hPa
    """
    return _style_library.get_optimal_for_file_id(file_id)
