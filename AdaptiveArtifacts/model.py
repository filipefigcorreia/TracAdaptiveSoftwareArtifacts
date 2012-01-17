# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import uuid
from util import is_uuid

class Version(object):
    id = None

    @classmethod
    def get_all_version(cls, instance=None):
        """
        Returns all the versions of the system, or of a given instance in case it's specified
        """
        return []

    @classmethod
    def get_latest_version(cls, instance=None):
        """
        Returns the latest version of the system, or the latest version for a given instance in case it's specified
        """
        return Version()

    def __init__(self):
        self.states = [] # array of InstanceStates that were created in this version


class Instance(object):
    """
    Represents an instance at any model level
    """
    id = None

    def __init__(self, pool, id_meta, identifier=None, text_repr_expr = '', iname=None, meta_level='0'):
        """
        Arguments:
        pool -- the pool that the instances of this class will belong to
        id_meta -- the Entity to which this instance complies. For M2 and M3 instances it will always be 'Entity'
        identifier -- the uuid that uniquely identifies this instance
        iname -- internal name; exists only for meta-model (M2) instances
        meta_level -- the model level that the instance belongs to: '0', '1' or '2'
        """
        if meta_level == '0' and self.__class__.__name__ != 'Instance':
            raise Exception("All M0s should be naturally born instances.")

        if identifier is None:
            self.__identifier = str(uuid.uuid4())
        else:
            self.__identifier = identifier
        self.__iname = iname
        self.__meta_level = meta_level

        meta = pool.get_instance(id_meta)
        inames_dict = {}
        if not meta is None:
            # This dict will not be complete while the properties roof isn't closed.
            # That's why calling set_properties_definite_id(...) is needed in the end
            inames_dict = meta.get_properties_inames()

        self.state = InstanceState(inames=inames_dict) # TODO: refactor this to a self.states dictionary in which each key,value is of type Version,InstanceState
        self.set_value_by_iname('__meta', id_meta)
        self.set_value_by_iname('__text_repr_expr', text_repr_expr)

        if not pool is None:
            pool.add(self)
        self.pool = pool

    def set_properties_definite_id(self):
        """
        Replace all magic words used in the slots by the respective uuids. Magic words are used
        only while bootstrapping the M2, while the "roof" isn't yet closed.
        """
        for key in self.state.slots.keys():
            if not self.get_property_from_meta(key) is None: # it's a iname. replace by a proper uuid!
                self.set_property_ref(key, self.get_property_from_meta(key).get_identifier())

    def get_identifier(self):
        return self.__identifier

    def get_iname(self):
        return self.__iname

    def get_meta_level(self):
        return self.__meta_level

    def get_id_meta(self):
        return self.get_value_by_iname('__meta')

    def get_meta(self):
        return self.pool.get_instance(self.get_value_by_iname('__meta'))

    def get_text_repr(self):
        text_repr_expr = self.get_value_by_iname('__text_repr_expr')
        if text_repr_expr is None or text_repr_expr=='':
            return self.get_meta().get_name() + " object with id: " + self.get_identifier()[:5] + ".."
        return eval(text_repr_expr)

    def get_property_from_meta(self, iname):
        return self.pool.get_property(self.__class__.id, iname=iname)

    #TODO: refactor. delegate this logic to the state object
    def add_value(self, property_ref, value):
        """
        property_ref: can be either a private system reference, like '__meta', or a uuid identifier, if a reference to a Property
        """
        if not property_ref in self.state.slots:
            self.state.slots[property_ref] = []
        elif property_ref in self.state.slots and not isinstance(self.state.slots[property_ref], list):
            val = self.state.slots[property_ref]
            self.state.slots[property_ref] = [val]
        self.state.slots[property_ref].append(value)

    #TODO: refactor. delegate this logic to the state object
    def set_property_ref(self, iname, property_ref):
        """
        Sets the property_ref for a given iname.
        """
        value = self.get_value_by_iname(iname)
        if not value is None:
            self.set_value(iname, None)
            self.set_value(property_ref, value)
            if iname in self.state.inames.keys():
                del self.state.inames[iname]
            self.state.inames[property_ref] = iname

    #TODO: refactor. delegate this logic to the state object
    def set_value(self, property_ref, value):
        """Overwrite the value for the specified property."""
        if value is None:
            if property_ref in self.state.slots:
                del self.state.slots[property_ref]
        else:
            self.state.slots[property_ref] = value

    #TODO: refactor. delegate this logic to the state object
    def set_value_by_iname(self, iname, value):
        property_ref = self.get_property_ref_if_known(iname)
        self.set_value(property_ref, value)
        self.state.inames[property_ref] = iname

    #TODO: refactor. delegate this logic to the state object
    def get_value(self, property_ref):
        return self.get_slot_value(property_ref)

    #TODO: refactor. delegate this logic to the state object
    def get_value_by_iname(self, iname):
        value = self.get_slot_value(iname)
        if value is None:
            value = self.get_slot_value(self.get_property_ref_if_known(iname))
        return value

    #TODO: refactor. delegate this logic to the state object
    def get_property_iname(self, property_ref):
        if property_ref in self.state.inames:
            return self.state.inames[property_ref]
        return None

    #TODO: refactor. delegate this logic to the state object
    def get_property_ref_if_known(self, iname):
        """
        If property_ref is not know, returns the iname provided as input.
        """
        for property_ref_key, iname_value in self.state.inames.items():
            if iname_value == iname:
                return property_ref_key
        return iname

    #TODO: refactor. delegate this logic to the state object
    def get_slot_value(self, property_ref):
        if not property_ref is None and property_ref in self.state.slots:
            return self.state.slots[property_ref]
        return None

    #TODO: refactor. delegate this logic to the state object
    def get_values(self, property_ref):
        if not property_ref is None and property_ref in self.state.slots:
            return self.state.slots[property_ref]
        else:
            return []

    def reset_class_from_inner_state(self):
        """
        Inspects the instance's state and changes its __class__ accordingly
        """
        if self.get_identifier()==self.get_id_meta(): # special case: closing the meta-* roof
            self.__class__ = Entity
        else:
            self.__class__ = self.pool.get_metamodel_python_class_by_name(self.get_meta().get_name())

    def is_instance(self, name):
        """
        Checks if this instance is of the specified entity (or one of it's parents)
        """
        if self.get_meta().get_name() == name:
            return True
        return self.get_meta().is_subclass(name)

    @classmethod
    def create_from_properties(cls, pool, identifier, iname, meta_level, contents_dict, property_inames_dict):
        instance = Instance(pool, None, identifier) # TODO: fix. id_meta should not be None
        instance.pool.remove(identifier) #TODO: rethink. the instance should not exist in the pool yet. ever. because we're only loading instances only if they don't exist in the pool
        instance.__identifier = identifier
        instance.__iname = iname
        instance.__meta_level = meta_level
        #TODO: state should probably be a dictionary and not a var
        instance.state = InstanceState.create_from_properties(contents_dict, property_inames_dict)
        instance.reset_class_from_inner_state()
        instance.reset_class_id()
        pool.add(instance)
        return instance


