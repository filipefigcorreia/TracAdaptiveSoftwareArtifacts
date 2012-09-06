# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

"""
The approach taken here is similar in goal to the Adaptive Object-Model
architectural panel, but instead of implementing the Type-Square pattern
from scratch, we shall try to use the python language's mechanisms as
much as possible, hence minimizing accidental complexity.

Entity is a metaclass. It descends from "type", and adds some extra data
to the class during its initialization. That data is used to "extend" the
"type" class.

Instance is a class. It descends from "object", and adds some extra data
that you don't get with a plain "object". This is also done to provide
some extra features to instances

The meta/instantiation and the inheritance mechanisms are python's
(i.e., all system calls that depend on these features work normally when
working with Instances and Entities). For "extra" features, like
multiplicity and attribute types, sometimes extra work has to be done
for convenient access (e.g., see the __get_all() method)
"""
from AdaptiveArtifacts.model import util

class Version(object):
    def __init__(self, id, comment, author, time, readonly):
        self.id = id
        self.comment = comment
        self.author = author
        self.time = time
        self.readonly = readonly

class Instance(object):
    """
    The metaclass of Instance should be Entity, at the very least because
    we need to reference its name. Unfortunately, that would cause a
    chicken-and-egg problem, so we just hardcode a name attribute.
    """

    name = '__Instance'
    _is_new = False
    _is_modified = False
    attributes = []

    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id', None)
        self.version = kwargs.pop('version', None)
        self.str_attr = kwargs.pop('str_attr', "id")
        self._is_new = not kwargs.pop('persisted', False)
        self._is_modified = False
        values = kwargs.pop('values', {})
        self.attr_identifiers = {}
        for name, value in values.iteritems():
            self.set_value(name, value)

    def __str__(self):
        str_value = eval("self." + self.str_attr)
        if not str_value is None:
            return str_value
        else:
            return repr(self)

    @util.classinstancemethod
    def get_id(self, cls):
        if self is None: # the Instance class
            return cls.name
        else: # a instance of the Instance class or one of its descendants
            return self.id

    @util.classinstancemethod
    def is_uncommitted(self, cls):
        if self is None: # the Instance class or one of its descendents
            if cls is Instance:
                return False # the Instance class is always committed, as it's not changeable
            else:
                return cls._is_new or cls._is_modified
        else: # a instance of the Instance class or one of its descendants
            return self._is_new or self._is_modified

    @util.classinstancemethod
    def is_new(self, cls):
        if self is None: # the Instance class
            return False
        else: # a instance of the Instance class or one of its descendants
            return self._is_new


    @classmethod
    def get_name(cls):
        return cls.name

    @classmethod
    def get_attributes(cls):
        """
        Returns a list of the attributes of the instance, collected
        through the class' inheritance chain.
        """
        merged_lst = []
        for base in reversed(cls.mro()):
            if hasattr(base, 'attributes'):
                merged_lst += getattr(base, 'attributes')
        return merged_lst

    def set_value(self, name, value):
        """
        Sets the value for the attribute with the specified name.
        """
        py_identifier = util.to_valid_identifier_name(name)
        self.attr_identifiers[name] = py_identifier
        setattr(self, py_identifier, value)

    def add_values(self, values_list):
        """
        values_list: A list of tuples (attr_name, attr_value)
        """
        for name, value in values_list:
            py_identifier = util.to_valid_identifier_name(name)
            self.attr_identifiers[name] = py_identifier
            if not hasattr(self, py_identifier):
                setattr(self, py_identifier, value)
            else:
                old_val = getattr(self, py_identifier)
                if type(old_val)==list:
                    old_val.append(value)
                    setattr(self, py_identifier, old_val)
                else:
                    setattr(self, py_identifier, [old_val, value])

    def get_values(self):
            """
            Returns (attribute,value) pairs of all the values of the instance, independently in they are defined by any spec.
            """
            return [(name, getattr(self, py_id, None)) for name, py_id in self.attr_identifiers.iteritems()]

    def get_value(self, name):
            """
            Returns the value for the attribute with the specified name.
            """
            if not self.attr_identifiers.has_key(name):
                return None
            return getattr(self, self.attr_identifiers[name], None)

    def get_meta_violations(self):
        """
        Compares an instance with it's meta, and returns a list of
        noncompliant attributes
        """
        violations = []
        if isinstance(self, Instance) and not self.__class__ is Instance: # if there's a meta other than "Instance"
            # are the multiplicities of all instance values ok?
            for attr_cls in self.__class__.get_attributes():
                low, high = attr_cls.multiplicity

                val = self.get_value(attr_cls.name)
                if val is None:
                    if not low is None and low > 0:
                        violations.append((attr_cls, "Lower bound violation. Expected at least '%s', got '0'" % low))
                    continue
                amount = 1
                if type(val) == list:
                    amount = len(val)
                if not low is None and amount < low:
                    violations.append((attr_cls, "Lower bound violation. Expected at least '%s', got '%s'" % (low, amount)))
                if not high is None and amount > high:
                    violations.append((attr_cls, "Upper bound violation. Expected at most '%s', got '%s'" % (high, amount)))

            # is the type of all instance values ok?
            for attr_self_name in self.attr_identifiers.keys():
                for attr_cls in self.__class__.get_attributes():
                    if attr_self_name==attr_cls.name:
                        if attr_cls.type is None:
                            continue
                        value = self.get_value(attr_self_name)
                        value_list = [value] if type(value) != list else value
                        for value_item in value_list:
                            if type(value_item) != attr_cls.type:
                                violations.append((attr_self_name, "Type violation. Expected '%s', got '%s'" % (attr_cls.type, type(value_item))))
        return violations


