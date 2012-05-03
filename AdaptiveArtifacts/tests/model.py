# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.
#

import unittest
from AdaptiveArtifacts.model import *

class BasicEntityBehaviour(unittest.TestCase):
    def test_named_entity(self):
        corsa = Entity(name="Opel Corsa")
        self.assertEqual(corsa.get_name(), "Opel Corsa")

class EntityInheritance(unittest.TestCase):
    def setUp(self):
        self.Car = Entity("Car")
        self.Corsa = Entity("Opel Corsa", bases=(self.Car,))
        self.Enjoy = Entity("Opel Corsa Enjoy", bases=(self.Corsa,))
        self.my_corsa = self.Corsa()

    def test_inherited_entity_1level(self):
        self.assertEqual(self.Corsa.__bases__[0], self.Car)

    def test_inherited_entity_2levels(self):
        self.assertEqual(self.Enjoy.__bases__[0].__bases__[0], self.Car)

    def test_inheritance_hierarchy(self):
        self.assertTrue(issubclass(self.Enjoy, self.Car))
        self.assertFalse(issubclass(self.Car, self.Enjoy))

    def test_instantiation_hierarchy(self):
        self.assertTrue(isinstance(self.my_corsa, self.Corsa))
        self.assertFalse(isinstance(self.my_corsa, self.Enjoy))


class Properties(unittest.TestCase):
    def setUp(self):
        self.Car = Entity(name="Car",
            attributes=[
                    Attribute(name="Wheels", multiplicity=4, type=str)
                ]
            )

    def test_property(self):
        self.assertEqual(len(self.Car.attributes), 1)
        self.assertEqual(self.Car.attributes[0].name, 'Wheels')

    def test_existing_property_values(self):
        self.lightningMcQueen = self.Car(
            wheels=['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel'])
        self.assertEqual(len(self.lightningMcQueen.wheels), 4)

    def test_new_property_values(self):
        self.lightningMcQueen = self.Car()
        self.lightningMcQueen.__dict__['wheels'] = ['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel']
        self.assertEqual(len(self.lightningMcQueen.wheels), 4)

    def test_new_instance_has_iname_translation(self):
        for key in self.car.get_state().slots.keys():
            self.assertTrue(not key.startswith('__'), "Found a iname ('%s') where a uuid was expected." % key)


class MetaModelSanityCheck(unittest.TestCase):
    def setUp(self):
        self.pool = InstancePool()
        self.Vehicle = Entity(name="Vehicle",
                attributes=[
                    Attribute(name="Number of Engines"),
                    Attribute(name="Brand", multiplicity=1, type=str)
                ]
            )
        self.myvehicle = self.Vehicle(values={"Number of Engines":2, "Brand":"Volvo"})
        self.Car = Entity(name="Car", bases=(self.Vehicle,),
                attributes=[
                    Attribute(name="Number of Doors", multiplicity=1, type=int)
                ]
        )
        self.mycar = self.Car(values={"Number of Engines":1, "Brand":"Ford", "Number of Doors":5})

    def test_entities_are_instances_of_instance(self):
        self.assertTrue(isinstance(self.Car, Entity))
        self.assertTrue(isinstance(self.Vehicle, Entity))

    def test_entities_are_subclasses_of_instance(self):
        self.assertTrue(issubclass(self.Car, self.Vehicle))
        self.assertTrue(issubclass(self.Vehicle, Instance))

    def test_instances_are_instance_of_instance(self):
        self.assertTrue(isinstance(self.mycar, self.Car))
        self.assertTrue(isinstance(self.mycar, self.Vehicle))
        self.assertTrue(isinstance(self.mycar, Instance))

    def test_instance_properties(self):
        instance_iname = "__instance"
        expected_prop_inames = ['__text_repr_expr', '__packageof','__name', '__meta'] # the "instance" Entity has no __inherits
        self.assert_properties(instance_iname, expected_prop_inames, number_filled_slots=4)

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
        slot_inames = instance.get_state().inames.values()
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
        self.assertEqual(len(expected_prop_inames), len(slot_inames), "Instance '%s' contains unexpected inames. \nExpected %s. \nFound: %s." % (instance_iname, expected_prop_inames, slot_inames))
        self.assertEqual(len(expected_prop_inames), number_filled_slots, "Instance '%s' contains unexpected inames. \nExpected %s. \nFound: %s." % (instance_iname, expected_prop_inames, prop_inames))

    def test_no_inames_as_property_id(self):
        for instance in self.pool.instances.values():
            for key in instance.get_state().slots.keys():
                self.assertTrue(not key.startswith('__'), "The instance with iname '%s' has a property with an iname ('%s') instead of an id." % (instance.get_iname(), key))

class ModelInspection(unittest.TestCase):
    def setUp(self):
        self.pool = InstancePool()
        self.Car = Entity(name="Car")
        self.Corsa = Entity(name="Opel Corsa", bases=(self.Car,))
        self.Enjoy = Entity(name="Opel Corsa Enjoy", bases=(self.Corsa,))
        self.pool.add(self.Car)
        self.pool.add(self.Corsa)
        self.pool.add(self.Enjoy)

    def test_model_instances(self):
        entities = self.pool.get_entities()
        self.assertTrue(len(entities) == 3)
        for ent in entities:
            self.assertEqual(ent.__class__.name, Entity.get_id())
        self.assertTrue(len([ent for ent in entities if ent.get_id() == self.Car.get_id()])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_id() == self.Corsa.get_id()])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_id() == self.Enjoy.get_id()])==1)

    def test_model_instances_names(self):
        entities = self.pool.get_entities()
        for ent in entities:
            self.assertEqual(ent.__class__.__name__, "Entity")
        self.assertTrue(len([ent for ent in entities if ent.get_name() == "Car"])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_name() == "Opel Corsa"])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_name() == "Opel Corsa Enjoy"])==1)

class Instantiation(unittest.TestCase):
    def test_instance_meta(self):
        Car = Entity(name="Car")
        car = Car()
        self.assertEqual(Car.get_id(), car.__class__.get_id())

class InstanceVersions(unittest.TestCase):
    def setUp(self):
        self.Car = Entity(name="Car",
            attributes=[Attribute(name="Brand", multiplicity=1, type=str)]
            )
        self.lightningMcQueen = self.Car()

    def test_change_uncommitted_instance(self):
        self.assertEquals(self.lightningMcQueen.version, None)
        self.assertTrue(self.lightningMcQueen.is_uncommitted())

        self.lightningMcQueen.set_value("Brand", 'Dodge')

        self.assertEquals(self.lightningMcQueen.get_value("Brand"), 'Dodge')
        self.assertEquals(self.lightningMcQueen.version, None)
        self.assertTrue(self.lightningMcQueen.is_uncommitted())


class PoolOperations(unittest.TestCase):
    def test_inexistent_instance(self):
        pool = InstancePool()
        self.assertTrue(pool.get_instance(id="somerandomid") is None)

if __name__ == "__main__":
    unittest.main()