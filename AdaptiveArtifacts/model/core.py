# -*- coding: utf-8 -*-

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

class Util(object):
    @staticmethod
    def to_valid_identifier_name(name):
        """
        Uses "name" to create a valid python identifier by removing illegal
        characters, as described in:
        http://docs.python.org/reference/lexical_analysis.html#identifiers

        Ultimately, the identifiers could be semantically opaque but, for
        eased debugging, it's handy if they're not. As this process doesn't
        produce identifiers that can be guaranteed to unique, we suffix it
        with a hash to ensure it doesn't clash with other identifiers.
        """
        def gen_valid_identifier(seq):
            itr = iter(seq)
            # pull characters until we get a legal one for first in identifer
            for ch in itr:
                if ch == '_' or ch.isalpha():
                    yield ch
                    break
            # pull remaining characters and yield legal ones for identifier
            for ch in itr:
                if ch == ' ':
                    ch = '_'
                if ch == '_' or ch.isalpha() or ch.isdigit():
                    yield ch
        import hashlib
        return ''.join(gen_valid_identifier(name)) + "_" + hashlib.md5(name).hexdigest()

class classinstancemethod(object):
    """
    Acts like a class method when called from a class, like an
    instance method when called by an instance.  The method should
    take two arguments, 'self' and 'cls'. 'self' will be None if
    called via class, but they will both have values if called via
    instance. See http://stackoverflow.com/a/10413769/684253
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, type=None):
        return _methodwrapper(self.func, obj=obj, type=type)

class _methodwrapper(object):

    def __init__(self, func, obj, type):
        self.func = func
        self.obj = obj
        self.type = type

    def __call__(self, *args, **kw):
        assert 'self' not in kw and 'cls' not in kw, (
            "You cannot use 'self' or 'cls' arguments to a "
            "classinstancemethod")
        return self.func(*((self.obj, self.type) + args), **kw)

    def __repr__(self):
        if self.obj is None:
            return ('<bound class method %s.%s>'
                    % (self.type.__name__, self.func.func_name))
        else:
            return ('<bound method %s.%s of %r>'
                    % (self.type.__name__, self.func.func_name, self.obj))

class Instance(object):
    id = '__Instance'
    attributes = []

    """
    The metaclass of Instance should be Entity, at the very least because
    we need to reference its id. Unfortunately, that would causes a
    chicken-and-egg problem, so we just hardcode an id attribute.
    """

    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id', None)
        self.str_attr = kwargs.pop('str_attr', "id")
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __str__(self):
        str_value = eval("self." + self.str_attr)
        if not str_value is None:
            return str_value
        else:
            return repr(self)

    @classinstancemethod
    def get_id(self, cls):
        if self is None: # the Instance class
            return cls.name
        else: # a instance of the Instance class or one of its descendants
            return self.id

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

    def get_meta_violations(self):
        """
        Compares an instance with it's meta, and returns a list of
        noncompliant attributes
        """
        violations = []
        if isinstance(self, Instance) and not self.__class__ is Instance: # if there's a meta other than "Instance"
            # are the multiplicities of all instance values ok?
            for attr in self.__class__.__get_attributes():
                if attr.multiplicity is None:
                    continue
                if type(attr.multiplicity) == tuple:
                    low, high = attr.multiplicity # expects a tuple of 2 int values
                elif type(attr.multiplicity) == int:
                    low=high=attr.multiplicity
                else:
                    raise ValueError("Wrong type for multiplicity: '%s'" % type(attr.multiplicity))

                if not self.__dict__.has_key(attr.py_id):
                    if low > 0:
                        violations.append((attr, "Lower bound violation. Expected at least '%s', got '0'" % low))
                    continue
                val = self.__dict__.get(attr.py_id)
                amount = 1
                if type(val) == list:
                    amount = len(val)
                if amount < low:
                    violations.append((attr, "Lower bound violation. Expected at least '%s', got '%s'" % (low, amount)))
                if amount > high:
                    violations.append((attr, "Upper bound violation. Expected at most '%s', got '%s'" % (high, amount)))

            # is the type of all instance values ok?
            for attr_self_id, value in self.__dict__.iteritems():
                for attr_cls in self.__class__.__get_attributes():
                    if attr_self_id==attr_cls.py_id:
                        if attr_cls.type is None:
                            continue
                        value_list = [value] if type(value) != list else value
                        for value_item in value_list:
                            if type(value_item) != attr_cls.type:
                                violations.append((attr_self_id, "Type violation. Expected '%s', got '%s'" % (attr_cls.type, type(value_item))))
        return violations


class Attribute(object):
    def __init__(self, name, multiplicity=None, type=None, py_id=None):
        """
        The py_id param should only be used for testing purposes. In the real
        world, the id will always be (automatically) derived from the name.
        """
        self.py_id = py_id or Util.to_valid_identifier_name(name)
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
        name = Util.to_valid_identifier_name(
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
        name = Util.to_valid_identifier_name(cls.name)
        bases = args[1] if len(args)>1 else extra_kwargs.pop('bases', None)
        dct = args[2] if len(args)>2 else extra_kwargs.pop('dct', None)
        cls.attributes = extra_kwargs.get('attributes', [])
        #cls.py_id = Util.to_valid_identifier_name(cls.id) # not needed as an extra attribute, it's already the class identifier!
        super(Entity, cls).__init__(name, bases, dct)

    @classinstancemethod
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
                    Attribute(py_id="num_engines", name="Number of Engines"),
                    Attribute(py_id="brand", name="Brand", multiplicity=1, type=str)
                ]
            )
        self.myvehicle = self.Vehicle(num_engines=2, brand="Volvo")
        self.Car = Entity(name="Car", bases=(self.Vehicle,),
                attributes=[
                    Attribute(py_id="ndoors", name="Number of Doors", multiplicity=1, type=int)
                ]
        )
        self.mycar = self.Car(ndoors=5, brand="Ford")
        self.Plane = Entity(name="Plane", bases=(self.Vehicle,),
                attributes=[
                    Attribute(py_id="wings_lengths", name="Lengths of the Wings", multiplicity=(2,5), type=int)
                ]
            )
        self.my_plane_invalid_multiplicity = self.Plane(num_engines=4, brand="Airbus", wings_lengths=[120, 120, 20, 20, 10, 10])
        self.my_plane_invalid_type = self.Plane(brand="Airbus", wings_lengths=[120, 120, 20, 20, "10"])
        self.my_plane_invalid_multiplicity_inherited = self.Plane(wings_lengths=[120, 120, 20, 20, 10])
        self.my_plane_invalid_type_inherited = self.Plane(brand=7, wings_lengths=[120, 120, 20, 20, 10])

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