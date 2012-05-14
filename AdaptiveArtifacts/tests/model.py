# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

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

    def test_entity_attributes(self):
        self.assertEqual(len(self.Car.attributes), 1)
        self.assertEqual(self.Car.attributes[0].name, 'Wheels')
        self.assertEqual(self.Car.attributes[0].multiplicity, 4)
        self.assertEqual(self.Car.attributes[0].type, str)

    def test_existing_attribute_values(self):
        self.lightningMcQueen = self.Car(
            values={"Wheels": ['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel']}
            )
        self.assertEqual(len(self.lightningMcQueen.get_value("Wheels")), 4)

    def test_new_attribute_values(self):
        self.lightningMcQueen = self.Car()
        self.lightningMcQueen.set_value('Wheels', ['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel'])
        self.assertEqual(len(self.lightningMcQueen.get_value("Wheels")), 4)

class SimpleTwoLevelInheritanceWithTwoInstancesScenario(unittest.TestCase):
    def setUp(self):
        self.Vehicle = Entity(name="Vehicle",
                attributes=[
                    Attribute(name="Number of Engines"),
                    Attribute(name="Brand", multiplicity=1, type=str)
                ]
            )
        self.Car = Entity(name="Car", bases=(self.Vehicle,),
                attributes=[
                    Attribute(name="Number of Doors", multiplicity=1, type=int)
                ]
            )

        self.myvehicle = self.Vehicle(values={"Number of Engines":2, "Brand":"Volvo"})
        self.mycar = self.Car(values={"Number of Engines":1, "Brand":"Ford", "Number of Doors":5})

class MetaModelRules(SimpleTwoLevelInheritanceWithTwoInstancesScenario):
    """
    Tests if the rules defined at the meta-model level for the construction
    of entities and instances are producing the right results.
    """
    def test_entities_are_instances_of_entity(self):
        self.assertTrue(isinstance(self.Car, Entity))
        self.assertTrue(isinstance(self.Vehicle, Entity))

    def test_entities_are_subclasses_of_instance(self):
        self.assertTrue(issubclass(self.Car, self.Vehicle))
        self.assertTrue(issubclass(self.Vehicle, Instance))

    def test_instances_are_instances_of_instance(self):
        self.assertTrue(isinstance(self.mycar, self.Car))
        self.assertTrue(isinstance(self.mycar, self.Vehicle))
        self.assertTrue(isinstance(self.mycar, Instance))

    def test_builtin_properties_of_entities(self):
        for entity in [self.Vehicle, self.Car]:
            self.assertTrue(hasattr(entity, 'name'))
            self.assertTrue(hasattr(entity, 'version'))
            self.assertTrue(hasattr(entity, 'attributes'))

    def test_builtin_properties_of_instances(self):
        for instance in [self.myvehicle, self.mycar]:
            self.assertTrue(hasattr(instance, 'id'))
            self.assertTrue(hasattr(instance, 'version'))
            self.assertTrue(hasattr(instance, 'str_attr'))
            self.assertTrue(hasattr(instance, 'attr_identifiers'))

    def test_extra_properties_of_instances(self):
        from AdaptiveArtifacts.model.util import to_valid_identifier_name
        self.assertTrue(hasattr(self.myvehicle, to_valid_identifier_name("Number of Engines")))
        self.assertTrue(hasattr(self.myvehicle, to_valid_identifier_name("Brand")))
        self.assertTrue(hasattr(self.mycar, to_valid_identifier_name("Number of Doors")))

class ModelRules(SimpleTwoLevelInheritanceWithTwoInstancesScenario):
    """
    Tests if the rules defined at the model level for the construction
    of instances are producing the right results.
    """
    def test_extra_properties_of_instances(self):
        from AdaptiveArtifacts.model.util import to_valid_identifier_name
        self.assertTrue(hasattr(self.myvehicle, to_valid_identifier_name("Number of Engines")))
        self.assertTrue(hasattr(self.myvehicle, to_valid_identifier_name("Brand")))
        self.assertTrue(hasattr(self.mycar, to_valid_identifier_name("Number of Doors")))

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