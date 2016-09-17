import copy
import logging
import re

from . import language
from . import patterns
from .utils import strip_quotation_marks

log = logging.getLogger(__name__)

# print(language.activities_dict)
# print(patterns.print_regular_expressions())

from collections import defaultdict

tr = defaultdict(list)


def create_relation(self, *args):
    tr['relation'].append(args)
    return None


def create_node(self, *args):
    tr['node'].append(args)
    return None


def parse_statement(statement_string, annotation_informations, context, complete_origin):
    """
        This method identifies the BEL-terms in the given BEL-statement.

        :param statement_string: A BEL-statement string. Example: subject-term relation object-term
        :type statement_string: str
        :param annotation_informations: Dictionary that contains the annotation-information for the actual line of BEL-Document
        :type annotation_informations: dict
        :param context: keyword in which context statement is valid
        :type context: str
        :param complete_origin: If set to true, proteins will be extended ex. Protein <- translatedTo - RNA <- transcribedTo - Gene
        :type complete_origin: bool

        :return: Dictionary, containing: subject_node, relation, relationType, object_node

    """

    statement = patterns.regex_statement.search(statement_string)
    complexStatement = patterns.regex_complex_statement.search(statement_string)

    #     print "Test:",statement_string
    #     if complexStatement:
    #         print "Comples STMNT!",complexStatement.groupdict()
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

    if statement and not complexStatement:
        statement_dict = statement.groupdict()

        subject_act = patterns.regex_activity.search(statement_dict['subject'])
        subject_tloc = patterns.regex_translocation.search(statement_dict['subject'])
        object_act = patterns.regex_activity.search(statement_dict['object'])
        object_tloc = patterns.regex_translocation.search(statement_dict['object'])

        if subject_act:
            subject_actDict = subject_act.groupdict()
            subject_node = parse_term(term_string=subject_actDict['activity_parameters'].strip(),
                                      complete_origin=complete_origin)

        elif subject_tloc:
            subject_tlocDict = subject_tloc.groupdict()
            subject_tloc_information = get_translocation(
                tloc_function=subject_tlocDict['translocation_function'].strip(),
                tloc_parameters=subject_tlocDict['translocation_parameters'].strip())
            subject_node = subject_tloc_information['translocated_element_node']

        else:
            subject_node = parse_term(term_string=statement_dict['subject'].strip(),
                                      complete_origin=complete_origin)

        if object_act:
            object_actDict = object_act.groupdict()
            object_node = parse_term(term_string=object_actDict['activity_parameters'].strip(),
                                     complete_origin=complete_origin)

        elif object_tloc:
            object_tlocDict = object_tloc.groupdict()
            object_tloc_information = get_translocation(
                tloc_function=object_tlocDict['translocation_function'].strip(),
                tloc_parameters=object_tlocDict['translocation_parameters'].strip())
            object_node = object_tloc_information['translocated_element_node']

        else:
            object_node = parse_term(term_string=statement_dict['object'].strip(),
                                     complete_origin=complete_origin)

        if subject_node and object_node:
            additional_parameters = {
                'context': context,
                'evidence': annotation_informations['Evidence'],
                'citation': annotation_informations['Citation'],
                'annotations': None,
                'subject_activity': None if not subject_act else subject_actDict['activity'],
                'subject_translocation': None if not subject_tloc else True,
                'subject_translocation_from_namespace': None if not subject_tloc else subject_tloc_information[
                    'namespace_from'],
                'subject_translocation_from_value': None if not subject_tloc else subject_tloc_information[
                    'value_from'],
                #                                          'subject_translocation_from_no_namespace':None if not subject_tloc else subject_tloc_information['undefined_namespace_from'],
                'subject_translocation_to_namespace': None if not subject_tloc else subject_tloc_information[
                    'namespace_to'],
                'subject_translocation_to_value': None if not subject_tloc else subject_tloc_information[
                    'value_to'],
                #                                          'subject_translocation_to_no_namespace':None if not subject_tloc else subject_tloc_information['undefined_namespace_to'],
                'object_activity': None if not object_act else object_actDict['activity'],
                'object_translocation': None if not object_tloc else True,
                'object_translocation_from_namespace': None if not object_tloc else object_tloc_information[
                    'namespace_from'],
                'object_translocation_from_value': None if not object_tloc else object_tloc_information[
                    'value_from'],
                #                                          'object_translocation_from_no_namespace':None if not object_tloc else object_tloc_information['undefined_namespace_from'],
                'object_translocation_to_namespace': None if not object_tloc else object_tloc_information[
                    'namespace_to'],
                'object_translocation_to_value': None if not object_tloc else object_tloc_information['value_to'],
                #                                          'object_translocation_to_no_namespace':None if not object_tloc else object_tloc_information['undefined_namespace_to']
            }

            for given_annotation in annotation_informations['given_annotations']:
                additional_parameters[given_annotation] = annotation_informations['given_annotations'][
                    given_annotation]
            decoded_relation = statement_dict['relation'].strip() if statement_dict[
                                                                         'relation'].strip() not in language.relations_decode_dict else \
                language.relations_decode_dict[statement_dict['relation'].strip()]
            rel = create_relation(subject_node, object_node, decoded_relation, additional_parameters)

        else:
            log.warn("parsing_errors: {}".format(statement_dict))

    elif complexStatement:
        complex_statement_dict = complexStatement.groupdict()
        inner_statement = parse_statement(complex_statement_dict['objectStatement'], annotation_informations,
                                          context, complete_origin)
        complex_subject_act = patterns.regex_activity.search(complex_statement_dict['subject'])
        complex_subject_tloc = patterns.regex_translocation.search(complex_statement_dict['subject'])

        if complex_subject_act:
            complex_subject_actDict = complex_subject_act.groupdict()
            complex_subject_node = parse_term(
                term_string=complex_subject_actDict['activity_parameters'].strip(), complete_origin=complete_origin)

        elif complex_subject_tloc:
            complex_subject_tlocDict = complex_subject_tloc.groupdict()
            complex_subject_tloc_information = get_translocation(
                tloc_function=complex_subject_tlocDict['translocation_function'].strip(),
                tloc_parameters=complex_subject_tlocDict['translocation_parameters'].strip())
            complex_subject_node = complex_subject_tloc_information['translocated_element_node']

        else:
            complex_subject_node = parse_term(term_string=complex_statement_dict['subject'].strip(),
                                              complete_origin=complete_origin)

        if complex_subject_node and inner_statement['object_node']:
            decoded_relation = complex_statement_dict['relation'].strip() if complex_statement_dict[
                                                                                 'relation'].strip() not in language.relations_decode_dict else \
                language.relations_decode_dict[complex_statement_dict['relation'].strip()]
            if (decoded_relation[-1], inner_statement['relationType']) in complex_statement_map_dict:
                resulting_relation = complex_statement_map_dict[(decoded_relation[-1], inner_statement['relationType'])]

                additional_parameters_dict = {
                    'context': context,
                    'evidence': str(annotation_informations['Evidence']),
                    'citation': str(annotation_informations['Citation']),
                    'subject_activity': False if not subject_act else subject_actDict['activity'],
                    'subject_translocation': False if not subject_tloc else True,
                    'subject_translocation_from_namespace': None if not subject_tloc else
                    subject_tloc_information['namespace_from'],
                    'subject_translocation_from_value': None if not subject_tloc else
                    subject_tloc_information['value_from'],
                    # 'subject_translocation_from_no_namespace':None if not subject_tloc else subject_tloc_information['undefined_namespace_from'],
                    'subject_translocation_to_namespace': None if not subject_tloc else
                    subject_tloc_information['namespace_to'],
                    'subject_translocation_to_value': None if not subject_tloc else
                    subject_tloc_information['value_to']
                }

                rel = create_relation(complex_subject_node, inner_statement['object_node'], resulting_relation,
                                      additional_parameters_dict)

    return {
        'subject_node': subject_node,
        'relation': rel,
        'relationType': decoded_relation,
        'object_node': object_node
    }


