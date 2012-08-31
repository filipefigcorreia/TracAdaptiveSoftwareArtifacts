# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.mimeview.api import Context
from trac.web.chrome import add_notice
from util import is_uuid
from AdaptiveArtifacts.model.core import Entity, Instance

#All the methods here should return a `(template_name, data, content_type)` tuple

def index_get(req, dbp, inst, resource):
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


def view_get(req, dbp, inst, resource):
    data = {
        'context': Context.from_request(req, resource),
        'action': 'view',
        'instance': inst,
        'dir': dir(inst),
        'type': type(inst),
        'repr': type(inst),
        'version': inst.version,
    }
    return 'asa_view.html', data, None

def list_get(req, dbp, inst, resource):
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


def new_get(req, dbp, inst, resource):
    from model import Instance, Entity

    if not inst is Instance and not inst is Entity and not isinstance(inst, Entity):
        raise Exception("Trying to instanciate something that is not instantiatable '%s'." % inst)

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'instance_meta': inst,
    }
    return 'asa_new_entity.html' if inst is Entity else 'asa_new_instance.html', data, None


def new_post(req, dbp, inst, resource):
    from model import InstancePool, Entity, Instance, Attribute

    meta = inst
    if meta is Entity: #creating a m1
        name = req.args.get('name')
        parent_name = req.args.get('parent')
        attributes = [
            Attribute(req.args.get('attr_name'), req.args.get('attr_multiplicity'), req.args.get('attr_type'))
        ]
        if parent_name:
            dbp.load_spec(parent_name)
            bases = (dbp.pool.get_item(parent_name),)
        else:
            bases = tuple()
        brand_new_inst = Entity(name=name, attributes=attributes, bases=bases)
    elif issubclass(meta, Instance): #creating a m0
        # group posted values into a dict of attr_name:attr_value
        # {'attr_name_1':'Age', 'attr_value_1':'42'} -> {'Age':'42'}
        values = {}
        for key in req.args.keys():
            if key[0:9] == 'attr-name' and len(req.args[key]) > 0 and key[10:] != 'X':
                idx = key[10:]
                attr_name = req.args[key]
                values[attr_name] = req.args['attr-value-'+idx]
                if 'attr-default_'+idx in req.args:
                    values['str-attr'] = attr_name
        brand_new_inst = meta(values=values)
    else:
        raise Exception("Trying to instanciate a not instantiatable instance '%s'." % meta)

    dbp.pool.add(brand_new_inst)
    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts(brand_new_inst.get_id(), action='view')
    req.redirect(url)