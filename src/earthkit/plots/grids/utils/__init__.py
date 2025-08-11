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
Grid utilities module.

This module provides grid specification and utility functions for working with
different grid types in earthkit-plots.
"""

from .gridspec import GRIDSPECS, GridSpec, HEALPix, ReducedGG

__all__ = [
    "GridSpec",
    "ReducedGG",
    "HEALPix",
    "GRIDSPECS",
]
