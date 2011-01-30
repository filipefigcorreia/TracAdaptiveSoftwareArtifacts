# AdaptiveArtifacts plugin

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider #, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, datefmt
from time import time


#ToDo: implement this: trac.env.IEnvironmentSetupParticipant

class AdaptiveArtifactsPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)


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



