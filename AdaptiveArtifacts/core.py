# -*- coding: utf-8 -*-
import uuid
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
    def __init__(self, pool, meta, identifier=None):
        """
        pool --- the pool that the instances of this class will belong to
        identifier --- the uuid that uniquely identifies this instance
        meta -- the Entity to which this instance complies. For M2 and M3 instances it will always be 'Entity'
        """
        if meta != 'Entity' and self.__class__.__name__ != 'Instance':
            raise Exception("All M0s should be naturally born instances.")

        #TODO: it should be validated that the meta is always an Entity!
        if identifier is None:
            self.identifier = str(uuid.uuid4())
        else:
            self.identifier = identifier
        self.__meta_name = meta
        self.states = {} # dictionay in which each key,value is of type Version,InstanceState
        pool.add(self)
        self.pool = pool

    def get_meta(self):
        return self.pool.get(name=self.__meta_name)

    def get_latest_state(self):
        return self.states[Version.get_latest_version(self)]


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
    An instance that may is described by a name. Usually everything except M0s
    """
    def __init__(self, pool, name):
         super(MetaElementInstance, self).__init__(pool=pool, meta=Entity.__name__)
         #self.states[self.version].slots['name'] = name
         self.name = name

    def get_name(self):
        """
        Returns the name that was assigned to self.
        Assumes the name is stored in a string property called "displayname"
        """
        #return self.states[self.version].slots['name']
        return self.name

class Property(MetaElementInstance):
    def __init__(self, pool, name):
        super(Property, self).__init__(pool=pool, name=name)
        #TODO: changing an instance of this class will have to automatically result in changing instance that represents it in the pool.
        self.owner = None #ObjectType
        self.lower_bound = 0
        self.upper_bound = 1
        self.unique = False
        self.read_only = False
        self.domain = None #Classifier

class Classifier(MetaElementInstance):
    def __init__(self, pool, name):
        super(Classifier, self).__init__(pool=pool, name=name)
        self.package = None #Package

class Entity(Classifier):
    def __init__(self, pool, name, inherits=None):
        super(Entity, self).__init__(pool=pool, name=name)
        self.__inherits = inherits
        self.properties = [] #0..* Properties

    def get_inherits(self):
        return self.pool.get(name=self.__inherits)

class Package(MetaElementInstance):
    def __init__(self, pool, name):
        super(Package, self).__init__(pool=pool, name=name)


class InstancePool(object):
    def __init__(self):
        self.pool = {}
        self.bootstrap_m2()

    def add(self, instance):
        self.pool[instance.identifier] = instance

    def get(self, id=None, name=None):
        if not id is None:
            return self.pool[id]
        elif not name is None:
            for id, instance in self.pool.items():
                if hasattr(instance, 'get_name'):
                    if instance.get_name()==name:
                        return instance
            return None # no instance by this name exists in the pool
        else:
            return None

    def bootstrap_m2(self):
        Entity(self, name=Instance.__name__,             inherits=None)
        Entity(self, name=MetaElementInstance.__name__,  inherits=Instance.__name__)
        Entity(self, name=Classifier.__name__,           inherits=MetaElementInstance.__name__)
        Entity(self, name=Package.__name__,              inherits=MetaElementInstance.__name__)
        Entity(self, name=Property.__name__,             inherits=MetaElementInstance.__name__)
        Entity(self, name=Entity.__name__,               inherits=Entity.__name__)


