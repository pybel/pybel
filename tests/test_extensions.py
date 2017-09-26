# -*- coding: utf-8 -*-

import unittest

try:
    import pybel_test_extension
    run_test_extensions = True
except ModuleNotFoundError:
    run_test_extensions = False


@unittest.skipUnless(run_test_extensions, 'PyBEL test extension is not installed')
class TestExtensions(unittest.TestCase):
    def test_import_extension(self):
        import pybel.ext.test

        assert pybel.ext.test.an_extension_function() == 42

    def test_import_extension_2(self):
        from pybel.ext.test import an_extension_function

        assert an_extension_function() == 42

    def test_import_extension_3(self):
        from pybel.ext import test

        assert test.an_extension_function() == 42

    def test_import_extension_4(self):
        with self.assertRaises(ImportError):
            from pybel.ext import not_an_extension
