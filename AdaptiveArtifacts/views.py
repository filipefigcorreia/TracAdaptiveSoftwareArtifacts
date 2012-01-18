from trac.mimeview.api import Context
from trac.web.chrome import add_notice
from util import is_uuid

def _render_view(req, ppool, instance, resource):
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


def _render_list(req, entities, context_instance, instances, resource):
    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'resource': resource,
        'context_instance': context_instance,
        'entities': entities,
        'instances': instances,
    }
    return 'asa_list.html', data, None

def _render_instantiate(req, instance_meta, shallow_instance, resource):
    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'resource': resource,
        'instance_meta': instance_meta,
        'instance': shallow_instance,
    }
    return 'asa_edit.html', data, None


#All the methods here should return a `(template_name, data, content_type)` tuple

def get_view(req, ppool, instance, resource):
    return _render_view(req, instance, resource)

def get_list(req, ppool, instance, resource):
    entities = [pi.instance for pi in ppool.get_instances_of(ppool.env, instance.get_identifier(), [1])]
    instances = [pi.instance for pi in ppool.get_instances_of(ppool.env, instance.get_identifier(), [0])]
    return _render_list(req, entities, instance, instances, resource)

def get_instantiate(req, ppool, instance, resource):
    from model import InstancePool, Package, Property, Entity
    from presentable_instance import PresentableInstance

    a_m2_class = InstancePool.get_metamodel_python_class_by_id(instance.get_identifier())
    if not a_m2_class in [Package, Property, Entity]:
        raise Exception("Trying to instanciate a not instantiatable instance '%s'." % a_m2_class)
    brand_new_instance = a_m2_class.get_new_default_instance(pool=ppool.pool, name="A New " + a_m2_class.__name__)
    Property(ppool.pool, "A New Property", owner=brand_new_instance.get_identifier())
    return _render_instantiate(req, PresentableInstance(instance), PresentableInstance(brand_new_instance), resource)

def post_instantiate(req, ppool, instance, resource):
    from model import InstancePool, Package, Property, Entity

    meta = instance
    a_m2_class = InstancePool.get_metamodel_python_class_by_id(instance.get_identifier())
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
    ppool.save(ppool.env)
    add_notice(req, 'Your changes have been saved.')
    id = brand_new_instance.get_identifier()
    url = req.href.adaptiveartifacts(id, action='view')
    req.redirect(url)