# -*- coding: utf-8 -*-

import itertools as itt
import logging
import re

log = logging.getLogger('pybel')

re_match_bel_header = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")


def sanitize_file_lines(f):
    """Enumerates a line iterator and returns the pairs of (line number, line) that are cleaned"""
    it = (line.strip() for line in f)
    it = filter(lambda i_l: i_l[1] and not i_l[1].startswith('#'), enumerate(it, start=1))
    it = iter(it)

    for line_number, line in it:
        if line.endswith('\\'):
            log.log(4, 'Multiline quote starting on line: %d', line_number)
            line = line.strip('\\').strip()
            next_line_number, next_line = next(it)
            while next_line.endswith('\\'):
                log.log(3, 'Extending line: %s', next_line)
                line += " " + next_line.strip('\\').strip()
                next_line_number, next_line = next(it)
            line += " " + next_line.strip()
            log.log(3, 'Final line: %s', line)

        elif 1 == line.count('"'):
            log.log(4, 'PyBEL013 Missing new line escapes [line: %d]', line_number)
            next_line_number, next_line = next(it)
            next_line = next_line.strip()
            while not next_line.endswith('"'):
                log.log(3, 'Extending line: %s', next_line)
                line = '{} {}'.format(line.strip(), next_line)
                next_line_number, next_line = next(it)
                next_line = next_line.strip()
            line = '{} {}'.format(line, next_line)
            log.log(3, 'Final line: %s', line)

        comment_loc = line.rfind(' //')
        if 0 <= comment_loc:
            line = line[:comment_loc]

        yield line_number, line


def split_file_to_annotations_and_definitions(file):
    """Enumerates a line iterable and splits into 3 parts"""
    content = list(sanitize_file_lines(file))

    end_document_section = 1 + max(j for j, (i, l) in enumerate(content) if l.startswith('SET DOCUMENT'))
    end_definitions_section = 1 + max(j for j, (i, l) in enumerate(content) if re_match_bel_header.match(l))

    log.info('File length: %d lines', len(content))
    documents = content[:end_document_section]
    definitions = content[end_document_section:end_definitions_section]
    statements = content[end_definitions_section:]

    return documents, definitions, statements


def check_stability(ns_dict, ns_mapping):
    """Check the stability of namespace mapping

    :param ns_dict: dict of {name: set of values}
    :param ns_mapping: dict of {name: {value: (other_name, other_value)}}
    :return: if the mapping is stable
    :rtype: Boolean
    """
    flag = True
    for ns, kv in ns_mapping.items():
        if ns not in ns_dict:
            log.warning('missing namespace %s', ns)
            flag = False
            continue
        for k, (k_ns, v_val) in kv.items():
            if k not in ns_dict[ns]:
                log.warning('missing value %s', k)
                flag = False
            if k_ns not in ns_dict:
                log.warning('missing namespace link %s', k_ns)
                flag = False
            elif v_val not in ns_dict[k_ns]:
                log.warning('missing value %s in namespace %s', v_val, k_ns)
                flag = False
    return flag


def list2tuple(l):
    """turns a nested list to a nested tuple"""
    if not isinstance(l, list):
        return l
    else:
        return tuple(list2tuple(e) for e in l)


def subdict_matches(a, b):
    """Checks if all the keys in b are in a, and that their values match

    :param a: a dictionary
    :type a: dict
    :param b: a dictionary
    :type b: dict
    :return: if all keys in b are in a and their values match
    :rtype: bool
    """
    for k, v in b.items():
        if k not in a:
            return False
        elif isinstance(v, (str, dict)) and a[k] != v:
            return False
        elif isinstance(v, (list, set, tuple)) and a[k] not in v:
            return False
        elif not isinstance(v, (str, list, set, dict, tuple)):
            raise ValueError('invalid value: {}'.format(v))
    return True


def any_subdict_matches(a, b):
    """Checks if dictionary b matches one of the subdictionaries of a

    :param a: dictionary of dictionaries
    :param b: dictionary
    :return: if dictionary b matches one of the subdictionaries of a
    :rtype: bool
    """
    return any(subdict_matches(sd, b) for sd in a.values())


def cartesian_dictionary(d):
    """takes a dictionary of sets and provides subdicts

    :param d: a dictionary of sets
    :type d: dict
    :rtype: list
    """
    q = {}
    for key in d:
        q[key] = {(key, value) for value in d[key]}

    res = []
    for values in itt.product(*q.values()):
        res.append(dict(values))

    return res


def handle_debug(fmt):
    """logging hook for pyparsing

    :param fmt: a format string with {s} for string, {l} for location, and {t} for tokens
    """

    def handle(s, l, t):
        log.log(5, fmt.format(s=s, location=l, tokens=t))
        return t

    return handle


def ensure_quotes(s):
    """Quote a string that isn't solely alphanumeric

    :param s: a string
    :type s: str
    :rtype: str
    """
    return '"{}"'.format(s) if not s.isalnum() else s
