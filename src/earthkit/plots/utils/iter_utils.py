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


def symmetrical_iter(lst):
    """
    Iterate over an iterable from both ends simultaneously.

    Parameters
    ----------
    lst : iterable
        The iterable to iterate over.
    """
    mid = (len(lst) + 1) // 2
    for x, y in zip(lst[:mid], lst[::-1]):
        if x is y:
            yield x
        else:
            yield (x, y)


def all_equal(iterable):
    """
    Check if all elements in an iterable are equal.

    Parameters
    ----------
    iterable : iterable
        The iterable to check.

    Returns
    -------
    bool
        True if all elements are equal, False otherwise.
    """
    from itertools import groupby

    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def flatten(lst):
    """
    Flatten a nested list.

    Parameters
    ----------
    lst : list
        The list to flatten.

    Returns
    -------
    list
        The flattened list.
    """
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list
