# -*- coding: utf-8 -*-

"""Validation for PyBEL data."""

import json
import os

import jsonschema

__all__ = [
    'validate_node',
]

HERE = os.path.abspath(os.path.dirname(__file__))
NODES_SCHEMA_PATH = os.path.join(HERE, 'nodes.schema.json')

with open(NODES_SCHEMA_PATH) as file:
    NODES_SCHEMA = json.load(file)


def validate_node(node):
    """Validate against the JSON Schema for PyBEL nodes."""
    try:
        jsonschema.validate(node, NODES_SCHEMA)
    except jsonschema.ValidationError:
        return False
    else:
        return True
