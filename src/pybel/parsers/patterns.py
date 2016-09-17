import re

from . import language

predefined_translocation_dict = {
    'sec': {
        'namespace_from': "MESHCL",
        'value_from': "Intracellular Space",
        'namespace_to': "MESHCL",
        'value_to': "Extracellular Sapce"
    },
    'surf': {
        'namespace_from': "MESHCL",
        'value_from': "Intracellular Space",
        'namespace_to': "MESHCL",
        'value_to': "Cell Membrane"
    }
}
"""Dictonary that contains the attributes of predefined translocation-functions."""

complex_statement_map_dict = {
    (">", ">"): "->",
    ("|", "|"): "->",
    ("|", ">"): "-|",
    (">", "|"): "-|"
}
"""Dictionary that is used to translate relations of nested statements."""

label_dict = {
    'p': 'Protein',
    'g': 'Gene',
    'm': 'MicroRNA',
    'r': 'RNA',
    'a': 'Abundance',
    'bp': 'Biological_process',
    'path': 'Pathology'
}
"""Dictionary that translates BEL-functions (bio. entities) to neo4j labels."""

regex_identify_definition = re.compile(
    '^DEFINE\s*(?P<defined_element>(NAMESPACE|ANNOTATION))\s*(?P<keyName>.+?)\s+AS\s+(?P<definition_type>(URL|LIST))\s+(?P<definition>.+)$')
"""Regular expression that is used to identify definitions of Namespaces and Annotations."""

regex_activity = re.compile("^\s*(?P<activity>" +
                            "|".join(language.activities) +
                            ")\s*\(\s*(?P<activity_parameters>.+)\s*\)\s*$")
"""Regular expression that is used to identify BEL-activities."""

regex_function = re.compile("^\s*(?P<term>(?P<function>" +
                            "|".join(language.functions) +
                            ")\s*\((?P<function_parameters>.+?)\s*\))\s*$")
"""Regular expression that is used to identify BEL-functions (bio. entities)."""
# TODO added [^\"] (check if code still runs the same way!!)


regex_modification = re.compile("(?P<modification>" +
                                "|".join(language.modifications) +
                                ")\s*\(\s*(?P<modification_parameters>.+)\s*\)\s*")
"""Regular expression that is used to identify modifications."""

regex_namespace_value = re.compile('(((?P<namespace>[^\":\(]+)\s*:\s*' +
                                   '(?P<value>((\".+\")|([^\"\),]+))))|(?P<undefined_namespace>\".+\"))')
"""Regular expression that is used to identify namespace:value parameters."""

regex_list = re.compile("^\s*(?P<term>(?P<list_function>" +
                        "|".join(language.lists) +
                        ")\s*\((?P<list_parameters>.+)\s*\))\s*$")
"""Regular expression that is used to identify BEL-list-functions."""

regex_reaction_parameters = re.compile("^\s*reactants\s*\(" +
                                       "(?P<reactant_parameters>.+)\)\s*,\s*products\s*\(" +
                                       "(?P<product_parameters>.+)\)\s*$")
"""Regular expression that is used to identify reactants and products of a BEL-reaction-function."""

regex_translocation = re.compile("^\s*(?P<translocation_function>(" +
                                 "|".join(language.translocations) +
                                 "))\s*\((?P<translocation_parameters>.+)\)\s*$")
"""Regular expression that is used to identify BEL-translocation-functions."""

regex_translocation_parameter = re.compile("^(?P<translocated_element>((" +
                                           "|".join(language.functions + language.lists + language.activities) +
                                           "))\s*\(\s*(.+)\))\s*,\s*((" +
                                           "(?P<namespace_from>[^\":\(]+)\s*:\s*" +
                                           "(?P<value_from>((\".+\")|([^\"\),]+))))|" +
                                           "(?P<undefined_namespace_from>\".+\"))\s*,\s*((" +
                                           "(?P<namespace_to>[^\":\(]+)\s*:\s*" +
                                           "(?P<value_to>((\".+\")|([^\"\),]+))))|" +
                                           "(?P<undefined_namespace_to>\".+\"))\s*$")
"""Regular expression that is used to identify the parameters of a BEL-translocation-function."""

regex_statement = re.compile("^\s*(?P<subject>(" +
                             "|".join(
                                 language.activities + language.functions + language.lists + language.translocations) +
                             ")\s*\(.+\))\s*(?P<relation>" +
                             "|".join(language.relations) +
                             ")\s*(?P<object>(" +
                             "|".join(
                                 language.activities + language.functions + language.lists + language.translocations) +
                             ")\s*\(.+\))\s*$")
"""Regular expression that is used to identify BEL-statements."""

regex_complex_statement = re.compile("^\s*(?P<subject>(" +
                                     "|".join(language.activities + language.functions +
                                              language.lists +
                                              language.translocations) +
                                     ")\s*\(.+\))\s*(?P<relation>" +
                                     "|".join(language.relations) +
                                     ")\s*\(\s*(?P<objectStatement>.+)\s*\)\s*$")
"""Regular expression that is used to identify nested BEL-statements."""


def print_regular_expressions():
    print("\n== STATEMENT ==\n")
    print(regex_statement.pattern)
    print("\n== ACTIVITY ==\n")
    print(regex_activity.pattern)
    print("\n== FUNCTION ==\n")
    print(regex_function.pattern)
    print("\n== NAMESPACE / VALUE ==\n")
    print(regex_namespace_value.pattern)
    print("\n== MODIFICATION ==\n")
    print(regex_modification.pattern)
    print("\n== LIST ==\n")
    print(regex_list.pattern)
    print("\n== REACTION PARAMETERS ==\n")
    print(regex_reaction_parameters.pattern)
    print("\n== TRANSLOCATION ==\n")
    print(regex_translocation.pattern)
    print("\n== TRANSLOCATION PARAMETERS ==\n")
    print(regex_translocation_parameter.pattern, "\n")
