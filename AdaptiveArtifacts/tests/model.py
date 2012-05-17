# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import unittest
from AdaptiveArtifacts.model import *

class SimpleTwoLevelInheritanceWithTwoInstancesScenario(object):
    @staticmethod
    def setUp(testecase):
        testecase.Vehicle = Entity(name="Vehicle",
                attributes=[
                    Attribute(name="Number of Engines"),
                    Attribute(name="Brand", multiplicity=1, type=str)
                ]
            )
        testecase.Car = Entity(name="Car", bases=(testecase.Vehicle,),
                attributes=[
                    Attribute(name="Number of Doors", multiplicity=1, type=int)
                ]
            )
        testecase.Corsa = Entity(name="Opel Corsa", bases=(testecase.Car,))

        testecase.myvehicle = testecase.Vehicle(values={"Number of Engines":2, "Brand":"Volvo"})
        testecase.mycar = testecase.Car(values={"Number of Engines":1, "Brand":"Ford", "Number of Doors":5})

        # The pool is not used by this test case but by the ones in the
        # "persistence" module. Despite that, it's defined here because it
        # needs to be updated if we create more entities/instances in this
        # setUp, and having it here makes it easier to be aware of that
        testecase.pool = InstancePool()
        testecase.pool.add(testecase.Vehicle)
        testecase.pool.add(testecase.Car)
        testecase.pool.add(testecase.Corsa)
        testecase.pool.add(testecase.myvehicle)
        testecase.pool.add(testecase.mycar)

class MetaModelInstancesStructure(unittest.TestCase):
    """
    Tests if the rules defined at the meta-model level for the construction
    of entities and instances are producing the right results.
    """
    def setUp(self):
        SimpleTwoLevelInheritanceWithTwoInstancesScenario.setUp(self)

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

    def test_entities_name(self):
        self.assertEqual(self.Car.get_name(), "Car")

    def test_entities_attributes(self):
        for attr, val in {'name': "Vehicle", 'version': None}.iteritems():
            self.assertTrue(hasattr(self.Vehicle, attr))
            self.assertEqual(getattr(self.Vehicle, attr), val)
        for attr, val in {'name': "Car", 'version': None}.iteritems():
            self.assertTrue(hasattr(self.Car, attr))
            self.assertEqual(getattr(self.Car, attr), val)

    def test_entities_extra_attributes(self):
        self.assertTrue(hasattr(self.Vehicle, 'attributes'))
        self.assertEqual(len(self.Vehicle.attributes), 2)
        self.assertTrue(hasattr(self.Car, 'attributes'))
        self.assertEqual(len(self.Car.attributes), 1)

    def test_instances_attributes(self):
        self._assert_instance_attributes(
                myvehicle_expectations = {'id': None, 'version': None, 'str_attr': 'id'},
                mycar_expectations = {'id': None, 'version': None, 'str_attr': 'id'}
            )

    def _assert_instance_attributes(self, myvehicle_expectations, mycar_expectations):
        for attr, val in myvehicle_expectations.iteritems():
            self.assertTrue(hasattr(self.myvehicle, attr))
            self.assertEqual(getattr(self.myvehicle, attr), val)
        self.assertTrue(hasattr(self.myvehicle, 'attr_identifiers'))
        self.assertEqual(len(getattr(self.myvehicle, 'attr_identifiers')), 2)
        for attr, val in mycar_expectations.iteritems():
            self.assertTrue(hasattr(self.mycar, attr))
            self.assertEqual(getattr(self.mycar, attr), val)
        self.assertTrue(hasattr(self.mycar, 'attr_identifiers'))
        self.assertEqual(len(getattr(self.mycar, 'attr_identifiers')), 3)

