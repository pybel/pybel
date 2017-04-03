# -*- coding: utf-8 -*-

"""Extensions for PyBEL can be imported from the :code:`pybel.ext` namespace just like normal modules and packages::

    import pybel.ext.extension
    # or
    from pybel.ext import extension as ex
    # or
    from pybel.ext.extension import a_function as af
    # or
    from pybel.ext.extension import *
    # or, even
    from pybel.ext import *

This magic is brought to you by import hooks and :code:`pkg_resources`.

To create your own extension, simply register a :code:`pybel.ext` entry point in your package's :code:`setup.py`::

    setuptools.setup(
        ...
        entry_points = {
            'pybel.ext':
                ['name_of_your_extension = package.module']
        }
        ...
    )

This works just like the standard :code:`console_scripts` entry point and the syntax follows all the same rules.

Your extension will then be importable as :code:`pybel.ext.name_of_your_extension`

.. WARNING::
    PyBEL does not check for collisions in extension names. Please be careful when naming your extension!

See the `test extension on GitHub <https://github.com/pybel/pybel-test-extension>`_ to see a working example of an extension.

:code:`pybel.ext` exists as a package on its own to trick the Python import system...if we just did this work in PyBEL's :code:`__init__.py`, there could be trouble.
"""
from pkg_resources import iter_entry_points

GROUP_NAME = 'pybel.ext'

# Allow `from pybel.ext import *`
__all__ = [entry_point.name for entry_point in iter_entry_points(group=GROUP_NAME, name=None)]


def setup():
    """Add the :code:`pybel.ext` importer/loader to the meta_path. Should probably only be called once."""
    from ..exthook import ExtensionImporter
    importer = ExtensionImporter(GROUP_NAME)
    importer.install()


setup()
del setup  # Do a bit of cleanup. Not sure if it's necessary, but Flask did...
