# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import unittest
from AdaptiveArtifacts import Core
from AdaptiveArtifacts.views import get_view_spec, post_new_artifact
from AdaptiveArtifacts.requests.request import Request as Request

class RequestPartialMock(Request):
    def __init__(self):
        pass

class RequestHandling(unittest.TestCase):
    def test_view_resolution(self):
        req = RequestPartialMock()
        req._resolve_view(res_type="spec", action="view", method="GET")
        self.assertEqual(get_view_spec, req.view)
        req._resolve_view(res_type="artifact", action="new", method="POST")
        self.assertEqual(post_new_artifact, req.view)