class ModelInstancesStructure(SimpleTwoLevelInheritanceWithTwoInstancesScenario):
    """
    Tests if the rules defined at the model level for the construction
    of instances are producing the right results.
    """
    def setUp(self):
        SimpleTwoLevelInheritanceWithTwoInstancesScenario.setUp(self)

    def test_inherited_entity_1level(self):
        self.assertEqual(self.Corsa.__bases__[0], self.Car)

    def test_inherited_entity_2levels(self):
        self.assertEqual(self.Corsa.__bases__[0].__bases__[0], self.Vehicle)

    def test_inheritance_hierarchy(self):
        self.assertTrue(issubclass(self.Corsa, self.Car))
        self.assertFalse(issubclass(self.Car, self.Corsa))

    def test_instantiation_hierarchy(self):
        self.assertTrue(isinstance(self.mycar, self.Car))
        self.assertFalse(isinstance(self.mycar, self.Corsa))

    def test_entity_attributes(self):
        self.assertEqual(len(self.Car.attributes), 1)
        self.assertEqual(self.Car.attributes[0].name, 'Number of Doors')
        self.assertEqual(self.Car.attributes[0].multiplicity[0], 1)
        self.assertEqual(self.Car.attributes[0].multiplicity[1], 1)
        self.assertEqual(self.Car.attributes[0].type, int)

    def test_instance_extra_attributes(self):
        self.assertEquals(self.mycar.get_value("Number of Engines"), 1)
        self.assertEquals(self.mycar.get_value("Brand"), "Ford")
        self.assertEquals(self.mycar.get_value("Number of Doors"), 5)

    def test_instance_existing_attribute_values(self):
        self.lightningMcQueen = self.Car(
            values={"Wheels": ['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel']}
            )
        self.assertEqual(len(self.lightningMcQueen.get_value("Wheels")), 4)

    def test_instance_new_attribute_values(self):
        self.lightningMcQueen = self.Car()
        self.lightningMcQueen.set_value('Wheels', ['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel'])
        self.assertEqual(len(self.lightningMcQueen.get_value("Wheels")), 4)

class ModelComplianceValidation(unittest.TestCase):

    def setUp(self):
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
        self.mycar = self.Car(values={"Number of Doors":5, "Brand":"Ford"})
        self.Plane = Entity(name="Plane", bases=(self.Vehicle,),
                attributes=[
                    Attribute(name="Lengths of the Wings", multiplicity=(2,5), type=int)
                ]
            )

        self.my_plane_invalid_multiplicity = self.Plane(values={"Number of Engines":4, "Brand":"Airbus", "Lengths of the Wings":[120, 120, 20, 20, 10, 10]})
        self.my_plane_invalid_type = self.Plane(values={"Brand":"Airbus", "Lengths of the Wings":[120, 120, 20, 20, "10"]})
        self.my_plane_invalid_multiplicity_inherited = self.Plane(values={"Lengths of the Wings":[120, 120, 20, 20, 10]})
        self.my_plane_invalid_type_inherited = self.Plane(values={"Brand":7, "Lengths of the Wings":[120, 120, 20, 20, 10]})

    def test_no_violations(self):
        vvs=self.myvehicle.get_meta_violations()
        self.assertEqual(len(vvs), 0, vvs)
        cvs=self.mycar.get_meta_violations()
        self.assertEqual(len(cvs), 0, cvs)

    def test_multiplicity(self):
        pvs = self.my_plane_invalid_multiplicity.get_meta_violations()
        self.assertEqual(len(pvs), 1, pvs)

    def test_type(self):
        self.assertEqual(len(self.my_plane_invalid_type.get_meta_violations()), 1)

    def test_inherited_multiplicity(self):
        pvs = self.my_plane_invalid_multiplicity_inherited.get_meta_violations()
        self.assertEqual(len(pvs), 1, pvs)

    def test_inherited_type(self):
        pvs = self.my_plane_invalid_type_inherited.get_meta_violations()
        self.assertEqual(len(pvs), 1, pvs)

class PoolOperations(unittest.TestCase):
    def setUp(self):
        self.pool = InstancePool()
        self.Car = Entity(name="Car")
        self.Corsa = Entity(name="Opel Corsa", bases=(self.Car,))
        self.Enjoy = Entity(name="Opel Corsa Enjoy", bases=(self.Corsa,))
        self.pool.add(self.Car)
        self.pool.add(self.Corsa)
        self.pool.add(self.Enjoy)

    def test_pool_items_identities(self):
        entities = self.pool.get_instances_of(Entity.get_id())
        self.assertTrue(len(entities) == 3)
        for ent in entities:
            self.assertEqual(ent.__class__.name, Entity.get_id())
        self.assertTrue(len([ent for ent in entities if ent.get_id() == self.Car.get_id()])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_id() == self.Corsa.get_id()])==1)
        self.assertTrue(len([ent for ent in entities if ent.get_id() == self.Enjoy.get_id()])==1)

    def test_inexistent_instance(self):
            self.assertTrue(self.pool.get_item(id="somerandomid") is None)

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