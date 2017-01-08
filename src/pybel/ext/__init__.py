from pkg_resources import iter_entry_points

GROUP_NAME = 'pybel.ext'

__all__ = [entry_point.name for entry_point in iter_entry_points(group=GROUP_NAME, name=None)]


def setup():
    from ..exthook import ExtensionImporter
    importer = ExtensionImporter(GROUP_NAME)
    importer.install()

setup()
del setup
