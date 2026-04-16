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

"""earthkit-plots frames: iterate over dataset dimensions.

Provides two classes for stepping through multi-field datasets frame by frame:

- :class:`Batch` — render each frame to a separate output file (bulk export).
- :class:`Browser` — browse frames interactively in a Jupyter notebook widget.

Both classes accept an existing :class:`~earthkit.plots.components.maps.Map`
or :class:`~earthkit.plots.components.subplots.Subplot` (or a list of them)
that has already been added to a
:class:`~earthkit.plots.components.figures.Figure`.

Example::

    from earthkit.plots import Figure
    from earthkit.plots.frames import Batch, Browser

    fig = Figure(figsize=(10, 6))
    m = fig.add_map(domain="Europe")

    batch = Batch(m)
    m.contourf(data, style="auto")
    m.coastlines()
    m.legend()
    batch.title("{variable_name} — {valid_time:%d %b %Y %H:%M}")
    paths = batch.save("{variable_name}_{valid_time:%Y%m%d_%H}.png")
"""

from earthkit.plots.frames.batch import Batch
from earthkit.plots.frames.browser import Browser

__all__ = ["Batch", "Browser"]
