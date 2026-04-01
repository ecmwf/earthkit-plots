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

from earthkit.plots.resample._base import Resample


class Chain(Resample):
    """
    Apply two or more resample steps in sequence.

    Pass a list (or multiple positional arguments) of :class:`Resample`
    instances.  Steps are applied in order: data-space resamplers first
    (e.g. :class:`Regrid`), pixel-space resamplers last (e.g.
    :class:`Bilinear`, :class:`NearestNeighbour`).

    Examples
    --------
    >>> Chain(Regrid(5), Bilinear())  # regrid to 5° then pixel-sample
    >>> Chain([Regrid(), Bilinear()])  # same via list
    """

    def __init__(self, *steps):
        if len(steps) == 1 and isinstance(steps[0], (list, tuple)):
            steps = steps[0]
        if len(steps) < 2:
            raise ValueError("Chain requires at least two resample steps.")
        self.steps = list(steps)

    @property
    def data_steps(self):
        """Non-pixel-sampler steps, applied in data space (Step 6.5)."""
        from earthkit.plots.resample._pixel_sampler import _PixelSampler

        return [s for s in self.steps if not isinstance(s, _PixelSampler)]

    @property
    def pixel_step(self):
        """The last _PixelSampler step, or None (applied at Step 8.5)."""
        from earthkit.plots.resample._pixel_sampler import _PixelSampler

        pixel_steps = [s for s in self.steps if isinstance(s, _PixelSampler)]
        return pixel_steps[-1] if pixel_steps else None

    def __repr__(self):
        return f"Chain({', '.join(repr(s) for s in self.steps)})"
