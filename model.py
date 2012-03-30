# -*- coding: utf-8 -*-

"""
Goal is not to avoid reinventing the Wheel™, and try to use the python
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
        self.name = kwargs.pop('name', "An Entity")
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __str__(self):
        str_value = eval("self." + self.str_attr)
        if not str_value is None:
            return str_value
        else:
            return repr(self)

    @classmethod
    def __get_all(cls, attr_name):
        merged_dict = {}
        for base in reversed(cls.mro()):
            if hasattr(base, attr_name):
                merged_dict = dict(merged_dict.items() + getattr(base, attr_name).items())
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
                            violations.append((attr, "Type violation. Expected '%s', got '%s'" % (self.__class__.types.get(attr), type(value_item))))
        return violations

class Entity(type):
    def __new__(mcs, *args, **kwargs):
        """
        It's not very usual for __new__ to receive args and kwargs,
        instead of the usual: mcs, name, bases, dct.
        We need it here because we want to pass extra params, to
        be picked up by __init__
        """
        name = args[0] if len(args)>0 else kwargs.get('name', None)
        bases = args[1] if len(args)>1 else kwargs.get('bases', tuple())
        dct = args[2] if len(args)>2 else kwargs.get('dct', {})
        if len(bases) == 0:
            bases = (Instance, )
        return super(Entity, mcs).__new__(mcs, name, bases, dct)

    def __init__(cls, *args, **kwargs):
        extra_kwargs = dict(kwargs)
        name = args[0] if len(args)>0 else extra_kwargs.pop('name', None)
        bases = args[1] if len(args)>1 else extra_kwargs.pop('bases', None)
        dct = args[2] if len(args)>2 else extra_kwargs.pop('dct', None)
        cls.attributes = extra_kwargs.get('attributes', {})
        cls.types = extra_kwargs.get('types', {})
        cls.multiplicities = extra_kwargs.get('multiplicities', {})
        super(Entity, cls).__init__(name, bases, dct)

#no constraint
E1 = Entity(name="Car", attributes={"ndoors":"Number of Doors", "brand":"Brand"})
i1 = E1(ndoors=5, brand="Volvo")
print i1.get_meta_violations()

# multiplicity & type from base class
C = Entity(name="Car",
        attributes={"ndoors":"Number of Doors", "brand":"Brand"},
        multiplicities={"ndoors": 1},
        types={"ndoors": int},
    )

EC = Entity(name="Electric Car", bases=(C,),
        attributes={"tires_pressure": "Tires Pressure"},
        multiplicities={"tires_pressure": 4}
    )
ec = EC(ndoors=3, brand="Ford", tires_pressure=[22,23,21,22])
print ec.get_meta_violations()

# multiplicity
E2 = Entity(
    name="Plane",
    attributes={"tires_pressure": "Tires Pressure", "max_air_speed": "Maximum Air Speed"},
    multiplicities={"tires_pressure": 3})
i2 = E2(tires_pressure=[12,15,13])
print i2.get_meta_violations()

# type
E3 = Entity(name="Tank", types={"occupants_names": str})
i3 = E3(occupants_names=["Jhon", "Jack"])
print i3.get_meta_violations()

#no class
i4 = Instance(name="Cenas", age=42, yo=[12,23,34])
print i4.get_meta_violations()
