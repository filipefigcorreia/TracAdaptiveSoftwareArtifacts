# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import uuid
from trac.mimeview.api import Context
from trac.web.chrome import add_notice
from trac.util import get_reporter_id
from AdaptiveArtifacts.model.core import Entity, Instance, Attribute

#All the methods here should return a `(template_name, data, content_type)` tuple

def get_index(request, dbp, obj, resource):
    # Load *everything* TODO: make more efficient
    dbp.load_specs()
    dbp.load_artifacts_of(Instance.get_name())

    specs = []
    for spec in dbp.pool.get_items((1,)):
        specs.append((spec, len(dbp.pool.get_instances_of(spec.get_name()))))

    data = {
        'context': Context.from_request(request.req, resource),
        'action': 'list',
        'specs': specs,
    }
    return 'index_page.html', data, None

def get_view_spec(request, dbp, obj, resource):
    data = {
        'context': Context.from_request(request.req, resource),
        'spec': obj,
    }
    return 'view_spec_page.html', data, None

def get_view_artifact(request, dbp, obj, resource):
    data = {
        'context': Context.from_request(request.req, resource),
        'artifact': obj,
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

def post_list_search_artifact_json(request, dbp, obj, resource):
    from AdaptiveArtifacts.persistence.search import Searcher
    import json
    from trac.resource import get_resource_url
    from trac.resource import Resource

    terms = request.req.args.get('q', '')

    data = []
    for and_terms in terms:
        search_results = Searcher.search_artifacts(dbp, and_terms)
        data.extend([dict({'term' : term, 'id': artifact.get_id(), 'title': str(artifact), 'url':get_resource_url(dbp.env, Resource('asa', artifact.get_id(), artifact.version), request.req.href)}) for artifact, term in search_results])

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
    return

def get_list_search(request, dbp, obj, resource):
    if obj == 'no_spec':
        return get_list_search_no_spec(request, dbp, obj, resource)

def post_list_search(request, dbp, obj, resource):
    if obj == 'artifact':
        a = post_list_search_artifact_json(request, dbp, obj, resource)
        return a

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
        'types' : ['text', 'number', 'artifact'],
        'multiplicities' : ['1', '0..*', '1..*'],
        'url_path': request.req.path_info,
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
    url = request.req.href.adaptiveartifacts('spec/%s' % (brand_new_inst.get_name(),), action='view')
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
        'types' : ['text', 'number', 'artifact'],
        'multiplicities' : ['1', '0..*', '1..*'],
        'url_path': request.req.path_info,
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
    url = request.req.href.adaptiveartifacts('spec/%s' % (obj.get_name(),), action='view')
    request.req.redirect(url)

def get_new_artifact(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity)) # otherwise, we're trying to instantiate something that is not an artifact

    data = {
        'context': Context.from_request(request.req, resource),
        'spec': obj,
        'url_path': request.req.path_info,
    }
    return 'edit_artifact_%s.html' % (request.get_format(),), data, None

def post_new_artifact(request, dbp, obj, resource):
    assert(obj is Instance or isinstance(obj, Entity)) # otherwise, we're trying to instantiate something that is not an atifact

    values, str_attr = _group_artifact_values(request.req)
    brand_new_inst = obj(str_attr=str_attr, values=values)

    dbp.pool.add(brand_new_inst)
    dbp.save(get_reporter_id(request.req), 'comment', request.req.remote_addr)

    if request.get_format() == 'page':
        add_notice(request.req, 'Your changes have been saved.')
        url = request.req.href.adaptiveartifacts('artifact/%d' % (brand_new_inst.get_id(),), action='view', format=request.get_format())
        request.req.redirect(url)
    else:
        import json
        url = request.req.href.adaptiveartifacts('artifact/%d' % (brand_new_inst.get_id(),), action='view')
        msg = json.dumps([{'result': 'success', 'resource': url}])
        request.req.send_response(200)
        request.req.send_header('Content-Type', 'application/json')
        request.req.send_header('Content-Length', len(msg))
        request.req.end_headers()
        request.req.write(msg)

def get_edit_artifact(request, dbp, obj, resource):
    assert(isinstance(obj, Instance)) # otherwise, we're trying to edit something that is not an artifact

    data = {
        'context': Context.from_request(request.req, resource),
        'spec': obj.__class__,
        'artifact': obj,
        'values': [(attr,val) for attr,val in obj.get_values()],
        'default': obj.str_attr,
        'url_path': request.req.path_info,
    }
    return 'edit_artifact_page.html', data, None

def post_edit_artifact(request, dbp, obj, resource):
    assert(isinstance(obj, Instance)) # otherwise, we're trying to edit something that is not an artifact

    values, str_attr = _group_artifact_values(request.req)
    obj.replace_values(values.items())
    obj.str_attr = str_attr if not str_attr is None else 'id'

    dbp.save('author', 'comment', 'address')
    add_notice(request.req, 'Your changes have been saved.')
    url = request.req.href.adaptiveartifacts('artifact/%s' % (obj.get_id(),), action='view')
    request.req.redirect(url)

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

def _group_artifact_values(req):
    # group posted values into a dict of attr_name:attr_value
    # {'attr_name_1':'Age', 'attr_value_1':'42'} -> {'Age':'42'}
    values = {}
    default = None
    for key in req.args.keys():
        if key[0:9] == 'attr-name' and len(req.args[key]) > 0 and key[10:] != 'X':
            idx = key[10:]
            attr_name = req.args[key]
            values[attr_name] = req.args['attr-value-' + idx]
    if 'default' in req.args:
        default = req.args['attr-name-' + req.args['default']]
    return values, default

def _group_spec_attributes(req):
    # group posted attributes into a list of tuples (attr_name,attr_type,attr_multiplicity)
    # {'attr_name_1':'Age', 'attr_type_1':'str', 'attr_multiplicity_1':None} -> [('Age','str',None)]
    attrs = []
    for key in req.args.keys():
        if key[0:9] == 'attr-name' and len(req.args[key]) > 0 and key[10:] != 'X':
            idx = key[10:]
            attr_name = req.args[key]
            attr_type = req.args['attr-type-' + idx]
            attr_multiplicity = req.args['attr-multiplicity-' + idx]
            attrs.append((attr_name, attr_type, attr_multiplicity))
    return attrs
