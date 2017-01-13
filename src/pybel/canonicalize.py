from __future__ import print_function

import itertools as itt
import sys
from operator import itemgetter

from .parser import language
from .parser.language import rev_activity_labels, inv_document_keys
from .parser.utils import ensure_quotes
from .constants import GOCC_LATEST

__all__ = ['to_bel']

# TODO extract from .parse_control
CITATION_ENTRIES = 'type', 'name', 'reference', 'date', 'authors', 'comments'

BLACKLIST_EDGE_ATTRIBUTES = {'relation', 'subject', 'object', 'citation', 'SupportingText'}

variant_parent_dict = {
    'GeneVariant': 'g',
    'RNAVariant': 'r',
    'ProteinVariant': 'p'
}

fusion_parent_dict = {
    'GeneFusion': 'g',
    'RNAFusion': 'r',
    'ProteinFusion': 'p'
}


def get_neighbors_by_path_type(g, v, relation):
    """Gets the set of neighbors of a given node that have a relation of the given type

    :param g: A BEL network
    :type g: :class:`pybel.BELGraph`
    :param v: a node from the BEL network
    :param relation: the relation to follow from the given node
    :return:
    """
    result = []
    for neighbor in g.edge[v]:
        for data in g.edge[v][neighbor].values():
            if data['relation'] == relation:
                result.append(neighbor)
    return set(result)


def postpend_location(s, location_model):
    """Rips off the closing parentheses and adds canonicalized modification.

    I did this because writing a whole new parsing model for the data would be sad and difficult

    :param s:
    :type s: BEL string representing node
    :param location_model:
    :return:
    """

    if all(k in location_model for k in {'namespace', 'name'}):
        return "loc({}:{})".format(location_model['namespace'], ensure_quotes(location_model['name']))
    raise ValueError('Location model missing namespace and/or name keys: {}'.format(location_model))


def decanonicalize_variant(tokens):
    if tokens[0] == 'ProteinModification':
        if isinstance(tokens[1], str):
            return 'pmod({})'.format(', '.join(map(str, tokens[1:])))
        return 'pmod({}:{}{})'.format(tokens[1][0], tokens[1][1], ''.join(', {}'.format(t) for t in tokens[2:]))
    elif tokens[0] == 'Variant':
        return 'var({})'.format(''.join(map(str, tokens[1:])))
    elif tokens[0] == 'Fragment':
        if '?' == tokens[1] and len(tokens) == 2:
            return 'frag(?)'
        elif '?' == tokens[1] and len(tokens) == 3:  # has description
            return 'frag(?, {})'.format(tokens[2])
        elif len(tokens) == 4:
            return 'frag({})'.format(''.join(map(str, tokens[1:])))
        else:
            return 'frag({}, {})'.format(''.join(map(str, tokens[1:])), tokens[-1])
    elif tokens[0] == 'GeneModification':
        return 'gmod({})'.format(tokens[1])
    else:
        raise ValueError('Invalid variant: {}'.format(tokens))


def decanonicalize_fusion_range(tokens):
    if '?' == tokens[0]:
        return '?'
    return '{}.{}_{}'.format(tokens[0], tokens[1], tokens[2])


