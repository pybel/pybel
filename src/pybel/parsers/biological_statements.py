import logging

from . import patterns

log = logging.getLogger(__name__)


# print(language.activities_dict)
# print(patterns.print_regular_expressions())


def tokenize_statement(statement_string):
    '''
    Parses complex biological statement string into S-Expression
    :return:
    '''

    rel = None
    subject_node = None
    object_node = None
    decoded_relation = None

    ##
    subject_act = None
    subject_actDict = None
    subject_tloc = None
    complex_statement_map_dict = None
    subject_tloc_information = None
    ##

    statement = patterns.regex_statement.search(statement_string)
    complexStatement = patterns.regex_complex_statement.search(statement_string)

    print('Statement:', statement.groupdict())
    print('Complex Statement:', complexStatement.groupdict())

    if statement and not complexStatement:
        statement_dict = statement.groupdict()

        subject_act = patterns.regex_activity.search(statement_dict['subject'])
        subject_tloc = patterns.regex_translocation.search(statement_dict['subject'])
        object_act = patterns.regex_activity.search(statement_dict['object'])
        object_tloc = patterns.regex_translocation.search(statement_dict['object'])

        print('Subject Activity', subject_act)
        print('Subject Translocation', subject_tloc)
        print('Object Activity', object_act)
        print('Object Translocation', object_tloc)


    elif complexStatement:
        complex_statement_dict = complexStatement.groupdict()
        # inner_statement = parse_statement(complex_statement_dict['objectStatement'], annotation_informations, context, complete_origin)
        complex_subject_act = patterns.regex_activity.search(complex_statement_dict['subject'])
        complex_subject_tloc = patterns.regex_translocation.search(complex_statement_dict['subject'])

        print('Complex Subject Activity', complex_subject_act)
        print('Complex Subject Translocation', complex_subject_tloc)

    return {
        'subject_node': subject_node,
        'relation': rel,
        'relationType': decoded_relation,
        'object_node': object_node
    }


def validate_sexpr(sexpr, statement_info, entity_info):
    '''
    Validates a complex biological express.

    :param sexpr: A S-expression representing a complex biological statement
    :param statement_info: a dictionary of {statement:
    :param entity_info: a dictionary of {namespace: set of entries}
    :return:



    '''
    pass


def canonicalize_sexpr(sexpr):
    '''
    Turns a validated S-expression representing a complex biological staetment into a list of nodes and list of edges.
    :param sexpr:
    :return:
    '''
