# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with INDRA.

After assembling a model with `INDRA <https://github.com/sorgerlab/indra>`_, a list of
:class:`indra.statements.Statement` can be converted to a :class:`pybel.BELGraph` with
:class:`indra.assemblers.PybelAssembler`.

.. code-block:: python

    from indra.assemblers import PybelAssembler
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

import warnings
from six.moves.cPickle import load

__all__ = [
    'from_indra_statements',
    'from_indra_pickle',
    'to_indra_statements',
    'from_biopax',
]


def from_indra_statements(stmts, name=None, version=None, description=None, authors=None, contact=None, license=None,
                          copyright=None, disclaimer=None):
    """Import a model from :mod:`indra`.

    :param list[indra.statements.Statement] stmts: A list of statements
    :param str name: The graph's name
    :param str version: The graph's version. Recommended to use `semantic versioning <http://semver.org/>`_ or
                        ``YYYYMMDD`` format.
    :param str description: A description of the graph
    :param str authors: The authors of this graph
    :param str contact: The contact email for this graph
    :param str license: The license for this graph
    :param str copyright: The copyright for this graph
    :param str disclaimer: The disclaimer for this graph
    :rtype: pybel.BELGraph
    """
    from indra.assemblers import PybelAssembler

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


def from_indra_pickle(path, name=None, version=None, description=None):
    """Import a model from :mod:`indra`.

    :param str path: Path to pickled list of :class:`indra.statements.Statement`
    :param str name: The name for the BEL graph
    :param str version: The version of the BEL graph
    :param str description: The description of the BEL graph
    :rtype: pybel.BELGraph
    """
    with open(path, 'rb') as f:
        statements = load(f)

    return from_indra_statements(
        stmts=statements,
        name=name,
        version=version,
        description=description
    )


def to_indra_statements(graph):
    """Export this graph as a list of INDRA statements using `indra.sources.pybel.PybelProcessor`.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: list[indra.statements.Statement]


    """
    warnings.warn('export to INDRA is not yet complete')
    from indra.sources.bel import process_pybel_graph

    pbp = process_pybel_graph(graph)
    return pbp.statements


def from_biopax(path, name=None, version=None, description=None):
    """Import a model encoded in Pathway Commons `BioPAX <http://www.biopax.org/>`_ via :mod:`indra`.

    :param str path: Path to a BioPAX OWL file
    :param str name: The name for the BEL graph
    :param str version: The version of the BEL graph
    :param str description: The description of the BEL graph
    :rtype: pybel.BELGraph

    .. warning:: Not compatible with all BioPAX! See INDRA documentation.
    """
    from indra.sources.biopax.biopax_api import process_owl

    model = process_owl(path)

    return from_indra_statements(
        stmts=model.statements,
        name=name,
        version=version,
        description=description
    )
