# -*- coding: utf-8 -*-

"""Input and output functions for BEL graphs.

PyBEL provides multiple lossless interchange options for BEL. Lossy output formats are also included for convenient
export to other programs. Notably, a *de facto* interchange using Resource Description Framework (RDF) to match the
ability of other existing software is excluded due the immaturity of the BEL to RDF mapping.
"""

from . import extras, gpickle, indra, jgif, lines, neo4j, nodelink, web
from .extras import *
from .gpickle import *
from .indra import *
from .jgif import *
from .lines import *
from .neo4j import *
from .nodelink import *
from .web import *

__all__ = (
    lines.__all__ +
    nodelink.__all__ +
    gpickle.__all__ +
    neo4j.__all__ +
    extras.__all__ +
    jgif.__all__ +
    indra.__all__ +
    web.__all__
)
