import os

from typing import Mapping, Any, Optional, Tuple

import json
import jsonschema

HERE = os.path.abspath(os.path.dirname(__file__))

def _load_schema(filename: str) -> Mapping[str, Any]:
    """
    Load a schema from its filename.

    :param filename: The relative path to the schema including the extension, e.g. "variant.schema.json"
    """
    path = os.path.join(HERE, filename)
    with open(path) as json_schema:
        schema = json.load(json_schema)
    return schema

def _validator(filename: str) -> jsonschema.Draft7Validator:
    """
    Return a validator that checks against a given schema.

    :param filename: The relative path to the schema including the extension, e.g. "variant.schema.json"
    """
    schema = _load_schema(filename)
    # In order to use schemas from other files, jsonschema needs to know where the references point to
    # So, create a resolver that directs any references (like "fusion.schema.json") to the schemas directory
    resolver = jsonschema.RefResolver(base_uri = 'file://' + HERE + "/", referrer = __file__)
    return jsonschema.Draft7Validator(schema, resolver=resolver)

def _get_schema(node: Mapping[str, Any]) -> Tuple[str, bool]:
    """
    Get the filename for the appropriate schema for a given node.
    
    :return: The filename for the schema and an error bool. """
    err = False
    filename = ""
    # Check if the node is a subclass of FusionBase
    if 'fusion' in node.keys():
        filename = 'fusion.schema.json'
    # Check if the "function" is present (if not, the node is invalid)
    elif 'function' in node.keys():
        if node['function'] == 'Reaction':
            filename = 'reaction.schema.json'
        elif node['function'] in ['Complex', 'Composite']:
            filename = 'list_abundance.schema.json'
        else:
            filename = 'base_abundance.schema.json'
    else:
        err = True
    return filename, err
def is_valid_node(node: Mapping[str, Any]) -> bool:
    """
    Determine whether a given node is valid based on the node's JSON schema.

    :param node: A dict representing a PyBEL node.
    :return: if the node is valid
    """
    filename, err = _get_schema(node)
    if err: return False
    try:
        _validator(filename).validate(node)
        return True
    except jsonschema.ValidationError as err:
        print(err)
        return False