# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

class Query(object):
    def __init__(self):
        self.resource_name = None
        self.action = None

    def execute(self):
        result = QueryResult()
        if self.resource_name in ('', 'entrypoints'):
            result = None
        elif self.resource_name == 'entities':
            result = None
        return result

    @classmethod
    def from_url_params(cls, resource_name, action):
        query = Query()
        query.resource_name = resource_name
        query.action = action
        return query

class QueryResult(object):
    def __init__(self):
        self.meta = None # let's assume all items in the collection have the same meta
        self.items = []
        self.columns = {} # key,value = column_name,property_to_get