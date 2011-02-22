# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider #, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, datefmt
from trac.env import IEnvironmentSetupParticipant
from AdaptiveArtifacts.environment_maintainer import ASAEnvironmentMaintainer

class Core(Component):
    """Core module of the plugin. Provides the Adaptive-Artifacts themselves."""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IEnvironmentSetupParticipant)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'adaptiveartifacts'

    def get_navigation_items(self, req):
        yield 'mainnav', 'adaptiveartifacts', Markup('<a href="%s">Adaptive Artifacts</a>' % (
                self.env.href.adaptiveartifacts() ) )

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/adaptiveartifacts'

    def process_request(self, req):
        #add_stylesheet(req, 'adaptiveartifacts/css/style.css')
        return "adaptive_artifacts.cs", "text/html"
        """response_str = 'Hello world!'
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Last-Modified', datefmt.http_date(time()))
        req.send_header('Content-Length', len(response_str))
        req.end_headers()
        req.write(response_str)"""

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('adaptiveartifacts', resource_filename(__name__, 'htdocs'))]

    # IEnvironmentSetupParticipant
    def environment_created(self):
        em = ASAEnvironmentMaintainer(self.env)
        em.install_asa_support()

    def environment_needs_upgrade(self, db):
        return ASAEnvironmentMaintainer(self.env).needs_upgrade()

    def upgrade_environment(self, db):
        ASAEnvironmentMaintainer(self.env).upgrade()

