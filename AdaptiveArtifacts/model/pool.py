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

    def add(self, instance):
        self._items.append(instance)

    def remove(self, item):
        self._items.remove(item)

    def get_item(self, id):
        assert(not id is None)
        for item in self._items:
            if item.get_id() == id:
                return item
        return None

    def get_items(self):
        return self._items

    def get_instances_of(self, meta_id):
        assert(not meta_id is None)
        return [item for item in self._items if item.__class__.get_id() == meta_id]

    def get_possible_domains(self):
        pool = self
        possible_domains = {'string':'string'}
        possible_domains.update(dict([(i.get_identifier(), i.get_name()) for i in pool.get_model_instances(Entity.get_id())]))
        return possible_domains

