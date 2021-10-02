# -*- coding: utf-8 -*-

"""Constants for SBGN-ML conversion."""

import pyobo

RDF = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
NS1 = '{http://biomodels.net/biology-qualifiers/}'
SBGN_VERSIONS = {
    '0.2': '{http://sbgn.org/libsbgn/0.2}',
    '0.3': '{http://sbgn.org/libsbgn/0.3}',
}
XHTML = '{http://www.w3.org/1999/xhtml}'

hgnc_name_to_id = pyobo.get_name_id_mapping('hgnc')
chebi_name_to_id = pyobo.get_name_id_mapping('chebi')
go_name_to_id = pyobo.get_name_id_mapping('go')
