# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import uuid
from persistable_instance import PersistableInstance, PersistablePool
#from meta_model import meta_model

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
    id = None

    """Represents an instance at any model level"""
    def __init__(self, pool, id_meta, identifier=None, meta_level='0'):
        """
        pool --- the pool that the instances of this class will belong to
        identifier --- the uuid that uniquely identifies this instance
        meta -- the Entity to which this instance complies. For M2 and M3 instances it will always be 'Entity'
        """
        #if name_meta != 'Entity' and self.__class__.__name__ != 'Instance':
        #    raise Exception("All M0s should be naturally born instances.")
        ##TODO: it should be validated that the meta is always an Entity! should it not?

        self.state = InstanceState() # TODO: refactor this to a self.states dictionay in which each key,value is of type Version,InstanceState
        if identifier is None:
            self.__identifier = str(uuid.uuid4())
        else:
            self.__identifier = identifier
        self.set_value('__meta', id_meta)
        self.set_value('__meta_level', meta_level)
        if not pool is None:
            pool.add(self)
        self.pool = pool

    def get_identifier(self):
        return self.__identifier

    def get_id_meta(self):
        return self.get_value('__meta')

    def get_meta(self):
        return self.pool.get(self.get_value('__meta'))

    def get_meta_level(self):
        return self.get_value('__meta_level')

    #def get_latest_state(self):
    #    return self.states[Version.get_latest_version(self)]

    def add_value(self, property_ref, property_value):
        """
        property_ref: can be either a private system reference, like '__meta_level', or a uuid identifier, if a reference to a Property
        """
        if not property_ref in self.state.slots:
            self.state.slots[property_ref] = []
        elif property_ref in self.state.slots and not isinstance(self.state.slots[property_ref], list):
            val = self.state.slots[property_ref]
            self.state.slots[property_ref] = [val]
        self.state.slots[property_ref].append(property_value)

    def set_value(self, property_ref, property_value):
        """Overrite the value, no matter what"""
        if property_value is None and property_ref in self.state.slots:
            del self.state.slots[property_ref]
        else:
            self.state.slots[property_ref] = property_value

    def get_value(self, property_ref): #QUANDO APARECE AQUI UM IDENTIFIER, KAPUT
        if property_ref in self.state.slots:
            val = self.state.slots[property_ref]
            if isinstance(val, list):
                if len(val) > 0:
                    return val[0]
            else:
                return val
        return None

    def get_values(self, property_ref):
        if property_ref in self.state.slots:
            return self.state.slots[property_ref]
        else:
            return []

    def add_state(self, state):
        """
        Adds a new state to the dictionary and changes the instance's __class__
        """
        self.state = state #TODO: this should be a dictionary and not a var
        if self.get_identifier()==self.get_id_meta(): # special case: closing the meta-* roof
            self.__class__ = Entity
        else:
            name_meta = self.get_meta().get_name()
            if name_meta==Entity.__name__:
                self.__class__ = Entity
            elif name_meta==Instance.__name__:
                self.__class__ = Instance
            elif name_meta==Package.__name__:
                self.__class__ = Package
            elif name_meta==Property.__name__:
                self.__class__ = Property
            else:
                raise Exception("Unknown element meta: %s" % name_meta)

    @classmethod
    def create_from_properties(cls, pool, identifier, contents_dict):
        instance = Instance(pool, 'Instance', identifier)
        instance.pool.remove(identifier)
        instance.__identifier = identifier
        instance.add_state(InstanceState.create_from_properties(contents_dict))
        pool.add(instance)
        return instance

#    def get_property_names(self, property_name):
#        return [property_name for property_name in self.state.slots if not property_name.startswith('__')]

class InstanceState(object):

    def __init__(self, version=None):
        self.slots = {} # dictionay in which each key,value is of type unicodestring,arbitraryvalue
        #self.version = version # version in which this state was created

    """
    def __getattr__(self, name):
        # proxy unknow attributes to the appropriate slot
        return self.slots[name]

    def __setattr__(self, name, value):
        # proxy unknow attributes to the appropriate slot 
        self.slots[name] = value
    """

    @classmethod
    def create_from_properties(cls, contents_dict):
        state = InstanceState()
        state.slots = contents_dict
        return state


class MetaElementInstance(Instance):
    """
    An instance of a meta-level. I.e., everything except M0s
    """
    id = None

    def __init__(self, pool, name, id_meta, meta_level='1'):
        if meta_level < '1':
            raise Exception("MetaElementInstances' level must be at least 1")
        super(MetaElementInstance, self).__init__(pool=pool, id_meta=id_meta, meta_level=meta_level)
        self.set_value('__name', name)

    def get_name(self):
        """
        Returns the name that was assigned to self.
        Assumes the name is stored in a string property called "name"
        """
        return self.get_value('__name')

class Property(MetaElementInstance):
    id = None

    def __init__(self, pool, name, owner, domain = "string", lower_bound = 0, upper_bound = 1, meta_level='1'):
        super(Property, self).__init__(pool=pool, name=name, id_meta=Property.id, meta_level=meta_level)
        #TODO: mindtwist: changing an instance of this class will have to automatically result in changing instance that represents it in the pool.
        self.set_value('__meta_level', meta_level)
        self.set_value('__owner', owner) #Entity
        self.set_value('__domain', domain) #Classifier. will be the id to an other instance, but can also assume the special value "string"
        self.set_value('__lower_bound', lower_bound)
        self.set_value('__upper_bound', upper_bound)
        #self.set_value('__unique', False)
        #self.set_value('__read_only', False)

    def get_domain(self):
        """
        Returns the domain of the property.
        """
        return self.get_value('__domain')

