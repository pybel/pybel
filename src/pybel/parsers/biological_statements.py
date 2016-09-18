import logging

log = logging.getLogger(__name__)


def validate_sexpr(sexpr, statement_info, entity_info):
    """
    Validates a complex biological express.

    :param sexpr: A S-expression representing a complex biological statement
    :param statement_info: a dictionary of {statement:
    :param entity_info: a dictionary of {namespace: set of entries}
    :return:
    """
    pass


def canonicalize_sexpr(sexpr):
    """
    Turns a validated S-expression representing a complex biological staetment into a list of nodes and list of edges.
    :param sexpr:
    :return:
    """
