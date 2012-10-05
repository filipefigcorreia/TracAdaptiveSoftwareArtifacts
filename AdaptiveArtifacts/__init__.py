# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import re
from trac.core import *
from trac.resource import IResourceManager, Resource
from trac.web.chrome import Chrome, INavigationContributor, ITemplateProvider, add_javascript, add_stylesheet
from trac.web.main import IRequestHandler
from trac.web.api import IRequestFilter
from trac.util import Markup
from AdaptiveArtifacts.persistence.data import DBPool
from AdaptiveArtifacts.model.pool import InstancePool
from AdaptiveArtifacts.model.pool import Entity, Instance
from AdaptiveArtifacts.requests.request import Request


class Core(Component):
    """Core module of the plugin. Provides the Adaptive-Artifacts themselves."""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IResourceManager, IRequestFilter)

    def __init__(self):
        self.base_url = 'adaptiveartifacts'

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'adaptiveartifacts'

    def get_navigation_items(self, req):
        yield 'mainnav', self.base_url, Markup('<a href="%s">Adaptive Artifacts</a>' % (
                self.env.href.adaptiveartifacts() ) )

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/%s(?:/([^/]+))?/?(.+)?$' % self.base_url, req.path_info)
        if match:
            if match.group(1):
                req.args['asa_resource_type'] = match.group(1)
            if match.group(2):
                req.args['asa_resource'] = match.group(2)
            return True
        else:
            return False

    def process_request(self, req):
        asa_resource_id = req.args.get('asa_resource', None)
        if not asa_resource_id is None and asa_resource_id.endswith('/'):
            req.redirect(req.href.adaptiveartifacts(asa_resource_id.strip('/')))

        dbp = DBPool(self.env, InstancePool())
        request = Request(dbp, req)

        Chrome(self.env).add_jquery_ui(req)
        add_javascript(req, 'adaptiveartifacts/js/util.js')
        add_javascript(req, 'adaptiveartifacts/js/uuid.js')
        add_javascript(req, 'adaptiveartifacts/js/forms.js')
        add_javascript(req, 'adaptiveartifacts/js/dialogs.js')
        add_stylesheet(req, 'adaptiveartifacts/css/asa.css', media='screen')
        res = Core._get_resource(request.obj) if not request.obj in (Entity, Instance, None) else None
        return request.view(request, dbp, request.obj, res)


    @staticmethod
    def _get_resource(instance):
        return Resource('asa', instance.get_id(), instance.version)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('adaptiveartifacts', resource_filename(__name__, 'htdocs'))]

    # IResourceManager
    def get_resource_realms(self):
        yield 'asa'

    def get_resource_url(self, resource, href, **kwargs):
        dbp = DBPool(self.env, InstancePool())
        item = dbp.load_item(resource.id)
        return href.adaptiveartifacts('artifact/%d' % (resource.id,), action='view')

    """
    def get_resource_description(self, resource, format='default', context=None, **kwargs):
        pi = AdaptiveArtifact.load(self.env, identifier=resource.id, version=resource.version)
        #TODO: instead of using the identifier, use the text_repr_expr property value, if it exists
        return "ASA: '" + pi.instance.get_identifier() + "'"

    def resource_exists(self, resource):
        pi = AdaptiveArtifact.load(self.env, identifier=resource.id, version=resource.version)
        return not pi.instance is None
    """

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_javascript(req, "adaptiveartifacts/js/wiki.js")
        return (template, data, content_type)

from trac.search import ISearchSource, search_to_sql
from trac.resource import get_resource_url
class Search(Component):
    """Search asa resources."""

    implements(ISearchSource)

    # ISearchSource methods

    def get_search_filters(self, req):
        yield ('asa', 'Adaptive Artifacts', False)

    def get_search_results(self, req, terms, filters):
        if 'asa' in filters:
            with self.env.db_query as db:
                sql_query, args = search_to_sql(db, ['val.attr_value'], terms)

                for id, attr_name, attr_value, vid, time, author in db("""
                        SELECT a.id, val.attr_name, val.attr_value, max(v.id), v.time, v.author
                        FROM asa_artifact_value val
                            INNER JOIN asa_version v ON v.id=val.version_id
                            INNER JOIN asa_artifact a ON a.id=val.artifact_id
                        WHERE """ + sql_query +
                        """GROUP BY a.id""", args):
                    #args = '?owner=%s&or&reporter=%s' % (name, name)
                    #link = req.href.query() #+ args
                    res = Resource('asa', id, vid)
                    link = get_resource_url(self.env, res, req.href)
                    yield (link, "%s: %s" % (attr_name,attr_value), time, author, '')
        return