def parse_term(term_string, complete_origin=False):  # TODO: This methode seems to be too long
    """
        This method identifies the type of the given BEL-term and applies the corresponding regular expressions
        to collect the needed data.

        :param term_string: A BEL-term string. Example: p(HGNC:APP)
        :type term_string: str
        :param complete_origin: If set to true, proteins will be extended ex. Protein <- translatedTo - RNA <- transcribedTo - Gene
        :type complete_origin: bool

        :return: Py2Neo node-object

    """
    functionWithParametersRegexObj = patterns.regex_function.search(term_string)
    listWithParametersRegExObj = patterns.regex_list.search(term_string)

    node = None

    term_dict = {'BEL': None,
                 'function': None,
                 'namespace': None,
                 'value': None,
                 #                      'valid_NSV':None,
                 'modification': None,
                 'modification_parameters': None}

    if functionWithParametersRegexObj:
        function_dict = functionWithParametersRegexObj.groupdict()
        term_dict['function'] = function_dict['function']

        namespaceValue = patterns.regex_namespace_value.search(function_dict['function_parameters'])

        namespaceValue_dict = {'namespace': 'UNDEFINED',
                               'value': function_dict['function_parameters']}  # CHEBI:"gamma-secretase inhibitor"

        if namespaceValue:
            namespaceValue_dict = namespaceValue.groupdict()

            if not namespaceValue_dict['namespace']:
                namespaceValue_dict['namespace'] = "UNDEFINED"
                namespaceValue_dict['value'] = namespaceValue_dict['undefined_namespace']
                del (namespaceValue_dict['undefined_namespace'])

        term_dict.update(namespaceValue_dict)

        value = strip_quotation_marks(term_dict['value'])  # if term_dict['value'] else term_dict['undefined_namespace']
        namespace = term_dict['namespace']  # if term_dict['namespace'] else 'UNDEFINED'

        term_dict['valid_NSV'], term_dict['value'], term_dict['namespace'] = check_NSorA_entry(str(namespace),
                                                                                               str(value))

        node_term_dict = copy.deepcopy(term_dict)
        node_term_dict['BEL'] = function_dict['function'] + "(" + str(namespace) + ":\"" + str(value) + "\")"

        node = create_node(node_dict=node_term_dict,
                           label=patterns.label_dict[node_term_dict['function']],
                           complete_origin=complete_origin)

        modification = patterns.regex_modification.search(function_dict['function_parameters'])
        if modification:
            modification_dict = patterns.regex_modification.search(function_dict['function_parameters']).groupdict()
            term_dict['modification'] = modification_dict['modification']
            term_dict.update(get_modification(modification=modification_dict['modification'],
                                              modification_parameters=modification_dict[
                                                  'modification_parameters']))

            #             term_dict['BEL'] = function_dict['term']
            term_dict['BEL'] = function_dict['function'] + "(" + str(namespace) + ":\"" + str(value) + "\"," + \
                               modification_dict['modification'] + "(" + modification_dict[
                                   'modification_parameters'] + "))"

            mod_node = create_node(term_dict, 'Modification')

            create_relation(subject_node=node,
                            object_node=mod_node,
                            relation='has_modification')

            node = mod_node

    elif listWithParametersRegExObj:
        list_dict = listWithParametersRegExObj.groupdict()
        term_dict['function'] = list_dict['list_function']
        sub_func = patterns.regex_function.search(list_dict['list_parameters'])

        if not sub_func:
            if list_dict['list_function'] in ('reaction', 'rxn'):
                reaction_parameters_dict = patterns.regex_reaction_parameters.search(
                    list_dict['list_parameters']).groupdict()
                term_dict['BEL'] = list_dict['list_function'] + "(reactants(" + reaction_parameters_dict[
                    'reactant_parameters'] + "),products(" + reaction_parameters_dict['product_parameters'] + "))"
                node = create_node(term_dict, 'Reaction')

                reactants_list = get_list(list_parameters=reaction_parameters_dict['reactant_parameters'])
                reactant_nodes_list = [parse_term(reactant) for reactant in reactants_list]

                for reactant_node in reactant_nodes_list:
                    create_relation(reactant_node, node, 'reactant')

                products_list = get_list(list_parameters=reaction_parameters_dict['product_parameters'])
                product_nodes_list = [parse_term(product) for product in products_list]

                for product_node in product_nodes_list:
                    create_relation(node, product_node, 'product')

            else:
                term_dict['BEL'] = list_dict['list_function'] + "(" + list_dict['list_parameters'] + ")"
                term_dict.update(patterns.regex_namespace_value.search(list_dict['list_parameters']).groupdict())

        if node is None:
            if sub_func and term_dict['function'] in ('complex', 'composite', 'list'):
                sub_func_dict = sub_func.groupdict()
                term_dict['BEL'] = term_dict['function'] + "(" + sub_func_dict['function'] + "(" + sub_func_dict[
                    'function_parameters'] + "))"
                term_dict['list'] = "true"
            elif term_dict['function'] in ('complex'):
                term_dict['BEL'] = list_dict['term']
            node = create_node(term_dict, term_dict['function'], complete_origin)

        if sub_func:
            participants_list = get_list(list_parameters=list_dict['list_parameters'])

            participant_nodes_list = [parse_term(participant) for participant in participants_list]

            for participant_node in participant_nodes_list:
                create_relation(participant_node, node, 'in_list')

    else:
        logging.debug("[ERROR] at FUNC / LIST detection [ " + term_string + " ].")
    return node


