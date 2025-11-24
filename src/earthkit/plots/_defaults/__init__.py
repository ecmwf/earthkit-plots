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
Built-in default styles and configurations for earthkit-plots.

This package contains:
- schema.yml: Default behavior settings and plot function defaults
- earthkit-default.mplstyle: Matplotlib appearance settings
- styles/: Variable-specific style definitions
- identities/: Variable identification criteria
"""

from pathlib import Path

# Paths to default resources
DEFAULTS_DIR = Path(__file__).parent
SCHEMA_PATH = DEFAULTS_DIR / "schema.yml"
MPLSTYLE_PATH = DEFAULTS_DIR / "earthkit-default.mplstyle"
STYLES_DIR = DEFAULTS_DIR / "styles"
IDENTITIES_DIR = DEFAULTS_DIR / "identities"
