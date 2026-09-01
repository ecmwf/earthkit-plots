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

"""Optional benchmarking hook for timing earthkit-plots internals.

A host application that wants to time the internal steps of a render
(source construction, domain cropping, the matplotlib draw, ...) installs
a callable here via :func:`set_timing_hook`; it takes a step name and
returns a context manager wrapping that step. The default is a no-op, so
there is no cost and no dependency when nothing is installed.

This lives in its own tiny module (rather than on ``Tile``) so that any
part of the plotting pipeline can be instrumented without import cycles -
``components/_pipeline.py`` and ``components/tiles.py`` both use it, and
earthkit-server plugs its per-request benchmark accumulator in (see
``earthkit_server.benchmark``).
"""

from contextlib import contextmanager


@contextmanager
def _null_step(name):
    yield


_TIMING_HOOK = _null_step


def set_timing_hook(hook):
    """Install a ``hook(name) -> context manager`` to time internal steps.

    Pass ``None`` to restore the no-op default. The hook is called as
    ``with hook("plots.crop"): ...`` around each instrumented internal
    step, so a benchmark harness can fold these durations into its own
    summary.
    """
    global _TIMING_HOOK
    _TIMING_HOOK = hook if hook is not None else _null_step


def step(name):
    """Context manager for one internally-timed step."""
    return _TIMING_HOOK(name)
