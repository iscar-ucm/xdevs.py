import unittest
from xdevs.models import *


class TestModels(unittest.TestCase):
    
        def test_port(self):
            p = Port(int, "test")
            self.assertEqual(p.p_type, int)
            self.assertEqual(p.name, "test")
            self.assertEqual(str(p), "test<int>")
            self.assertIsNone(p.parent)
            self.assertFalse(p) # __bool__ is !empty()

            p.add(1)
            self.assertTrue(p)
            self.assertEqual(p.get(), 1)
            self.assertEqual(len(p), 1)

            p.add(2)
            self.assertTrue(p)
            self.assertEqual(p.get(), 1)
            self.assertEqual(len(p), 2)

            p.clear()
            self.assertFalse(p)

            self.assertRaises(TypeError, p.add, "test")


if __name__ == '__main__':
    unittest.main()
