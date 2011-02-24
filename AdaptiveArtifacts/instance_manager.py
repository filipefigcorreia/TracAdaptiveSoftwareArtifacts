# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Filipe Correia
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.core import *
from trac.resource import Resource
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
from AdaptiveArtifacts.meta_model import InstancePool, Instance

class PersistableInstance(object):
    """
    Proxy to an AdaptiveArtifacts.meta_model.Instance instance (new or existing).
    This class provides behavior required by Trac's plugin architecture. Namely, behavior to deal with loading
    and saving instances from the database.
    """

    realm = 'asa'

    def __init__(self, env, identifier=None, version=None, db=None):
        self.env = env
        self.instance = None
        if version:
            version = int(version) # must be a number or None
        self.resource = Resource('asa', identifier, version)

        if identifier:
            self._fetch_instance(identifier, version, db)
        else:
            self.version = 0
            self.time = None
            self.comment = self.author = ''
            #self.text =
            #self.readonly = 0
        #self.old_text = self.text
        #self.old_readonly = self.readonly

    def _fetch_instance(self, identifier, version=None, db=None):
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        if version is not None:
            cursor.execute("SELECT name_meta, name, version, time, author, ipnr, contents, op_type, comment"
                           "FROM asa_instance "
                           "WHERE name=%s AND version=%s",
                           (identifier, int(version)))
        else:
            cursor.execute("SELECT name_meta, name, version, time, author, ipnr, contents, op_type, comment"
                           "FROM asa_instance "
                           "WHERE id=%s ORDER BY version DESC LIMIT 1",
                           (identifier,))
        row = cursor.fetchone()
        if row:
            name_meta, name, version, time, author, ipnr, contents, op_type, comment = row
            contents_dict = unpickle(contents)
            pool = InstancePool()
            self.instance = pool.get(identifier)
            if self.instance is None:
                self.instance = Instance(pool=None, name_meta=None)
                self.instance.load_from_properties(pool, identifier, contents_dict)
                self.version = 1
            self.version = int(version)
            self.time = from_utimestamp(time)
            self.author = author
            self.comment = comment
            #self.text = text
            #self.readonly = readonly and int(readonly) or 0
        else:
            self.version = 0
            self.time = None
            self.comment = self.author = ''
            #self.text = ''
            #self.readonly = 0

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
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO asa_instance (id, name_meta, name, version, time, author, ipnr, contents,
                                  op_type, comment)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (self.identifier, self.get_name(), self.version + 1, to_utimestamp(t),
                      author, remote_addr, self.instance.state.slots, comment,
                      self.readonly))
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
