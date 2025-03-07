import copy
import os
import tempfile

import pytest
import yaml

import earthkit.plots as ekp


def create_temp_schema(temp_dir, schema):

    schema_file_path = os.path.join(temp_dir, "schema.yml")
    print(schema)
    with open(schema_file_path, "w") as schema_file:
        yaml.dump(schema, schema_file)

    os.makedirs(os.path.join(temp_dir, "styles"))
    os.makedirs(os.path.join(temp_dir, "identities"))

    return temp_dir


def test_default_schema():

    old_schema = copy.deepcopy(ekp.schema)
    print(old_schema)
    new_schema = ekp.schema
    new_schema.reset()
    print(new_schema)

    assert old_schema == new_schema


def test_add_schema():
    schema_1 = {"foo": "bar", "key": "val"}
    schema_1_dir = create_temp_schema(tempfile.mkdtemp(), schema_1)

    schema_2 = {"foo": "bar2", "other_key": "other_val"}
    schema_2_dir = create_temp_schema(tempfile.mkdtemp(), schema_2)

    with pytest.raises(AttributeError):
        ekp.schema.get("foo")

    ekp.schema.add(schema_1_dir)
    print(ekp.schema["foo"])
    assert ekp.schema["foo"] == "bar"
    assert ekp.schema["key"] == "val"

    with ekp.schema.add(schema_2_dir):
        print(ekp.schema["foo"])
        assert ekp.schema["foo"] == "bar2"
        assert ekp.schema["key"] == "val"
        assert ekp.schema["other_key"] == "other_val"

    assert ekp.schema["foo"] == "bar"
    assert ekp.schema["key"] == "val"
    with pytest.raises(AttributeError):
        ekp.schema.get("other_key")

    ekp.schema.reset()


def test_use_schema():

    schema_1 = {"foo": "bar", "key": "val"}
    schema_1_dir = create_temp_schema(tempfile.mkdtemp(), schema_1)

    schema_2 = {"foo": "bar2", "other_key": "other_val"}
    schema_2_dir = create_temp_schema(tempfile.mkdtemp(), schema_2)

    with pytest.raises(AttributeError):
        ekp.schema.get("foo")

    ekp.schema.use(schema_1_dir)
    print(ekp.schema["foo"])
    assert ekp.schema["foo"] == "bar"

    with ekp.schema.use(schema_2_dir):
        print(ekp.schema["foo"])
        assert ekp.schema["foo"] == "bar2"
        assert ekp.schema["other_key"] == "other_val"
        with pytest.raises(AttributeError):
            ekp.schema.get("key")

    print(ekp.schema["foo"])
    assert ekp.schema["foo"] == "bar"
