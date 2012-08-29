# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import unittest
from trac.test import EnvironmentStub, Mock
from AdaptiveArtifacts.persistence.db import Setup
from AdaptiveArtifacts.persistence.data import DBPool
from AdaptiveArtifacts.model.core import Instance, Entity, Attribute
from AdaptiveArtifacts.model.pool import InstancePool
from AdaptiveArtifacts.tests.model import MetaModelInstancesStructure, ModelInstancesStructure, ModelComplianceValidation, PoolOperations, InstanceVersions

class TestBasicEntityBehaviour(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.db.*'])
        Setup(self.env).upgrade_environment(self.env.get_db_cnx())

        self.Vehicle = Entity(name="Vehicle")
        self.Car = Entity(name="Car", bases=(self.Vehicle,),
                attributes=[Attribute(name="Wheels", multiplicity=4, type=str)]
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

    def test_delete_unmodified(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lightningMcQueen = pool.get_item(self.lightningMcQueen.get_id())
        dbp.delete(lightningMcQueen)
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
        dbp.delete(sallyCarrera)
        self.assertEqual(3, len(dbp.pool.get_items((0,1))))


    def test_delete_changed(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lightningMcQueen = pool.get_item(self.lightningMcQueen.get_id())
        self.lightningMcQueen.set_value('Wheels', ['front middle wheel', 'rear left wheel', 'front right wheel'])
        dbp.delete(lightningMcQueen)
        self.assertTrue(pool.get_item(lightningMcQueen.get_id()) is None)
        self.assertEqual(2, len(dbp.pool.get_items((0,1))))

        pool2 = InstancePool()
        dbp2 = DBPool(self.env, pool2)
        self.assertRaises(ValueError, dbp2.load_artifact, self.lightningMcQueen.get_id())
        self.assertTrue(pool2.get_item(self.lightningMcQueen.get_id()) is None)

    def test_retrieve_history(self):
        self.assertTrue(False)


class Scenarios(object):
    @staticmethod
    def build_saved_and_reloaded_pool(testcase):
        testcase.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.db.*'])
        Setup(testcase.env).upgrade_environment(testcase.env.get_db_cnx())

        # this works as far as no one inherits from MetaModelInstancesStructureAfterLoad and ModelInstancesStructureAfterLoad
        super(testcase.__class__, testcase).setUp()

        dbp = DBPool(testcase.env, testcase.pool)
        dbp.save('anonymous',"","120.0.0.1")

        new_pool = InstancePool()
        new_dbp = DBPool(testcase.env, new_pool)
        for instance in testcase.pool.get_instances_of(Instance.get_id()):
            new_dbp.load_artifact(instance.get_id())
        for entity in testcase.pool.get_instances_of(Entity.get_id()):
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