class Classifier(MetaElementInstance):
    id = None

    def __init__(self, pool, name, id_meta, meta_level='1'):
        super(Classifier, self).__init__(pool=pool, name=name, id_meta=id_meta, meta_level=meta_level)
        self.set_value('__package', None) #Package

class Entity(Classifier):
    id = None

    def __init__(self, pool, name, inherits=None, meta_level='1'):
        super(Entity, self).__init__(pool=pool, name=name, id_meta=Entity.id, meta_level=meta_level)
        self.set_value('__inherits', inherits)
        # There will also be 0..* Properties, each stored in its own key
        # TODO: handle properties with cardinality > 1

    def get_parent(self):
        """
        Returns the parent class, following the inheritance relation.
        """
        return self.pool.get(name=self.get_value('__inherits'))

    def is_a(self, name):
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

    def add_property_old(self, property):
        #meta = self.pool.get(name=self.get_value('__meta'))
        self.add_value('__properties', property)

    def get_properties_old(self): #TODO: fix this. The '__properties' magic word showld not be used anymore, right?
        #self = self.pool.get(name=self.get_value('__meta'))
        return self.get_values('__properties')

    def get_properties(self):
        return self.pool.get_properties(self.get_identifier())


class Package(MetaElementInstance):
    id = None

    def __init__(self, pool, name, id_meta):
        super(Package, self).__init__(pool=pool, name=name, id_meta=id_meta)

class InstancePool(object):
    def __init__(self, bootstrap_with_new_m2=False):
        self.instances = {}
        
        if bootstrap_with_new_m2:
            import sys
            model = sys.modules[__name__]

            pool = self
            # Create new M2 instances
            instance_ent = Entity(pool, name=Instance.__name__, inherits=None, meta_level='2')
            metaelement_ent = Entity(pool, name=MetaElementInstance.__name__, inherits=Instance.__name__, meta_level='2')
            property_ent = Entity(pool, name=Property.__name__, inherits=MetaElementInstance.__name__, meta_level='2')
            classifier_ent = Entity(pool, name=Classifier.__name__, inherits=MetaElementInstance.__name__, meta_level='2')
            package_ent = Entity(pool, name=Package.__name__, inherits=MetaElementInstance.__name__, meta_level='2')
            entity_ent = Entity(pool, name=Entity.__name__, inherits=Entity.__name__, meta_level='2')

            # Copy identifiers from the data-meta-model to the hardcoded-meta-model, for convenience
            Instance.id = instance_ent.get_identifier()
            MetaElementInstance.id = metaelement_ent.get_identifier()
            Property.id = property_ent.get_identifier()
            Classifier.id = classifier_ent.get_identifier()
            Package.id = package_ent.get_identifier()
            Entity.id = entity_ent.get_identifier()

            # Properties of Entity
            a = Property(pool, "Meta", Entity.id, Entity.id, 1, 1, "2")
            b = Property(pool, "Name", Entity.id, "string", 1, 1, "2")
            c = Property(pool, "Inherits", Entity.id, Entity.id, 1, 1, "2")
            # Properties of Property
            d = Property(pool, "Meta", Property.id, Entity.id, 1, 1, "2")
            e = Property(pool, "Name", Property.id, "string", 1, 1, "2")
            f = Property(pool, "Domain", Property.id, "string", 0, 1, "2")
            g = Property(pool, "Owner", Property.id, Entity.id, 1, 1, "2")
            # Properties of Instance
            h = Property(pool, "Meta", Instance.id, Entity.id, 1, 1, "2")

            # The meta of all M2 instances is Entity. This is what finally ClosesTheRoof
            for entity in (instance_ent, metaelement_ent, property_ent, classifier_ent, package_ent, entity_ent):
                entity.set_value("Meta", Entity.id)

            # Now that we have real uuids, we replace all magic words by the respective identifiers
            for property in (a,b,c,d,e,f,g,h):
                property.move_value("__meta", d.get_identifier())
                property.move_value("__name", e.get_identifier())
                property.move_value("__domain", f.get_identifier())
                property.move_value("__owner", g.get_identifier())

            for entity in (instance_ent, metaelement_ent, property_ent, classifier_ent, package_ent, entity_ent):
                entity.move_value("__meta", a.get_identifier())
                entity.move_value("__name", b.get_identifier())
                entity.move_value("__inherits", c.get_identifier())




    def add(self, instance):
        self.instances[instance.get_identifier()] = instance

    def remove(self, identifier):
        del self.instances[identifier]

    def get(self, id=None, name=None):
        if not id is None:
            if not id in self.instances:
                return None
            return self.instances[id]
        elif not name is None:
            for id, instance in self.instances.items():
                if hasattr(instance, 'get_name'):
                    if instance.get_name()==name:
                        return instance
            return None # no instance by this name exists in the pool
        else:
            return None

    def get_properties(self, owner_id):
        """
        Get Properties of the specified Entity
        """
        props = []
        for id, instance in self.instances.items():
            if type(instance) == Property:
                if instance.get_value('__owner') == owner_id:
                    props.append(instance)
        return props


    def get_metamodel_instances(self):
        return [instance for id, instance in self.instances.items() if instance.get_meta_level() == '2']

    def get_model_instances(self):
        return [instance for id, instance in self.instances.items() if instance.get_meta_level() == '1']