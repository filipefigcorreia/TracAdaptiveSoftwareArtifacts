# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import uuid
import json
from datetime import datetime
from urllib2 import quote
from trac.mimeview.api import Context
from trac.web.chrome import add_notice, add_warning
from trac.util import get_reporter_id
from trac.resource import Resource, get_resource_url
from trac.util.datefmt import format_datetime, user_time
from AdaptiveArtifacts.model.core import Entity, Instance, Attribute
from AdaptiveArtifacts.persistence.search import Searcher

#All the methods here should return a `(template_name, data, content_type)` tuple

def get_index(request, dbp, obj, resource):
    # Load *everything* TODO: make more efficient
    dbp.load_specs()
    dbp.load_artifacts_of(Instance.get_name())

    def get_spec_data(base_spec):
        specs = []
        for spec in sorted(dbp.pool.get_items((1,), base_spec), key=lambda spec: spec.get_name()):
            specs.append((spec, get_spec_data(spec.get_name()), len(dbp.pool.get_instances_of(spec.get_name()))))
        return specs

    specs = get_spec_data(Instance.get_name())

    selected_spec = dbp.pool.get_item(request.req.args.get('spec', ''))
    selected_search = request.req.args.get('search', None)

    if selected_spec is None and not selected_search is None and selected_search == 'no_spec':
        selected_spec = Instance

    if selected_spec is None:
        spec_attrs = []
        artifacts_attrs = []
        artifacts_values = []
        artifacts_pages_count = {}
        artifacts_rel_artifact_count = {}
    else:
        if not selected_search is None and selected_search == 'no_spec':
            artifacts = dbp.pool.get_instances_of(selected_spec.get_name(), direct_instances_only=True)
        else:
            artifacts = dbp.pool.get_instances_of(selected_spec.get_name())

        # Get attributes defined at the spec level ...
        spec_attrs = [(attribute.name, attribute.owner_spec.get_name()) for attribute in selected_spec.get_attributes()]
        # ... and those that only exist at the level of the artifacts themselves
        keys_count = {}
        for a in artifacts:
            for k,v in a.get_values():
                if v:
                    if k in keys_count:
                        keys_count[k].append(v)
                    else:
                        keys_count[k] = [v]
        # first, order attributes by how many values there are for them. that being equal order by attribute name
        all_values = sorted(keys_count.items(), key=lambda x: (len(x[1])*-1, unicode.lower(x[0])))
        artifacts_attrs_names = [k for k,_ in all_values]
        for a_name, a_owner in spec_attrs:
            if a_name in artifacts_attrs_names:
                artifacts_attrs_names.remove(a_name)
        artifacts_attrs = [(a_name, None) for a_name in artifacts_attrs_names]

        # Build a matrix of the attribute values to be shown in the index page
        artifacts_values = []
        for artifact in artifacts:
            values = dict(artifact.get_values())
            ordered_values_lst = []
            for attributes in [spec_attrs, artifacts_attrs]:
                for attribute in attributes:
                    if attribute[0] in values:
                        data = values[attribute[0]]
                        if not type(data) is list:
                            data = [data]
                        joined = ", ".join(data)
                        ordered_values_lst.append({"full": joined, "is_long": True if len(joined) > 40 else None})
                    else:
                        ordered_values_lst.append({"full": u"", "is_long": None})
            artifacts_values.append((artifact, ordered_values_lst))

        # Reorder the lines of the matrix so that artifacts with the first columns filled in appear first
        artifacts_values = sorted(artifacts_values, key=lambda x: tuple([unicode.lower(v["full"]) if v["full"] else 'zzzzzzzzzz' for v in x[1]]))

        # get a count of the number of pages and number of artifacts that are referenced by each artifact
        artifacts_pages_count = {}
        artifacts_rel_artifact_count = {}
        for artifact in artifacts:
            artifacts_pages_count[artifact] = len(list(dbp.get_wiki_page_ref_counts(artifact)))
            artifacts_rel_artifact_count[artifact] = len(list(dbp.get_related_artifact_ref_counts(artifact)))

    # track access
    dbp.track_it("index", "", "view", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'action': 'list',
        'specs': specs,
        'selected_spec': selected_spec,
        'selected_search': selected_search,
        'spec_columns': spec_attrs,
        'arti_columns': artifacts_attrs,
        'artifacts_values': artifacts_values,
        'artifacts_pages_count': artifacts_pages_count,
        'artifacts_rel_artifact_count': artifacts_rel_artifact_count,
    }
    return 'index_page.html', data, None

