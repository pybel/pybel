# -*- coding: utf-8 -*-

"""

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

from six.moves.cPickle import load
import warnings

__all__ = [
    'from_indra_statements',
    'from_indra_pickle',
    'to_indra',
    'from_biopax',
]


def from_indra_statements(statements, name=None, version=None, description=None):
    """Imports a model from :mod:`indra`.

    :param list[indra.statements.Statement] statements: A list of statements
    :param str name: The name for the BEL graph
    :param str version: The version of the BEL graph
    :param str description: The description of the BEL graph
    :rtype: pybel.BELGraph
    """
    from indra.assemblers import PybelAssembler

    pba = PybelAssembler(
        stmts=statements,
        name=name,
        version=version,
        description=description
    )

    graph = pba.make_model()

    return graph


def from_indra_pickle(path, name=None, version=None, description=None):
    """Imports a model from :mod:`indra`.

    :param str path: Path to pickled list of :class:`indra.statements.Statement`
    :param str name: The name for the BEL graph
    :param str version: The version of the BEL graph
    :param str description: The description of the BEL graph
    :rtype: pybel.BELGraph
    """
    with open(path, 'rb') as f:
        statements = load(f)

    return from_indra_statements(
        statements=statements,
        name=name,
        version=version,
        description=description
    )


def to_indra(graph):
    """Exports this graph as a list of INDRA statements using `indra.sources.pybel.PybelProcessor`

    :param pybel.BELGraph graph: A BEL graph
    :rtype: list[indra.statements.Statement]

    .. warning:: Not fully implemented yet! Needs the pybel_client branch of sorgerlab/indra
    """
    warnings.warn('export to INDRA is not yet complete')
    from indra.sources.pybel import PybelProcessor

    pbp = PybelProcessor(graph)
    pbp.get_statements()
    return pbp.statements


def from_biopax(path, name=None, version=None, description=None):
    """Imports a model encoded in `BioPAX <http://www.biopax.org/>`_ via :mod:`indra`.

    :param str path: Path to a BioPAX OWL file
    :param str name: The name for the BEL graph
    :param str version: The version of the BEL graph
    :param str description: The description of the BEL graph
    :rtype: pybel.BELGraph
    """
    from indra.sources.biopax.biopax_api import process_owl

    model = process_owl(path)

    return from_indra_statements(
        statements=model.statements,
        name=name,
        version=version,
        description=description
    )
