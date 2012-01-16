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
        pass
