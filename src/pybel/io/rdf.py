# -*- coding: utf-8 -*-

"""Conversion of BEL to RDF."""

import logging

import rdflib
from rdflib import BNode, Literal, Namespace, RDF, RDFS
from tqdm import tqdm

from pybel import constants as pc
from pybel.canonicalize import edge_to_bel
from pybel.dsl import BaseConcept, BaseEntity, CentralDogma, EntityVariant, FusionBase, ListAbundance, Reaction, Variant
from pybel.language import Entity
from pybel.struct.graph import BELGraph
from pybel.typing import EdgeData

__all__ = [
    'to_rdf',
    'to_rdflib',
]

logger = logging.getLogger(__name__)

BELS = Namespace("https://biological-expression-language.github.io/schema#")

FUNCTION_TO_BELS = {
    f: BELS[f.lower()]
    for f in pc.PYBEL_NODE_FUNCTIONS
}

VARIANT_TO_BELS = {
    f: BELS[f.lower()]
    for f in pc.PYBEL_VARIANT_KINDS
}

RELATION_TO_BELS = {
    f: BELS[f]
    for f in pc.RELATIONS
}


def to_rdf(graph: BELGraph, destination, fmt: str = 'turtle'):
    """Serialize a BEL graph to RDF.

    :param graph: A BEL graph
    :param destination: The
    :param fmt: One of "xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig" and "nquads" based on
     the ones available from :meth:`rdflib.Graph.serialize`.
    """
    r = to_rdflib(graph)
    r.serialize(destination=destination, format=fmt)


def to_rdflib(graph: BELGraph, use_tqdm: bool = True) -> rdflib.Graph:
    """"Convert a BEL graph to RDF in a :class:`rdflib.Graph`."""
    g = rdflib.Graph()
    g.namespace_manager.bind('bels', BELS)

    # This node represents the graph
    graph_node = BNode()
    g.add((graph_node, RDF.type, BELS.graph))
    g.add((graph_node, RDFS.label, Literal(graph.name)))

    it = graph.edges(keys=True, data=True)
    if use_tqdm:
        it = tqdm(it, desc='converting to RDF')

    nodes = {
        node: _add_node(g, node)
        for node in graph
    }

    for u, v, k, d in it:
        edge_bnode = _add_edge(g, u, v, k, d)
        g.add((graph_node, BELS.edge, edge_bnode))
        g.add((edge_bnode, BELS.source, nodes[u]))
        g.add((edge_bnode, BELS.target, nodes[v]))
    return g


def _add_edge(g: rdflib.Graph, u: BaseEntity, v: BaseEntity, k: str, d: EdgeData) -> BNode:
    rv = BNode()
    g.add((rv, RDF.type, BELS.edge))
    g.add((rv, RDFS.label, Literal(edge_to_bel(u, v, d))))
    g.add((rv, BELS.edgehash, Literal(k)))
    _add_data(g, rv, d)
    return rv


def _add_data(g: rdflib, edge: BNode, edge_data: EdgeData):
    g.add((edge, BELS.relation, RELATION_TO_BELS[edge_data[pc.RELATION]]))
    for key, side_predicate in ((pc.SUBJECT, BELS.subject_modifier), (pc.OBJECT, BELS.object_modifier)):
        side_data = edge_data.get(key)
        if side_data is None:
            continue
        # side_node = _add_side_data(g, edge, side_data)
        # g.add((edge, side_predicate, side_node))


def _add_side_data(g, edge: BNode, side_data) -> BNode:
    pass


def _add_node(g: rdflib.Graph, u: BaseEntity) -> BNode:
    rv = BNode()
    g.add((rv, RDF.type, FUNCTION_TO_BELS[u.function]))
    g.add((rv, BELS.nodehash, Literal(u.md5)))
    g.add((rv, RDFS.label, Literal(u.as_bel())))

    if isinstance(u, BaseConcept):
        _add_entity(g, rv, u.entity)

    if isinstance(u, CentralDogma) and u.variants:
        for variant in u.variants:
            variant_bnode = _add_variant(g, variant)
            g.add((rv, BELS.variant, variant_bnode))

    if isinstance(u, ListAbundance):
        for member in u.members:
            member_bnode = _add_node(g, member)
            g.add((member_bnode, BELS[pc.PART_OF], rv))
            g.add((rv, BELS.hasPart, member_bnode))
    if isinstance(u, Reaction):
        for reactant in u.reactants:
            reactant_bnode = _add_node(g, reactant)
            g.add((rv, BELS[pc.HAS_REACTANT], reactant_bnode))
            g.add((reactant_bnode, BELS.reactantOf, rv))
        for product in u.products:
            product_bnode = _add_node(g, product)
            g.add((rv, BELS[pc.HAS_PRODUCT], product_bnode))
            g.add((product_bnode, BELS.productOf, rv))
    if isinstance(u, FusionBase):
        pass  # FIXME

    return rv


def _add_entity(g: rdflib.Graph, rv: BNode, entity: Entity):
    g.add((rv, BELS.prefix, Literal(entity.namespace)))
    g.add((rv, BELS.identifier, Literal(entity.identifier)))
    g.add((rv, BELS.name, Literal(entity.name)))


def _add_variant(g: rdflib.Graph, variant: Variant) -> BNode:
    rv = BNode()
    g.add((rv, RDFS.label, Literal(variant.as_bel())))
    g.add((rv, RDF.type, VARIANT_TO_BELS[variant[pc.KIND]]))

    if isinstance(variant, EntityVariant):
        _add_entity(g, rv, variant.entity)
    logger.warning('unhandled variant')

    return rv
