# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import re
from trac.core import *
from trac.resource import IResourceManager
from trac.web.chrome import INavigationContributor, ITemplateProvider #, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, datefmt
from trac.env import IEnvironmentSetupParticipant
from AdaptiveArtifacts.environment_maintainer import ASAEnvironmentMaintainer
from AdaptiveArtifacts.query import Query
from AdaptiveArtifacts.meta_model import InstancePool, Instance

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
            req.args['asa_resource'] = match.group(1) or ''
            return True
        else:
            return False

    def process_request(self, req):
        action = req.args.get('action', 'view')
        asa_resource_name = req.args.get('asa_resource', '')
        #version = req.args.get('version') #TODO: uncomment when we have version ASAs
        #old_version = req.args.get('old_version')

        if asa_resource_name.endswith('/'):
            req.redirect(req.href.wiki(asa_resource_name.strip('/')))

        query = Query.from_url_params(asa_resource_name)
        result = query.execute()
        if len(result.items) == 0:
            pass
        elif len(result.items) == 1:
            result.items

        WikiPage(self.env, resource)
        versioned_page = WikiPage(self.env, asa_resource_name, version=version)

        req.perm(page.resource).require('WIKI_VIEW')
        req.perm(versioned_page.resource).require('WIKI_VIEW')

        if version and versioned_page.version != int(version):
            raise ResourceNotFound(
                _('No version "%(num)s" for Wiki page "%(name)s"',
                  num=version, name=page.name))

        add_stylesheet(req, 'common/css/wiki.css')

        if req.method == 'POST':
            if action == 'edit':
                if 'cancel' in req.args:
                    req.redirect(req.href.wiki(page.name))

                has_collision = int(version) != page.version
                for a in ('preview', 'diff', 'merge'):
                    if a in req.args:
                        action = a
                        break
                versioned_page.text = req.args.get('text')
                valid = self._validate(req, versioned_page)
                if action == 'edit' and not has_collision and valid:
                    return self._do_save(req, versioned_page)
                else:
                    return self._render_editor(req, page, action, has_collision)
            elif action == 'delete':
                self._do_delete(req, versioned_page)
            elif action == 'rename':
                return self._do_rename(req, page)
            elif action == 'diff':
                style, options, diff_data = get_diff_options(req)
                contextall = diff_data['options']['contextall']
                req.redirect(req.href.wiki(versioned_page.name, action='diff',
                                           old_version=old_version,
                                           version=version,
                                           contextall=contextall or None))
        elif action == 'delete':
            return self._render_confirm_delete(req, versioned_page)
        elif action == 'rename':
            return self._render_confirm_rename(req, page)
        elif action == 'edit':
            return self._render_editor(req, versioned_page)
        elif action == 'diff':
            return self._render_diff(req, versioned_page)
        elif action == 'history':
            return self._render_history(req, versioned_page)
        else:
            format = req.args.get('format')
            if format:
                Mimeview(self.env).send_converted(req, 'text/x-trac-wiki',
                                                  versioned_page.text,
                                                  format, versioned_page.name)
            return self._render_view(req, versioned_page)

    def process_request_old(self, req):
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



    # IResourceManager
    def get_resource_realms(self):
        yield 'asa_resource'

    def get_resource_url(self, resource, href, **kwargs):
        return href.asa_resource(resource.id)

    def get_resource_description(self, resource, format='default', context=None, **kwargs):
        """Return a string representation of the resource, according to the
        `format`.

        :param resource: the `Resource` to describe
        :param format: the kind of description wanted. Typical formats are:
                       `'default'`, `'compact'` or `'summary'`.
        :param context: an optional rendering context to allow rendering rich
                        output (like markup containing links)
        :type context: `Context`

        Additional keyword arguments can be given as extra information for
        some formats.

        For example, the ticket with the id 123 is represented as:
         - `'#123'` in `'compact'` format,
         - `'Ticket #123'` for the `default` format.
         - `'Ticket #123 (closed defect): This is the summary'` for the
           `'summary'` format

        Note that it is also OK to not define this method if there's no
        special way to represent the resource, in which case the standard
        representations 'realm:id' (in compact mode) or 'Realm id' (in
        default mode) will be used.
        """
        pool = InstancePool()
        instance = Instance(self.env, resource.id, resource.version)
        if context:
            return tag.a('Blog: '+instance.title, href=context.href.blog(resource.id))
        else:
            return 'Blog: '+bp.title

    def resource_exists(resource):
        """Check whether the given `resource` exists physically.

        :rtype: bool

        Attempting to retrieve the model object for a non-existing
        resource should raise a `ResourceNotFound` exception.
        (''since 0.11.8'')
        """