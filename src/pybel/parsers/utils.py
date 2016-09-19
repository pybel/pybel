import logging
import re

log = logging.getLogger(__name__)
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


def check_stability(ns_dict, ns_mapping):
    """
    Check the stability of namespace mapping
    :param ns_dict: dict of {name: set of values}
    :param ns_mapping: dict of {name: {value: (other_name, other_value)}}
    :return: if the mapping is stable
    :rtype: Boolean
    """
    flag = True
    for ns, kv in ns_mapping.items():
        if ns not in ns_dict:
            log.warning('missing namespace {}'.format(ns))
            flag = False
        for k, (k_ns, v_val) in kv.items():
            if k not in ns_dict[ns]:
                log.warning('missing value {}'.format(k))
                flag = False
            if k_ns not in ns_dict:
                log.warning('missing namespace link {}'.format(k_ns))
                flag = False
            if v_val not in ns_dict[k_ns]:
                log.warning('missing value {} in namespace {}'.format(v_val, k_ns))
                flag = False
    return flag
