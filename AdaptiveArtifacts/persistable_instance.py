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

class PersistableInstance(object):
    """
    Proxy to an AdaptiveArtifacts.meta_model.Instance instance (new or existing).
    This class provides behavior required by Trac's plugin architecture. Namely, behavior to deal with loading
    and saving instances from the database.
    """
    realm = 'asa'

    def __init__(self, env, identifier=None, name=None, version=None):
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
    def load(cls, env, identifier=None, name=None, version=None, ppool=None):
        """
        Loads an existing PersistableInstance from the database
        """
        pi = PersistableInstance(env, identifier, name, version)
        pi._fetch_contents(identifier=identifier, name=name, version=version, ppool=ppool)
        pi.resource = Resource('asa', pi.instance.get_identifier(), version) # in case we fetched the instance byits name instead of its identifier
        return pi

    def _fetch_contents(self, identifier=None, name=None, version=None, ppool=None):
        """
        Retrieves from the database a given state, or a set of states, for the specified instance
        """
        if not identifier and not name:
            raise Exception("Nothing to fetch. Either identifier or name must be previded")

        query = """
            SELECT id, version, time, author, ipnr, op_type, comment
            FROM asa_instance i
            """
        if not name is None:
            query += """
            	INNER JOIN asa_value v ON v.instance_id=i.id
            WHERE property_instance_id='__name' AND value='%s'""" %  name
        else:
            query += " WHERE id='%s'" %  identifier

        if not version is None:
            query += " AND version=%d" %  int(version)
        else:
            query += ' ORDER BY version DESC LIMIT 1'

        db = self.env.get_read_db()
        cursor = db.cursor()
        row = None
        emsg = ''
        try:
            cursor.execute(query)
            row = cursor.fetchone()
        except Exception, e:
            row = None
            emsg = e.message

        if not row:
            raise Exception("""Could not fetch data for instance.\n %s \n %s""" % (emsg, query))

        identifier, version, time, author, ipnr, op_type, comment = row

        query = """
                SELECT property_instance_id, value
                FROM asa_value
                WHERE instance_id='%s' AND instance_version='%s'
                """ % (identifier, version)
        
        cursor.execute(query)
        contents_dict = dict(cursor.fetchall())
        #contents_dict = pickle.loads(contents.encode('utf-8'))

        if ppool is None:
            ppool = PersistablePool.load(self.env)
        #self.instance = ppool.pool.get(identifier) #TODO: we should probably get this directly from PersistablePool?
        #if self.instance is None:
        from AdaptiveArtifacts.model import Instance
        self.instance =  Instance.create_from_properties(ppool.pool, identifier, contents_dict)
        #    self.version = 1
        self.version = int(version)
        self.time = from_utimestamp(time)
        self.author = author
        self.comment = comment
        #self.text = text
        #self.readonly = readonly and int(readonly) or 0


    exists = property(fget=lambda self: self.version > 0)

    def delete_instance(self, version=None, db=None):
        assert self.exists, 'Cannot delete non-existent asa_instance'

        @self.env.with_transaction()
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute("DELETE FROM asa_instance WHERE id=%s", (self.identifier,))
            cursor.execute("DELETE FROM asa_value WHERE instance_id=%s", (self.identifier,))
            self.env.log.info('Deleted asa_instance %s' % self.identifier)

    def save_instance(self, author, comment, remote_addr, t=None, db=None):
        @self.env.with_transaction()
        def do_save(db):
            #data = pickle.dumps(self.instance.state.slots).decode('utf-8')
            new_version = self.version + 1
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO asa_instance (id, version, time, author, ipnr, op_type, comment)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (self.instance.get_identifier(), new_version, to_utimestamp(t), author, remote_addr, 'C', comment))
            for property_ref in self.instance.state.slots:
                #pool = self.instance.pool
                #instance_meta = pool.get(id=self.instance.get_value('__id_meta'))
                #properties_meta = pool.get_properties(instance_meta)
                #if property_ref in properties_meta:
                cursor.execute("""
                    INSERT INTO asa_value (instance_id, instance_version, property_instance_id, value)
                    VALUES (%s,%s,%s,%s)
                    """, (self.instance.get_identifier(), new_version, property_ref, self.instance.state.slots[property_ref]))
                
            self.version += new_version
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

class PersistablePool(object):
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    def load(cls, env):
        from AdaptiveArtifacts.model import Instance, MetaElementInstance, Classifier, Package, Property, Entity, InstancePool
        ppool = PersistablePool(InstancePool())
        # load m2 from database
        for m2_class in (Entity, Instance, MetaElementInstance, Classifier, Package, Property):
            pi = PersistableInstance.load(env, name=m2_class.__name__, ppool=ppool)
            m2_class.id = pi.instance.get_identifier()
            pi.instance.set_value('__id_meta', Entity.id) # the meta of all M2 instances is Entity
            pi.instance.__class__ = Entity
        return ppool

    def get_instance(self, env, identifier=None, name=None, version=None):
        return PersistableInstance.load(env, identifier=identifier, name=name, version=version, ppool=self)

    def get_instances(self, env, id_meta, levels=[0,1]):
        instances = []
        db = env.get_read_db()
        cursor = db.cursor()
        rows = cursor.execute("""
                            SELECT id, max(version) version
                            FROM asa_instance i
                            	INNER JOIN asa_value v_idm ON v_idm.instance_id=i.id
                            	INNER JOIN asa_value v_lvm ON v_lvm.instance_id=i.id
                            WHERE
                                v_idm.property_instance_id='__id_meta' AND v_idm.value='%s' AND
                                v_lvm.property_instance_id='__meta_level' AND v_lvm.value in (%s)
                            GROUP BY id""" % (id_meta, ",".join(["%s" % lvl for lvl in levels])))
        for id, version in rows.fetchall():
            instances.append(PersistableInstance.load(env, id, version=version, ppool=self))
        return instances