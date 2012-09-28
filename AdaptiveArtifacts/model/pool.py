# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from core import *

class InstancePool(object):
    """
    Container for instances of Instance and Entity, that provides
    some utility methods to search through them.
    """
    def __init__(self):
        self._items = []

        # Handle special case of the top-most classes of the instantiation chain (Entity and Instance).
        # They are not loaded explicitly, and are always available from any pool.
        self.add(Entity)
        self.add(Instance)

    def add(self, instance):
        id = instance.get_id()
        if not id is None and not self.get_item(id) is None:
            # raising an exception is an option. an alternative would be to silently replace the instance with the one
            # being loaded, but there may be implications when working with multiple versions of a same instance
            raise Exception("Instance with id '%s' already exists in the pool" % (instance.get_id(),))
        self._items.append(instance)

    def remove(self, item):
        self._items.remove(item)

    def get_item(self, id):
        assert(not id is None)
        for item in self._items:
            if item.get_id() == id:
                return item
        return None

    def get_items(self, levels=(0,1,2), base_name=None):
        result = self._items
        if not levels == (0,1,2):
            result = [item for item in result if
                    isinstance(item, Instance) and 0 in levels or
                    isinstance(item, Entity) and 1 in levels or
                    item in (Entity, Instance) and 2 in levels]
        if not base_name is None:
            base = self.get_item(base_name)
            result = [item for item in result if isinstance(item, Entity) and len(item.__bases__) > 0 and item.__bases__[0] is base]
        return result

    def get_instances_of(self, spec_name, direct_instances_only=False):
        assert(not spec_name is None)
        if direct_instances_only:
            return [item for item in self._items if hasattr(item.__class__, 'name') and item.__class__.name == spec_name]
        else:
            spec_and_childs = self.get_spec_and_child_specs(spec_name)
            return [item for item in self._items if item.__class__ in spec_and_childs]

    def get_spec_and_child_specs(self, spec_name):
        inh_chain = current = [self.get_item(spec_name)]
        while True:
            childs = [self.get_items(base_name=spec.get_name()) for spec in current]
            current = [child for sublist in childs for child in sublist]
            if len(current) == 0:
                break
            inh_chain.extend(current)
        return inh_chain

    def get_possible_domains(self):
        pool = self
        possible_domains = {'string':'string'}
        possible_domains.update(dict([(i.get_identifier(), i.get_name()) for i in pool.get_items(levels=(1,))]))
        return possible_domains

