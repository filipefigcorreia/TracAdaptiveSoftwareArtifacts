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

    def get_items(self, levels=(0,1,2)):
        if levels == (0,1,2):
            return self._items
        else:
            return [item for item in self._items if
                    isinstance(item, Instance) and 0 in levels or
                    isinstance(item, Entity) and 1 in levels or
                    item in (Entity, Instance) and 2 in levels]

    def get_instances_of(self, meta_id):
        assert(not meta_id is None)
        return [item for item in self._items if hasattr(item.__class__, 'get_id') and item.__class__.get_id() == meta_id]

    def get_possible_domains(self):
        pool = self
        possible_domains = {'string':'string'}
        possible_domains.update(dict([(i.get_identifier(), i.get_name()) for i in pool.get_model_instances(Entity.get_id())]))
        return possible_domains

