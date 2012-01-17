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

class BasicEntityBehaviour(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'AdaptiveArtifacts.*', 'AdaptiveArtifacts.db.*'])
        self.env.path = tempfile.mkdtemp()
        Setup(self.env).upgrade_environment(self.env.get_db_cnx())

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_something(self):
        from AdaptiveArtifacts.persistable_instance import PersistablePool
        from AdaptiveArtifacts.model import InstancePool, Entity, Property, Instance

        pool = InstancePool(True)
        car = Entity(pool, "Car")
        wheels = Property(pool, "Wheels", car.get_identifier(), "string", "4", "4")
        lightningMcQueen = Instance(pool, car.get_identifier())
        lightningMcQueen.set_value(wheels.get_identifier(), 'front left wheel')
        lightningMcQueen.add_value(wheels.get_identifier(), 'front right wheel')
        lightningMcQueen.add_value(wheels.get_identifier(), 'rear left wheel')
        lightningMcQueen.add_value(wheels.get_identifier(), 'front right wheel')
        ppool = PersistablePool(self.env, pool)
        ppool.save(self.env)
        ppool = PersistablePool.load(self.env)
        pinstances = ppool.get_instances_of(self.env, ppool.get_instance(iname='__property').get_identifier())
        self.assertEqual(len(pinstances), 4)
