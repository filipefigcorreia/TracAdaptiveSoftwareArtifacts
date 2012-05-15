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
from AdaptiveArtifacts.model import Entity, InstancePool, Attribute

class BasicEntityBehaviour(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.db.*'])
        #self.env.path = tempfile.mkdtemp()
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

    def tearDown(self):
        pass
        #shutil.rmtree(self.env.path)

    def test_load_one(self):
        pool = InstancePool()
        dbp = DBPool(self.env, pool)
        dbp.load_artifact(self.lightningMcQueen.get_id())
        lightningMcQueen = pool.get_instance(self.lightningMcQueen.get_id())
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

