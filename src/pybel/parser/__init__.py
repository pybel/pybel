# -*- coding: utf-8 -*-

"""The :mod:`pybel.parser` module contains utilities for parsing BEL documents and BEL statements."""

from .modifiers import *
from .parse_bel import BELParser
from .parse_control import ControlParser
from .parse_identifier import IdentifierParser
from .parse_metadata import MetadataParser
