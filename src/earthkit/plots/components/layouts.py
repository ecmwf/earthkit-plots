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

PRESET_SHAPES = {
    0: (0, 0),
    1: (1, 1),
    2: (1, 2),
    3: (1, 3),
    4: (2, 2),
    5: (2, 3),
    6: (2, 3),
    7: (2, 4),
    8: (2, 4),
    9: (2, 5),
    10: (2, 5),
    11: (3, 4),
    12: (3, 4),
    13: (3, 5),
    14: (3, 5),
    15: (3, 5),
    16: (3, 6),
    17: (3, 6),
    18: (3, 6),
    19: (4, 5),
    20: (4, 5),
}


def rows_cols(num_subplots, rows=None, columns=None, max_columns=8):
    """
    Calculate the number of rows and columns for a figure with the given number
    of subplots.

    Parameters
    ----------
    num_subplots : int
        The number of subplots to be plotted.
    rows : int, optional
        The number of rows in the figure. If not provided, it will be calculated
        based on the number of columns and the number of subplots.
    columns : int, optional
        The number of columns in the figure. If not provided, it will be calculated
        based on the number of rows and the number of subplots.
    max_columns : int, optional
        The maximum number of columns in the figure. Default is 8.
    """

    if rows is None and columns is None:
        if num_subplots in PRESET_SHAPES:
            rows, columns = PRESET_SHAPES[num_subplots]
        else:
            columns = min(max_columns, num_subplots)
            rows = (num_subplots + columns - 1) // columns
    elif rows is not None and columns is None:
        if rows == 1:
            columns = num_subplots
        else:
            columns = (num_subplots + rows - 1) // rows
    elif rows is None and columns is not None:
        if columns == 1:
            rows = num_subplots
        else:
            rows = (num_subplots + columns - 1) // columns
    else:
        if rows * columns < num_subplots:
            raise ValueError(
                f"{num_subplots} subplots is too many for a figure with {rows} "
                f"rows and {columns} columns; this figure can contain a maximum "
                f"of {rows * columns} subplots"
            )

    return rows, columns