def decanonicalize_node(g, v):
    """Returns a node from a graph as a BEL string

    :param g: a BEL network
    :type g: :class:`pybel.BELGraph`
    :param v: a node from the BEL graph
    """
    tokens = g.node[v]

    if tokens['type'] == 'Reaction':
        reactants = get_neighbors_by_path_type(g, v, 'hasReactant')
        reactants_canon = map(lambda n: decanonicalize_node(g, n), sorted(reactants))
        products = get_neighbors_by_path_type(g, v, 'hasProduct')
        products_canon = map(lambda n: decanonicalize_node(g, n), sorted(products))
        return 'rxn(reactants({}), products({}))'.format(', '.join(reactants_canon), ', '.join(products_canon))

    if tokens['type'] in ('Composite', 'Complex') and 'namespace' not in tokens:
        members_canon = map(lambda n: decanonicalize_node(g, n), v[1:])
        return '{}({})'.format(language.rev_abundance_labels[tokens['type']], ', '.join(members_canon))

    if 'type' in tokens and 'variants' in tokens:
        variants = ', '.join(map(decanonicalize_variant, sorted(tokens['variants'])))
        return "{}({}:{}, {})".format(variant_parent_dict[tokens['type']],
                                      tokens['namespace'],
                                      ensure_quotes(tokens['name']),
                                      variants)

    if tokens['type'] in ('Gene', 'RNA', 'miRNA', 'Protein', 'Abundance', 'Complex', 'Pathology', 'BiologicalProcess'):
        return "{}({}:{})".format(language.rev_abundance_labels[tokens['type']], tokens['namespace'],
                                  ensure_quotes(tokens['name']))

    if tokens['type'].endswith('Fusion'):
        return "{}(fus({}:{}, {}, {}:{}, {}))".format(
            fusion_parent_dict[tokens['type']],
            tokens['partner_5p']['namespace'],
            tokens['partner_5p']['name'],
            decanonicalize_fusion_range(tokens['range_5p']),
            tokens['partner_3p']['namespace'],
            tokens['partner_3p']['name'],
            decanonicalize_fusion_range(tokens['range_3p'])
        )

    raise ValueError('Unknown node data: {} {}'.format(v, tokens))


def decanonicalize_edge_node(g, node, edge_data, node_position):
    node_str = decanonicalize_node(g, node)

    if node_position not in edge_data:
        return node_str

    node_edge_data = edge_data[node_position]

    if 'location' in node_edge_data:
        node_str = postpend_location(node_str, node_edge_data['location'])

    if 'modifier' in node_edge_data and 'Degradation' == node_edge_data['modifier']:
        node_str = "deg({})".format(node_str)
    elif 'modifier' in node_edge_data and 'Activity' == node_edge_data['modifier']:
        node_str = "act({}".format(node_str)
        # switch missing, default, and dict
        if 'effect' in node_edge_data and 'MolecularActivity' in node_edge_data['effect']:
            ma = node_edge_data['effect']['MolecularActivity']

            if isinstance(ma, str):
                node_str = "{}, ma({}))".format(node_str, rev_activity_labels[ma])
            elif isinstance(ma, dict):
                node_str = "{}, ma({}:{}))".format(node_str, ma['namespace'], ensure_quotes(ma['name']))
        else:
            node_str = "{})".format(node_str)

    elif 'modifier' in node_edge_data and 'Translocation' == node_edge_data['modifier']:
        fromLoc = "fromLoc("
        toLoc = "toLoc("

        if not isinstance(node_edge_data['effect']['fromLoc'], dict):
            raise ValueError()

        fromLoc += "{}:{})".format(node_edge_data['effect']['fromLoc']['namespace'],
                                   ensure_quotes(node_edge_data['effect']['fromLoc']['name']))

        if not isinstance(node_edge_data['effect']['toLoc'], dict):
            raise ValueError()

        toLoc += "{}:{})".format(node_edge_data['effect']['toLoc']['namespace'],
                                 ensure_quotes(node_edge_data['effect']['toLoc']['name']))

        node_str = "tloc({}, {}, {})".format(node_str, fromLoc, toLoc)

    return node_str


def decanonicalize_edge(g, u, v, k):
    """Takes two nodes and gives back a BEL string representing the statement

    :param g: A BEL graph
    :type g: :class:`BELGraph`
    :param u: The edge's source node
    :param v: The edge's target node
    :param k: The edge's key
    :return: The canonical BEL for this edge
    :rtype: str
    """

    ed = g.edge[u][v][k]

    u_str = decanonicalize_edge_node(g, u, ed, node_position='subject')
    v_str = decanonicalize_edge_node(g, v, ed, node_position='object')

    return "{} {} {}".format(u_str, ed['relation'], v_str)


