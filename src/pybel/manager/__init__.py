# -*- coding: utf-8 -*-

"""

The :mod:`pybel.manager` module serves as an interface between the BEL graph data structure and underlying relational
databases. Its inclusion allows for the caching of namespaces and annotations for much faster lookup than
downloading and parsing upon each compilation.

"""

from . import base_manager
from . import cache_manager
from . import database_io
from . import make_json_serializable
from . import models
from . import query_manager
from .base_manager import *
from .cache_manager import *
from .database_io import *
from .models import *
from .query_manager import *

__all__ = (
    cache_manager.__all__ +
    database_io.__all__ +
    models.__all__ +
    base_manager.__all__ +
    query_manager.__all__
)
