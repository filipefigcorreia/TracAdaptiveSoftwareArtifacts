# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.
#

"""Unit tests for AdaptiveArtifacts.core (core.py)"""
import unittest
from AdaptiveArtifacts.model import *

class BasicEntityBehaviour(unittest.TestCase):
    def test_named_entity(self):
        pool = InstancePool()
        corsa = Entity(pool, "Opel Corsa")
        self.assertEqual(corsa.get_name(), "Opel Corsa")

class EntityInheritance(unittest.TestCase):
    def setUp(self):
        self.pool = InstancePool()
        self.car = Entity(self.pool, "Car")
        self.corsa = Entity(self.pool, "Opel Corsa", self.car.get_name())
        self.enjoy = Entity(self.pool, "Opel Corsa Enjoy", self.corsa.get_name())

    def test_inherited_entity_1level(self):
        self.assertEqual(self.corsa.get_parent().get_name(), 'Car')

    def test_inherited_entity_2levels(self):
        self.assertEqual(self.enjoy.get_parent().get_parent().get_name(), 'Car')

    def test_inheritance_hierarchy(self):
        self.assertTrue(self.enjoy.is_a(self.car.get_name()))
        self.assertFalse(self.car.is_a(self.enjoy.get_name()))

class Properties(unittest.TestCase):
    def setUp(self):
        self.pool = InstancePool()
        self.car = Entity(self.pool, "Car")
        self.wheels = Property(self.pool, 'Wheels', 4, 4)
        self.car.add_property_old(self.wheels)

    def test_access_property(self):
        self.assertEqual(len(self.car.get_properties_old()), 1)
        self.assertEqual(self.car.get_properties_old()[0].get_name(), 'Wheels')

    def test_add_property(self):
        self.lightningMcQueen = Instance(self.pool, self.car)
        self.lightningMcQueen.add_value('Wheels', 'front left wheel')
        self.lightningMcQueen.add_value('Wheels', 'front right wheel')
        self.lightningMcQueen.add_value('Wheels', 'rear left wheel')
        self.lightningMcQueen.add_value('Wheels', 'front right wheel')
        self.assertEqual(len(self.lightningMcQueen.get_values('Wheels')), 4)


class MetaModelSanityCheck(unittest.TestCase):
    def test_self_meta(self):
        pool = InstancePool(True)
        self.assertEqual(pool.get(name="Entity").get_meta().get_name(), "Entity")

class ModelInspection(unittest.TestCase):
    def setUp(self):
        self.pool = InstancePool(True)
        car = Entity(self.pool, "Car")
        corsa = Entity(self.pool, "Opel Corsa", car.get_name())
        enjoy = Entity(self.pool, "Opel Corsa Enjoy", corsa.get_name())

    def test_list_model_entities(self):
        entities = self.pool.get_model_instances()
        self.assertTrue(len(entities) == 3)
        for ent in entities:
            self.assertEqual(ent.get_meta().get_name(), "Entity")
        self.assertTrue(len([ent for ent in entities if ent.get_name() == "Car"])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_name() == "Opel Corsa"])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_name() == "Opel Corsa Enjoy"])==1)

class Instantiation(unittest.TestCase):
    def test_instance_meta(self):
        pool = InstancePool(True)
        ent = Entity(pool, "Car")
        inst = Instance(pool, ent.get_identifier())
        self.assertEqual(ent.get_name(), inst.get_meta().get_name())


"""
class Inheritance(unittest.TestCase):
class Properties(unittest.TestCase):
"""

class PoolOperations(unittest.TestCase):
    def test_inexistent_instance(self):
        pool = InstancePool()
        self.assertTrue(pool.get(id="someid") is None)
        self.assertTrue(pool.get(name="somename") is None)

if __name__ == "__main__":
    unittest.main()