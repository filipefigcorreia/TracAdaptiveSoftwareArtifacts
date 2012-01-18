# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from util import Proxy

class PresentableInstance(Proxy):
    """
     Proxy to an instance of AdaptiveArtifacts.model.Instance.
     This class contains logic specific to the user-interface.
     """
    def __init__(self, instance):
        super(PresentableInstance, self).__init__(instance)
        self.instance = instance

    # shadowing the instance function
    def get_properties(self):
        return [PresentableProperty(prop) for prop in self.instance.get_properties() if int(prop.get_order() or "1") > 0]

class PresentableProperty(Proxy):
    def __init__(self, property):
        super(PresentableProperty, self).__init__(property)
        self.property = property

    def is_mandatory(self):
        return int(self.property.get_lower_bound()) > 0

    def get_domain_name(self):
        domain = self.property.get_domain()
        if domain in ('string', 'python'):
            return domain
        else:
            type_instance = self.property.pool.get_instance(domain)
            if not type_instance is None:
                return type_instance.get_name()
            else:
                return None

    def get_field_type(self):
        domain = self.property.get_domain()
        if domain in ('string', 'python'):
            return 'text'
        else:
            return 'combo'

    def get_possible_values(self, pinstance):
        values = self.property.get_possible_values(pinstance.instance)
        if values is None: values = []
        return values