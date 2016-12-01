import itertools as itt
import sys
from operator import itemgetter

from .parse_bel import write_bel_term

# TODO extract from .parse_control
CITATION_ENTRIES = 'type', 'name', 'reference', 'date', 'authors', 'comments'


def write_bel_statement(tokens):
    return "{} {} {}".format(write_bel_term(tokens['subject']),
                             tokens['relation'],
                             write_bel_term(tokens['object']))


def decanonicalize_node(g, v):
    """Returns a node from a graph as a BEL string

    :param g:
    :param v:
    :return:
    """
    return g.node[v]['bel']


def postpend_location(s, location_model):
    """Rips off the closing parentheses and adds canonicalized modification.

    I did this because writing a whole new parsing model for the data would be sad and difficult

    :param s:
    :type s: BEL string representing node
    :param location_model:
    :return:
    """

    if all(k in location_model for k in {'namespace', 'name'}):
        return "loc({}:{})".format(location_model['namespace'], location_model['name'])
    raise ValueError('Confused! {}'.format(location_model))


def decanonicalize_edge_node(g, u, ed, p='subject'):
    u_str = decanonicalize_node(g, u)

    if p not in ed:
        return u_str

    part = ed[p]

    if 'location' in part:
        u_str = postpend_location(u_str, part['location'])

    if 'modifier' in part and 'Degredation' == part['modifier']:
        u_str = "deg({})".format(u_str)
    elif 'modifier' in part and 'Activity' == part['modifier']:
        u_str = "act({}".format(u_str)
        # switch missing, default, and dict
        if 'effect' in part and 'MolecularActivity' in part['effect']:
            ma = part['effect']['MolecularActivity']

            if isinstance(ma, str):
                u_str = "{}, ma({}))".format(u_str, ma)
            elif isinstance(ma, dict):
                u_str = "{}, ma({}:{}))".format(u_str, ma['namespace'], ma['name'])
        else:
            u_str = "{})".format(u_str)

    elif 'modifier' in part and 'Translocation' == part['modifier']:
        fromLoc = "fromLoc("
        toLoc = "toLoc("

        if isinstance(part['effect']['fromLoc'], dict):
            fromLoc += "{}:{})".format(part['effect']['fromLoc']['namespace'], part['effect']['fromLoc']['name'])
        else:
            raise ValueError()

        if isinstance(part['effect']['toLoc'], dict):
            toLoc += "{}:{})".format(part['effect']['toLoc']['namespace'], part['effect']['toLoc']['name'])
        else:
            raise ValueError()

        u_str = "tloc({}, {}, {})".format(u_str, fromLoc, toLoc)

    return u_str


def decanonicalize_edge(g, u, v, k):
    """Takes two nodes and gives back a BEL string representing the statement

    :param g:
    :type g: BELGraph
    :param u:
    :param v:
    :return:
    """

    ed = g.edge[u][v][k]

    u_str = decanonicalize_edge_node(g, u, ed, p='subject')
    v_str = decanonicalize_edge_node(g, v, ed, p='object')

    return "{} {} {}".format(u_str, ed['relation'], v_str)


blacklist_features = ['relation', 'subject', 'object', 'citation', 'SupportingText']


def flatten_citation(citation):
    #return "\t".join(d[k] for k in CITATION_ENTRIES)
    return ','.join('"{}"'.format(citation[x]) for x in CITATION_ENTRIES[:len(citation)])


def sort_edges(d):
    return (flatten_citation(d['citation']), d['SupportingText']) + tuple(
        itt.chain.from_iterable((k, v) for k, v in sorted(d.items(), key=itemgetter(0)) if k not in blacklist_features))


def decanonicalize_graph(g, file=sys.stdout):
    for k in sorted(g.document):
        print('SET DOCUMENT {} = "{}"'.format(k, g.document[k]), file=file)

    print('###############################################\n', file=file)

    for namespace, url in sorted(g.namespace_url.items(), key=itemgetter(0)):
        print('DEFINE NAMESPACE {} AS URL "{}"'.format(namespace, url), file=file)

    for namespace, url in sorted(g.namespace_owl.items(), key=itemgetter(0)):
        print('DEFINE NAMESPACE {} AS OWL "{}"'.format(namespace, url), file=file)

    for namespace, ns_list in sorted(g.namespace_list.items(), key=itemgetter(0)):
        ns_list_str = ', '.join('"{}"'.format(e) for e in ns_list)
        print('DEFINE NAMESPACE {} AS LIST {{{}}}'.format(namespace, ns_list_str), file=file)

    print('###############################################\n', file=file)

    for annotation, url in sorted(g.annotation_url.items(), key=itemgetter(0)):
        print('DEFINE ANNOTATION {} AS URL "{}"'.format(annotation, url), file=file)

    for annotation, an_list in sorted(g.annotation_list.items(), key=itemgetter(0)):
        an_list_str = ', '.join('"{}"'.format(e) for e in an_list)
        print('DEFINE ANNOTATION {} AS LIST {{{}}}'.format(annotation, an_list_str), file=file)

    print('###############################################\n', file=file)

    # sort by citation, then supporting text
    qualified_edges = filter(lambda u_v_k_d: 'citation' in u_v_k_d[3] and 'SupportingText' in u_v_k_d[3],
                             g.edges_iter(data=True, keys=True))
    qualified_edges = sorted(qualified_edges, key=lambda u_v_k_d: sort_edges(u_v_k_d[3]))

    for citation, citation_edges in itt.groupby(qualified_edges,
                                                key=lambda u_v_k_d: flatten_citation(u_v_k_d[3]['citation'])):
        #quoted_citation = ['"{}"'.format(citation[x]) for x in CITATION_ENTRIES[:len(citation)]]
        #print('SET Citation = {{{}}}'.format(','.join(quoted_citation)), file=file)
        print('SET Citation = {{{}}}'.format(citation), file=file)

        for evidence, evidence_edges in itt.groupby(citation_edges, key=lambda u_v_k_d: u_v_k_d[3]['SupportingText']):
            print('SET SupportingText = "{}"'.format(evidence), file=file)

            for u, v, k, d in evidence_edges:
                for dk in sorted(d):
                    if dk in blacklist_features:
                        continue
                    print('SET {} = "{}"'.format(dk, d[dk]), file=file)
                print(decanonicalize_edge(g, u, v, k), file=file)
            print('UNSET SupportingText', file=file)
        print('\n', file=file)
