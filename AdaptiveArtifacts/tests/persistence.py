# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import shutil
import tempfile
import unittest
from trac.test import EnvironmentStub, Mock
from trac.util import get_reporter_id
from trac.web.api import Request, RequestDone
from AdaptiveArtifacts.persistence.db import Setup
from AdaptiveArtifacts.persistence.data import DBPool
from AdaptiveArtifacts.model.core import Instance, Entity, Attribute
from AdaptiveArtifacts.model.pool import InstancePool
from AdaptiveArtifacts.tests.model import MetaModelInstancesStructure, ModelInstancesStructure, ModelComplianceValidation, PoolOperations, InstanceVersions

class BasicEntityBehaviour(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.db.*'])
        Setup(self.env).upgrade_environment(self.env.get_db_cnx())

        self.Car = Entity(name="Car",
                attributes=[Attribute(name="Wheels", multiplicity=4, type=str)]
            )
        self.lightningMcQueen = self.Car(
                values={"Wheels": ['front left wheel', 'front right wheel', 'rear left wheel', 'front right wheel']}
            )

        pool = InstancePool()
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

"""
    def test_properties(self):
        dbp = DBPool(self.env)
        pinstances = dbp.load_instances_of(ppool.pool.get_instance_by_iname('__property').get_identifier())
        self.assertEqual(len(pinstances), 1, "Wrong number of properties. Expected %r. Got %r.")
        self.assertEqual(self.wheels.get_identifier(), pinstances[0].instance.get_identifier(), "Wrong property. Expected %r. Got %r.")

    def test_property_values(self):
        ppool = PersistablePool.load(self.env)
        pi_car = ppool.get_instance(self.env, self.car.get_identifier())
        pi_a_car = ppool.get_instance(self.env, self.lightningMcQueen.get_identifier())
        values = pi_a_car.instance.get_value(self.wheels.get_identifier())
        self.assertTrue(isinstance(values, list), "Expected values with multiplicity > 1 ('%s')" % (values,))
        self.assertEqual(4, len(values), "Wrong number of wheels. Expected %r. Got %r." % (4, len(values)))
"""

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
        ModelComplianceValidation.setUp(self)

class TestPoolOperationsAfterLoad(PoolOperations, unittest.TestCase):
    def setUp(self):
        PoolOperations.setUp(self)

class TestInstanceVersionsAfterLoad(InstanceVersions, unittest.TestCase):
    def setUp(self):
        InstanceVersions.setUp(self)