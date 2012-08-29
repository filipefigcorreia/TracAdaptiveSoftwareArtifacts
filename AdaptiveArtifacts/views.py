# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.mimeview.api import Context
from trac.web.chrome import add_notice
from util import is_uuid

#All the methods here should return a `(template_name, data, content_type)` tuple

def index_get(req, dbp, inst, resource):
    dbp.load_instances_of(inst.get_id())
    instances = dbp.pool.get_instances_of(inst.get_id())

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'context_instance': inst,
        'instances': instances,
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

    if not inst in [Instance, Entity]:
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
    elif meta is Instance: #creating a m0
        values = {
            'spec_name': req.args['spec_name'],
            'attr_name': req.args['attr_name'],
            'attr_value': req.args['attr_value']
            }
        brand_new_inst = meta(values=values)
    else:
        raise Exception("Trying to instanciate a not instantiatable instance '%s'." % meta)

    dbp.pool.add(brand_new_inst)
    dbp.save('author', 'comment', 'address')
    add_notice(req, 'Your changes have been saved.')
    url = req.href.adaptiveartifacts(brand_new_inst.get_id(), action='view')
    req.redirect(url)