class InstanceState(object):

    def __init__(self, inames=None, version=None):
        if inames is None:
            inames = {}
        self.slots = {} # dict in which each key,value is of type unicodestring,arbitraryvalue
        self.inames = inames # translation of uuids to internal names
        #self.version = version # version in which this state was created

    @classmethod
    def create_from_properties(cls, contents_dict, inames_dict):
        state = InstanceState(inames=inames_dict)
        state.slots = contents_dict
        return state


class MetaElementInstance(Instance):
    """
    An instance of a meta-level. I.e., everything except M0s
    """
    id = None

    def __init__(self, pool, name, id_meta, iname, text_repr_expr=None, meta_level='1'):
        if meta_level < '1':
            raise Exception("MetaElementInstances' level must be at least 1")
        if text_repr_expr is None:
            text_repr_expr = 'self.get_name()'
        super(MetaElementInstance, self).__init__(pool=pool, id_meta=id_meta, text_repr_expr=text_repr_expr, iname=iname, meta_level=meta_level)
        self.set_value_by_iname('__name', name)

    @classmethod
    def get_new_default_instance(cls, pool, name):
        #ToDo: Check if there's anything stopping us from making this class abstract
        raise Exception(cls.__name__ + " should never be instantiated directly.")

    def reset_class_id(self):
        if self.get_meta_level() == u'2': # if a meta-model (m2) instance, copy its id to the corresponding python class
            a_m2_class = self.pool.get_metamodel_python_class_by_name(self.get_name())
            if not a_m2_class is None: # not all m2 instances have corresponding python classes
                a_m2_class.id = self.get_identifier()

    def get_name(self):
        """
        Returns the name that was assigned to self.
        Assumes the name is stored in a string property called "name"
        """
        return self.get_value_by_iname('__name')

