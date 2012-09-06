# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import re
from trac.core import *
from trac.resource import IResourceManager, ResourceNotFound
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_javascript #, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import Markup
from AdaptiveArtifacts.persistable_instance import AdaptiveArtifact, PersistablePool
from AdaptiveArtifacts.persistence.data import DBPool
from AdaptiveArtifacts.model.pool import InstancePool
from AdaptiveArtifacts.model.pool import Entity, Instance
from util import is_uuid
from AdaptiveArtifacts.persistence.db import *

class Core(Component):
    """Core module of the plugin. Provides the Adaptive-Artifacts themselves."""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IResourceManager)

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
        action = req.args.get('action', None) # view, edit, list, index, new
        asa_resource_type = req.args.get('asa_resource_type', None)
        asa_resource_name = req.args.get('asa_resource', None)
        version = req.args.get('version')
        #old_version = req.args.get('old_version')

        if not asa_resource_name is None and asa_resource_name.endswith('/'):
            req.redirect(req.href.adaptiveartifacts(asa_resource_name.strip('/')))

        dbp = DBPool(self.env, InstancePool())

        if asa_resource_type is None:
            inst = None
            action = 'index'
        else:
            if not asa_resource_type in ['spec', 'artifact']:
                raise Exception("Unknown type of resource '%s'" % (asa_resource_type,))

            if asa_resource_name is None:
                if asa_resource_type == 'spec':
                    inst = Entity
                elif asa_resource_type == 'artifact':
                    inst = Instance
            else:
                dbp.load_item(asa_resource_name)
                inst = dbp.pool.get_item(asa_resource_name)
                if inst is None:
                    raise ResourceNotFound("No resource found with identifier '%s'" % asa_resource_name)

        if action is None: # default action depends on the instance's meta-level
            if inst is Entity:
                action = 'index'
            elif isinstance(inst, type):
                action = 'list'
            else:
                action = 'view'

        add_javascript(req, 'adaptiveartifacts/js/uuid.js')
        view = Core._resolve_view(asa_resource_type, action, req.method)
        if not view is None:
            res = Core._get_resource(inst) if not inst in (Entity, Instance, None) else None
            return view(req, dbp, inst, res)
        else:
            raise Exception("Unable to find a view for %s, %s, %s" % (asa_resource_type, action, req.method))

    @staticmethod
    def _resolve_view(res_type, action, method):
        assert res_type in ['spec', 'artifact', None]
        from AdaptiveArtifacts import views
        mlist = [method_name for method_name in dir(views) if callable(getattr(views, method_name)) and method_name.startswith(('get_', 'post_'))]
        if res_type is None:
            mname = '%s_%s' % (method.lower(), action.lower())
        else:
            mname = '%s_%s_%s' % (method.lower(), action.lower(), res_type.lower())
        if mname in mlist:
            return getattr(views, mname)
        else:
            return None

    @staticmethod
    def _get_resource(instance):
        from trac.resource import Resource
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
        return href.asa_resource(resource.id)

    def get_resource_description(self, resource, format='default', context=None, **kwargs):
        pi = AdaptiveArtifact.load(self.env, identifier=resource.id, version=resource.version)
        #TODO: instead of using the identifier, use the text_repr_expr property value, if it exists
        return "ASA: '" + pi.instance.get_identifier() + "'"

    def resource_exists(self, resource):
        pi = AdaptiveArtifact.load(self.env, identifier=resource.id, version=resource.version)
        return not pi.instance is None

