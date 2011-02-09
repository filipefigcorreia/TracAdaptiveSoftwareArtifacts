"""Unit tests for AdaptiveArtifacts.core (core.py)"""

import unittest
from AdaptiveArtifacts.core import *

class BasicEntityBehaviour(unittest.TestCase):
    def testNamedEntity(self):
        pool = InstancePool()
        ent = Entity(pool, "A new Entity")
        self.assertEqual(ent.name, "A new Entity")

class Instantiation(unittest.TestCase):
    def testSelfMeta(self):
        pool = InstancePool()
        self.assertEqual(pool.get(name="Entity").get_meta().name, "Entity")

    def testOtherMeta(self):
        pool = InstancePool()
        ent = Entity(pool, "Car")
        inst = Instance(pool, "Car")
        self.assertEqual(ent.name, inst.get_meta().name)


"""
    def testStuff2(self):
        self.assertRaises(roman.InvalidRomanNumeralError, roman.fromRoman, s)

class Inheritance(unittest.TestCase):
    def testStuff1(self):
        self.assertRaises(roman.OutOfRangeError, roman.toRoman, 4000)

    def testStuff2(self):
        self.assertRaises(roman.InvalidRomanNumeralError, roman.fromRoman, s)

class Properties(unittest.TestCase):
    pass
"""

if __name__ == "__main__":
    unittest.main()