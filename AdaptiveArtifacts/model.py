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
    """Represents an instance at any model level"""
    def __init__(self, pool, name_meta, identifier=None, meta_level='0'):
        """
        pool --- the pool that the instances of this class will belong to
        identifier --- the uuid that uniquely identifies this instance
        meta -- the Entity to which this instance complies. For M2 and M3 instances it will always be 'Entity'
        """
        if name_meta != 'Entity' and self.__class__.__name__ != 'Instance':
            raise Exception("All M0s should be naturally born instances.")
        #TODO: it should be validated that the meta is always an Entity! should it not?

        self.state = InstanceState() # TODO: refactor this to a self.states dictionay in which each key,value is of type Version,InstanceState
        if identifier is None:
            self.__identifier = str(uuid.uuid4())
        else:
            self.__identifier = identifier
        self.add_value('__name_meta', name_meta)
        self.add_value('__meta_level', meta_level)
        if not pool is None:
            pool.add(self)
        self.pool = pool

    def get_identifier(self):
        return self.__identifier

    def get_name_meta(self):
        return self.get_value('__name_meta')

    def get_meta_level(self):
        return self.get_value('__meta_level')

    #def get_latest_state(self):
    #    return self.states[Version.get_latest_version(self)]

    def add_value(self, property_name, property_value):
        if not property_name in self.state.slots:
            self.state.slots[property_name] = []
        elif property_name in self.state.slots and not isinstance(self.state.slots[property_name], list):
            val = self.state.slots[property_name]
            self.state.slots[property_name] = [val]
        self.state.slots[property_name].append(property_value)

    def set_value(self, property_name, property_value):
        """Overrite the value, no matter what"""
        self.state.slots[property_name] = property_value

    def get_value(self, property_name):
        if property_name in self.state.slots:
            val = self.state.slots[property_name]
            if isinstance(val, list):
                if len(val) > 0:
                    return val[0]
            else:
                return val
        return None

    def get_values(self, property_name):
        if property_name in self.state.slots:
            return self.state.slots[property_name]
        else:
            return []

    @classmethod
    def create_from_properties(cls, pool, identifier, properties):
        instance = Instance(pool, 'Instance', identifier)
        instance.pool.remove(identifier)
        instance.__identifier = identifier
        instance.state.slots = properties
        name_metas = properties['__name_meta']
        if Instance.__name__ in name_metas:
            instance.__class__ = Instance
        elif Package.__name__ in name_metas:
            instance.__class__ = Package
        elif Property.__name__ in name_metas:
            instance.__class__ = Property
        elif Entity.__name__ in name_metas:
            instance.__class__ = Entity
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

class MetaElementInstance(Instance):
    """
    An instance that may is described by a name. I.e., everything except M0s
    """
    def __init__(self, pool, name):
         super(MetaElementInstance, self).__init__(pool=pool, name_meta=Entity.__name__)
         self.set_value('__meta_level', '1') # MetaElementInstances' level is at least 1
         self.set_value('__name', name)

    def get_name(self):
        """
        Returns the name that was assigned to self.
        Assumes the name is stored in a string property called "name"
        """
        return self.get_value('__name')

class Property(MetaElementInstance):
    def __init__(self, pool, name, lower_bound = 0, upper_bound = 1):
        super(Property, self).__init__(pool=pool, name=name)
        #TODO: changing an instance of this class will have to automatically result in changing instance that represents it in the pool.
        self.set_value('__owner', None) #ObjectType
        self.set_value('__lower_bound', lower_bound)
        self.set_value('__upper_bound', upper_bound)
        self.set_value('__unique', False)
        self.set_value('__read_only', False)
        self.set_value('__domain', None) #Classifier

class Classifier(MetaElementInstance):
    def __init__(self, pool, name):
        super(Classifier, self).__init__(pool=pool, name=name)
        self.set_value('__package', None) #Package

class Entity(Classifier):
    def __init__(self, pool, name, inherits=None, meta_level='1'):
        super(Entity, self).__init__(pool=pool, name=name)
        self.set_value('__meta_level', meta_level)
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

    def add_property(self, property):
        #meta = self.pool.get(name=self.get_value('__meta'))
        self.add_value('__properties', property)

    def get_properties(self):
        #self = self.pool.get(name=self.get_value('__meta'))
        return self.get_values('__properties')


class Package(MetaElementInstance):
    def __init__(self, pool, name):
        super(Package, self).__init__(pool=pool, name=name)

class InstancePool(object):
    def __init__(self):
        self.instances = {}

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

    def get_metamodel_instances(self):
        return [instance for id, instance in self.instances.items() if instance.get_meta_level() == '2']

    def get_model_instances(self):
        return [instance for id, instance in self.instances.items() if instance.get_meta_level() == '1']

def bootstrap_m2(env):
    pool = InstancePool()
    # Create all M2 instances to the database
    Entity(pool, name=Instance.__name__,             inherits=None, meta_level='2')
    Entity(pool, name=MetaElementInstance.__name__,  inherits=Instance.__name__, meta_level='2')
    Entity(pool, name=Classifier.__name__,           inherits=MetaElementInstance.__name__, meta_level='2')
    Entity(pool, name=Package.__name__,              inherits=MetaElementInstance.__name__, meta_level='2')
    Entity(pool, name=Property.__name__,             inherits=MetaElementInstance.__name__, meta_level='2')
    Entity(pool, name=Entity.__name__,               inherits=Entity.__name__, meta_level='2')

    db = env.get_db_cnx()
    for entity in pool.get_metamodel_instances():
        pi = PersistableInstance(env, entity.get_identifier(), entity.get_name(), 0, db)
        pi.instance = entity
        pi.save_instance("system", "", "")

