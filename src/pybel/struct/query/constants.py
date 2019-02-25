# -*- coding: utf-8 -*-

"""Constants for the query builder."""

#: Induce a subgraph over the given nodes
SEED_TYPE_INDUCTION = 'induction'
#: Induce a subgraph over the given nodes and expand to their first neighbors
SEED_TYPE_NEIGHBORS = 'neighbors'
#: Induce a subgraph over the given nodes and expand to their second neighbors
SEED_TYPE_DOUBLE_NEIGHBORS = 'dneighbors'
#: Induce a subgraph over the nodes in all shortest paths between the given nodes
SEED_TYPE_PATHS = 'shortest_paths'
#: Induce a subgraph over the edges provided by the given authors and their neighboring nodes
SEED_TYPE_AUTHOR = 'authors'
#: Induce a subgraph over the edges provided by the given citations and their neighboring nodes
SEED_TYPE_PUBMED = 'pubmed'
#: Generate an upstream candidate mechanism
SEED_TYPE_UPSTREAM = 'upstream'
#: Generate a downstream candidate mechanism
SEED_TYPE_DOWNSTREAM = 'downstream'
#: Induce a subgraph over the edges matching the given annotations
SEED_TYPE_ANNOTATION = 'annotation'
#: Induce a subgraph over a random set of (hopefully) connected edges
SEED_TYPE_SAMPLE = 'sample'

#: A set of the allowed seed type strings, as defined above
SEED_TYPES = {
    SEED_TYPE_INDUCTION,
    SEED_TYPE_NEIGHBORS,
    SEED_TYPE_DOUBLE_NEIGHBORS,
    SEED_TYPE_PATHS,
    SEED_TYPE_UPSTREAM,
    SEED_TYPE_DOWNSTREAM,
    SEED_TYPE_PUBMED,
    SEED_TYPE_AUTHOR,
    SEED_TYPE_ANNOTATION,
    SEED_TYPE_SAMPLE,
}

#: Seed types that don't take node lists as their arguments
NONNODE_SEED_TYPES = {
    SEED_TYPE_ANNOTATION,
    SEED_TYPE_AUTHOR,
    SEED_TYPE_PUBMED,
    SEED_TYPE_SAMPLE,
}

NODE_SEED_TYPES = SEED_TYPES - NONNODE_SEED_TYPES