def get_list_pages(request, dbp, obj, resource):
    artifact_id = request.req.args.get('artifact', None)
    if artifact_id is None:
        raise Exception("No artifact was specified.")
    dbp.load_artifact(artifact_id)
    artifact = dbp.pool.get_item(artifact_id)

    results = []
    from trac.wiki.model import WikiPage
    from trac.resource import get_resource_url
    from trac.search import shorten_result
    for pagename, page_version_id, ref_count in dbp.get_wiki_page_ref_counts(artifact):
        page = WikiPage(dbp.env, pagename)

        results.append(
            {'href': get_resource_url(dbp.env, page.resource, request.req.href),
             'title': pagename,
             'date': user_time(request.req, format_datetime, page.time),
             'author': page.author,
             'excerpt': shorten_result(page.text)}
        )

    data = {
        'context': Context.from_request(request.req, resource),
        'artifact': artifact,
        'results': results,
    }
    return 'list_pages.html', data, None


def get_view_spec(request, dbp, obj, resource):
    # track access
    dbp.track_it("spec", obj.get_id(), "view", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'spec': obj,
        'artifacts_url': request.req.href.adaptiveartifacts(spec=obj.get_name()),
    }
    return 'view_spec_page.html', data, None

def get_view_artifact(request, dbp, obj, resource):
    if not obj.__class__ == Instance:
        spec_name = obj.__class__.get_name()
        spec_url = request.req.href.adaptiveartifacts('spec/' + obj.__class__.get_id(), action='view')
    else:
        spec_name = spec_url = ""

    # Processing artifact values
    values = []
    for name,val in obj.get_values():
        if type(val) is list:
            n_values = len(val)
        else:
            n_values = 1
        values.append((name, n_values, val))


    # Getting wiki pages that refer the artifact
    related_pages = []
    from trac.wiki.model import WikiPage
    from trac.resource import get_resource_url
    from trac.search import shorten_result
    for pagename, page_version_id, ref_count in dbp.get_wiki_page_ref_counts(obj):
        page = WikiPage(dbp.env, pagename)
        related_pages.append(
            {'href': get_resource_url(dbp.env, page.resource, request.req.href),
             'title': pagename,
             'date': user_time(request.req, format_datetime, page.time),
             'author': page.author,
             'excerpt': shorten_result(page.text)})

    # Getting artifacts that this artifact refers to
    referred_artifacts = []
    from AdaptiveArtifacts import get_artifact_id_names_from_text
    for attribute_name, value in obj.get_values():
        for related_artifact_id,related_artifact_text in get_artifact_id_names_from_text(unicode(value)):
            if dbp.pool.get_item(related_artifact_id) is None:
                dbp.load_artifact(related_artifact_id)
            referred_artifacts.append((dbp.pool.get_item(related_artifact_id),  "%s (%s)" % (related_artifact_text, attribute_name)))

    # Getting artifacts whose attribute values refer this artifact
    referring_artifacts = []
    for related_artifact_id, related_artifact_version_id, ref_count in dbp.get_related_artifact_ref_counts(obj):
        if dbp.pool.get_item(related_artifact_id) is None:
            dbp.load_artifact(related_artifact_id)
        artifact = dbp.pool.get_item(related_artifact_id)

        url = request.req.href.adaptiveartifacts('artifact/%d' % (artifact.get_id(),), action='view')
        rel_spec_name = artifact.__class__.get_name() if not artifact.__class__ is Instance else None
        rel_spec_url = request.req.href.adaptiveartifacts('spec', artifact.__class__.get_id(), action='view'),
        id_version, time, author, ipnr, comment, readonly = dbp.get_latest_version_details(artifact.get_id())
        referring_artifacts.append(
            {'href': url,
             'spec_name': rel_spec_name,
             'spec_url': rel_spec_url,
             'author': author,
             'date': user_time(request.req, format_datetime, time),
             'artifact': artifact}
        )

    # Build yuml url
    class YUMLDiagram(object):
        def __init__(self):
            self.classes = []
            self.base_url = "http://yuml.me/diagram/plain/class/"
            self._diagram = ""
            self.is_incomplete = False

        def add_class(self, header, body, associations):
            self.classes.append({'header': header, 'body': body, 'associations': associations})

        def serialize(self):
            for yuml_class in self.classes:
                yuml_fragment = "[" + yuml_class['header']
                if yuml_class['body']:
                    yuml_fragment += "|" + ";".join(yuml_class['body'])
                yuml_fragment += "],"
                self._diagram += yuml_fragment

                if yuml_class['associations']:
                    for association_target,association_label, in yuml_class['associations']:
                        yuml_fragment = "[%s]-%s>[%s]," % (yuml_class['header'], association_label, association_target)
                        self._diagram += yuml_fragment

        def get_dsl_text(self):
            return self._diagram.encode('utf8').replace(" ", "&nbsp;")

        def get_url(self):
            #Could be used for GET requests, as long as it doesn't exceed the maximum URL size
            #return self.base_url + quote(self.get_dsl_text(), "[],;:->=")
            from urllib2 import Request, urlopen
            from urllib import urlencode
            image_filename = urlopen(Request(yuml.base_url, data=urlencode({'dsl_text': yuml.get_dsl_text()}))).read()
            return self.base_url + image_filename

    yuml = YUMLDiagram()

    def artifact_to_yuml_class(rel_artifact, include_values=True):
        def sanitize(value):
            if type(value) == list:
                value = ",".join(value)
            for i, j in {"[": "(",
                         "]": ")",
                         ",": ".",
                         ";": ".",
                         "->": "-",
                         "|": "\\",
                         }.iteritems():
                value = value.replace(i, j)
            return value if len(value) < 128 else "..."

        rel_artifact_title = str(rel_artifact)
        rel_spec_name = (" : " + rel_artifact.__class__.get_name()) if not rel_artifact.__class__ is Instance else ""
        header = rel_artifact_title + rel_spec_name
        body = []
        if include_values:
            for attribute_name, value in rel_artifact.get_values():
                body.append("%s = %s" % (sanitize(attribute_name), sanitize(value)))
        return {'header': sanitize(header), 'body': body, 'associations': []}

    yuml_class = artifact_to_yuml_class(obj)
    yuml_class['body'].append('{bg:orange}') # color the main artifact differently
    yuml_class['associations'] = [(artifact_to_yuml_class(rel_artifact, False)['header'], rel_artifact_text) for rel_artifact, rel_artifact_text in referred_artifacts]
    yuml.add_class(**yuml_class)

    for rel_artifact in referring_artifacts:
        rel_yuml_class = artifact_to_yuml_class(rel_artifact['artifact'])
        rel_yuml_class['associations'] = [(artifact_to_yuml_class(obj, False)['header'], "")]
        yuml.add_class(**rel_yuml_class)

    yuml.serialize()

    # track access
    dbp.track_it("artifact", obj.get_id(), "view", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'spec_name': spec_name,
        'spec_url': spec_url,
        'artifact': obj,
        'artifacts_values': values,
        'related_pages': related_pages,
        'related_artifacts': referring_artifacts,
        'yuml_url': yuml.get_url(),
    }
    return 'view_artifact_%s.html' % (request.get_format(),), data, None

