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

import shutil
import subprocess
import tempfile

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--test-images",
        action="store_true",
        default=False,
        help="Run tests that use image comparison with reference images.",
    )


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
