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
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_notice, add_javascript #, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import Markup
from trac.env import IEnvironmentSetupParticipant
from trac.mimeview.api import Context
from AdaptiveArtifacts.environment_maintainer import ASAEnvironmentMaintainer
from AdaptiveArtifacts.persistable_instance import PersistableInstance, PersistablePool
from AdaptiveArtifacts.presentable_instance import PresentableInstance
from util import is_uuid


class Core(Component):
    """Core module of the plugin. Provides the Adaptive-Artifacts themselves."""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IEnvironmentSetupParticipant, IResourceManager)

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
        if action == 'view':
            return self._render_view(req, pi.instance, pi.resource)
        elif action == 'list':
            entities = [pi.instance for pi in ppool.get_instances_of(self.env, pi.instance.get_identifier(), [1])]
            instances = [pi.instance for pi in ppool.get_instances_of(self.env, pi.instance.get_identifier(), [0])]
            return self._render_list(req, entities, pi.instance, instances, pi.resource)
        elif action == 'instantiate':
            if req.method == 'GET': # show instance creation form
                from model import InstancePool, Package, Property, Entity
                a_m2_class = InstancePool.get_metamodel_python_class_by_id(pi.instance.get_identifier())
                if not a_m2_class in [Package, Property, Entity]:
                    raise Exception("Trying to instanciate a not instantiatable instance '%s'." % a_m2_class)
                brand_new_instance = a_m2_class.get_new_default_instance(pool=ppool.pool, name="A New " + a_m2_class.__name__)
                Property(ppool.pool, "A New Property", owner=brand_new_instance.get_identifier())
                return self._render_instantiate(req, PresentableInstance(pi.instance), PresentableInstance(brand_new_instance), pi.resource)
            elif req.method == 'POST': # check for form data and create instance as instructed
                from model import InstancePool, Package, Property, Entity
                meta = pi.instance
                a_m2_class = InstancePool.get_metamodel_python_class_by_id(pi.instance.get_identifier())
                if not a_m2_class in [Package, Property, Entity]:
                    raise Exception("Trying to instanciate a not instantiatable instance '%s'." % a_m2_class)
                #create empty instance of meta
                brand_new_instance = a_m2_class.get_new_default_instance(pool=ppool.pool, name="A brand new " + a_m2_class.__name__)
                for key in req.args.keys(): # go through submitted values
                    value = req.args.get(key)
                    if is_uuid(key): # it's a property of meta
                        ref = key
                        prop = meta.get_property(ref)
                        if prop is None: # let's retrieve it from meta, just to make sure
                            raise Exception("Property '%s' was not found in meta '%s'." % (ref, meta.get_identifier()))
                        if not prop.is_valid_value(value):
                            raise Exception("Not a valid value for property '%s': '%s'" % (prop.get_name(), value))
                        brand_new_instance.set_value(key, value)
                    elif key.startswith('property-name-'): # it's a property of the instance (it's name, to be precise)
                        ref = key.lstrip('property-name-')
                        if not is_uuid(ref):
                            continue # probably a html prototype
                        name = req.args.get(key, '')
                        domain = req.args.get('property-domain-' + ref, '')
                        Property(ppool.pool, name, owner=brand_new_instance.get_identifier(), domain = domain)
                    elif key.startswith('property-domain-'): # it's a property of the instance. ignore, as these properties are already handled when their names are found
                        pass
                    else: # something else that we don't care about
                        pass
                ppool.save(self.env)
                add_notice(req, 'Your changes have been saved.')
                id = brand_new_instance.get_identifier()
                url = req.href.adaptiveartifacts(id, action='view')
                req.redirect(url)
            else:
                return None # Something's very wront

    def _render_view(self, req, instance, resource):
        data = {
            'context': Context.from_request(req, resource),
            'action': 'view',
            'instance': instance,
            'dir': dir(instance),
            'type': type(instance),
            'repr': type(instance),
            'version': resource.version,
        }
        return 'asa_view.html', data, None

    def _render_list(self, req, entities, context_instance, instances, resource):
        data = {
            'context': Context.from_request(req, resource),
            'action': 'list',
            'resource': resource,
            'context_instance': context_instance,
            'entities': entities,
            'instances': instances,
        }
        return 'asa_list.html', data, None

    def _render_instantiate(self, req, instance_meta, shallow_instance, resource):
        data = {
            'context': Context.from_request(req, resource),
            'action': 'list',
            'resource': resource,
            'instance_meta': instance_meta,
            'instance': shallow_instance,
        }
        return 'asa_edit.html', data, None


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
