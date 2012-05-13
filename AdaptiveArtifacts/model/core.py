# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

"""
Goal is to avoid reinventing the Wheel™, and try to use the python
language's mechanisms as much as possible, instead of implementing the
Type-Square pattern from scratch.

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
for convenient access (e.g., see the the __get_all() method)
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
    id = '__Instance'
    _is_new = False
    attributes = []

    """
    The metaclass of Instance should be Entity, at the very least because
    we need to reference its id. Unfortunately, that would causes a
    chicken-and-egg problem, so we just hardcode an id attribute.
    """

    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id', None)
        self.version = kwargs.pop('version', None)
        self.str_attr = kwargs.pop('str_attr', "id")
        self._is_new = not kwargs.pop('persisted', False)
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
        if self is None: # the Instance class
            return cls._is_new
        else: # a instance of the Instance class or one of its descendants
            return self._is_new

    @classmethod
    def __get_attributes(cls):
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
            for attr_cls in self.__class__.__get_attributes():
                if attr_cls.multiplicity is None:
                    continue
                if type(attr_cls.multiplicity) == tuple:
                    low, high = attr_cls.multiplicity # expects a tuple of 2 int values
                elif type(attr_cls.multiplicity) == int:
                    low=high=attr_cls.multiplicity
                else:
                    raise ValueError("Wrong type for multiplicity: '%s'" % type(attr_cls.multiplicity))

                val = self.get_value(attr_cls.name)
                if val is None:
                    if low > 0:
                        violations.append((attr_cls, "Lower bound violation. Expected at least '%s', got '0'" % low))
                    continue
                amount = 1
                if type(val) == list:
                    amount = len(val)
                if amount < low:
                    violations.append((attr_cls, "Lower bound violation. Expected at least '%s', got '%s'" % (low, amount)))
                if amount > high:
                    violations.append((attr_cls, "Upper bound violation. Expected at most '%s', got '%s'" % (high, amount)))

            # is the type of all instance values ok?
            for attr_self_name in self.attr_identifiers.keys():
                for attr_cls in self.__class__.__get_attributes():
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
        """
        The py_id param should only be used for testing purposes. In the real
        world, the id will always be (automatically) derived from the name.
        """
        self.py_id = util.to_valid_identifier_name(name)
        self.name=name
        self.type = type
        self.multiplicity = multiplicity

class Entity(type):
    name = '__Entity'
    attributes = []

    """
    Entity should be its own metaclass, at the very least because
    we need to reference its id. Unfortunately, that would causes a
    chicken-and-egg problem, so we just hardcode an id attribute.
    """

    def __new__(mcs, *args, **kwargs):
        """
        It's not very usual for __new__ to receive args and kwargs,
        instead of the usual: mcs, name, bases, dct.
        We need it here because we want to pass extra params, to
        be picked up by __init__
        """
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
        cls.attributes = extra_kwargs.get('attributes', [])
        #cls.py_id = util.to_valid_identifier_name(cls.id) # not needed as an extra attribute, it's already the class identifier!
        super(Entity, cls).__init__(name, bases, dct)

    @util.classinstancemethod
    def get_id(self, cls):
        if self is None: # the Entity class
            return cls.name
        else: # a class, instance of the Entity class
            return self.name

    def get_name(cls):
        return cls.name

import unittest

class TestModel(unittest.TestCase):

    def setUp(self):
        self.Vehicle = Entity(name="Vehicle",
                attributes=[
                    Attribute(name="Number of Engines"),
                    Attribute(name="Brand", multiplicity=1, type=str)
                ]
            )
        self.myvehicle = self.Vehicle(values={"Number of Engines":2, "Brand":"Volvo"})
        self.Car = Entity(name="Car", bases=(self.Vehicle,),
                attributes=[
                    Attribute(name="Number of Doors", multiplicity=1, type=int)
                ]
        )
        self.mycar = self.Car(values={"Number of Doors":5, "Brand":"Ford"})
        self.Plane = Entity(name="Plane", bases=(self.Vehicle,),
                attributes=[
                    Attribute(name="Lengths of the Wings", multiplicity=(2,5), type=int)
                ]
            )

        self.my_plane_invalid_multiplicity = self.Plane(values={"Number of Engines":4, "Brand":"Airbus", "Lengths of the Wings":[120, 120, 20, 20, 10, 10]})
        self.my_plane_invalid_type = self.Plane(values={"Brand":"Airbus", "Lengths of the Wings":[120, 120, 20, 20, "10"]})
        self.my_plane_invalid_multiplicity_inherited = self.Plane(values={"Lengths of the Wings":[120, 120, 20, 20, 10]})
        self.my_plane_invalid_type_inherited = self.Plane(values={"Brand":7, "Lengths of the Wings":[120, 120, 20, 20, 10]})

    def test_no_violations(self):
        vvs=self.myvehicle.get_meta_violations()
        self.assertEqual(len(vvs), 0, vvs)
        cvs=self.mycar.get_meta_violations()
        self.assertEqual(len(cvs), 0, cvs)

    def test_multiplicity(self):
        pvs = self.my_plane_invalid_multiplicity.get_meta_violations()
        self.assertEqual(len(pvs), 1, pvs)

    def test_type(self):
        self.assertEqual(len(self.my_plane_invalid_type.get_meta_violations()), 1)

    def test_inherited_multiplicity(self):
        pvs = self.my_plane_invalid_multiplicity_inherited.get_meta_violations()
        self.assertEqual(len(pvs), 1, pvs)

    def test_inherited_type(self):
        pvs = self.my_plane_invalid_type_inherited.get_meta_violations()
        self.assertEqual(len(pvs), 1, pvs)

if __name__ == '__main__':
    unittest.main()