def get_translocation(tloc_function, tloc_parameters):
    """
        This method identifies the parameters in the given translocation parameters string.

        :param tloc_function: The translocation function [tloc,sec,surf].
        :type tloc_function: str
        :param tloc_parameters: The parameters for the given translocation.
        :type tloc_parameters: str

        :return: Dictionary containing the translocation informations

    """
    translocation_information_dict = {
        'translocated_element_node': None,
        'namespace_from': None,
        'value_from': None,
        #                                       'undefined_namespace_from':None,
        'namespace_to': None,
        'value_to': None,
        #                                       'undefined_namespace_to':None
    }

    tloc_dict = None

    # TODO: Ask Alpha / Raegon for completion of tlocs in BEL-Files!! replace elif tloc_dict

    if tloc_function in ('tloc', 'translocation'):
        tloc = patterns.regex_translocation_parameter.search(tloc_parameters)
        tloc_dict = None
        if tloc:
            tloc_dict = tloc.groupdict()
            translocation_information_dict['translocated_element_node'] = parse_term(
                term_string=tloc_dict['translocated_element'])
        else:
            translocation_information_dict['translocated_element_node'] = parse_term(tloc_parameters)
            translocation_information_dict['namespace_from'] = 'UNDEFINED'
            translocation_information_dict['value_from'] = 'UNDEFINED'
            translocation_information_dict['namespace_to'] = 'UNDEFINED'
            translocation_information_dict['value_to'] = 'UNDEFINED'

        # translocation_information_dict['undefined_namespace_from'] = "UNDEFINED"
        #             translocation_information_dict['undefined_namespace_to'] = "UNDEFINED"

        if tloc_dict and tloc_dict['namespace_from']:
            translocation_information_dict['namespace_from'] = tloc_dict['namespace_from']
            translocation_information_dict['value_from'] = tloc_dict['value_from']

        elif tloc_dict:
            translocation_information_dict['namespace_from'] = 'UNDEFINED'
            translocation_information_dict['value_from'] = tloc_dict['undefined_namespace_from']

        if tloc_dict and tloc_dict['namespace_to']:
            translocation_information_dict['namespace_to'] = tloc_dict['namespace_to']
            translocation_information_dict['value_to'] = tloc_dict['value_to']

        elif tloc_dict:
            translocation_information_dict['namespace_to'] = 'UNDEFINED'
            translocation_information_dict['value_to'] = tloc_dict['undefined_namespace_to']

    elif tloc_function in ('sec', 'surf'):
        translocation_information_dict.update(patterns.predefined_translocation_dict[tloc_function])
        translocation_information_dict['translocated_element_node'] = parse_term(tloc_parameters)

    else:
        logging.error("Translocation-Function is used wrong! [ " + tloc_function + "(" + tloc_parameters + ")" + " ]")

    return translocation_information_dict


