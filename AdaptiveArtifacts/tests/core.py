"""Unit tests for AdaptiveArtifacts.core (core.py)"""

import unittest
from AdaptiveArtifacts.core import *

class BasicEntityBehaviour(unittest.TestCase):
    def test_named_entity(self):
        pool = InstancePool()
        corsa = Entity(pool, "Opel Corsa")
        self.assertEqual(corsa.name, "Opel Corsa")

    def test_inherited_entity_1level(self):
        pool = InstancePool()
        car = Entity(pool, "Car")
        corsa = Entity(pool, "Opel Corsa", car.name)
        self.assertEqual(corsa.get_parent().name, 'Car')

    def test_inherited_entity_2levels(self):
        pool = InstancePool()
        car = Entity(pool, "Car")
        corsa = Entity(pool, "Opel Corsa", car.name)
        enjoy = Entity(pool, "Opel Corsa Enjoy", corsa.name)
        self.assertEqual(enjoy.get_parent().get_parent().name, 'Car')

    def test_inheritance_hierarchy(self):
        pool = InstancePool()
        car = Entity(pool, "Car")
        corsa = Entity(pool, "Opel Corsa", car.name)
        enjoy = Entity(pool, "Opel Corsa Enjoy", corsa.name)
        self.assertTrue(enjoy.is_a(car.name))
        self.assertFalse(car.is_a(enjoy.name))

class Properties(unittest.TestCase):
    def test_add_property(self):
        pool = InstancePool()
        car = Entity(pool, "Car")
        wheels = Property(pool, 'Wheels', 4, 4)
        car.add_property(wheels)
        lightningMcQueen = Instance(pool, car)
        lightningMcQueen.add_value('Wheels', 'front left wheel')
        lightningMcQueen.add_value('Wheels', 'front right wheel')
        lightningMcQueen.add_value('Wheels', 'rear left wheel')
        lightningMcQueen.add_value('Wheels', 'front right wheel')
        self.assertEqual(len(lightningMcQueen.values['Wheels']), 4)


class Instantiation(unittest.TestCase):
    def test_self_meta(self):
        pool = InstancePool()
        self.assertEqual(pool.get(name="Entity").get_meta().name, "Entity")

    def test_other_meta(self):
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