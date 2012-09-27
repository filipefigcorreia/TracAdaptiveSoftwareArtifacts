# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.mimeview.api import Context
from trac.web.chrome import add_notice
import uuid
from AdaptiveArtifacts.model.core import Entity, Instance, Attribute

#All the methods here should return a `(template_name, data, content_type)` tuple

def get_index(req, dbp, inst, resource):
    # Load *everything* TODO: make more efficient
    dbp.load_specs()
    dbp.load_instances_of(Instance.get_name())

    specs = []
    for spec in dbp.pool.get_items((1,)):
        specs.append((spec, len(dbp.pool.get_instances_of(spec.get_name()))))

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'specs': specs,
    }
    return 'asa_index.html', data, None

def get_view_spec(req, dbp, inst, resource):
    data = {
        'context': Context.from_request(req, resource),
        'spec': inst,
    }
    return 'asa_view_spec.html', data, None

def get_view_artifact(req, dbp, inst, resource):
    data = {
        'context': Context.from_request(req, resource),
        'artifact': inst,
    }
    return 'asa_view_artifact.html', data, None

def get_list_spec(req, dbp, inst, resource):
    dbp.load_instances_of(inst.get_name())
    artifacts = dbp.pool.get_instances_of(inst.get_name())

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'list_title': inst.get_name() + "s",
        'spec': inst,
        'artifacts': artifacts,
    }
    return 'asa_list_spec_artifacts.html', data, None

def get_list_aggregate(req, dbp, inst, resource):
    dbp.load_instances_of(Instance.get_name())
    artifacts_with_no_spec = dbp.pool.get_instances_of(Instance.get_name(), direct_instances_only=True)

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'list_title': 'Artifacts without a spec',
        'spec': Instance,
        'artifacts': artifacts_with_no_spec,
    }
    return 'asa_list_spec_artifacts.html', data, None

def get_new_spec(req, dbp, inst, resource):
    from model import Entity

    if inst is Entity: # instantiating Entity (i.e., creating a spec)
        pass
    elif inst is Instance or isinstance(inst, Entity): # instantiating an existing spec
        return get_new_artifact(req, dbp, inst, resource)
    else:
        raise Exception("Trying to instantiate something that can't be instantiated '%s'" % (inst,))

    data = {
        'context': Context.from_request(req, resource),
        'types' : ['text', 'number', 'artifact'],
        'multiplicities' : ['1', '0..*', '1..*'],
        'url_path': req.path_info,
    }
    return 'asa_edit_spec.html', data, None

def post_new_spec(req, dbp, inst, resource):
    if inst is Entity: # instantiating Entity (i.e., creating a spec)
        pass
    elif inst is Instance or isinstance(inst, Entity): # instantiating an existing spec
        return post_new_artifact(req, dbp, inst, resource)
    else:
        raise Exception("Trying to instantiate something that can't be instantiated '%s'" % (inst,))

    name = req.args.get('name')
    parent_name = req.args.get('parent')

    attributes = [Attribute(n,m,t) for n,t,m in _group_spec_attributes(req)]

    if parent_name:
        dbp.load_spec(parent_name)
        bases = (dbp.pool.get_item(parent_name),)
    else:
        bases = tuple()
    brand_new_inst = Entity(name=name, attributes=attributes, bases=bases)

    dbp.pool.add(brand_new_inst)
    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts('spec/%s' % (brand_new_inst.get_name(),), action='view')
    req.redirect(url)

def get_edit_spec(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity))

    data = {
        'context': Context.from_request(req, resource),
        'spec': inst,
        'attributes': [(str(uuid.uuid4()),
                        attr.name,
                        attr.owner_spec,
                        attr.get_type_readable(),
                        attr.get_multiplicity_readable()) for attr in inst.get_attributes()],
        'types' : ['text', 'number', 'artifact'],
        'multiplicities' : ['1', '0..*', '1..*'],
        'url_path': req.path_info,
    }
    return 'asa_edit_spec.html', data, None

def post_edit_spec(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity))

    attributes = [Attribute(n,m,t) for n,t,m in _group_spec_attributes(req)]

    base = None
    base_name = req.args['parent']
    if base_name:
        dbp.load_spec(base_name)
        base = dbp.pool.get_item(req.args['parent'])

    inst.replace_state(
        name=req.args['name'],
        base=base,
        attributes=attributes)

    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts('spec/%s' % (inst.get_name(),), action='view')
    req.redirect(url)

def get_new_artifact(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity)) # otherwise, we're trying to instantiate something that is not an artifact

    data = {
        'context': Context.from_request(req, resource),
        'spec': inst,
        'url_path': req.path_info,
    }
    return 'asa_edit_artifact.html', data, None

def post_new_artifact(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity)) # otherwise, we're trying to instantiate something that is not an atifact

    values, str_attr = _group_artifact_values(req)
    brand_new_inst = inst(str_attr=str_attr, values=values)

    dbp.pool.add(brand_new_inst)
    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts('artifact/%d' % (brand_new_inst.get_id(),), action='view')
    req.redirect(url)

def get_edit_artifact(req, dbp, inst, resource):
    assert(isinstance(inst, Instance)) # otherwise, we're trying to edit something that is not an artifact

    data = {
        'context': Context.from_request(req, resource),
        'spec': inst.__class__,
        'artifact': inst,
        'values': [(attr,val) for attr,val in inst.get_values()],
        'default': inst.str_attr,
        'url_path': req.path_info,
    }
    return 'asa_edit_artifact.html', data, None

def post_edit_artifact(req, dbp, inst, resource):
    assert(isinstance(inst, Instance)) # otherwise, we're trying to edit something that is not an artifact

    values, str_attr = _group_artifact_values(req)
    inst.replace_values(values.items())
    inst.str_attr = str_attr if not str_attr is None else 'id'

    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts('artifact/%s' % (inst.get_id(),), action='view')
    req.redirect(url)

def get_delete_spec(req, dbp, inst, resource):
    assert(isinstance(inst, Entity)) # otherwise, we're trying to delete something that is not a spec

    dbp.delete(inst, 'author', 'comment', 'address')

    url = req.href.adaptiveartifacts()
    req.redirect(url)

def get_delete_artifact(req, dbp, inst, resource):
    assert(isinstance(inst, Instance)) # otherwise, we're trying to delete something that is not an artifact

    spec = inst.__class__
    dbp.delete(inst, 'author', 'comment', 'address')

    url = req.href.adaptiveartifacts('spec/%s' % (spec.get_name(),), action='list')
    req.redirect(url)

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