class Property(MetaElementInstance):
    id = None

    def __init__(self, pool, name, owner, domain = "string", lower_bound = 0, upper_bound = 1, order=None, iname=None, meta_level='1'):
        super(Property, self).__init__(pool=pool, name=name, id_meta=Property.id, iname=iname, meta_level=meta_level)
        self.set_value_by_iname('__owner', owner) #Entity
        self.set_value_by_iname('__domain', domain) #Classifier. will be the id to an other instance, but can also assume the special value "string"
        self.set_value_by_iname('__lower_bound', lower_bound)
        self.set_value_by_iname('__upper_bound', upper_bound)
        self.set_value_by_iname('__order', order)
        #self.set_value_by_iname('__unique', False)
        #self.set_value_by_iname('__read_only', False)

    @classmethod
    def get_new_default_instance(cls, pool, name, owner=None):
        return Property(pool, name, owner)

    def get_domain(self):
        """
        Returns the domain of the property.
        """
        return self.get_value_by_iname("__domain")

    def get_owner_id(self):
        return self.get_value_by_iname("__owner")

    def get_owner(self):
        return self.pool.get_instance(self.get_value_by_iname("__owner"))

    def get_order(self):
        return self.get_value_by_iname("__order")

    def get_lower_bound(self):
        return self.get_value_by_iname("__lower_bound")

    def get_upper_bound(self):
        return self.get_value_by_iname("__lower_bound")

    def get_possible_values(self, instance):
        domain = self.get_domain()
        if is_uuid(domain):
            return [inst_value for inst_value in self.pool.get_instances_of(domain) if not inst_value is instance and int(inst_value.get_meta_level()) == int(self.get_meta_level())-1]
        else:
            return None

    def is_valid_value(self, value):
        #domain
        if not value is None and not value == '':
            possible_values = self.get_possible_values(None)
            if not possible_values is None and not value in possible_values:
                return False

        #cardinality
        #TODO: check cardinality
        return True



class Classifier(MetaElementInstance):
    id = None

    def __init__(self, pool, name, id_meta, iname=None, meta_level='1'):
        super(Classifier, self).__init__(pool=pool, name=name, id_meta=id_meta, iname=iname, meta_level=meta_level)
        self.set_value_by_iname('__packageof', 'default') #Package

class Entity(Classifier):
    id = None

    def __init__(self, pool, name, inherits=None, iname=None, meta_level='1'):
        """
        Arguments:
        pool -- the pool that the instances of this class will belong to
        name -- the name attribute of the entity
        inherits -- the uuid of the Entity from which this Entity derives from
        meta_level -- the model level that the instance belongs to: '0', '1' or '2'. Usually '1'.
        """
        super(Entity, self).__init__(pool=pool, name=name, iname=iname, id_meta=Entity.id, meta_level=meta_level)
        if not inherits is None:
            self.set_value_by_iname('__inherits', inherits)
        else:
            if meta_level=='1':
                self.set_value_by_iname('__inherits', Instance.id) # default value for entities without a parent

        # There will also be 0..* Properties, each stored in its own key
        # TODO: handle properties with cardinality > 1

        # Copy identifiers from the data-meta-model to the hardcoded-meta-model, for convenience
        # Only does something for M2 entities
        self.reset_class_id()

    @classmethod
    def get_new_default_instance(cls, pool, name):
        return Entity(pool, name)

    def get_parent(self):
        """
        Returns the parent class, following the inheritance relation.
        """
        return self.pool.get_instance(self.get_value_by_iname('__inherits'))

    def is_subclass(self, name):
        """
        Searches for a MetaElementInstance name by traversing the inheritance relations; going up, from child to parent
        """
        child = self
        while True:
            if child.get_name() == name:
                return True
            if not child.get_parent() is None:
                child = child.get_parent()
            else:
                break
        return False

    def get_properties(self):
        return self.pool.get_properties(self.get_identifier())

    def get_property(self, ref):
        for p in self.get_properties():
            if p.get_identifier() == ref:
                return p
        return None

    def get_properties_inames(self):
        """
        Returns a dictionary of property uuids to iname.
        """
        return dict([(prop.get_identifier(), prop.get_iname()) for prop in self.get_properties()])
        # When there isn't a iname, the property's ref is returned twice (i.e., as both key and value)
#        return dict([(prop.get_identifier(), prop.get_iname() if not prop.get_iname() is None else prop.get_identifier()) for prop in self.get_properties()])

class Package(MetaElementInstance):
    id = None

    def __init__(self, pool, name, iname=None):
        super(Package, self).__init__(pool=pool, name=name, id_meta=Package.id, iname=iname)

    @classmethod
    def get_new_default_instance(cls, pool, name):
        return Package(pool, name)