def flatten_citation(citation):
    return ','.join('"{}"'.format(citation[x]) for x in CITATION_ENTRIES[:len(citation)])


def sort_edges(d):
    return (flatten_citation(d['citation']), d['SupportingText']) + tuple(
        itt.chain.from_iterable(
            (k, v) for k, v in sorted(d.items(), key=itemgetter(0)) if k not in BLACKLIST_EDGE_ATTRIBUTES))


def to_bel(graph, file=sys.stdout):
    """Outputs the BEL graph as a canonical BEL Script (.bel)

    :param graph: the BEL Graph to output as a BEL Script
    :type graph: BELGraph
    :param file: a filelike object
    :type file: file
    """
    for k in sorted(graph.document):
        print('SET DOCUMENT {} = "{}"'.format(inv_document_keys[k], graph.document[k]), file=file)

    print('###############################################\n', file=file)

    if 'GOCC' not in graph.namespace_url:
        graph.namespace_url['GOCC'] = GOCC_LATEST

    for namespace, url in sorted(graph.namespace_url.items(), key=itemgetter(0)):
        print('DEFINE NAMESPACE {} AS URL "{}"'.format(namespace, url), file=file)

    for namespace, url in sorted(graph.namespace_owl.items(), key=itemgetter(0)):
        print('DEFINE NAMESPACE {} AS OWL "{}"'.format(namespace, url), file=file)

    print('###############################################\n', file=file)

    for annotation, url in sorted(graph.annotation_url.items(), key=itemgetter(0)):
        print('DEFINE ANNOTATION {} AS URL "{}"'.format(annotation, url), file=file)

    for annotation, an_list in sorted(graph.annotation_list.items(), key=itemgetter(0)):
        an_list_str = ', '.join('"{}"'.format(e) for e in an_list)
        print('DEFINE ANNOTATION {} AS LIST {{{}}}'.format(annotation, an_list_str), file=file)

    print('###############################################\n', file=file)

    # sort by citation, then supporting text
    qualified_edges = filter(lambda u_v_k_d: 'citation' in u_v_k_d[3] and 'SupportingText' in u_v_k_d[3],
                             graph.edges_iter(data=True, keys=True))
    qualified_edges = sorted(qualified_edges, key=lambda u_v_k_d: sort_edges(u_v_k_d[3]))

    for citation, citation_edges in itt.groupby(qualified_edges,
                                                key=lambda u_v_k_d: flatten_citation(u_v_k_d[3]['citation'])):
        print('SET Citation = {{{}}}'.format(citation), file=file)

        for evidence, evidence_edges in itt.groupby(citation_edges, key=lambda u_v_k_d: u_v_k_d[3]['SupportingText']):
            print('SET SupportingText = "{}"'.format(evidence), file=file)

            for u, v, k, d in evidence_edges:
                dkeys = sorted(dk for dk in d if dk not in BLACKLIST_EDGE_ATTRIBUTES)
                for dk in dkeys:
                    print('SET {} = "{}"'.format(dk, d[dk]), file=file)
                print(decanonicalize_edge(graph, u, v, k), file=file)
                if dkeys:
                    print('UNSET {{{}}}'.format(', '.join('"{}"'.format(dk) for dk in dkeys)), file=file)
            print('UNSET SupportingText', file=file)
        print('\n', file=file)

    print('###############################################\n', file=file)

    print('SET Citation = {"PyBEL","",""}', file=file)
    print('SET Evidence = "Automatically added by PyBEL"', file=file)

    for u in graph.nodes_iter():
        if any(d['relation'] not in language.unqualified_edges for v in graph.adj[u] for d in graph.edge[u][v].values()):
            continue

        print(decanonicalize_node(graph, u), file=file)

    # Can't infer hasMember relationships, but it's not due to specific evidence or citation
    for u, v in graph.edges_iter(relation='hasMember'):
        print("{} hasMember {}".format(decanonicalize_node(graph, u), decanonicalize_node(graph, v)), file=file)
