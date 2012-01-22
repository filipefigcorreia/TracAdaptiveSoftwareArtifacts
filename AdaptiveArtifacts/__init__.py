# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import re
from trac.core import *
from trac.resource import IResourceManager, ResourceNotFound
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_javascript #, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import Markup
from AdaptiveArtifacts.persistable_instance import PersistableInstance, PersistablePool
from util import is_uuid


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
        match = re.match(r'/%s(?:/(.+))?$' % self.base_url, req.path_info)
        if match:
            if match.group(1):
                req.args['asa_resource'] = match.group(1)
            return True
        else:
            return False

    def process_request(self, req):
        action = req.args.get('action', None) # view, edit, list, instantiate
        asa_resource_name = req.args.get('asa_resource', 'entity')
        version = req.args.get('version')
        #old_version = req.args.get('old_version')

        if asa_resource_name.endswith('/'):
            req.redirect(req.href.adaptiveartifacts(asa_resource_name.strip('/')))

        ppool = PersistablePool.load(self.env)
        pi = None
        if is_uuid(asa_resource_name):
            pi = ppool.get_instance(self.env, identifier=asa_resource_name, version=version)
            if pi is None:
                raise ResourceNotFound("No resource found with identifier '%s'" % asa_resource_name)
        else:
            pi = ppool.get_instance(self.env, iname="__"+asa_resource_name, version=version)
            if pi is None:
                raise ResourceNotFound("No resource goes by the iname of '%s'" % asa_resource_name)

        if action is None: # default action depends on the instance's meta-level
            if pi.instance.get_meta_level() > 0:
                action = 'list'
            else:
                action = 'view'

        add_javascript(req, 'adaptiveartifacts/js/uuid.js')
        view = Core._resolve_view(action, req.method)
        if not view is None:
            return view(req, ppool, pi.instance, Core._get_resource(pi.instance))
        else:
            return None # Something's very wront

    @staticmethod
    def _get_resource(instance):
        from trac.resource import Resource
        return Resource('asa', instance.get_identifier(), instance.get_state().version)

    @staticmethod
    def _resolve_view(action, method):
        from AdaptiveArtifacts import views
        mlist = [method_name for method_name in dir(views) if callable(getattr(views, method_name)) and method_name.split('_',1)[0] in ('get', 'post')]
        mname = method.lower() + '_' + action.lower()
        if mname in mlist:
            return getattr(views, mname)
        else:
            return None

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
        pi = PersistableInstance.load(self.env, identifier=resource.id, version=resource.version)
        return "ASA: '" + pi.instance.get_identifier() + "'"

    def resource_exists(self, resource):
        pi = PersistableInstance.load(self.env, identifier=resource.id, version=resource.version)
        return not pi.instance is None

