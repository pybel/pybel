"""PyBEL Extensions"""
from pkg_resources import iter_entry_points
import sys


class ExtensionImporter(object):
    def __init__(self, group):
        self.group = group

    @property
    def _group_with_dot(self):
        return '{}.'.format(self.group)

    def install(self):
        sys.meta_path.append(self)

    def find_module(self, fullname, path=None):
        if not fullname.startswith(self._group_with_dot):
            return
        end_name = fullname[len(self._group_with_dot):]
        for entry_point in iter_entry_points(group=self.group, name=None):
            name = entry_point.name
            if name == end_name:
                return self

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        end_name = fullname[len(self._group_with_dot):]
        for entry_point in iter_entry_points(group=self.group, name=end_name):
            mod = entry_point.load()
            sys.modules[fullname] = mod
            return mod
