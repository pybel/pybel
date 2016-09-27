import unittest

from pybel.parsers import utils


class TestUtils(unittest.TestCase):
    def test_list2tuple(self):
        l = [None, 1, 's', [1, 2, [4], [[]]]]
        e = (None, 1, 's', (1, 2, (4,), ((),)))
        t = utils.list2tuple(l)

        self.assertEqual(t, e)

    def test_subiterator(self):
        d = [
            (True, 0),
            (False, 1),
            (False, 2),
            (True, 1),
            (False, 1),
            (True, 2),
            (False, 1),
            (False, 2),
            (False, 3)
        ]

        it = iter(utils.subitergroup(d, lambda x: x[0]))

        matched, subit = next(it)
        subit = iter(subit)
        self.assertEqual(matched, (True, 0))
        self.assertEqual((False, 1), next(subit))
        self.assertEqual((False, 2), next(subit))

        matched, subit = next(it)
        subit = iter(subit)
        self.assertEqual(matched, (True, 1))
        self.assertEqual((False, 1), next(subit))

        matched, subit = next(it)
        subit = iter(subit)
        self.assertEqual(matched, (True, 2))
        self.assertEqual((False, 1), next(subit))
        self.assertEqual((False, 2), next(subit))
        self.assertEqual((False, 3), next(subit))
