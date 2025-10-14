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

import unittest.mock as mock

import pytest

from earthkit.plots.schemas import Schema


def test_schema_init():
    """Test Schema initialisation."""
    schema = Schema(linewidth=2, color="red")
    assert schema["linewidth"] == 2
    assert schema["color"] == "red"


def test_schema_init_with_parent():
    """Test Schema initialisation with parent."""
    schema = Schema(parent="contour", linewidth=2)
    assert schema._parent == "contour"
    assert schema["linewidth"] == 2


def test_schema_getattr():
    """Test Schema attribute access."""
    schema = Schema(linewidth=2, color="red")
    assert schema.linewidth == 2
    assert schema.color == "red"


def test_schema_getattr_missing():
    """Test Schema attribute access with missing key."""
    schema = Schema(linewidth=2)
    with pytest.raises(AttributeError):
        _ = schema.missing_key


def test_schema_setattr():
    """Test Schema attribute setting."""
    schema = Schema()
    schema.linewidth = 2
    assert schema["linewidth"] == 2


def test_schema_setattr_nested_dict():
    """Test Schema setting nested dictionary converts to Schema."""
    schema = Schema()
    schema.contour = {"linewidth": 2, "color": "red"}
    assert isinstance(schema.contour, Schema)
    assert schema.contour.linewidth == 2
    assert schema.contour.color == "red"


def test_schema_update():
    """Test Schema _update method."""
    schema = Schema(linewidth=1)
    schema._update(linewidth=2, color="red")
    assert schema.linewidth == 2
    assert schema.color == "red"


def test_schema_to_dict():
    """Test Schema _to_dict method."""
    schema = Schema(linewidth=2, color="red")
    schema.nested = Schema(parent="nested", alpha=0.5)
    result = schema._to_dict()
    assert result["linewidth"] == 2
    assert result["color"] == "red"
    assert isinstance(result["nested"], dict)
    assert result["nested"]["alpha"] == 0.5
    assert "_parent" not in result
    assert "_parent" not in result["nested"]


def test_schema_apply_basic_functionality():
    """Test basic apply functionality with schema values and kwargs override."""
    schema = Schema(parent="contour", linewidth=2.5, color="red", linestyle="dashed")

    with mock.patch("earthkit.plots.schemas.schema") as mock_global:
        # Mock global schema to not have 'contour', so it falls back to init schema
        mock_global.__contains__ = lambda self, key: False
        mock_global.get.return_value = Schema()  # Empty schema

        @schema.apply()
        def mock_function(**kwargs):
            return kwargs

        # Test 1: All schema values are used when no kwargs passed
        result = mock_function()
        assert result["linewidth"] == 2.5
        assert result["color"] == "red"
        assert result["linestyle"] == "dashed"

        # Test 2: Passed kwargs override schema defaults
        result = mock_function(linewidth=5.0)
        assert result["linewidth"] == 5.0  # overridden
        assert result["color"] == "red"  # from schema
        assert result["linestyle"] == "dashed"  # from schema

        # Test 3: Partial override of schema values
        result = mock_function(color="blue", alpha=0.8)
        assert result["color"] == "blue"  # overridden
        assert result["alpha"] == 0.8  # new value
        assert result["linewidth"] == 2.5  # from schema
        assert result["linestyle"] == "dashed"  # from schema


def test_schema_apply_with_keys_filter():
    """Test apply with keys parameter to filter specific keys."""
    schema = Schema(
        parent="contour", linewidth=2, color="red", linestyle="dashed", alpha=0.5
    )

    with mock.patch("earthkit.plots.schemas.schema") as mock_global:
        # Mock global schema to not have 'contour', so it falls back to init schema
        mock_global.__contains__ = lambda self, key: False
        mock_global.get.return_value = Schema()  # Empty schema

        @schema.apply("linewidth", "color")
        def mock_function(**kwargs):
            return kwargs

        result = mock_function()

        # Only specified keys should be present
        assert result["linewidth"] == 2
        assert result["color"] == "red"
        assert "linestyle" not in result
        assert "alpha" not in result


def test_schema_apply_with_global_schema():
    """Test apply using schema.contour.apply() pattern with global schema lookup."""
    with mock.patch("earthkit.plots.schemas.schema") as mock_global:
        # Set up schema.contour (init values)
        contour_schema = Schema(parent="contour", linewidth=1.5, color="red", alpha=0.5)

        # Mock the global schema to have contour attribute
        mock_global.contour = contour_schema
        mock_global.__contains__ = lambda self, key: key == "contour"
        mock_global.get.return_value = contour_schema
        mock_global.__getitem__ = (
            lambda self, key: contour_schema if key == "contour" else None
        )

        # Use the actual pattern: @schema.contour.apply()
        @mock_global.contour.apply()
        def mock_function(**kwargs):
            return kwargs

        # Test 1: Schema values used when no kwargs
        result = mock_function()
        assert result["linewidth"] == 1.5
        assert result["color"] == "red"
        assert result["alpha"] == 0.5

        # Test 2: Kwargs override schema values
        result = mock_function(linewidth=3.0, color="blue")
        assert result["linewidth"] == 3.0  # overridden
        assert result["color"] == "blue"  # overridden
        assert result["alpha"] == 0.5  # from schema