def get_list_spec(request, dbp, obj, resource):
    dbp.load_artifacts_of(obj.get_name())
    artifacts = dbp.pool.get_instances_of(obj.get_name())

    data = {
        'context': Context.from_request(request.req, resource),
        'action': 'list',
        'list_title': obj.get_name() + "s",
        'spec': obj,
        'artifacts': artifacts,
    }
    return 'list_spec_artifacts_page.html', data, None

def get_list_search_no_spec(request, dbp, obj, resource):
    dbp.load_artifacts_of(Instance.get_name())
    artifacts_with_no_spec = dbp.pool.get_instances_of(Instance.get_name(), direct_instances_only=True)

    data = {
        'context': Context.from_request(request.req, resource),
        'action': 'list',
        'list_title': 'Artifacts without a spec',
        'spec': Instance,
        'artifacts': artifacts_with_no_spec,
    }
    return 'list_spec_artifacts_page.html', data, None

def get_list_search_by_filter(request, dbp, obj, resource):
    dbp.load_artifacts_of(Instance.get_name())
    artifacts_with_no_spec = dbp.pool.get_instances_of(Instance.get_name(), direct_instances_only=True)

    # track access
    dbp.track_it("pick_artifact", "", "view", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'url_path': '',
    }
    return 'index_dialog.html', data, None

