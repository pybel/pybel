# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with INDRA.

After assembling a model with `INDRA <https://github.com/sorgerlab/indra>`_, a list of
:class:`indra.statements.Statement` can be converted to a :class:`pybel.BELGraph` with
:class:`indra.assemblers.pybel.PybelAssembler`.

.. code-block:: python

    from indra.assemblers.pybel import PybelAssembler
    import pybel

    stmts = [
        # A list of INDRA statements
    ]

    pba = PybelAssembler(
        stmts,
        name='Graph Name',
        version='0.0.1',
        description='Graph Description'
    )
    graph = pba.make_model()

    # Write to BEL file
    pybel.to_bel_path(belgraph, 'simple_pybel.bel')

.. warning::

    These functions are hard to unit test because they rely on a whole set of java dependencies and will likely
    not be for a while.
"""

import json
from pickle import load
from typing import Any, List, Mapping, Optional, TextIO, Union

from networkx.utils import open_file

__all__ = [
    'from_indra_statements',
    'from_indra_statements_json',
    'from_indra_statements_json_file',
    'from_indra_pickle',
    'to_indra_statements',
    'to_indra_statements_json',
    'to_indra_statements_json_file',
    'from_biopax',
]


def from_indra_statements(
    stmts,
    name: Optional[str] = None,
    version: Optional[str] = None,
    description: Optional[str] = None,
    authors: Optional[str] = None,
    contact: Optional[str] = None,
    license: Optional[str] = None,
    copyright: Optional[str] = None,
    disclaimer: Optional[str] = None,
):
    """Import a model from :mod:`indra`.

    :param List[indra.statements.Statement] stmts: A list of statements
    :param name: The graph's name
    :param version: The graph's version. Recommended to use `semantic versioning <http://semver.org/>`_ or
                        ``YYYYMMDD`` format.
    :param description: The description of the graph
    :param authors: The authors of this graph
    :param contact: The contact email for this graph
    :param license: The license for this graph
    :param copyright: The copyright for this graph
    :param disclaimer: The disclaimer for this graph
    :rtype: pybel.BELGraph
    """
    from indra.assemblers.pybel import PybelAssembler

    pba = PybelAssembler(
        stmts=stmts,
        name=name,
        version=version,
        description=description,
        authors=authors,
        contact=contact,
        license=license,
        copyright=copyright,
        disclaimer=disclaimer,
    )

    graph = pba.make_model()
    return graph


def from_indra_statements_json(stmts_json: List[Mapping[str, Any]], **kwargs):
    """Get a BEL graph from INDRA statements JSON.

    :rtype: BELGraph

    Other kwargs are passed to :func:`from_indra_statements`.
    """
    from indra.statements import stmts_from_json
    statements = stmts_from_json(stmts_json)
    return from_indra_statements(statements, **kwargs)


@open_file(0, mode='r')
def from_indra_statements_json_file(file, **kwargs):
    """Get a BEL graph from INDRA statements JSON file.

    :rtype: BELGraph

    Other kwargs are passed to :func:`from_indra_statements`.
    """
    return from_indra_statements_json(json.load(file), **kwargs)


def from_indra_pickle(path: str, **kwargs):
    """Import a model from :mod:`indra`.

    :param path: Path to pickled list of :class:`indra.statements.Statement`
    :rtype: pybel.BELGraph

    Other kwargs are passed to :func:`from_indra_statements`.
    """
    with open(path, 'rb') as f:
        statements = load(f)

    return from_indra_statements(stmts=statements, **kwargs)


def to_indra_statements(graph):
    """Export this graph as a list of INDRA statements using the :py:class:`indra.sources.pybel.PybelProcessor`.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: list[indra.statements.Statement]
    """
    from indra.sources.bel import process_pybel_graph

    pbp = process_pybel_graph(graph)
    return pbp.statements


def to_indra_statements_json(graph) -> List[Mapping[str, Any]]:
    """Export this graph as INDRA JSON list.

    :param pybel.BELGraph graph: A BEL graph
    """
    return [
        statement.to_json()
        for statement in to_indra_statements(graph)
    ]


@open_file(1, mode='w')
def to_indra_statements_json_file(graph, path: Union[str, TextIO], indent: Optional[int] = 2, **kwargs):
    """Export this graph as INDRA statement JSON.

    :param pybel.BELGraph graph: A BEL graph
    :param path: A writable file or file-like

    Other kwargs are passed to :func:`json.dump`.
    """
    json.dump(to_indra_statements_json(graph), path, indent=indent, **kwargs)


def from_biopax(path: str, **kwargs):
    """Import a model encoded in Pathway Commons `BioPAX <http://www.biopax.org/>`_ via :mod:`indra`.

    :param path: Path to a BioPAX OWL file
    :rtype: pybel.BELGraph

    Other kwargs are passed to :func:`from_indra_statements`.

    .. warning:: Not compatible with all BioPAX! See INDRA documentation.
    """
    from indra.sources.biopax import process_owl

    model = process_owl(path)
    return from_indra_statements(stmts=model.statements, **kwargs)
