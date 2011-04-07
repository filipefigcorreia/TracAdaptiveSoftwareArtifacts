# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.db import Table, Column, Index

schema_version = 1
schema = [
    Table('asa_instance', key=('id', 'version'))[ #Instance and InstanceState rolled into a single table
        Column('id'),
        Column('version', type='int64'),
        Column('time', type='int64'),
        Column('author'),
        Column('ipnr'),
        Column('op_type'), # 'C','U','D'
        Column('comment'),
        Index(['id', 'version'], unique=True),
    ],
    Table('asa_value', key=('instance_id', 'instance_version', 'property_instance_id'))[
        Column('instance_id'),
        Column('instance_version'),
        Column('property_instance_id'),
        #Column('id_meta'),
        #Column('name'), # only filled if meta_level >= 1
        #Column('contents'), # contains pickled properties dictionary
        Column('value'),
        Index(['instance_id', 'instance_version', 'property_instance_id'], unique=True),
    ],
]

