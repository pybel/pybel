# -*- coding: utf-8 -*-

"""Resources for PyBEL."""

CHEBI_URL = 'https://raw.githubusercontent.com/pharmacome/conso/d67144bc27a21626a514837b3b4382413dd6866b/external/chebi-names.belns'
EC_URL = 'https://raw.githubusercontent.com/pharmacome/conso/d67144bc27a21626a514837b3b4382413dd6866b/external/ec-code.belns'
FB_URL = 'https://raw.githubusercontent.com/pharmacome/conso/80171ae62cf43aa1fc8a6c326b94537ab342458c/external/fb-names.belns'
GO_URL = 'https://raw.githubusercontent.com/pharmacome/conso/d9d270e11aac480542c412d4222983a5f042b8ae/external/go-names.belns'
HGNC_URL = 'https://raw.githubusercontent.com/pharmacome/conso/d67144bc27a21626a514837b3b4382413dd6866b/external/hgnc-names.belns'
MESH_URL = 'https://raw.githubusercontent.com/pharmacome/conso/f02c6ad4a4791a8ed45448513b9de8c8f1b00c87/external/mesh-names.belns'
MGI_URL = 'https://raw.githubusercontent.com/pharmacome/conso/efc856fb009a39e4d284269a6801f79ed3d3cf56/external/mgi-names.belns'
NCBIGENE_URL = 'https://raw.githubusercontent.com/pharmacome/conso/d67144bc27a21626a514837b3b4382413dd6866b/external/ncbigene-names.belns'
RGD_URL = 'https://raw.githubusercontent.com/pharmacome/conso/efc856fb009a39e4d284269a6801f79ed3d3cf56/external/rgd-names.belns'

FPLX_URL = 'https://raw.githubusercontent.com/sorgerlab/famplex/da9f2187b694e6b425e668604e24ac9fac0f2c31/export/famplex.belns'

#: Default URL lookup for some keywords
keyword_to_url = dict(
    chebi=CHEBI_URL,
    ec=EC_URL,
    fb=FB_URL,
    go=GO_URL,
    hgnc=HGNC_URL,
    mesh=MESH_URL,
    mgi=MGI_URL,
    ncbigene=NCBIGENE_URL,
    rgd=RGD_URL,
    fplx=FPLX_URL,
)