class Attribute(object):
    def __init__(self, name, multiplicity=None, type=None):
        self.py_id = util.to_valid_identifier_name(name)
        self.name=name
        self.type = type
        if not multiplicity:
            self.multiplicity = (None, None)
        elif isinstance(multiplicity, int):
            self.multiplicity = (multiplicity, multiplicity)
        elif isinstance(multiplicity, tuple) and len(multiplicity)==2:
            self.multiplicity = multiplicity
        else:
            raise ValueError("The value provided for multiplicity is not valid: %s" % (multiplicity,))

class Entity(type):
    """
    Entity should be its own metaclass, at the very least because
    we need to reference its name. Unfortunately, that would cause a
    chicken-and-egg problem, so we just hardcode a name attribute.
    """
    name = '__Entity'
    attributes = []

    def __new__(mcs, *args, **kwargs):
        """
        It's not very usual for __new__ to receive args and kwargs,
        instead of the usual: mcs, name, bases, dct.
        We need it here because we want to pass extra params, to
        be picked up by __init__
        """
        assert 'name' in kwargs
        name = util.to_valid_identifier_name(
            args[0] if len(args)>0 else kwargs.get('name', None)
        )
        bases = args[1] if len(args)>1 else kwargs.get('bases', tuple())
        dct = args[2] if len(args)>2 else kwargs.get('dct', {})
        if len([b for b in bases if issubclass(b,Instance)]) == 0:
            bases = (Instance, )
        return super(Entity, mcs).__new__(mcs, name, bases, dct)

    def __init__(cls, *args, **kwargs):
        extra_kwargs = dict(kwargs)
        cls.name = args[0] if len(args)>0 else extra_kwargs.pop('name', None)
        name = util.to_valid_identifier_name(cls.name)
        bases = args[1] if len(args)>1 else extra_kwargs.pop('bases', None)
        dct = args[2] if len(args)>2 else extra_kwargs.pop('dct', None)
        cls.version = extra_kwargs.get('version', None)
        cls._is_new = not kwargs.pop('persisted', False)
        cls._is_modified = False
        cls.attributes = extra_kwargs.get('attributes', [])
        #cls.py_id = util.to_valid_identifier_name(cls.id) # not needed as an extra attribute, it's already the class identifier!
        super(Entity, cls).__init__(name, bases, dct)

    @util.classinstancemethod
    def get_id(self, cls):
        if self is None: # the Entity class
            return cls.name
        else: # a class, instance of the Entity class
            return self.name

    @util.classinstancemethod
    def get_name(self, cls):
        if self is None: # the Entity class
            return cls.name
        else: # a class, instance of the Entity class
            return self.name

    @util.classinstancemethod
    def get_parent(self, cls):
        if self is None: # the Entity class
            return None
        else: # a class, instance of the Entity class
                return self.__bases__[0] if len(self.__bases__) > 0 and not self.__bases__[0] in (type, Instance) else None

    @classmethod
    def get_attributes(mcs):
        return []

    @classmethod
    def is_uncommitted(mcs):
        return False # report the "Entity" class as always committed as it's not even changeable...

    @classmethod
    def is_new(mcs):
        return False
