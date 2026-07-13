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

import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Image-test timings
# ---------------------------------------------------------------------------
#
# Every test marked ``mpl_image`` is timed (one test = one plot), giving a
# per-plot performance profile of the library analogous to the baseline
# images.  Timings are printed as a summary table at the end of the run and
# written to ``mpl-results/timings.json`` (gitignored).
#
# Workflow:
#
#   1. Record a baseline (committed to the repo):
#        pytest tests/images --save-timings-baseline
#   2. On subsequent runs, each test is compared against the baseline and
#      regressions beyond the threshold are flagged in the summary table.
#
# The measured duration covers the pytest "call" phase, which includes both
# building the figure *and* pytest-mpl's savefig + image comparison.  The
# comparison overhead is roughly constant per test, so pipeline slowdowns
# still stand out — but avoid comparing timings recorded on different
# machines (the baseline records its platform and a mismatch is warned).
#
# Comparison is informational only (it never fails the run): wall-clock
# timings are inherently noisy, especially on shared CI runners.

# A test is flagged as a regression when it is BOTH >25% slower and >0.1s
# slower in absolute terms (filters out jitter on very fast tests).
_REGRESSION_RATIO = 1.25
_REGRESSION_MIN_DELTA = 0.1  # seconds

_TIMINGS_KEY = pytest.StashKey[dict]()


def _default_baseline_path(config):
    return Path(config.rootpath) / "tests" / "images" / "timings-baseline.json"


def _results_path(config):
    # Keep the per-run timings next to the pytest-mpl image results.
    results_dir = config.getoption("--mpl-results-path", default=None) or "mpl-results"
    return Path(config.rootpath) / results_dir / "timings.json"


def pytest_addoption(parser):
    parser.addoption(
        "--test-images",
        action="store_true",
        default=False,
        help="Run tests that use image comparison with reference images.",
    )
    group = parser.getgroup("timings", "image-test timing baseline")
    group.addoption(
        "--timings-baseline",
        default=None,
        help="Path to the timings baseline JSON (default: tests/images/timings-baseline.json).",
    )
    group.addoption(
        "--save-timings-baseline",
        action="store_true",
        default=False,
        help="Write this run's image-test timings as the new baseline.",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Time the call phase of every mpl_image test."""
    if item.get_closest_marker("mpl_image") is None:
        yield
        return

    start = time.perf_counter()
    outcome = yield
    duration = time.perf_counter() - start

    # Only record clean passes — a failed comparison or an exception mid-plot
    # would produce a misleading duration.
    if outcome.excinfo is None:
        timings = item.config.stash.setdefault(_TIMINGS_KEY, {})
        timings[item.nodeid] = duration


def _load_baseline(path):
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("timings", {}), data.get("meta", {})
    except (OSError, json.JSONDecodeError):
        return None, {}


def _short_name(nodeid):
    # "tests/images/test_healpix.py::test_healpix_pixels" -> "test_healpix.py::test_healpix_pixels"
    return nodeid.split("/")[-1]


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    timings = config.stash.get(_TIMINGS_KEY, None)
    if not timings:
        return
    tr = terminalreporter

    baseline_opt = config.getoption("--timings-baseline")
    baseline_path = Path(baseline_opt) if baseline_opt else _default_baseline_path(config)
    baseline, baseline_meta = (None, {})
    if baseline_path.exists():
        baseline, baseline_meta = _load_baseline(baseline_path)

    # --- write this run's timings (always) --------------------------------
    meta = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
    }
    results_path = _results_path(config)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump({"meta": meta, "timings": dict(sorted(timings.items()))}, f, indent=2)
        f.write("\n")

    # --- optionally save as the new baseline ------------------------------
    if config.getoption("--save-timings-baseline"):
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(baseline_path, "w") as f:
            json.dump({"meta": meta, "timings": dict(sorted(timings.items()))}, f, indent=2)
            f.write("\n")

    # --- summary table -----------------------------------------------------
    tr.section("image test timings", sep="=")

    if baseline and baseline_meta.get("platform") not in (None, meta["platform"]):
        tr.write_line(
            f"WARNING: baseline was recorded on a different platform "
            f"({baseline_meta['platform']}) — comparison may not be meaningful.",
            yellow=True,
        )

    name_width = max(len(_short_name(n)) for n in timings) + 2
    if baseline:
        tr.write_line(f"{'test':<{name_width}}{'current':>9}{'baseline':>10}{'change':>9}")
    else:
        tr.write_line(f"{'test':<{name_width}}{'current':>9}")

    regressions = []
    for nodeid, duration in sorted(timings.items(), key=lambda kv: kv[1], reverse=True):
        name = _short_name(nodeid)
        if baseline and nodeid in baseline:
            ref = baseline[nodeid]
            delta = duration - ref
            pct = (duration / ref - 1.0) * 100 if ref > 0 else float("inf")
            flag = ""
            markup = {}
            if duration > ref * _REGRESSION_RATIO and delta > _REGRESSION_MIN_DELTA:
                flag = "  SLOWER"
                markup = {"red": True}
                regressions.append((name, ref, duration))
            elif ref > duration * _REGRESSION_RATIO and -delta > _REGRESSION_MIN_DELTA:
                flag = "  faster"
                markup = {"green": True}
            tr.write_line(
                f"{name:<{name_width}}{duration:>8.2f}s{ref:>9.2f}s{pct:>+8.0f}%{flag}",
                **markup,
            )
        else:
            suffix = "  (no baseline entry)" if baseline else ""
            tr.write_line(f"{name:<{name_width}}{duration:>8.2f}s{suffix}")

    total = sum(timings.values())
    if baseline:
        common = [n for n in timings if n in baseline]
        base_total = sum(baseline[n] for n in common)
        cur_total = sum(timings[n] for n in common)
        tr.write_line("-" * (name_width + 28))
        tr.write_line(f"{'TOTAL (common tests)':<{name_width}}{cur_total:>8.2f}s{base_total:>9.2f}s")
    else:
        tr.write_line("-" * (name_width + 9))
        tr.write_line(f"{'TOTAL':<{name_width}}{total:>8.2f}s")
        if not config.getoption("--save-timings-baseline"):
            tr.write_line("")
            tr.write_line("No timings baseline found — record one with: pytest tests/images --save-timings-baseline")

    if regressions:
        tr.write_line("")
        tr.write_line(
            f"{len(regressions)} test(s) slower than baseline by >{int((_REGRESSION_RATIO - 1) * 100)}% "
            f"(threshold {_REGRESSION_MIN_DELTA}s):",
            red=True,
        )
        for name, ref, duration in regressions:
            tr.write_line(f"  {name}: {ref:.2f}s -> {duration:.2f}s", red=True)

    if config.getoption("--save-timings-baseline"):
        tr.write_line("")
        tr.write_line(f"Timings baseline saved to {baseline_path}", green=True)


@pytest.fixture(scope="session")
def mpl_image_compare_setup(request):
    if not request.config.getoption("--test-images"):
        pytest.skip("Skipping image comparison tests because --test-images not set")

    temp_dir = tempfile.mkdtemp()
    repo_url = "https://github.com/ecmwf/earthkit-plots-test-images.git"

    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)