def post_list_search_artifact_json(request, dbp, obj, resource):
    unparsed_spec = request.req.args.get('spec', '')
    spec_name = json.loads(unparsed_spec) if unparsed_spec else ''
    attributes = json.loads(request.req.args.get('attributes', '[]'))

    search_results = Searcher.search_artifacts(dbp, spec=spec_name, attributes=attributes)
    data = [dict({'term' : term, 'id': artifact.get_id(), 'title': str(artifact), 'spec': artifact.__class__.get_name() if artifact.__class__ != Instance else '', 'url':get_resource_url(dbp.env, Resource('asa', artifact.get_id(), artifact.version), request.req.href)}) for artifact, term in search_results]
    _return_as_json(request, data)
    return

def post_list_search_relatedpages_json(request, dbp, obj, resource):
    unparsed_spec = request.req.args.get('spec', '')
    spec_name = json.loads(unparsed_spec) if unparsed_spec else ''
    attributes = json.loads(request.req.args.get('attributes', '[]'))

    if attributes is None:
        raise Exception("No artifacts specified.")

    from trac.wiki.model import WikiPage
    from trac.resource import get_resource_url
    from trac.search import shorten_result

    artifacts_array = []

    for artifact in attributes:
        try:
            dbp.load_artifact(artifact)
            full_artifact = dbp.pool.get_item(artifact)
            #artifacts_array.append(full_artifact)
            results = []
            for pagename, page_version_id, ref_count in dbp.get_wiki_page_ref_counts(full_artifact):
                page = WikiPage(dbp.env, pagename)

                results.append(
                    {'href': get_resource_url(dbp.env, page.resource, request.req.href),
                     'title': pagename,
                     'date': user_time(request.req, format_datetime, page.time),
                     'author': page.author,
                     'excerpt': shorten_result(page.text)}
                )

            artifacts_array.append(
                {'id': full_artifact.get_id(),
                 'href': request.req.href.adaptiveartifacts('artifact', full_artifact.get_id(), action='view'),
                 'title': str(full_artifact),
                 'results' : results})
        except ValueError:
            continue
    _return_as_json(request, artifacts_array)
    return

def post_list_search_spec_json(request, dbp, obj, resource):
    from AdaptiveArtifacts.persistence.search import Searcher

    term = request.req.args.get('q', '')
    data = Searcher.search_spec_names(dbp, term)
    _return_as_json(request, data)
    return

def _return_as_json(request, data):
    import json
    try:
        msg = json.dumps(data)
        request.req.send_response(200)
        request.req.send_header('Content-Type', 'application/json')
    except Exception:
        import traceback;
        msg = "Oops...\n" + traceback.format_exc()+"\n"
        request.req.send_response(500)
        request.req.send_header('Content-Type', 'text/plain')
    request.req.send_header('Content-Length', len(msg))
    request.req.end_headers()
    request.req.write(msg)

