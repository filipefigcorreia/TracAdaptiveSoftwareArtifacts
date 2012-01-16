# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.db import DatabaseManager
from AdaptiveArtifacts import schema
import traceback

class ASAEnvironmentMaintainer(object):
    """Modifies environments according to the needs of the ASA plugin"""
    def __init__(self, env):
        from distutils import version
        self.db_key = 'asa_plugin_database_version'
        self.default_version = '0.0'
        self.schema_version = version.StrictVersion(get_system_value(env, self.db_key) or self.default_version)
        self.running_version = version.StrictVersion('0.1') # TODO: get this value from setup.py
        self.env = env

    def install_asa_support(self):
        self.env.log.debug("Adding support for the ASA plugin.")
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO system (name, value) VALUES ('%s', '%s')" %
                       (self.db_key, str(self.running_version)))
        for table in schema.schema:
            connector, _ = DatabaseManager(self.env)._get_connector()
            for stmt in connector.to_sql(table):
                self.env.log.debug("Running query: \n %s" % stmt)
                cursor.execute(stmt)

        self.schema_version = self.running_version

    def needs_upgrade(self):
        if self.schema_version == self.running_version:
            return False
        self.env.log.debug("The ASA plugin needs to upgrade the environment.")
        return True

    def upgrade(self):
        self.env.log.debug("The ASA plugin is upgrading the existing environment.")

        try:
            if self.schema_version == self.default_version:
                self.install_asa_support()
                _save_m2_bootstraped_pool(self.env)
#           elif self.schema_version == 'XXXX':
#                cursor = db.cursor()
#                cursor.execute("UPDATE various stuff ...")
#                cursor.execute("UPDATE system SET value=%s WHERE name='%s'" % (self.db_key, self.running_version))
#               self.log.info('Upgraded ASA tables from version %s to %s' % (self.db_key, self.running_version))
        finally:
            pass
            #self.env.log.error(traceback.format_exc())


def _save_m2_bootstraped_pool(env):
    from persistable_instance import PersistableInstance, PersistablePool
    from model import InstancePool

    ppool = PersistablePool(env, InstancePool(True))
    ppool.save(meta_levels=['2'])

# additional methods
def get_system_value(env, key):
    return get_scalar_value(env, "SELECT value FROM system WHERE name=%s", 0, key)

def get_scalar_value(env, query, col=0, *params):
    data = get_first_row(env, query, *params)
    if data:
        return data[col]
    else:
        return None

def get_first_row(env, query, *params):
    cursor = env.get_db_cnx().cursor()
    data = None
    try:
        cursor.execute(query, params)
        data = cursor.fetchone()
    except Exception, e:
        env.log.exception( \
            'There was a problem executing sql: %s \n \
            with parameters: %s\n \
            Exception: %s' % (query, params, e))
        cursor.connection.rollback()
    return data