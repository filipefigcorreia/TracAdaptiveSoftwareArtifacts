from trac.mimeview.api import Context
from trac.web.chrome import add_notice
from util import is_uuid

#All the methods here should return a `(template_name, data, content_type)` tuple

def view_get(req, ppool, instance, resource):
    data = {
        'context': Context.from_request(req, resource),
        'action': 'view',
        'instance': instance,
        'dir': dir(instance),
        'type': type(instance),
        'repr': type(instance),
        'version': instance.get_state().version,
    }
    return 'asa_view.html', data, None

def list_get(req, ppool, instance, resource):
    entities = [pi.instance for pi in ppool.get_instances_of(ppool.env, instance.get_identifier(), [1])]
    instances = [pi.instance for pi in ppool.get_instances_of(ppool.env, instance.get_identifier(), [0])]

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'context_instance': instance,
        'entities': entities,
        'instances': instances,
    }
    return 'asa_list.html', data, None


def instantiate_get(req, ppool, instance, resource):
    from model import InstancePool, Package, Property, Entity
    from presentable_instance import PresentableInstance

    a_m2_class = InstancePool.get_metamodel_python_class_by_id(instance.get_identifier())
    if not a_m2_class is None:
        if not a_m2_class in [Package, Property, Entity]:
            raise Exception("Trying to instanciate a not instantiatable instance '%s'." % a_m2_class)

        new_instance = a_m2_class.get_new_default_instance(pool=ppool.pool, name="A New " + instance.get_name())
    else: # we're instantiating a model (M1) instance, not a metamodel (M2) instance
        a_m2_class = Entity
        new_instance = a_m2_class.get_new_default_instance(pool=ppool.pool, name="A New " + instance.get_name(), id_meta=instance.get_identifier())

    Property(ppool.pool, "A New Property", owner=new_instance.get_identifier())

    data = {
        'context': Context.from_request(req, resource),
        'action': 'list',
        'instance_meta': PresentableInstance(instance),
        'instance': PresentableInstance(new_instance),
    }
    return 'asa_edit.html', data, None


def instantiate_post(req, ppool, instance, resource):
    from model import InstancePool, Package, Property, Entity, Instance

    meta = instance
    a_m2_class = InstancePool.get_metamodel_python_class_by_id(instance.get_identifier())
    if not a_m2_class is None:
        if not a_m2_class in [Package, Property, Entity]:
            raise Exception("Trying to instanciate a not instantiatable instance '%s'." % a_m2_class)

        brand_new_instance = a_m2_class.get_new_default_instance(pool=ppool.pool, name="A New " + instance.get_name())
    else: # we're instantiating a model (M1) instance, not a metamodel (M2) instance
        if instance.get_meta_level() == '2':
            a_m2_class = Entity
        else:
            a_m2_class = Instance
        brand_new_instance = a_m2_class.get_new_default_instance(pool=ppool.pool, name="A New " + instance.get_name(), id_meta=instance.get_identifier())

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