def get_list_search(request, dbp, obj, resource):
    if obj == 'no_spec':
        return get_list_search_no_spec(request, dbp, obj, resource)
    elif obj == 'by_filter':
        return get_list_search_by_filter(request, dbp, obj, resource)

def post_list_search(request, dbp, obj, resource):
    if obj == 'artifact':
        return post_list_search_artifact_json(request, dbp, obj, resource)
    elif obj == 'spec':
        return post_list_search_spec_json(request, dbp, obj, resource)
    elif obj == 'relatedpages':
        return post_list_search_relatedpages_json(request, dbp, obj, resource)

def get_new_spec(request, dbp, obj, resource):
    from model import Entity

    if obj is Entity: # instantiating Entity (i.e., creating a spec)
        pass
    elif obj is Instance or isinstance(obj, Entity): # instantiating an existing spec
        return get_new_artifact(request, dbp, obj, resource)
    else:
        raise Exception("Trying to instantiate something that can't be instantiated '%s'" % (obj,))

    # track access
    dbp.track_it("spec", "", "new", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'types' : ['Text', 'Number'], # , 'Adaptive Artifact'
        'multiplicities' : ['1', '0..*', '1..*'],
        'url_path': request.req.href.adaptiveartifacts('spec', obj.get_name()),
    }
    return 'edit_spec_page.html', data, None

def post_new_spec(request, dbp, obj, resource):
    if obj is Entity: # instantiating Entity (i.e., creating a spec)
        pass
    elif obj is Instance or isinstance(obj, Entity): # instantiating an existing spec
        return post_new_artifact(request.req, dbp, obj, resource)
    else:
        raise Exception("Trying to instantiate something that can't be instantiated '%s'" % (obj,))

    name = request.req.args.get('name')
    parent_name = request.req.args.get('parent')

    attributes = [Attribute(n,m,t) for n,t,m in _group_spec_attributes(request.req)]

    if parent_name:
        dbp.load_spec(parent_name)
        bases = (dbp.pool.get_item(parent_name),)
    else:
        bases = tuple()
    brand_new_inst = Entity(name=name, attributes=attributes, bases=bases)

    dbp.pool.add(brand_new_inst)
    dbp.save(get_reporter_id(request.req), 'comment', request.req.remote_addr)
    add_notice(request.req, 'Your changes have been saved.')
    url = request.req.href.adaptiveartifacts('spec', brand_new_inst.get_name(), action='view')
    request.req.redirect(url)

def get_edit_spec(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity))

    # track access
    dbp.track_it("spec", obj.get_id(), "edit", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'spec': obj,
        'attributes': [(str(uuid.uuid4()),
                        attr.name,
                        attr.owner_spec,
                        attr.get_type_readable(),
                        attr.get_multiplicity_readable()) for attr in obj.get_attributes()],
        'types' : ['Text', 'Number'], # , 'Adaptive Artifact'
        'multiplicities' : ['1', '0..*', '1..*'],
        'url_path': request.req.href.adaptiveartifacts('spec', obj.get_name()),

    }
    return 'edit_spec_page.html', data, None

def post_edit_spec(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity))

    attributes = [Attribute(n,m,t) for n,t,m in _group_spec_attributes(request.req)]

    base = None
    base_name = request.req.args['parent']
    if base_name:
        dbp.load_spec(base_name)
        base = dbp.pool.get_item(request.req.args['parent'])

    obj.replace_state(
        name=request.req.args['name'],
        base=base,
        attributes=attributes)

    dbp.save(get_reporter_id(request.req), 'comment', request.req.remote_addr)
    add_notice(request.req, 'Your changes have been saved.')
    url = request.req.href.adaptiveartifacts('spec', obj.get_name(), action='view')
    request.req.redirect(url)

