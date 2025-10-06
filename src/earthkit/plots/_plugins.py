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

from importlib.metadata import entry_points
from pathlib import Path


def register_plugins():
    plugins = dict()

    # Compatibility adjustment for Python 3.9 and earlier
    all_entry_points = entry_points()

    if hasattr(all_entry_points, "select"):
        # For Python 3.10 and above
        plugin_entry_points = all_entry_points.select(group="earthkit.plots.plugins")
    else:
        # For Python 3.9 and below, access the group directly from the dictionary
        # and ensure it defaults to an empty list if not found
        plugin_entry_points = all_entry_points.get("earthkit.plots.plugins", [])

        # Additional handling for consistency in 3.9 by converting entry points if needed
        if isinstance(plugin_entry_points, dict):
            plugin_entry_points = plugin_entry_points.get("earthkit.plots.plugins", [])

    for plugin in plugin_entry_points:
        path = Path(plugin.load().__file__).parents[0]
        plugins[plugin.name] = {
            "identities": path / "identities",
            "schema": path / "schema.yml",
            "styles": path / "styles",
        }
        for key, value in plugins[plugin.name].items():
            if not value.exists():
                plugins[plugin.name][key] = None

    return plugins


PLUGINS = register_plugins()
