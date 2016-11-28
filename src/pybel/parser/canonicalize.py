import sys

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


def decanonicalize_graph(g, file=sys.stdout):
    for k, v in g.document:
        print('SET DOCUMENT {} = ""'.format(k, v), file=file)

    for k, v in g.definitions:
        print('DEFINE {} AS URL {}'.format(k, v), file=file)

    for u, v, k, d in g.edges_iter(data=True, keys=True):
        quoted_citation = ['"{}"'.format(d['citation'][x]) for x in CITATION_ENTRIES[:len(d['citation'])]]
        print('SET Citation = {{{}}}'.format(','.join(quoted_citation)), file=file)
        print('SET SupportingText = "{}"'.format(d['SupportingText']), file=file)

        for dk in sorted(d):
            if dk in blacklist_features:
                continue
            print('SET {} = "{}"'.format(dk, d[dk]), file=file)

        print(decanonicalize_edge(g, u, v, k), file=file)
