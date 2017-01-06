"""PyBEL Extensions"""
from pkg_resources import iter_entry_points
import sys
import warnings

this_module = sys.modules[__name__]

for entry_point in iter_entry_points(group='pybel.ext', name=None):
    name = entry_point.name
    if getattr(this_module, name, None):
        warnings.warn('An extension named `{}` has already been imported. Alert the author of `{}` about this collision.'.format(name, entry_point.module_name))
    else:
        setattr(this_module, name, entry_point.load())
