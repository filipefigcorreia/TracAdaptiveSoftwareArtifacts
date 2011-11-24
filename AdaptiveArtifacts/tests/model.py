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
        self.corsa = Entity(self.pool, "Opel Corsa", self.car.get_identifier())
        self.enjoy = Entity(self.pool, "Opel Corsa Enjoy", self.corsa.get_identifier())

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
        self.wheels = Property(self.pool, "Wheels", self.car.get_identifier(), "string", "4", "4")

    def test_access_property(self):
        self.assertEqual(len(self.car.get_properties()), 1)
        self.assertEqual(self.car.get_properties()[0].get_name(), 'Wheels')

    def test_add_property(self):
        self.lightningMcQueen = Instance(self.pool, self.car)
        self.lightningMcQueen.add_value('Wheels', 'front left wheel')
        self.lightningMcQueen.add_value('Wheels', 'front right wheel')
        self.lightningMcQueen.add_value('Wheels', 'rear left wheel')
        self.lightningMcQueen.add_value('Wheels', 'front right wheel')
        self.assertEqual(len(self.lightningMcQueen.get_values('Wheels')), 4)


class MetaModelSanityCheck(unittest.TestCase):
    def setUp(self):
        self.pool = InstancePool(True)
        self.expected_entity_prop_inames = ['__inherits', '__packageof','__name', '__meta']
        self.expected_property_prop_inames = ['__owner', '__domain', '__lower_bound', '__upper_bound', '__order', '__name', '__meta']

    def test_self_meta(self):
        self.assertEqual(self.pool.get_instance_by_iname("__entity").get_meta().get_name(), "Entity")

    def test_instance_properties(self):
        instance_iname = "__instance"
        expected_prop_inames = ['__packageof','__name', '__meta']
        self.assert_properties(instance_iname, expected_prop_inames, number_filled_slots=3)

    def test_metaelement_properties(self):
        instance_iname = "__metaelement"
        self.assert_properties(instance_iname, self.expected_entity_prop_inames)

    def test_property_properties(self):
        instance_iname = "__property"
        self.assert_properties(instance_iname, self.expected_entity_prop_inames)

    def test_classifier_properties(self):
        instance_iname = "__classifier"
        self.assert_properties(instance_iname, self.expected_entity_prop_inames)

    def test_package_properties(self):
        instance_iname = "__package"
        self.assert_properties(instance_iname, self.expected_entity_prop_inames)

    def test_entity_properties(self):
        instance_iname = "__entity"
        self.assert_properties(instance_iname, self.expected_entity_prop_inames)

    def test_name_properties(self):
        instance_iname = "__name"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def test_packageof_properties(self):
        instance_iname = "__packageof"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def test_inherits_properties(self):
        instance_iname = "__inherits"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def test_domain_properties(self):
        instance_iname = "__domain"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def test_owner_properties(self):
        instance_iname = "__owner"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def test_lowerbound_properties(self):
        instance_iname = "__lower_bound"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def test_upperbound_properties(self):
        instance_iname = "__upper_bound"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def test_meta_properties(self):
        instance_iname = "__meta"
        self.assert_properties(instance_iname, self.expected_property_prop_inames)

    def assert_properties(self, instance_iname, expected_prop_inames, number_filled_slots=None):
        """
        number_filled_slots -- should be provided if different from the number of properties defined at the meta-level
        """
        instance = self.pool.get_instance_by_iname(instance_iname)
        entity = instance.get_meta()
        slot_inames = instance.state.inames.values()
        prop_inames = [prop.get_iname() for prop in entity.get_properties()]

        for iname in expected_prop_inames:
            # expected inames exist in the instance
            self.assertTrue(iname in slot_inames, "The iname '%s' was not found in the slots of '%s'" % (iname, instance.get_name()))
            # expected inames are defined by the instance's meta
            self.assertTrue(iname in prop_inames, "The iname '%s' was not found in the properties that '%s' defines for '%s'" % (iname, entity.get_name(), instance.get_name()))
            # the get_value_by_iname(...) function works as expected
            self.assertTrue(not instance.get_value_by_iname(iname) is None, "The iname '%s' was not found in '%s' using get_value_by_iname(...)" % (iname, instance.get_name()))

        # no more than the expected inames exist in the instance
        if number_filled_slots is None:
            number_filled_slots = len(prop_inames)
        #TODO: uncomment the following line after getting rid of __meta_level from the slots
        #self.assertEqual(len(expected_prop_inames), len(slot_inames), "Instance '%s' contains unexpected inames. Expected %s. Found: %s." % (instance_iname, expected_prop_inames, slot_inames))
        self.assertEqual(len(expected_prop_inames), number_filled_slots, "Instance '%s' contains unexpected inames. \nExpected %s. \nFound: %s." % (instance_iname, expected_prop_inames, prop_inames))

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
        self.assertTrue(pool.get_instance(id="somerandomid") is None)

if __name__ == "__main__":
    unittest.main()