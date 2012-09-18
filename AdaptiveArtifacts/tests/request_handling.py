# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import unittest
from AdaptiveArtifacts import Core
from AdaptiveArtifacts.views import get_view_spec, post_new_artifact

class RequestHandling(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_view_resolution(self):
        view = Core._resolve_view(res_type="spec", action="view", method="GET")
        self.assertEqual(get_view_spec, view)
        view = Core._resolve_view(res_type="artifact", action="new", method="POST")
        self.assertEqual(post_new_artifact, view)
