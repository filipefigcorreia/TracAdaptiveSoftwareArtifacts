from trac.db import Table, Column, Index

schema_version = 1
schema = [
    Table('asa_instance', key='id')[
        Column('id'),
        Index(['id'], unique=True),
    ],
    Table('asa_version', key='id')[
        Column('id'),
        Column('time', type='int64'),
        Column('author'),
        Column('ipnr'),
        Column('comment'),
        Index(['id'], unique=True),
    ],
    Table('asa_operation', key='id')[
        Column('id'),
        Column('version_id'),
        Column('name'),
        Index(['id'], unique=True),
    ],
    Table('asa_state')[
        Column('instance_id'),
        Column('contents'), # contains pickled instances
        Column('op_type'), # 'C','U','D'
    ]
]

