# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import unittest
from AdaptiveArtifacts import Core
from AdaptiveArtifacts.views import view_get, new_post

class RequestHandling(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_view_resolution(self):
        view = Core._resolve_view(action="view", method="GET")
        self.assertEqual(view_get, view)
        view = Core._resolve_view(action="new", method="POST")
        self.assertEqual(new_post, view)