def check_NSorA_entry(namespaceOrAnnotationKey, entry):
    """
        This method checks if the combination of namespace key and value is valid.

        :param namespaceOrAnnotationKey: The keyword that is used to represent the namespace or annotation in the loaded BEL-File. (Example: HGNC)
        :type namespaceOrAnnotationKey: str
        :param entry: Value that is used in the namespace or annotation. (Example: APP)
        :type entry: str

        :return: ([+|-),entry)
                 Returns a - if the entry is not defined in the namespace or annotation.
                 Returns a + if the entry is defined in the namespace or annotaiton.
                 Returns a corrected entry
    """
    is_valid = '+'
    return is_valid, entry, namespaceOrAnnotationKey


def get_modification(modification, modification_parameters):
    """
        This method is used to identify the parameters of the given modification.

        :param modification: BEL representation of the modification (pmod,trunc,sub,fus).
        :type modification: str
        :param modification_parameters: The parameters that are provided to the modification.
        :type modification_parameters: str

        :return: Dictionary that contains the identified parameters
    """
    aminoaccid_code_1 = "(?P<aminoacid_Code_1>" + "|".join(language.aminoacids) + ")"
    aminoaccid_code_2 = "(?P<aminoacid_Code_2>" + "|".join(language.aminoacids) + ")"
    protein_modType = "(?P<p_modType>" + "|".join(language.pmod_parameters_A) + ")"

    modification_parameters_regexDict = {'trunc': "(?P<position>\d+)",
                                         'sub': aminoaccid_code_1 + "\s*(,\s*(?P<position>\d+)\s*,\s*" + aminoaccid_code_2 + ")?",
                                         # TODO: position and aminoaccid_code_2 are not optional?!
                                         'pmod': protein_modType + "\s*(\s*,\s*" + aminoaccid_code_1 + ")?(,\s*(?P<position>\d+))?",
                                         'fus': patterns.regex_namespace_value.pattern + "\s*,*\s(?P<fivePrime>\d+)\s*,\s*(?P<threePrime>\d+)"}
    try:
        return re.search(modification_parameters_regexDict[modification], modification_parameters).groupdict()
    except:
        log.warn("[ERROR] Modification-search for: " + modification + "(" + modification_parameters + ")")
        # sys.exit("[ERROR] Modification-search for: "+modification+"("+modification_parameters+")")


def get_list(list_parameters):
    """
        This method translates a given list-string to an actual list object.

        :param list_parameters: String that represents the parameters of a BEL-list-function
        :type list_parameters: str

        :return: List of Strings. The strings represent biological entities (BEL-abundance-functions)

    """
    participants = list_parameters.split("),")
    list_participants = [x + ")" if not x == participants[len(participants) - 1] else x for x in participants]
    return list_participants
