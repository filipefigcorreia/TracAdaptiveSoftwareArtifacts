# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import uuid
import json
from trac.mimeview.api import Context
from trac.web.chrome import add_notice, add_warning
from trac.util import get_reporter_id
from trac.resource import Resource, get_resource_url
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
                        ordered_values_lst.append(joined[:40] + ' [...]' if len(joined) > 40 else joined)
                    else:
                        ordered_values_lst.append(u"")
            artifacts_values.append((artifact, ordered_values_lst))

        # Reorder the lines of the matrix so that artifacts with the first columns filled in appear first
        artifacts_values = sorted(artifacts_values, key=lambda x: tuple([unicode.lower(v) if v else 'zzzzzzzzzz' for v in x[1]]))

        # get a count of the number of pages that are referenced by each artifact
        artifacts_pages_count = {}
        for artifact in artifacts:
            artifacts_pages_count[artifact] = len(list(dbp.get_wiki_page_ref_counts(artifact)))

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
    }
    return 'index_page.html', data, None

def get_list_pages(request, dbp, obj, resource):
    from trac.util.datefmt import format_datetime, user_time, utc
    from datetime import datetime

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
             'date': user_time(request.req, format_datetime, datetime.now(utc)),
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
    data = {
        'context': Context.from_request(request.req, resource),
        'spec': obj,
    }
    return 'view_spec_page.html', data, None

def get_view_artifact(request, dbp, obj, resource):
    if not obj.__class__ == Instance:
        spec_name = obj.__class__.get_name()
        spec_url = request.req.href.adaptiveartifacts('spec/' + obj.__class__.get_id(), action='view')
    else:
        spec_name = spec_url = ""

    values = []
    for name,val in obj.get_values():
        if type(val) is list:
            n_values = len(val)
        else:
            n_values = 1
        values.append((name, n_values, val))

    data = {
        'context': Context.from_request(request.req, resource),
        'spec_name': spec_name,
        'spec_url': spec_url,
        'artifact': obj,
        'artifacts_values': values,
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

def get_new_spec(request, dbp, obj, resource):
    from model import Entity

    if obj is Entity: # instantiating Entity (i.e., creating a spec)
        pass
    elif obj is Instance or isinstance(obj, Entity): # instantiating an existing spec
        return get_new_artifact(request, dbp, obj, resource)
    else:
        raise Exception("Trying to instantiate something that can't be instantiated '%s'" % (obj,))

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
    dbp.save('author', 'comment', 'address')
    add_notice(request.req, 'Your changes have been saved.')
    url = request.req.href.adaptiveartifacts('spec', brand_new_inst.get_name(), action='view')
    request.req.redirect(url)

def get_edit_spec(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity))

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

    dbp.save('author', 'comment', 'address')
    add_notice(request.req, 'Your changes have been saved.')
    url = request.req.href.adaptiveartifacts('spec', obj.get_name(), action='view')
    request.req.redirect(url)

def get_new_artifact(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity)) # otherwise, we're trying to instantiate something that is not an artifact

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

    dbp.save('author', 'comment', 'address')
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

    url = request.req.href.adaptiveartifacts()
    request.req.redirect(url)

def get_delete_artifact(request, dbp, obj, resource):
    assert(isinstance(obj, Instance)) # otherwise, we're trying to delete something that is not an artifact

    spec = obj.__class__
    dbp.delete(obj, 'author', 'comment', 'address')

    url = request.req.href.adaptiveartifacts('spec/%s' % (spec.get_name(),), action='list')
    request.req.redirect(url)

def _group_spec_attributes(req):
    # group posted attributes into a list of tuples (attr_name, attr_type, attr_multiplicity)
    # {'attr_name_1':'Age', 'attr_type_1':'str', 'attr_multiplicity_1':None} -> [('Age', 'str', None)]
    def _group_attribute(attr_name, idx, req):
        attr_type = req.args['attr-type-' + idx]
        attr_multiplicity = req.args['attr-multiplicity-' + idx]
        return (attr_name, attr_type, attr_multiplicity)
    return _group_attributes_by_name(req, _group_attribute)

def _group_artifact_values(req):
    # group posted values into a list of ordered (attr_name, attr_value) tuples
    # {'attr_name_1':'Age', 'attr_value_1':'42'} -> [('Age', '42')]
    def _group_value(attr_name, idx, req):
        return (attr_name, req.args['attr-value-' + idx])
    values = _group_attributes_by_name(req, _group_value)
    default = None
    if 'default' in req.args:
        default = req.args['attr-name-' + req.args['default']]
    return values, default

def _group_attributes_by_name(req, group_fn):
    attributes = []
    ordered_names = {}
    for key in req.args.keys():
        if len(req.args[key]) > 0 and key[10:] != 'X':
            if key[0:9] == 'attr-name':
                idx = key[10:]
                attr_name = req.args[key]
                attributes.append(group_fn(attr_name, idx, req))
            if key[0:10] == 'attr-order':
                idx = key[11:]
                attr_name = req.args['attr-name-' + idx]
                attr_order = req.args[key]
                ordered_names[attr_name] = attr_order

    def get_order(key_val):
        if ordered_names.has_key(key_val[0]):
            val = ordered_names[key_val[0]]
            if val.isdigit():
                return int(val)
            else:
                return val
        else:
            return 0

    return sorted(attributes, key=lambda x: get_order(x))