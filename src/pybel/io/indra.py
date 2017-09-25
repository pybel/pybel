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

"""

from six.moves.cPickle import load


def from_indra(path, name=None, version=None, description=None):
    """Imports a model from INDRA.

    :param str path: Path to pickled list of :class:`indra.statements.Statement`
    :param str name: The name for the BEL graph
    :param str version: The version of the BEL graph
    :param str description: The description of the BEL graph
    :rtype: pybel.BELGraph
    """
    from indra.assemblers import PybelAssembler

    with open(path) as f:
        statments = load(f)

    pba = PybelAssembler(
        stmts=statments,
        name=name,
        version=version,
        description=description
    )

    graph = pba.make_model()

    return graph


def to_indra(graph):
    """Exports this graph as a list of INDRA statements.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: list[indra.statements.Statement]

    .. warning:: Not implemented yet!
    """
    raise NotImplementedError
