# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest
from trac.test import EnvironmentStub
from AdaptiveArtifacts.db import Setup
from AdaptiveArtifacts.model import Entity, InstancePool
from AdaptiveArtifacts.persistable_instance import PersistablePool

class BasicEntityBehaviour(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.db.*'])
        self.env.path = tempfile.mkdtemp()
        Setup(self.env).upgrade_environment(self.env.get_db_cnx())

        self.Car = Entity(name="Car",
            attributes={"wheels":"Wheels"},
            multiplicities={"wheels":4},
            types={"wheels":str}
        )
        self.lightningMcQueen = self.Car(wheels=['front left wheel', 'front right wheel', 'rear left wheel', 'rear right wheel'])

        pool = InstancePool()
        pool.add(self.Car)
        pool.add(self.lightningMcQueen)
        ppool = PersistablePool(self.env, pool)
        ppool.save(self.env)


    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_properties(self):
        ppool = PersistablePool.load(self.env)
        pinstances = ppool.get_instances_of(self.env, ppool.pool.get_instance_by_iname('__property').get_identifier())
        self.assertEqual(len(pinstances), 1, "Wrong number of properties. Expected %r. Got %r.")
        self.assertEqual(self.wheels.get_identifier(), pinstances[0].instance.get_identifier(), "Wrong property. Expected %r. Got %r.")

    def test_property_values(self):
        ppool = PersistablePool.load(self.env)
        pi_car = ppool.get_instance(self.env, self.car.get_identifier())
        pi_a_car = ppool.get_instance(self.env, self.lightningMcQueen.get_identifier())
        values = pi_a_car.instance.get_value(self.wheels.get_identifier())
        self.assertTrue(isinstance(values, list), "Expected values with multiplicity > 1 ('%s')" % (values,))
        self.assertEqual(4, len(values), "Wrong number of wheels. Expected %r. Got %r." % (4, len(values)))