def test_schema_apply_hierarchy_with_nested_parent():
    """Test apply with nested parent path - correctly traverses nested schema hierarchy.

    This test verifies the behavior when 'plot' exists in global but 'contour' is not found
    within 'plot', resulting in a fallback to the init schema.
    """
    nested_schema = Schema(parent="plot.contour", linewidth=2.0, color="init")

    with mock.patch("earthkit.plots.schemas.schema") as mock_global:
        # Set up: 'plot' exists in global schema but doesn't contain 'contour'
        plot_schema = Schema(parent="plot", linewidth=1.0)

        def get_side_effect(key):
            if key == "plot":
                return plot_schema
            # 'contour' is not in root schema
            return Schema()

        mock_global.__contains__ = lambda self, key: key == "plot"
        mock_global.get.side_effect = get_side_effect
        mock_global.__getitem__ = (
            lambda self, key: plot_schema if key == "plot" else Schema()
        )

        @nested_schema.apply()
        def mock_function(**kwargs):
            return kwargs

        result = mock_function()

        # Traversal: global schema finds 'plot', then looks for 'contour' in plot_schema
        # plot_schema doesn't contain 'contour' -> schema_child becomes empty Schema()
        # Empty global schema -> falls back to init nested_schema (correct hierarchy)
        assert result["linewidth"] == 2.0
        assert result["color"] == "init"


def test_schema_apply_fallback_to_init_when_global_not_found():
    """Test apply falls back to init schema when global path not found."""
    init_schema = Schema(
        parent="nonexistent.path", linewidth=4.0, color="yellow", alpha=0.7
    )

    with mock.patch("earthkit.plots.schemas.schema") as mock_global:
        # Global schema doesn't have the path
        mock_global.get.return_value = None

        @init_schema.apply()
        def mock_function(**kwargs):
            return kwargs

        result = mock_function()

        # Should fall back to init schema values
        assert result["linewidth"] == 4.0
        assert result["color"] == "yellow"
        assert result["alpha"] == 0.7


def test_schema_apply_complete_hierarchy():
    """Test complete hierarchy: kwargs > global schema > init schema using schema.contour.apply()."""
    with mock.patch("earthkit.plots.schemas.schema") as mock_global:
        # Set up schema.contour with init values (set at decorator initialisation)
        init_contour = Schema(
            parent="contour",
            linewidth=1.0,  # init default
            color="blue",  # init default
            alpha=0.3,  # init default
        )

        # Global schema overrides some init values
        global_contour = Schema(
            parent="contour",
            linewidth=2.0,  # override init
            color="red",  # override init
            # alpha not set in global, will fall back to init
        )

        # Set schema.contour to init_contour (what the decorator sees)
        mock_global.contour = init_contour

        # But when _update_kwargs looks up parent="contour", it finds global_contour
        mock_global.__contains__ = lambda self, key: key == "contour"
        mock_global.get.return_value = global_contour
        mock_global.__getitem__ = (
            lambda self, key: global_contour if key == "contour" else None
        )

        # Use actual pattern: @schema.contour.apply()
        @mock_global.contour.apply()
        def mock_function(**kwargs):
            return kwargs

        # Call with explicit kwargs override
        result = mock_function(linewidth=5.0)  # explicit override

        # linewidth: explicit kwargs wins (highest priority)
        assert result["linewidth"] == 5.0
        # color: from global schema (middle priority)
        assert result["color"] == "red"
        # alpha: from init schema (lowest priority - fallback when not in global)
        assert result["alpha"] == 0.3


def test_schema_set_context_manager():
    """Test Schema.set() as context manager."""
    schema = Schema(linewidth=1.0, color="blue")

    assert schema.linewidth == 1.0
    assert schema.color == "blue"

    with schema.set(linewidth=2.0, color="red"):
        assert schema.linewidth == 2.0
        assert schema.color == "red"

    # Values should be restored after context
    assert schema.linewidth == 1.0
    assert schema.color == "blue"


def test_schema_set_context_manager_new_keys():
    """Test Schema.set() with new keys that don't exist."""
    schema = Schema(linewidth=1.0)

    assert "color" not in schema

    with schema.set(color="red"):
        assert schema.color == "red"

    # New keys should be removed after context
    assert "color" not in schema


def test_schema_set_context_manager_nested():
    """Test nested Schema.set() calls."""
    schema = Schema(linewidth=1.0)

    with schema.set(linewidth=2.0):
        assert schema.linewidth == 2.0

        with schema.set(linewidth=3.0):
            assert schema.linewidth == 3.0

        assert schema.linewidth == 2.0

    assert schema.linewidth == 1.0


def test_schema_get():
    """Test Schema.get() method."""
    schema = Schema(linewidth=2.0, color="red")
    assert schema.get("linewidth") == 2.0
    assert schema.get("color") == "red"


def test_schema_apply_with_args_passthrough():
    """Test that apply decorator passes through positional args."""
    schema = Schema(parent="test", linewidth=2.0)

    @schema.apply()
    def mock_function(arg1, arg2, **kwargs):
        return {"arg1": arg1, "arg2": arg2, "kwargs": kwargs}

    result = mock_function("value1", "value2", color="red")

    assert result["arg1"] == "value1"
    assert result["arg2"] == "value2"
    assert result["kwargs"]["linewidth"] == 2.0
    assert result["kwargs"]["color"] == "red"


def test_schema_protected_keys_not_in_dict():
    """Test that protected keys like _parent are not in _to_dict output."""
    schema = Schema(parent="test", linewidth=2.0, color="red")
    result = schema._to_dict()

    assert "_parent" not in result
    assert "linewidth" in result
    assert "color" in result


def test_schema_apply_empty_schema():
    """Test apply with empty schema."""
    schema = Schema(parent="empty")

    @schema.apply()
    def mock_function(**kwargs):
        return kwargs

    result = mock_function(linewidth=2.0, color="red")

    # Should only have passed kwargs
    assert result["linewidth"] == 2.0
    assert result["color"] == "red"
