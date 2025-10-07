# Copyright 2025-, European Centre for Medium Range Weather Forecasts.
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

import pytest

from earthkit.plots.styles.auto import criteria_matches


class MockedData:
    def __init__(self, metadata):
        self._metadata = metadata

    def metadata(self, key, default=None):
        return self._metadata.get(key, default)


@pytest.mark.parametrize(
    "metadata,criteria,expected",
    [
        # Basic GRIB parameter matching
        ({"shortName": "2t", "levtype": "sfc"}, {"shortName": "2t"}, True),
        ({"shortName": "2t", "level": 2}, {"shortName": "msl"}, False),
        ({"shortName": "t", "level": 850}, {"shortName": "u", "level": 500}, False),
        # Empty cases
        ({}, {"shortName": "2t"}, False),
        ({}, {}, True),
        # None values in metadata or criteria
        ({"shortName": None, "level": 850}, {"shortName": "t"}, False),
        ({"shortName": "t", "level": None}, {"level": 850}, False),
        ({"shortName": None}, {"shortName": None}, False),
        # parameter lists - exact matches
        ({"param": ["130", "131"]}, {"param": ["130", "131"]}, True),
        ({"param": ["131", "130"]}, {"param": ["130", "131"]}, True),
        ({"shortName": ["t"]}, {"shortName": ["t"]}, True),
        # parameter lists - mismatches
        ({"param": ["130"]}, {"param": ["130", "131"]}, False),
        ({"shortName": "t"}, {"param": ["130", "131"]}, False),
        ({"param": ["130", "131", "132"]}, {"param": ["130", "131"]}, False),
        # Mixed type matching (string vs list) - GRIB parameters
        ({"shortName": "t"}, {"shortName": "t"}, True),
        ({"param": ["130"]}, {"param": "130"}, False),
        ({"shortName": "t"}, {"shortName": ["t"]}, True),
        # Complex combinations with lists
        (
            {"param": ["130", "131"], "levelist": [850, 500]},
            {"param": ["130", "131"], "levelist": [850, 500]},
            True,
        ),
        (
            {"param": ["130", "131"], "level": 850},
            {"param": "130", "level": 850},
            False,
        ),
        (
            {"shortName": ["t", "u"], "levelist": [850, 500]},
            {"shortName": ["t", "u"], "levelist": [500, 850]},
            True,
        ),
        # Multiple criteria keys - should match only if ALL keys matches
        ({"shortName": "t", "level": 850}, {"shortName": "t", "level": 850}, True),
        ({"shortName": "t", "level": 850}, {"shortName": "t", "level": 500}, False),
        ({"shortName": "msl", "level": 0}, {"shortName": "t", "level": 850}, False),
        # String vs number matching - levels and parameters
        ({"level": "850"}, {"level": "850"}, True),
        ({"level": 850}, {"level": 850}, True),
        ({"level": "850"}, {"level": 850}, False),
        ({"param": "130"}, {"param": 130}, False),
        # GRIB type of level matching
        ({"levtype": "pl"}, {"levtype": "pl"}, True),
        ({"levtype": "sfc"}, {"levtype": "pl"}, False),
        ({"levtype": "heightAboveGround"}, {"levtype": "sfc"}, False),
        # Complex GRIB metadata scenarios
        (
            {"shortName": "10u", "levtype": "heightAboveGround", "level": 10},
            {"shortName": "10u"},
            True,
        ),
        (
            {"shortName": "10v", "levtype": "heightAboveGround", "level": 10},
            {"levtype": "sfc"},
            False,
        ),
        (
            {"shortName": "sp", "levtype": "sfc", "step": 0},
            {"levtype": "sfc", "step": 0},
            True,
        ),
        # Edge case: key exists but with empty list
        ({"param": []}, {"param": []}, True),
        ({"param": []}, {"param": ["130"]}, False),
        ({"shortName": ["t"]}, {"shortName": []}, False),
        # GRIB parameter name case variations
        ({"shortName": "T"}, {"shortName": "t"}, False),
        ({"shortName": "MSL"}, {"shortName": "msl"}, False),
        # Special GRIB parameters
        ({"shortName": "2t"}, {"shortName": "2t"}, True),
        ({"shortName": "10u"}, {"shortName": "10v"}, False),
        ({"shortName": "tp"}, {"shortName": "cp"}, False),
    ],
)
def test_criteria_matches(metadata, criteria, expected):
    assert criteria_matches(MockedData(metadata), criteria) == expected
