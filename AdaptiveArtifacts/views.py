# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.mimeview.api import Context
from trac.web.chrome import add_notice
from util import is_uuid
import uuid
from AdaptiveArtifacts.model.core import Entity, Instance, Attribute

#All the methods here should return a `(template_name, data, content_type)` tuple

def get_index(req, dbp, inst, resource):
    # Load *everything* TODO: make more efficient
    dbp.load_specs()
    dbp.load_instances_of(Instance.get_id())

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
        'instance': inst,
    }
    return 'asa_view_entity.html', data, None

def get_view_artifact(req, dbp, inst, resource):
    data = {
        'context': Context.from_request(req, resource),
        'instance': inst,
    }
    return 'asa_view_instance.html', data, None

def get_list_spec(req, dbp, inst, resource):
    return get_list_artifact(req, dbp, inst, resource)

def get_list_artifact(req, dbp, inst, resource):
    dbp.load_instances_of(inst.get_id())
    instances = dbp.pool.get_instances_of(inst.get_id())

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'context_instance': inst,
        'instances': instances,
    }
    #TODO: return right template, depending if we're listing entities or instances
    #TODO: go through all TODOs
    return 'asa_list_instances.html', data, None

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
        'instance_meta': inst,
        'url_path': req.path_info,
    }
    return 'asa_new_entity.html', data, None

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
    url = req.href.adaptiveartifacts('spec/%s' % (brand_new_inst.get_id(),), action='view')
    req.redirect(url)

def get_edit_spec(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity))

    data = {
        'context': Context.from_request(req, resource),
        'instance_meta': inst.__class__,
        'instance': inst,
        'attributes': [(attr,str(uuid.uuid4())) for attr in inst.get_attributes()],
        'url_path': req.path_info,
    }
    return 'asa_new_entity.html', data, None

def post_edit_spec(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity))

    attributes = [Attribute(n,m,t) for n,t,m in _group_spec_attributes(req)]

    inst.replace_attributes(attributes)

    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts('spec/%s' % (inst.get_id(),), action='view')
    req.redirect(url)

def get_new_artifact(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity)) # otherwise, we're trying to instantiate something that is not an artifact

    data = {
        'context': Context.from_request(req, resource),
        'instance_meta': inst,
        'url_path': req.path_info,
    }
    return 'asa_new_instance.html', data, None

def post_new_artifact(req, dbp, inst, resource):
    assert(inst is Instance or isinstance(inst, Entity)) # otherwise, we're trying to instantiate something that is not an atifact

    brand_new_inst = inst(values=_group_artifact_values(req))

    dbp.pool.add(brand_new_inst)
    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts('artifact/%d' % (brand_new_inst.get_id(),), action='view')
    req.redirect(url)

def get_edit_artifact(req, dbp, inst, resource):
    assert(isinstance(inst, Instance)) # otherwise, we're trying to edit something that is not an artifact

    data = {
        'context': Context.from_request(req, resource),
        'instance_meta': inst.__class__,
        'instance': inst,
        'values': [(attr,val) for attr,val in inst.get_values()],
        'url_path': req.path_info,
    }
    return 'asa_new_instance.html', data, None

def post_edit_artifact(req, dbp, inst, resource):
    assert(isinstance(inst, Instance)) # otherwise, we're trying to edit something that is not an artifact

    inst.replace_values(_group_artifact_values(req).items())

    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts('artifact/%s' % (inst.get_id(),), action='view')
    req.redirect(url)

def _group_artifact_values(req):
    # group posted values into a dict of attr_name:attr_value
    # {'attr_name_1':'Age', 'attr_value_1':'42'} -> {'Age':'42'}
    values = {}
    for key in req.args.keys():
        if key[0:9] == 'attr-name' and len(req.args[key]) > 0 and key[10:] != 'X':
            idx = key[10:]
            attr_name = req.args[key]
            values[attr_name] = req.args['attr-value-' + idx]
            if 'attr-default-' + idx in req.args:
                values['str-attr'] = attr_name
    return values

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
