# -*- coding: utf-8 -*-

"""Validation for PyBEL data."""

import json
import logging
import os
import pathlib
from typing import Any, Mapping, Optional, Tuple

import jsonschema

__all__ = ['is_valid_node']

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))
SCHEMA_PATH = os.path.join(HERE, "node.schema.json")

# Load the top level schema
with open(SCHEMA_PATH) as json_schema:
    SCHEMA = json.load(json_schema)

# To use schemas from other files, jsonschema needs to know where the references point to, so
# create a resolver that directs any references (like "fusion.schema.json") to the schema's dir
schema_uri = pathlib.PurePath(__file__).as_uri()
resolver = jsonschema.RefResolver(base_uri=schema_uri, referrer=__file__)
# Define a validator that checks against the top-level schema
validator = jsonschema.Draft7Validator(SCHEMA, resolver=resolver)


def is_valid_node(node: Mapping[str, Any]) -> bool:
    """
    Determine whether a given node is valid based on the node's JSON schema.

    :param node: A dict representing a PyBEL node.
    :return: if the node is valid
    """
    try:
        validator.validate(node)
        return True
    except jsonschema.exceptions.ValidationError as err:
        logger.info(err)
        return False
