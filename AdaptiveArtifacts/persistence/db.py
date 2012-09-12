## -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.core import *
from trac.db import Table, Column, Index
from trac.db import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
#from AdaptiveArtifacts.environment_maintainer import ASAEnvironmentMaintainer

schema_version = 1
schema = [
    Table('asa_version', key='id')[
            Column('id', type='int64', auto_increment=True),
            Column('time', type='int64'),
            Column('author'),
            Column('ipnr'),
            Column('comment'),
            Column('readonly',  type='int'),
            Index(['id'], unique=True),
    ],
    # Workaround for sqlite not supporting multiple column primary keys with an auto-increment.
    # This table as the sole purpose of getting the auto-increment values
    Table('asa_artifact_id', key='id')[
        Column('id', type='int64', auto_increment=True),
    ],
    Table('asa_artifact', key=['id', 'version_id'])[
        Column('id', type='int64'),
        Column('version_id', type='int64'),
        Column('meta_class'),
        Column('title_expr'), # the "toString()" of artifacts
        Index(['id', 'version_id'], unique=True),
    ],
    Table('asa_artifact_value')[
        Column('artifact_id', type='int64'),
        Column('version_id', type='int64'),
        Column('attr_name'),
        Column('attr_value'),
        Index(['artifact_id', 'version_id']),
    ],
    Table('asa_spec', key=['name', 'version_id'])[
        Column('name'),
        Column('version_id', type='int64'),
        Column('base_class'),
        Index(['name', 'version_id'], unique=True),
    ],
    Table('asa_spec_attribute')[
        Column('spec_name'),
        Column('version_id', type='int64'),
        Column('name'),
        Column('multplicity_low'),
        Column('multplicity_high'),
        Column('type'),
        Index(['spec_name', 'version_id']),
    ],
]

class Setup(Component):
    """Installs, upgrades and uninstalls database support for the plugin."""
    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        super(Component, self).__init__()
        from distutils import version
        self.db_key = 'asa_plugin_database_version'
        self.default_version = '0.0'
        self.schema_version = version.StrictVersion(self._get_system_value(self.db_key) or self.default_version)
        self.running_version = version.StrictVersion('0.1') # TODO: get this value from setup.py

    # start IEnvironmentSetupParticipant methods
    def environment_created(self):
        self._install_asa_support()

    def environment_needs_upgrade(self, db):
        if self.schema_version == self.running_version:
            return False
        self.env.log.debug("The ASA plugin needs to upgrade the environment.")
        return True

    def upgrade_environment(self, db):
        self.env.log.debug("The ASA plugin is upgrading the existing environment.")

        try:
            if self.schema_version == self.default_version:
                self._install_asa_support()
#           elif self.schema_version == 'XXXX':
#                cursor = db.cursor()
#                cursor.execute("UPDATE various stuff ...")
#                cursor.execute("UPDATE system SET value=%s WHERE name='%s'" % (self.db_key, self.running_version))
#               self.log.info('Upgraded ASA tables from version %s to %s' % (self.db_key, self.running_version))
        except Exception as e:
            self.env.log.debug("Error while upgrading the environment.\n" + str(e))
        finally:
            pass
            #self.env.log.error(traceback.format_exc())

    # end IEnvironmentSetupParticipant methods

    def _install_asa_support(self):
        self.env.log.debug("Adding support for the ASA plugin.")
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO system (name, value) VALUES ('%s', '%s')" %
                       (self.db_key, str(self.running_version)))
        for table in schema: # TODO: fix. reference to global var
            connector, _ = DatabaseManager(self.env)._get_connector()
            for stmt in connector.to_sql(table):
                self.env.log.debug("Running query: \n %s" % stmt)
                cursor.execute(stmt)

        self.schema_version = self.running_version


    def _get_system_value(self, key):
        return self._get_scalar_value("SELECT value FROM system WHERE name=%s", 0, key)

    def _get_scalar_value(self, query, col=0, *params):
        data = self._get_first_row(query, *params)
        if data:
            return data[col]
        else:
            return None

    def _get_first_row(self, query, *params):
        cursor = self.env.get_db_cnx().cursor()
        data = None
        try:
            cursor.execute(query, params)
            data = cursor.fetchone()
        except Exception, e:
            self.env.log.exception(
                'There was a problem executing sql: %s \n \
                with parameters: %s\n \
                Exception: %s' % (query, params, e))
            cursor.connection.rollback()
        return data