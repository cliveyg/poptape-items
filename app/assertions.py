import os.path
import json
from jsonschema import validate, Draft7Validator
from jsonschema.exceptions import ValidationError as JsonValidationError

def assert_valid_schema(data, schema_type):
    # checks whether the given data matches the schema

    if schema_type == 'item':
        schema = _load_json_schema('schemas/item.json')
    elif schema_type == 'bulk_items':
        schema = _load_json_schema('schemas/items_array.json')

    return validate(data, schema, format_checker=Draft7Validator.FORMAT_CHECKER)


def _load_json_schema(filename):
    # loads the given schema file
    filepath = os.path.join(os.path.dirname(__file__), filename)

    with open(filepath) as schema_file:
        return json.loads(schema_file.read())
