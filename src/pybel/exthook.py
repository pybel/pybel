# -*- coding: utf-8 -*-

"""Import hook for PyBEL Extensions"""
import sys

from pkg_resources import iter_entry_points


class ExtensionImporter(object):
    """An importer and loader for package resources registered under a particular group.

    args:
        group: a string representing the package resources entry_points group that will be used
    """

    def __init__(self, group):
        self.group = group

    @property
    def _group_with_dot(self):
        return '{}.'.format(self.group)

    def install(self):
        """Call this method to install the new importer to :code:`sys.meta_path`. Should probably only be done once."""
        sys.meta_path.append(self)

    def find_module(self, fullname, path=None):
        """Find a module if its name starts with :code:`self.group` and is registered as a package resources entry_point."""
        if not fullname.startswith(self._group_with_dot):
            return
        end_name = fullname[len(self._group_with_dot):]
        for entry_point in iter_entry_points(group=self.group, name=None):
            name = entry_point.name
            if name == end_name:
                return self

    def load_module(self, fullname):
        """Load a module if its name starts with :code:`self.group` and is registered as a package resources entry_point."""
        if fullname in sys.modules:
            return sys.modules[fullname]
        end_name = fullname[len(self._group_with_dot):]
        for entry_point in iter_entry_points(group=self.group, name=end_name):
            mod = entry_point.load()
            sys.modules[fullname] = mod
            return mod
