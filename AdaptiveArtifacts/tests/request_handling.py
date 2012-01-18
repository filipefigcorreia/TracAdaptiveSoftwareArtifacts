# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.
#

import unittest
from AdaptiveArtifacts import Core
from AdaptiveArtifacts.views import get_view, post_instantiate

class RequestHandling(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_view_resolution(self):
        view = Core._resolve_view(action="view", method="GET")
        self.assertEqual(get_view, view)
        view = Core._resolve_view(action="instantiate", method="POST")
        self.assertEqual(post_instantiate, view)
