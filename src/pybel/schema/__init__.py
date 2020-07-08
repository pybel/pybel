# -*- coding: utf-8 -*-

"""Validation for PyBEL data.

The :mod:`pybel.schema` module houses functions to verify the format of a given node or edge.
Its inclusion will help ensure that all PyBEL data is stored in a consistent and
clearly defined manner across the repository.
"""

import json
import logging
import os
import pathlib
from typing import Any, Mapping, Optional, Tuple

import jsonschema

__all__ = ['is_valid_node', 'is_valid_edge']

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))

NODE_FILENAME = "base_node.schema.json"
EDGE_FILENAME = "edge.schema.json"

# To use schemas from other files, jsonschema needs to know where the references point to, so
# create a resolver that directs any references (like "entity.schema.json") to the schema's dir
schema_uri = pathlib.PurePath(__file__).as_uri()
RESOLVER = jsonschema.RefResolver(base_uri=schema_uri, referrer=__file__)


def _build_validator(filename: str) -> jsonschema.Draft7Validator:
    """
    Return a validator that checks against a given schema.

    :param filename: The relative path to the schema, e.g. "base_node.schema.json"
    """
    path = os.path.join(HERE, filename)
    with open(path) as json_schema:
        schema = json.load(json_schema)
    return jsonschema.Draft7Validator(schema, resolver=RESOLVER)


def _validate(validator: jsonschema.Draft7Validator, entity: Mapping[str, Any]) -> bool:
    """
    Determine whether a given entity is valid based on its JSON schema.

    :param input: A dict representing a PyBEL entity.
    :return: if the input is valid
    """
    try:
        validator.validate(entity)
        return True
    except jsonschema.exceptions.ValidationError as err:
        logger.info(err)
        return False


node_validator = _build_validator(NODE_FILENAME)
edge_validator = _build_validator(EDGE_FILENAME)


def is_valid_node(node: Mapping[str, Any]) -> bool:
    """
    Determine whether a given node is valid based on the node's JSON schema.

    :param node: A dict representing a PyBEL node.
    :return: if the node is valid
    """
    return _validate(node_validator, node)


def is_valid_edge(edge: Mapping[str, Any]) -> bool:
    """
    Determine whether a given edge is valid based on the edge's JSON schema.

    :param node: A dict representing an edge between two PyBEL nodes.
    :return: if the edge is valid
    """
    return _validate(edge_validator, edge)
