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
    Table('asa_instance', key='id')[
        Column('id'),
        Column('name_meta'),
        Column('name'), # only filled if meta_level >= 1
        Column('version', type='int64'),
        Column('time', type='int64'),
        Column('author'),
        Column('ipnr'),
        Column('contents'), # contains pickled properties dictionary
        Column('op_type'), # 'C','U','D'
        Column('comment'),
        Index(['id', 'version'], unique=True),
    ],
]