def get_new_artifact(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity)) # otherwise, we're trying to instantiate something that is not an artifact

    # track access
    dbp.track_it("artifact", obj.get_id(), "new", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'spec_name': obj.get_name() if not obj == Instance else "",
        'url_path': request.req.href.adaptiveartifacts('artifact'),
    }
    return 'edit_artifact_%s.html' % (request.get_format(),), data, None

def post_new_artifact(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity)) # otherwise, we're trying to instantiate something that is not an artifact

    spec_name = request.req.args['spec']
    if spec_name:
        try:
            dbp.load_spec(spec_name)
            spec = dbp.pool.get_item(spec_name)
        except ValueError:
            add_warning(request.req, "Spec '%s' not found, assumed an empty spec instead." % spec_name)
            spec = Instance
    else:
        spec = Instance

    values, str_attr = _group_artifact_values(request.req)
    brand_new_inst = spec(str_attr=str_attr, values=values)

    dbp.pool.add(brand_new_inst)
    dbp.save(get_reporter_id(request.req), 'comment', request.req.remote_addr)

    if request.get_format() == 'page':
        add_notice(request.req, 'Your changes have been saved.')
        url = request.req.href.adaptiveartifacts('artifact/%d' % (brand_new_inst.get_id(),), action='view', format=request.get_format())
        request.req.redirect(url)
    else:
        import json
        url = request.req.href.adaptiveartifacts('artifact/%d' % (brand_new_inst.get_id(),), action='view')
        msg = json.dumps([{'result': 'success', 'resource_id': brand_new_inst.get_id(), 'resource_url': url}])
        request.req.send_response(200)
        request.req.send_header('Content-Type', 'application/json')
        request.req.send_header('Content-Length', len(msg))
        request.req.end_headers()
        request.req.write(msg)

def get_edit_artifact(request, dbp, obj, resource):
    assert(isinstance(obj, Instance)) # otherwise, we're trying to edit something that is not an artifact

    aa_attributes = [name for name, val in obj.get_values()]
    attr_suggestions = [attr.name for attr in obj.get_attributes() if not attr.name in aa_attributes]

    values = []
    for name,val in obj.get_values():
        if type(val) is list:
            for v in val:
                values.append((str(uuid.uuid4()), name, v))
        else:
            values.append((str(uuid.uuid4()), name, val))

    # track access
    dbp.track_it("artifact", obj.get_id(), "edit", request.req.authname, str(datetime.now()))

    data = {
        'context': Context.from_request(request.req, resource),
        'spec_name': obj.__class__.get_name() if not obj.__class__ == Instance else "",
        'artifact': obj,
        'artifact_values': values,
        'attr_suggestions' : attr_suggestions,
        'default': obj.str_attr,
        'url_path': request.req.href.adaptiveartifacts('artifact', obj.get_id()),
        }
    return 'edit_artifact_%s.html' % (request.get_format(),), data, None

def post_edit_artifact(request, dbp, obj, resource):
    assert(isinstance(obj, Instance)) # otherwise, we're trying to edit something that is not an artifact

    spec_name = request.req.args['spec']
    if spec_name:
        try:
            dbp.load_spec(spec_name)
            spec = dbp.pool.get_item(spec_name)
        except ValueError:
            add_warning(request.req, "Type '%s' not found, assumed an empty type instead." % spec_name)
            spec = Instance
    else:
        spec = Instance

    obj.__class__ = spec

    values, str_attr = _group_artifact_values(request.req)
    obj.replace_values(values)
    obj.str_attr = str_attr if not str_attr is None else 'id'

    dbp.save(get_reporter_id(request.req), 'comment', request.req.remote_addr)
    url = request.req.href.adaptiveartifacts('artifact/%s' % (obj.get_id(),), action='view')
    if request.get_format() == 'page':
        add_notice(request.req, 'Your changes have been saved.')

        request.req.redirect(url)
    else:
        import json
        msg = json.dumps([{'result': 'success', 'resource_id': obj.get_id(), 'resource_url': url}])
        request.req.send_response(200)
        request.req.send_header('Content-Type', 'application/json')
        request.req.send_header('Content-Length', len(msg))
        request.req.end_headers()
        request.req.write(msg)

