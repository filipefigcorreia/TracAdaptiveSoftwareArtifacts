# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.resource import Resource
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
try:
    import cPickle as pickle
except:
    import pickle
from AdaptiveArtifacts.model import InstancePool, Instance

class PersistableInstance(object):
    """
    Proxy to an AdaptiveArtifacts.meta_model.Instance instance (new or existing).
    This class provides behavior required by Trac's plugin architecture. Namely, behavior to deal with loading
    and saving instances from the database.
    """

    realm = 'asa'

    def __init__(self, env, identifier=None, name=None, version=None, db=None):
        """
        Creates a brand new PersistableInstance. I.e., one that does not exist in the database yet.
        """
        self.env = env
        self.instance = None
        self.version = 0
        if version:
            self.version = int(version) # must be a number or None
        self.resource = Resource('asa', identifier, version)

        self.time = None
        self.comment = self.author = ''
        #self.text =
        #self.readonly = 0


    @classmethod
    def load(cls, env, identifier=None, name=None, version=None, db=None):
        """
        Loads an existing PersistableInstance from the database
        """
        pi = PersistableInstance(env, identifier, name, version, db)
        pi._fetch_instance(identifier=identifier, name=name, version=version, db=db)
        pi.resource = Resource('asa', pi.instance.get_identifier(), version) # in case we fetched the instance byits name instead of its identifier
        return pi

    def _fetch_instance(self, identifier=None, name=None, version=None, db=None):
        if not identifier and not name:
            raise Exception("Nothing to fetch. Either identifier or name must be previded")
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        if not name is None:
            filter = "name='%s'" %  name
        else:
            filter = "id='%s'" %  identifier
        if version is not None:
            cursor.execute("SELECT id, name_meta, name, version, time, author, ipnr, contents, op_type, comment "
                           "FROM asa_instance "
                           "WHERE %s AND version=%s",
                           (filter, int(version)))
        else:
            q = "SELECT id, name_meta, name, version, time, author, ipnr, contents, op_type, comment " + \
                "FROM asa_instance " + \
                "WHERE %s ORDER BY version DESC LIMIT 1" % (filter,)
            cursor.execute(q)
        row = cursor.fetchone()
        if row:
            identifier, name_meta, name, version, time, author, ipnr, contents, op_type, comment = row
            contents_dict = pickle.loads(contents.encode('utf-8'))
            pool = InstancePool()
            self.instance = pool.get(identifier)
            if self.instance is None:
                self.instance =  Instance.create_from_properties(pool, identifier, contents_dict)
                self.version = 1
            self.version = int(version)
            self.time = from_utimestamp(time)
            self.author = author
            self.comment = comment
            #self.text = text
            #self.readonly = readonly and int(readonly) or 0
        else:
            raise Exception("Resource not found")

    exists = property(fget=lambda self: self.version > 0)

    def delete_instance(self, version=None, db=None):
        assert self.exists, 'Cannot delete non-existent asa_instance'

        @self.env.with_transaction(db)
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute("DELETE FROM asa_instance WHERE id=%s", (self.identifier,))
            self.env.log.info('Deleted asa_instance %s' % self.identifier)

    def save_instance(self, author, comment, remote_addr, t=None, db=None):
        @self.env.with_transaction(db)
        def do_save(db):
            data = pickle.dumps(self.instance.state.slots).decode('utf-8')
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO asa_instance (id, name_meta, name, version, time, author, ipnr, contents,
                                  op_type, comment)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (self.instance.get_identifier(), self.instance.get_name_meta(), self.instance.get_name(), self.version + 1, to_utimestamp(t),
                      author, remote_addr, data, 'C', comment))
            self.version += 1
            self.resource = self.resource(version=self.version)

        self.author = author
        self.comment = comment
        self.time = t

    def get_history(self, db=None):
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT version,time,author,comment,ipnr FROM asa_instance "
                       "WHERE id=%s AND version<=%s "
                       "ORDER BY version DESC", (self.identifier, self.version))
        for version, ts, author, comment, ipnr in cursor:
            yield version, from_utimestamp(ts), author, comment, ipnr
