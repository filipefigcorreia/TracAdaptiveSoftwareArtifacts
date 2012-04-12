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

class Instance(object):
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

    @classmethod
    def __get_all(cls, ex_attr_name):
        """
        Receives an attribute name that has the goal of extending the
        python model (e.g., "multiplicities", "types") and collects
        its values from the class' inheritance chain.
        """
        merged_dict = {}
        for base in reversed(cls.mro()):
            if hasattr(base, ex_attr_name):
                merged_dict = dict(merged_dict.items() + getattr(base, ex_attr_name).items())
        return merged_dict

    def get_meta_violations(self):
        """
        Compares an instance with it's meta, and returns a list of
        noncompliant attributes
        """
        violations = []
        if isinstance(self, Instance) and not self.__class__ is Instance: # if there's a meta other than "Instance"
            # are the multiplicities of all instance values ok?
            for attr, multiplicity in self.__class__.__get_all("multiplicities").iteritems():
                if type(multiplicity) == tuple:
                    low, high = multiplicity
                elif type(multiplicity) == int:
                    low=high=multiplicity
                else:
                    raise ValueError("Wrong type for multiplicity: '%s'" % type(multiplicity))
                if not self.__dict__.has_key(attr):
                    if low > 0:
                        violations.append((attr, "Lower bound violation. Expected at least '%s', got '0'" % low))
                    continue
                val = self.__dict__.get(attr)
                amount = 1
                if type(val) == list:
                    amount = len(val)
                if amount < low:
                    violations.append((attr, "Lower bound violation. Expected at least '%s', got '%s'" % (low, amount)))
                if amount > high:
                    violations.append((attr, "Upper bound violation. Expected at most '%s', got '%s'" % (high, amount)))
            # is the type of all instance values ok?
            for attr, value in self.__dict__.iteritems():
                if self.__class__.__get_all("types").has_key(attr):
                    value_list = [value] if type(value) != list else value
                    for value_item in value_list:
                        if type(value_item) != self.__class__.__get_all("types").get(attr):
                            violations.append((attr, "Type violation. Expected '%s', got '%s'" % (self.__class__.__get_all("types").get(attr), type(value_item))))
        return violations

class Entity(type):
    def __new__(mcs, *args, **kwargs):
        """
        It's not very usual for __new__ to receive args and kwargs,
        instead of the usual: mcs, name, bases, dct.
        We need it here because we want to pass extra params, to
        be picked up by __init__
        """
        name = Entity.__to_valid_identifier_name(
            args[0] if len(args)>0 else kwargs.get('name', None)
        )
        bases = args[1] if len(args)>1 else kwargs.get('bases', tuple())
        dct = args[2] if len(args)>2 else kwargs.get('dct', {})
        if len(bases) == 0:
            bases = (Instance, )
        return super(Entity, mcs).__new__(mcs, name, bases, dct)

    def __init__(cls, *args, **kwargs):
        extra_kwargs = dict(kwargs)
        cls.id = args[0] if len(args)>0 else extra_kwargs.pop('name', None)
        name = Entity.__to_valid_identifier_name(cls.id)
        bases = args[1] if len(args)>1 else extra_kwargs.pop('bases', None)
        dct = args[2] if len(args)>2 else extra_kwargs.pop('dct', None)
        cls.attributes = extra_kwargs.get('attributes', {})
        cls.types = extra_kwargs.get('types', {})
        cls.multiplicities = extra_kwargs.get('multiplicities', {})
        super(Entity, cls).__init__(name, bases, dct)

    @staticmethod
    def __to_valid_identifier_name(name):
        """
        Uses name to create a valid identifier by removing illegal characters
        http://docs.python.org/reference/lexical_analysis.html#identifiers
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
                if ch == '_' or ch.isalpha() or ch.isdigit():
                    yield ch
        return ''.join(gen_valid_identifier(name))



import unittest

class TestModel(unittest.TestCase):

    def setUp(self):
        self.Vehicle = Entity(name="Vehicle",
            attributes={"num_engines":"Number of Engines", "brand":"Brand"},
            multiplicities={"brand":1},
            types={"brand":str}
        )
        self.myvehicle = self.Vehicle(num_engines=2, brand="Volvo")
        self.Car = Entity(name="Car", bases=(self.Vehicle,),
                attributes={"ndoors":"Number of Doors"},
                multiplicities={"ndoors":1},
                types={"ndoors":int}
        )
        self.mycar = self.Car(ndoors=5, brand="Ford")
        self.Plane = Entity(name="Plane", bases=(self.Vehicle,),
                attributes={"wings_lengths":"Lengths of the Wings"},
                multiplicities={"wings_lengths":(2,5)},
                types={"wings_lengths":int}
            )
        self.my_plane_invalid_multiplicity = self.Plane(num_engines=4, brand="Airbus", wings_lengths=[120, 120, 20, 20, 10, 10])
        self.my_plane_invalid_type = self.Plane(brand="Airbus", wings_lengths=[120, 120, 20, 20, "10"])
        self.my_plane_invalid_multiplicity_inherited = self.Plane(wings_lengths=[120, 120, 20, 20, 10])
        self.my_plane_invalid_type_inherited = self.Plane(brand=7, wings_lengths=[120, 120, 20, 20, 10])

    def test_no_violations(self):
        self.assertEqual(len(self.myvehicle.get_meta_violations()), 0)
        self.assertEqual(len(self.mycar.get_meta_violations()), 0)

    def test_multiplicity(self):
        self.assertEqual(len(self.my_plane_invalid_multiplicity.get_meta_violations()), 1)

    def test_type(self):
        self.assertEqual(len(self.my_plane_invalid_type.get_meta_violations()), 1)

    def test_inherited_multiplicity(self):
        self.assertEqual(len(self.my_plane_invalid_multiplicity_inherited.get_meta_violations()), 1)

    def test_inherited_type(self):
        self.assertEqual(len(self.my_plane_invalid_type_inherited.get_meta_violations()), 1)

if __name__ == '__main__':
    unittest.main()