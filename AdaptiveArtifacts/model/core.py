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
import types

class Instance(object):
    """
    The metaclass of Instance should be Entity, at the very least because
    we need to reference its name. Unfortunately, that would cause a
    chicken-and-egg problem, so we just hardcode a name attribute.
    """

    name = '__Instance'
    _is_new = False
    _is_modified = False
    _is_renamed = False
    attributes = []

    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id', None)
        self.version = kwargs.pop('version', None)
        self.str_attr = kwargs.pop('str_attr', "id")
        self._is_new = not kwargs.pop('persisted', False)
        self._is_modified = False
        values = kwargs.pop('values', [])
        if type(values) == dict:
            values = values.items()
        self.attr_identifiers = {}
        self.attr_orders = {}
        for name, value in values:
            self.set_value(name, value)

    def __str__(self):
        if self.str_attr in ('id', 'version'):
            return str(getattr(self, self.str_attr))

        str_value = self.get_value(self.str_attr)
        if not str_value is None:
            return str_value
        else:
            return str(self.id)

    @util.classinstancemethod
    def get_id(self, cls):
        if self is None: # the Instance class
            return cls.name
        else: # a instance of the Instance class or one of its descendants
            return self.id

    @classmethod
    def get_parent(cls):
        if cls is Instance: # the Instance class
            return None
        else: # a descendant of the Instance class
            return cls.__bases__[0] if len(cls.__bases__) > 0 and not cls.__bases__[0] in (type, Instance) else None

    @util.classinstancemethod
    def is_uncommitted(self, cls):
        if self is None: # the Instance class or one of its descendants
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

    def set_value(self, name, value, order=None):
        """
        Sets the value for the attribute with the specified name.
        """
        py_identifier = util.to_valid_identifier_name(name)
        self.attr_identifiers[name] = py_identifier
        if order:
            self.attr_orders[name] = order
        else:
            self.attr_orders[name] = max(self.attr_orders.values())+1 if len(self.attr_orders.values())>0 else 1
        setattr(self, py_identifier, value)
        self._is_modified = True

    def add_values(self, values_list):
        """
        values_list: A list of tuples (attr_name, attr_value)
        """
        for name, value in values_list:
            py_identifier = util.to_valid_identifier_name(name)
            self.attr_identifiers[name] = py_identifier
            self.attr_orders[name] = max(self.attr_orders.values())+1 if len(self.attr_orders.values())>0 else 1

            if not hasattr(self, py_identifier):
                setattr(self, py_identifier, value)
            else:
                old_val = getattr(self, py_identifier)
                if type(old_val)==list:
                    old_val.append(value)
                    setattr(self, py_identifier, old_val)
                else:
                    setattr(self, py_identifier, [old_val, value])

    def replace_values(self, values_list):
        """
        Replaces the attribute values of an instance.

        values_list: A list of tuples (attr_name, attr_value)
        """
        for py_identifier in self.attr_identifiers.values():
            delattr(self, py_identifier)
        self.attr_identifiers = {}
        self.add_values(values_list)
        self._is_modified = True

    def get_values(self):
            """
            Returns a list of (attribute_name,value) pairs of all the values of the instance, independently in they are defined by any spec.
            """
            return [(name, getattr(self, py_id, None)) for name, py_id in sorted(self.attr_identifiers.iteritems(), key=lambda x: self.attr_orders[x[0]] )]

    def get_value(self, name):
            """
            Returns the value for the attribute with the specified name.
            """
            if not self.attr_identifiers.has_key(name):
                return None
            return getattr(self, self.attr_identifiers[name], None)

    def get_order(self, name):
            """
            Returns the order for the attribute with the specified name.
            """
            if not self.attr_orders.has_key(name):
                return 0
            return self.attr_orders[name]

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
    def __init__(self, name, multiplicity=None, atype=None, order=None):
        self.py_id = util.to_valid_identifier_name(name)
        self.owner_spec = None # filled in when the attr is added to a spec
        self.name = name
        self.type = self._get_valid_type(atype)
        self.order = order
        self.multiplicity = self._get_valid_multiplicity(multiplicity)

    def _get_valid_multiplicity(self, multiplicity):
        # ensure multiplicity is (or becomes) a tuple of length 2 int values
        m = None
        if not multiplicity:
            m = (None, None)
        elif isinstance(multiplicity, unicode) or isinstance(multiplicity, int):
            if multiplicity == '0..*':
                m = (0, None)
            elif multiplicity == '1..*':
                m = (1, None)
            else:
                m = (multiplicity, multiplicity)
        elif isinstance(multiplicity, tuple):
            if len(multiplicity) == 2:
                m = multiplicity
            elif len(multiplicity) < 2:
                m = (multiplicity[0], None)
            elif len(multiplicity) > 2:
                m = None

        # ensure both bounds of the multiplicity are of the right type
        if not m is None:
            try:
                m = (int(m[0]) if not m[0] is None else None,
                     int(m[1]) if not m[1] is None else None)
            except ValueError:
                m = None
        if m is None:
            raise ValueError("The value provided for multiplicity is not valid: %s" % (multiplicity,))
        return m

    def get_multiplicity_readable(self):
         if self.multiplicity==(0, None):
             return '0..*'
         elif self.multiplicity==(1, None):
             return '1..*'
         elif self.multiplicity==(1, 1):
             return '1'
         elif self.multiplicity[0]==self.multiplicity[1]:
             return self.multiplicity[0]
         else:
             return str(self.multiplicity)

    def _get_valid_type(cls, user_type):
        if user_type in types.__dict__.values():
            return user_type # it's already a python type after all
        if user_type == 'text':
            python_type = str
        elif user_type == 'number':
            python_type = int
        else:
            python_type = None #TODO: fix. must account for user_type='artifact'
        return python_type

    def get_type_readable(self):
        python_type = self.type
        if python_type is str:
            user_type = 'text'
        elif python_type is int:
            user_type = 'number'
        else:
            user_type = '' #TODO: fix. must account for python_type=<artifact>
        return user_type


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
        cls.original_name = None
        cls.name = args[0] if len(args)>0 else extra_kwargs.pop('name', None)
        name = util.to_valid_identifier_name(cls.name)
        bases = args[1] if len(args)>1 else extra_kwargs.pop('bases', None)
        dct = args[2] if len(args)>2 else extra_kwargs.pop('dct', None)
        cls.version = extra_kwargs.get('version', None)
        cls._is_new = not kwargs.pop('persisted', False)
        cls._replace_attributes(extra_kwargs.get('attributes', []))
        cls._is_modified = False # will be switched to True if either the name bases or attributes are changed
        cls._is_renamed = False # will be switched to True if the name is changed
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

    @classmethod
    def get_parent(cls):
        return None

    @classmethod
    def get_attributes(mcs):
        return []

    def replace_state(cls, name, base, attributes):
        cls._replace_name(name)
        cls.__bases__ = (base,) if base else (Instance,)
        cls._replace_attributes(attributes)
        cls._is_modified = True

    def _replace_name(cls, name):
        cls.original_name = cls.name
        cls.name = name
        cls.__name__ = util.to_valid_identifier_name(cls.name)
        cls._is_renamed = True
        cls._is_modified = True

    def _replace_attributes(cls, attributes):
        cls.attributes = attributes
        for attribute in cls.attributes:
            attribute.owner_spec = cls
        cls._is_modified = True

    @classmethod
    def is_uncommitted(mcs):
        return False # report the "Entity" class as always committed as it's not even changeable...

    @classmethod
    def is_new(mcs):
        return False
