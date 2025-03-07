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

import os

from earthkit.plots import definitions


def test_ROOT_DIR():
    assert os.path.exists(definitions.ROOT_DIR)


def test_DATA_DIR():
    assert os.path.exists(definitions.DATA_DIR)


def test_TESTS_DIR():
    assert os.path.exists(definitions.TESTS_DIR)


def test_GEO_DIR():
    assert os.path.exists(definitions.GEO_DIR)


def test_STATIC_DIR():
    assert os.path.exists(definitions.STATIC_DIR)


def test_FONTS_DIR():
    assert os.path.exists(definitions.FONTS_DIR)
