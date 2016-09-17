import re

re_parse_list = re.compile('"\s*,\s*"')


def parse_list(s):
    s = s.strip('{}')
    q = re_parse_list.split(s)
    q = [z.strip('"') for z in q]
    return q


def sanitize_file_lines(f):
    content = [line.strip() for line in f]
    return [line for line in content if line and not line.startswith('#')]


def subitergroup(iterable, key):
    poss = (i for i, v in enumerate(iterable) if key(v))
    res = []
    last = next(poss)
    for pos in poss:
        k = iterable[last]
        z = iterable[last + 1:pos]
        last = pos
        res.append((k, z))
    res.append((iterable[last], iterable[last + 1:]))
    return res

def strip_quotation_marks(term):
    if isinstance(term, str):
        found = re.search('^\s*"\s*(.*)\s*"\s*$', term)
        if found:
            term = found.group(1)
    return term