def get_delete_spec(request, dbp, obj, resource):
    assert(isinstance(obj, Entity)) # otherwise, we're trying to delete something that is not a spec

    dbp.delete(obj, 'author', 'comment', 'address')

    add_notice(request.req, 'The Type was deleted.')
    url = request.req.href.adaptiveartifacts()
    request.req.redirect(url)

def get_delete_artifact(request, dbp, obj, resource):
    assert(isinstance(obj, Instance)) # otherwise, we're trying to delete something that is not an artifact

    dbp.delete(obj, 'author', 'comment', 'address')

    add_notice(request.req, 'The Custom Artifact was deleted.')
    url = request.req.href.adaptiveartifacts()
    request.req.redirect(url)

def post_new_tracking(request, dbp, obj, resource):
    data = {}
    if obj == "start":
        resource = json.loads(request.req.args['resource'])
        resource_type = resource['resource_type'] if 'resource_type' in resource else ""
        resource_id = resource['resource_id'] if 'resource_id' in resource else ""
        operation = resource['operation'] if 'operation' in resource else ""
        session_id = dbp.track_it_acc_start(resource_type, resource_id, operation, request.req.authname, str(datetime.now()))
        data = {"id": session_id}
    elif obj == "end":
        id = request.req.args['id']
        dbp.track_it_acc_end(id, str(datetime.now()))
    _return_as_json(request, data)
    return

def _group_spec_attributes(req):
    # group posted attributes into a list of tuples (attr_name, attr_type, attr_multiplicity)
    # {'attr_name_1':'Age', 'attr_type_1':'str', 'attr_multiplicity_1':None} -> [('Age', 'str', None)]
    def _get_details(idx, req):
        attr_type = req.args['attr-type-' + idx]
        attr_multiplicity = req.args['attr-multiplicity-' + idx]
        return {"type": attr_type, "multiplicity": attr_multiplicity}
    def _group_details(d):
        return (d["name"], d["type"], d["multiplicity"])
    return _group_attributes_by_name(req, _get_details, _group_details)

def _group_artifact_values(req):
    # group posted values into a list of ordered (attr_name, attr_value) tuples
    # {'attr_name_1':'Age', 'attr_value_1':'42'} -> [('Age', '42')]
    def _get_details(idx, req):
        return {"value": req.args['attr-value-' + idx]}
    def _group_details(d):
        return (d["name"], d["value"])
    values = _group_attributes_by_name(req, _get_details, _group_details)
    default = None
    if 'default' in req.args:
        default = req.args['attr-name-' + req.args['default']]
    return values, default

def _group_attributes_by_name(req, get_details_fn, group_details_fn):

    def _set_attribute_detail(idx, detail_name, value):
        if not idx in attributes:
            attributes[idx] = {}
        attributes[idx][detail_name] = value

    attributes = {} # { idx: {name: X, order: Y} }
    for key in req.args.keys():
        if len(req.args[key]) > 0 and key[10:] != 'X':
            if key[0:9] == 'attr-name':
                idx = key[10:]
                attr_name = req.args[key]
                _set_attribute_detail(idx, 'name', attr_name)
                for n,v in get_details_fn(idx, req).items():
                    _set_attribute_detail(idx, n, v)
            if key[0:10] == 'attr-order':
                idx = key[11:]
                attr_order = req.args[key]
                _set_attribute_detail(idx, 'order', attr_order)

    def _get_order(key_val):
        if "order" in key_val:
            val = key_val["order"]
            if val.isdigit():
                return int(val)
            else:
                return val
        else:
            return 0

    return [group_details_fn(a) for a in sorted(attributes.values(), key=_get_order)]