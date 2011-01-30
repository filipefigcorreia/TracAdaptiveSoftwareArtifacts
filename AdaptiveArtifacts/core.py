# -*- coding: utf-8 -*-
import uuid

class Version():
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
        self.state = [] # array of InstanceStates that were created in this version


class Instance():
    """Represents an instance at any model level"""
    def __init__(self, meta = None, identifier = uuid.uuid4()):
        """
        meta -- the Entity to which this instance complies. If None, the instance is made to be its own meta
        identifier --- the uuid that uniquely identifies this instance
        """
        #TODO: it should be validated that the meta is always an Entity!
        self.identifier = identifier
        if meta is None:
            meta = self
        self.meta = meta
        self.states = {} # dictionay in which each key,value is of type Version,InstanceState
        self.version = Version.get_latest_version(self)


class InstanceState():
    def __init__(self, version = None):
        self.slots = {} # dictionay in which each key,value is of type unicodestring,arbitraryvalue
        self.version = version # version in which this state was created


class MetaElementInstance(Instance):
    """
    An instance that may is described by a name. This name is not necessarily
    """
    def __init__(self):
        pass

    def get_name(self):
        """
        Returns the name of this meta-* element.
        Assumes the name is stored in a string property called "displayname"
        """
        return self.states[self.version].slots['displayname']

class Property(MetaElementInstance):
    def __init__(self):
        self.owner = None #ObjectType
        self.lower_bound = 0
        self.upper_bound = 1
        self.unique = False
        self.read_only = False
        self.domain = None #Classifier

class Classifier(MetaElementInstance):
    def __init__(self):
        self.package = None #Package

class Entity(Classifier):
    def __init__(self):
        self.properties = [] #0..* Properties

class Package(MetaElementInstance):
    def __init__(self):
        pass