class InstancePool(object):
    def __init__(self, bootstrap_with_new_m2=False):
        self.instances = {}
        
        if bootstrap_with_new_m2:
            pool = self
            # Create new M2 instances
            instance_ent = Entity(pool, name=Instance.__name__, inherits=None, iname="__instance", meta_level='2')
            metaelement_ent = Entity(pool, name=MetaElementInstance.__name__, inherits=Instance.id, iname="__metaelement", meta_level='2')
            property_ent = Entity(pool, name=Property.__name__, inherits=MetaElementInstance.id, iname="__property", meta_level='2')
            classifier_ent = Entity(pool, name=Classifier.__name__, inherits=MetaElementInstance.id, iname="__classifier", meta_level='2')
            package_ent = Entity(pool, name=Package.__name__, inherits=MetaElementInstance.id, iname="__package", meta_level='2')
            entity_ent = Entity(pool, name=Entity.__name__, inherits=Classifier.id, iname="__entity", meta_level='2')

            # Properties of Entity
            #Property(pool, "Meta", Entity.id, Entity.id, 1, 1, "__meta", "2")
            Property(pool, "PackageOf", Classifier.id, Package.id, 0, 1, 0, "__packageof", "2")
            Property(pool, "Inherits", Entity.id, Entity.id, 0, 1, 1, "__inherits", "2")
            Property(pool, "Name", MetaElementInstance.id, "string", 1, 1, 2, "__name", "2")
            # Properties of Property
            #Property(pool, "Meta", Property.id, Entity.id, 1, 1, "__meta", "2")
            #Property(pool, "Name", Property.id, "string", 1, 1, "__name", "2")
            Property(pool, "Domain", Property.id, "string", 1, 1, 2, "__domain", "2")
            Property(pool, "Owner", Property.id, Entity.id, 1, 1, 1, "__owner", "2")
            Property(pool, "Lower Bound", Property.id, "string", 1, 1, 3, "__lower_bound", "2")
            Property(pool, "Upper Bound", Property.id, "string", 1, 1, 4, "__upper_bound", "2")
            Property(pool, "Order", Property.id, "string", 1, 1, 5, "__order", "2")
            # Properties of Instance
            Property(pool, "Meta", Instance.id, Entity.id, 1, 1, 0, "__meta", "2")
            Property(pool, "Text Representation", Instance.id, "python", 0, 1, 0, "__text_repr_expr", "2")

            # The meta of all M2 instances is Entity. This is what finally ClosesTheRoof.
            for entity in (instance_ent, metaelement_ent, property_ent, classifier_ent, package_ent, entity_ent):
                entity.set_value_by_iname("__meta", Entity.id)

            # Close the roof also at the properties level, ovewriting all their ids with the proper uuids
            # TODO: check if this can, someway, be done from within the properties
            for instance in pool.get_metamodel_instances():
                instance.set_properties_definite_id()

    def add(self, instance):
        self.instances[instance.get_identifier()] = instance

    def remove(self, identifier):
        del self.instances[identifier]

    def get_instance(self, id=None):
        if not id in self.instances:
            return None
        return self.instances[id]

    def get_instance_by_iname(self, iname):
        for id, instance in self.instances.items():
            if instance.get_iname()==iname:
                return instance
        return None # no instance by this iname exists in the pool

    def get_instances_of(self, meta_id):
        return self.get_instances(meta_id=meta_id)

    def get_metamodel_instances(self, meta_id = None):
        return self.get_instances(['2'], meta_id)

    def get_model_instances(self, meta_id = None):
        return self.get_instances(['1'], meta_id)

    def get_instances(self, meta_levels=['0','1','2'], meta_id=None):
        instances = []
        for id, instance in self.instances.items():
            if not meta_levels is None and not instance.get_meta_level() in meta_levels:
                continue
            if not meta_id is None and instance.get_id_meta() != meta_id:
                continue
            instances.append(instance)
        return instances


    def get_properties(self, owner_id):
        """
        Get Properties of the specified Entity
        """
        props = []
        for id, instance in self.instances.items():
            if type(instance) == Property:
                if instance.get_value_by_iname('__owner') == owner_id:
                    props.append(instance)

        parent = self.get_instance(owner_id).get_parent()
        if not parent is None:
            props.extend(self.get_properties(parent.get_identifier()))

        props.sort(key=lambda prop: prop.get_order())
        return props

    def get_property(self, owner_id, iname=None, property_ref=None):
        if iname is None and property_ref is None:
            raise ValueError("Neither the name and property_ref params were provided.")
        for property in self.get_properties(owner_id):
            if not iname is None and property.get_iname() == iname or \
               not property_ref is None and property.get_identifier() == property_ref:
                return property

        return None

    @classmethod
    def get_metamodel_python_classes(cls):
        #TODO: Would be interesting to make this method more dynamic
        return [Instance, MetaElementInstance, Property, Classifier, Package, Entity]

    @classmethod
    def get_metamodel_python_class_by_id(cls, identifier):
        for a_class in cls.get_metamodel_python_classes():
            if a_class.id == identifier:
                return a_class
        return None

    @classmethod
    def get_metamodel_python_class_by_name(cls, name):
        for a_class in cls.get_metamodel_python_classes():
            if a_class.__name__ == name:
                return a_class
        return None

    def get_possible_domains(self):
        pool = self
        possible_domains = {'text':'text'}
        possible_domains.update(dict([(i.get_identifier(), i.get_name()) for i in pool.get_model_instances(Entity.id)]))
        return possible_domains

