class Instance(object):
    def __init__(self, *args, **kwargs):
        """
        The way we are dealing with meta and super is a reinvention of
        the wheel --- let's say, a BetterWheel™.

        Q: Why not just use python's meta/instantiation mechanism instead
        of having the "meta" attribute in Instance?
        A: Because we don't want to be forced to have a class/entity for
        the instances that we create. The class/entity can be attached
        to the instance later on.
        """

        self.id = kwargs.pop('id', None)
        self.str_attr = kwargs.pop('str_attr', "id")
        self.name = kwargs.pop('name', "An Entity")
        self.meta = kwargs.pop('meta', None)
        self.meta_level = kwargs.pop('meta_level', 0)
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __str__(self):
        str_value = eval("self." + self.str_attr)
        if not str_value is None:
            return str_value
        else:
            return repr(self)

    def get_meta_violations(self):
        violations = []
        if not self.meta is None:
            # are the multiplicities of all instance values ok?
            for attr, multiplicity in self.meta.multiplicities.iteritems():
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
                if self.meta.types.has_key(attr):
                    value_list = [value] if type(value) != list else value
                    for value_item in value_list:
                        if type(value_item) != self.meta.types.get(attr):
                            violations.append((attr, "Type violation. Expected '%s', got '%s'" % (type(value_item), self.meta.types.get(attr))))
        return violations

class Entity(Instance):
    def __init__(self, *args, **kwargs):
        kwargs['meta_level'] = 1
        self.__bases__ = kwargs.pop('bases', (Instance,))
        self.attributes = kwargs.pop('attributes', {})
        self.types = kwargs.pop('types', {})
        self.multiplicities = kwargs.pop('multiplicities', {})
        super(Entity, self).__init__(self, **kwargs)


#no constraint
e1 = Entity(name="Car", attributes={"nwheels":"Number of Wheels", "brand":"Brand"})
i1 = Instance(meta=e1, nwheels=4, brand="Volvo")
print i1.get_meta_violations()

# multiplicity
e2 = Entity(
    name="Plane",
    attributes={"tires_pressure": "Tires Pressure", "max_air_speed": "Maximum Air Speed"},
    multiplicities={"tires_pressure": 3})
i2 = Instance(meta=e2, tires_pressure=[12,15,13])
print i2.get_meta_violations()

#type
e3 = Entity(name="Tank", types={"occupants_names": str})
i3 = Instance(meta=e3, occupants_names=["Jhon", "Jack", 4])
print i3.get_meta_violations()