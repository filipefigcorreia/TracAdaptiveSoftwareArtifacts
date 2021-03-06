# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import re
from trac.core import *
from trac.resource import IResourceManager, Resource
from trac.web.chrome import Chrome, INavigationContributor, ITemplateProvider, add_javascript, add_stylesheet, add_script_data
from trac.web.main import IRequestHandler
from trac.web.api import IRequestFilter
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider, IWikiChangeListener
from trac.wiki.model import WikiPage
from trac.wiki.api import parse_args
from trac.wiki.formatter import system_message
from trac.util import Markup
from trac.mimeview.api import Context
from genshi.builder import tag
from AdaptiveArtifacts.persistence.data import DBPool
from AdaptiveArtifacts.persistence.search import Searcher
from AdaptiveArtifacts.model.pool import InstancePool
from AdaptiveArtifacts.model.pool import Entity, Instance
from AdaptiveArtifacts.requests.request import Request
from AdaptiveArtifacts.views import _get_artifact_details

def get_artifact_ids_from_text(wiki_text):
    return [aid for aid, val in get_artifact_id_names_from_text(wiki_text)]

def get_artifact_id_names_from_text(wiki_text):
    links = re.findall('\[asa[:]([0-9]+)(?:(?:\s+|\.)([^\]]+)?)?\]', wiki_text)
    embeds = get_embedded_artifact_ids_from_text(wiki_text)
    return links + [(aid, u'') for aid in embeds]

def get_embedded_artifact_ids_from_text(wiki_text):
    return re.findall('\[\[ASA\(([0-9]+)\)\]\]', wiki_text)

class Core(Component):
    """Core module of the plugin. Provides the Adaptive-Artifacts themselves. Needed by any of the other components."""
    implements(IRequestHandler, INavigationContributor, IResourceManager, IRequestFilter, ITemplateProvider)

    def __init__(self):
        self.base_url = 'customartifacts'

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
            req.redirect(req.href.customartifacts(asa_resource_id.strip('/')))

        dbp = DBPool(self.env, InstancePool())
        try:
            request = Request(dbp, req)
        except ValueError:
            if 'format' in req.args and req.args['format'] in ['dialog', 'json']:
                raise
            return 'unable_to_retrieve_resource.html', {}, None

        #add_javascript(req, 'customartifacts/js/lib/jstree/jquery.jstree.js')
        #add_javascript(req, 'customartifacts/js/indextree.js')
        add_javascript(req, 'customartifacts/js/index.js')

        if req.environ.get('PATH_INFO', '')[-5:] == 'pages' or req.args.get('asa_resource_type', None) == 'artifact':
            add_stylesheet(req, 'common/css/search.css')

        res = Core._get_resource(request.obj) if not request.obj in (Entity, Instance, None) and not type(request.obj)==unicode else None
        result = request.view(request, dbp, request.obj, res)
        if not request.req.get_header('Content-Length') is None: # we've written directly to the request object
            pass
        else:
            if not result:
                raise Exception("No data returned by view '%s'" % request.view.__name__)
            return result

    @staticmethod
    def _get_resource(instance):
        return Resource('asa', instance.get_id(), instance.version)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'customartifacts'

    def get_navigation_items(self, req):
        return []

    # IResourceManager
    def get_resource_realms(self):
        yield 'asa'

    def get_resource_url(self, resource, href, **kwargs):
        dbp = DBPool(self.env, InstancePool())
        item = dbp.load_item(resource.id)
        return href.customartifacts('artifact/%d' % (resource.id,), action='view')

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        Chrome(self.env).add_jquery_ui(req)
        add_javascript(req, "customartifacts/js/lib/ace/ace.js")
        add_javascript(req, "customartifacts/js/lib/ace/theme-trac_wiki.js")
        add_javascript(req, 'customartifacts/js/lib/jquery.balloon.js')

        add_javascript(req, "customartifacts/js/requests.js")
        add_javascript(req, 'customartifacts/js/tracking.js')
        add_javascript(req, "customartifacts/js/dialogs.js")
        add_javascript(req, 'customartifacts/js/util.js')
        add_javascript(req, 'customartifacts/js/uuid.js')
        add_javascript(req, 'customartifacts/js/forms.js')

        path_parts = req.environ.get('PATH_INFO', '').decode("utf-8").split("/")
        module_area = path_parts[1] if len(path_parts)>1 else None
        if module_area == 'wiki':
            from datetime import datetime
            dbp = DBPool(self.env, InstancePool())
            resource_id = u""
            if len(path_parts) > 2:
                resource_id = path_parts[2]

            if 'action' in req.args and req.args['action'] == 'edit':
                dbp.track_it("wiki", resource_id, "edit", req.authname, str(datetime.now()))
            else:
                dbp.track_it("wiki", resource_id, "view", req.authname, str(datetime.now()))

            page = WikiPage(dbp.env, resource_id)
            add_script_data(req, {'embedded_artifacts': get_embedded_artifact_ids_from_text(page.text)})

        if module_area == 'wiki' and 'action' in req.args and req.args['action'] == 'edit' or \
            module_area in ['ticket', 'newticket']:
                add_javascript(req, "customartifacts/js/wiki.js")

        add_script_data(req, {'baseurl': req.href.customartifacts()})
        add_script_data(req, {'form_token': req.form_token})
        add_stylesheet(req, 'customartifacts/css/asa.css', media='screen')
        add_stylesheet(req, 'customartifacts/css/wiki.css')
        add_stylesheet(req, 'customartifacts/css/ticket.css')
        add_stylesheet(req, 'customartifacts/css/index_page.css')

        return (template, data, content_type)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('customartifacts', resource_filename(__name__, 'htdocs'))]

