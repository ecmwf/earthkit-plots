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
Decorator for methods that should return self when chainable=True,
or their natural return value when chainable=False.
"""

from __future__ import annotations

import functools


def chainable_method(method):
    """
    Decorator that makes a Subplot/Map method respect self._chainable.

    When self._chainable is True  → return self  (fluent chaining)
    When self._chainable is False → return the method's natural result
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        return self if self._chainable else result

    return wrapper
