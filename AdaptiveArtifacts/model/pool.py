# -*- coding: utf-8 -*-
#
# Copyright (C) Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from core import *

class InstancePool(object):
    def __init__(self):
        self.instances = {}

    def add(self, instance):
        self.instances[instance.id] = instance

    def remove(self, identifier):
        del self.instances[identifier]

    def get_instance(self, id=None):
        if not id in self.instances:
            return None
        return self.instances[id]

    def get_instances_of(self, meta_id):
        return self.get_instances(meta_id=meta_id)

    def get_entities(self):
        return self.get_instances_of(meta_id='__Entity')

    def get_instances(self, meta_id=None):
        instances = []
        for id, instance in self.instances.items():
            if not meta_id is None and instance.__class__.id != meta_id:
                continue
            instances.append(instance)
        return instances

    def get_possible_domains(self):
        pool = self
        possible_domains = {'string':'string'}
        possible_domains.update(dict([(i.get_identifier(), i.get_name()) for i in pool.get_model_instances(Entity.id)]))
        return possible_domains