def inline_system_message(text):
    return tag.span(text, class_="inline-system-message")

class UI(Component):
    """Provides the plugin's user-interface."""
    implements(INavigationContributor, IWikiSyntaxProvider, IWikiMacroProvider, IWikiChangeListener)

    def __init__(self):
        self.base_url = 'customartifacts'

    def _get_link(self, href, artifact_id, label=None, art_attr=None):
        try:
            pool = InstancePool()
            dbp = DBPool(self.env, pool)
            dbp.load_artifact(id=artifact_id)
            artifact = pool.get_item(id=artifact_id)
            spec_name = artifact.__class__.get_name() if not artifact.__class__ is Instance else None
            if not art_attr is None:
                label = artifact.get_value(art_attr)
                if label is None:
                    return inline_system_message(u"Error: The attribute '{0}' was not found.".format(art_attr))

            if label is None:
                label = str(artifact)
            if spec_name is None:
                title = "Custom Software Artifact '%s'" % (label,)
            else:
                title = "Custom Software Artifact '%s' of type '%s'" % (label, spec_name)
        except ValueError:
            title = "Custom Software Artifact with ID '%s' does not exist" % (artifact_id,)
        return tag.a(label, href=href.customartifacts('artifact', artifact_id), class_="asa-link", title=title)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'customartifacts'

    def get_navigation_items(self, req):
        if 'WIKI_VIEW' in req.perm('wiki'): # TODO: there should be specific permissions for ASA
            yield 'mainnav', self.base_url, Markup('<a href="%s">Custom Artifacts</a>' % (
                    self.env.href.customartifacts() ) )

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        return [ ("asa", self._format_asa_link) ]

    def get_wiki_syntax(self):
        # Note that group numbers don't work as the following is only a regexp
        # fragment which will be part of a larger regexp, therefore one must
        # use group names, with reasonably unique names
        return []

    def _format_asa_link(self, formatter, ns, target, label):
        attr_name = None
        if "." in target:
            target, attr_name = target.split(".", 1)
            if len(attr_name)==0: # there are no chars after the ".", assume we want the title
                attr_name = None
                label = None
        else:
            if target==label: # label is the same as target when no label is specified
                label = None
        return self._get_link(formatter.href, target, label, art_attr=attr_name)

    # IWikiMacroProvider

    def get_macros(self):
        yield "ASA"

    def expand_macro(self, formatter, name, content):
        # Example: [[ASA(42)]]
        args, kw = parse_args(content)
        args = [arg.strip() for arg in args]
        if not args or not args[0].isdigit():
            raise TracError('Custom artifact id not specified')
        args, kw = parse_args(content)
        if not args or not args[0].isdigit():
            raise TracError('Custom artifact id not specified')
        artifact_id = int(args[0])
        dbp = DBPool(self.env, InstancePool())
        try:
            dbp.load_artifact(id=artifact_id)
        except ValueError:
            return system_message("Custom Artifact not found", "No custom artifact was found for id '{0}'.".format(artifact_id))
        artifact = dbp.pool.get_item(id=artifact_id)
        artifact_url = formatter.req.href.customartifacts('artifact/{0}'.format(artifact.get_id()))
        res = Core._get_resource(artifact) if not artifact in (Entity, Instance, None) and not type(artifact)==unicode else None
        spec_name, spec_url, values = _get_artifact_details(artifact, formatter.req)

        tpl='view_artifact_dialog.html'
        data = {
            'context': Context.from_request(formatter.req, res),
            'spec_name': spec_name,
            'spec_url': spec_url,
            'artifact': artifact,
            'artifact_url': artifact_url,
            'artifacts_values': values,
        }
        return Chrome(self.env).render_template(formatter.req, tpl, data, None, fragment=True)

    def get_macro_description(self, name):
        return """
Allows to embed Custom Artifacts in a wiki page.

This is how you would embed a custom artifact with identifier "42":
{{{
[[ASA(42)]]]
}}}
"""

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        self._update_wiki_page_ref_count(page)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self._update_wiki_page_ref_count(page)

    def wiki_page_deleted(self, page):
        self._update_wiki_page_ref_count(page)

    def wiki_page_version_deleted(self, page):
        self._update_wiki_page_ref_count(page)

    def wiki_page_renamed(self, page, old_name):
        # self._update_wiki_page_ref_count(old_name) TODO: transfer history linked to the old page name to the new page name
        self._update_wiki_page_ref_count(page)

    def _update_wiki_page_ref_count(self, page):
        artifacts_ids = get_artifact_ids_from_text(page.text)
        dbp = DBPool(self.env, InstancePool())
        dbp.update_wiki_page_references(page, artifacts_ids)

from trac.search import ISearchSource, shorten_result
from trac.resource import get_resource_url
class Search(Component):
    """Allows to search Adaptive-Artifacts resources."""

    implements(ISearchSource)

    # ISearchSource methods
    def get_search_filters(self, req):
        yield ('asa-filter', 'Custom Artifacts', True)

    def get_search_results(self, req, terms, filters):
        if 'asa-filter' in filters:
            for a_id, attr_name, attr_value, vid, time, author in Searcher.search(self.env, terms):
                dbp = DBPool(self.env, InstancePool())
                dbp.load_artifact(a_id)
                artifact = dbp.pool.get_item(a_id)

                res = Resource('asa', a_id, vid)
                link = get_resource_url(self.env, res, req.href)
                title = unicode(artifact)
                text = u"Custom Artifact of the type {0}.".format(artifact.__class__.get_name())
                text += u" {0}: {1}".format(attr_name, shorten_result(attr_value, terms))
                yield (link, title, time, author, text)
        return

