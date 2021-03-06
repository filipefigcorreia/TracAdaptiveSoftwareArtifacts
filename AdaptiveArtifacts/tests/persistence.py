# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import unittest
from trac.test import EnvironmentStub
from AdaptiveArtifacts.persistence.db import Setup
from AdaptiveArtifacts.persistence.data import DBPool
from AdaptiveArtifacts.model.core import Instance, Entity, Attribute
from AdaptiveArtifacts.model.pool import InstancePool
from AdaptiveArtifacts.tests.model import MetaModelInstancesStructure, ModelInstancesStructure, ModelComplianceValidation, PoolOperations, InstanceVersions

class TestBasicEntityBehaviour(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.persistence.db.*'])
        Setup(self.env).upgrade_environment(self.env.get_db_cnx())

        self.Vehicle = Entity(name="Vehicle")
        self.Car = Entity(name="Car", bases=(self.Vehicle,),
                attributes=[Attribute(name="Wheels", multiplicity=4, atype=str)]
            )
        self.lightningMcQueen = self.Car(
                values={"Wheels": ['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel']}
            )

        pool = InstancePool()
        pool.add(self.Vehicle)
        pool.add(self.Car)
        pool.add(self.lightningMcQueen)
        dbp = DBPool(self.env, pool)
        dbp.save('anonymous',"","120.0.0.1")

    def test_load_one(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lightningMcQueen = pool.get_item(self.lightningMcQueen.get_id())
        self.assertEqual(lightningMcQueen.get_id(), self.lightningMcQueen.get_id())
        self.assertEqual(len(lightningMcQueen.get_value("Wheels")), 4)

    def test_load_related(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lightningMcQueen = pool.get_item(self.lightningMcQueen.get_id())
        self.assertTrue(not pool.get_item(self.Car.get_id()) is None)
        self.assertTrue(not pool.get_item(self.Vehicle.get_id()) is None)

    def test_load_all_specs(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_specs()
        self.assertEqual(len(pool.get_items((1,))), 2)
        self.assertTrue(not pool.get_item(self.Car.get_id()) is None)
        self.assertTrue(not pool.get_item(self.Vehicle.get_id()) is None)

    def test_load_artifacts_of_spec(self):
        # add a couple more instances
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_specs()
        car1 = self.Car(values={"License": "GO-42-42"})
        plane2 = self.Vehicle(values={"License": "GO-55-55"})
        pool.add(car1)
        pool.add(plane2)
        dbp.save('me', 'a couple more instances', '127.0.0.1')

        # load cars only
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifacts_of(self.Car.get_name())
        
        self.assertEqual(len(pool.get_items((0,))), 2)
        self.assertTrue(not pool.get_item(self.lightningMcQueen.get_id()) is None)
        self.assertTrue(not pool.get_item(car1.get_id()) is None)

    def test_edit_spec_name(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_spec("Car")
        Car = dbp.pool.get_item("Car")

        # create three more versions
        Car._is_modified = True
        dbp.save('me', 'a new version', '127.0.0.1')
        Car._is_modified = True
        dbp.save('me', 'a new version', '127.0.0.1')
        Car._is_modified = True
        dbp.save('me', 'a new version', '127.0.0.1')

        # so, there should be 4 versions now
        ch = [(version, timestamp, author, ipnr, comment) for version, timestamp, author, ipnr, comment in dbp.get_history(Car)]
        self.assertEqual(len(ch), 4)

        # edit the name
        Car._replace_name("Automobile")
        dbp.save('me', 'a couple more instances', '127.0.0.1')

        # querying by the new name should render 5 versions
        self.assertEqual(Car.get_name(), "Automobile")
        ch = [(version, timestamp, author, ipnr, comment) for version, timestamp, author, ipnr, comment in dbp.get_history(Car)]
        self.assertEqual(len(ch), 5)

    def test_delete_unmodified(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lightningMcQueen = pool.get_item(self.lightningMcQueen.get_id())
        dbp.delete(lightningMcQueen, 'me', 'deleted stuff', '127.0.0.1')
        self.assertTrue(pool.get_item(lightningMcQueen.get_id()) is None)

        pool2 = InstancePool()
        dbp2 = DBPool(self.env, pool2)
        self.assertRaises(ValueError, dbp2.load_artifact, self.lightningMcQueen.get_id())
        self.assertTrue(pool2.get_item(self.lightningMcQueen.get_id()) is None)

    def test_delete_new(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())

        sallyCarrera = self.Car()
        pool.add(sallyCarrera)

        dbp = DBPool(self.env, pool)
        dbp.delete(sallyCarrera, 'me', 'deleted stuff', '127.0.0.1')
        self.assertEqual(3, len(dbp.pool.get_items((0,1))))

    def test_delete_changed(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lightningMcQueen = pool.get_item(self.lightningMcQueen.get_id())
        self.lightningMcQueen.set_value('Wheels', ['front middle wheel', 'rear left wheel', 'front right wheel'])
        dbp.delete(lightningMcQueen, 'me', 'deleted stuff', '127.0.0.1')
        self.assertTrue(pool.get_item(lightningMcQueen.get_id()) is None)
        self.assertEqual(2, len(dbp.pool.get_items((0,1))))

        pool2 = InstancePool()
        dbp2 = DBPool(self.env, pool2)
        self.assertRaises(ValueError, dbp2.load_artifact, self.lightningMcQueen.get_id())
        self.assertTrue(pool2.get_item(self.lightningMcQueen.get_id()) is None)

    def test_retrieve_history(self):
        # make change
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lm = pool.get_item(self.lightningMcQueen.get_id())
        lm.set_value('License', 'GO-42-42')
        dbp.save('me', 'added license information', '127.0.0.1')

        # reload and inspect
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lm = pool.get_item(self.lightningMcQueen.get_id())
        h = [(version, timestamp, author, ipnr, comment) for version, timestamp, author, ipnr, comment in dbp.get_history(lm)]
        self.assertEqual(len(h), 2)


class Scenarios(object):
    @staticmethod
    def build_saved_and_reloaded_pool(testcase):
        testcase.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.persistence.db.*'])
        Setup(testcase.env).upgrade_environment(testcase.env.get_db_cnx())

        # this works as far as no one inherits from MetaModelInstancesStructureAfterLoad and ModelInstancesStructureAfterLoad
        super(testcase.__class__, testcase).setUp()

        dbp = DBPool(testcase.env, testcase.pool)
        dbp.save('anonymous',"","120.0.0.1")

        new_pool = InstancePool()
        new_dbp = DBPool(testcase.env, new_pool)
        for instance in testcase.pool.get_instances_of(Instance.get_name()):
            new_dbp.load_artifact(instance.get_id())
        for entity in testcase.pool.get_instances_of(Entity.get_name()):
            new_dbp.load_spec(entity.get_name())

        testcase.pool = new_pool

class TestMetaModelInstancesStructureAfterLoad(MetaModelInstancesStructure, unittest.TestCase):
    def setUp(self):
        Scenarios.build_saved_and_reloaded_pool(self)

    def test_instances_attributes(self):
        self._assert_instance_attributes(
                myvehicle_expectations = {'id': 1, 'version': None, 'str_attr': 'id'},
                mycar_expectations = {'id': 2, 'version': None, 'str_attr': 'id'}
            )

class TestModelInstancesStructureAfterLoad(ModelInstancesStructure, unittest.TestCase):
    def setUp(self):
        Scenarios.build_saved_and_reloaded_pool(self)

class TestModelComplianceValidationAfterLoad(ModelComplianceValidation, unittest.TestCase):
    def setUp(self):
        Scenarios.build_saved_and_reloaded_pool(self)

class TestPoolOperationsAfterLoad(PoolOperations, unittest.TestCase):
    def setUp(self):
        Scenarios.build_saved_and_reloaded_pool(self)


