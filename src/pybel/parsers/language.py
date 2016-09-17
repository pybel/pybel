activities_dict = {
    'degradation': 'deg',
    'catalyticActivity': 'cat',
    'chaperoneActivity': 'chap',
    'gtpBoundActivity': 'gtp',
    'kinaseActivity': 'kin',
    'molecularActivity': 'act',
    'peptidaseActivity': 'pep',
    'phosphataseActivity': 'phos',
    'ribosylationActivity': 'ribo',
    'transcriptionalActivity': 'tscript',
    'transportActivity': 'tport'
}
"""Dictionary of all BEL-activities with long name as key and short name as value 
(if short is available else None)"""
activities = [x for x in activities_dict.keys() if x] + [x for x in activities_dict.values() if x]
"""List of all BEL-activities."""

functions_dict = {
    'abundance': 'a',
    'geneAbundance': 'g',
    'microRNAAbundance': 'm',
    'proteinAbundance': 'p',
    'rnaAbundance': 'r',
    'biologicalProcess': 'bp',
    'pathology': 'path'
}
"""Dictionary of all BEL-functions with long name as key and short name as value 
(if short is available else None)"""
functions = [x for x in functions_dict.keys() if x] + [x for x in functions_dict.values() if x]
"""List of all BEL-functions that describe a biological entity."""

modifications = ['trunc', 'sub', 'pmod', 'fus']
"""List of all BEL-modifications."""

# TODO: Amino acid code X is not defined by BEL Language v. 1.0
aminoacids = ['A', 'R', 'N', 'D', 'C', 'E', 'Q', 'G', 'H', 'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V', 'X']
"""List of all single-letter-amino acid-codes."""

# TODO: Protein Modification O is not defined by BEL Language v. 1.0
pmod_parameters_A = ['P', 'A', 'F', 'G', 'H', 'M', 'R', 'S', 'U', 'O']
"""List of all single-letter-modification-codes."""

lists = ['rxn', 'reaction', 'list', 'complex', 'composite']
"""List of all BEL-list-functions."""

translocations_dict = {
    'cellSecretion': 'sec',
    'cellSurfaceExpression': 'surf',
    'translocation': 'tloc'
}
"""Dictionary of all BEL-translocation-related BEL-functions with long name as key and short name as value"""
translocations = [x for x in translocations_dict.keys() if x] + [x for x in translocations_dict.values() if x]
"""List of all translocation-related BEL-functions."""

relations_dict = {
    'decreases': '-\|',
    'directlyDecreases': '=\|',
    'increases': '->',
    'directlyIncreases': '=>',
    'causesNoChange': None,
    'negativeCorrelation': None,
    'positiveCorrelation': None,
    'association': '--',
    'analogous': None,
    'orthologous': None,
    'transcribedTo': ':>',
    'translatedTo': '>>',
    'biomarkerFor': None,
    'hasMember': None,
    'hasMembers': None,
    'hasComponent': None,
    'hasComponents': None,
    'isA': None,
    'prognosticBiomarkerFor': None,
    'rateLimitingStepOf': None,
    'subProcessOf': None
}
"""Dictionary of all BEL-relationships with long name as key and short name as value 
(if short is available else None)"""
relations = [x for x in relations_dict.keys() if x] + [x for x in relations_dict.values() if x]
"""List of all BEL-relationships (short and long names)."""

relations_decode_dict = {
    '-|': 'decreases',
    '=|': 'directlyDecreases',
    '->': 'increases',
    '=>': 'directlyIncreases',
    '--': 'association',
    ':>': 'transcribedTo',
    '>>': 'translatedTo'
}
"""Dictionary for decoding of symbolic relationships with short name as key and long name as value"""



