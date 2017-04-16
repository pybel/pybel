# -*- coding: utf-8 -*-

"""

The :mod:`pybel.manager` module serves as an interface between the BEL graph data structure and underlying relational
databases. Its inclusion allows for the caching of namespaces and annotations for much faster lookup than
downloading and parsing upon each compilation.

"""

from . import cache
from . import database_io
from . import models
from .cache import *
from .database_io import *
from .models import *

__all__ = cache.__all__ + database_io.__all__ + models.__all__
