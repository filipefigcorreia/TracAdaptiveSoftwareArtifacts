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
    Proxy to an instance of AdaptiveArtifacts.model.Instance (new or existing).
    This class provides behavior required by Trac's plugin architecture. Namely, behavior to deal with loading
    and saving instances from the database.
    """
    realm = 'asa'

    def __init__(self, env, identifier=None, version=None):
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
    def load(cls, env, identifier=None, iname=None, version=None, ppool=None):
        """
        Loads an existing PersistableInstance from the database
        """
        pi = PersistableInstance(env, identifier, version)
        pi._fetch_contents(identifier=identifier, iname=iname, version=version, ppool=ppool)
        pi.resource = Resource('asa', pi.instance.get_identifier(), version) # in case we fetched the instance byits name instead of its identifier
        return pi

    def _fetch_contents(self, identifier=None, iname=None, version=None, ppool=None):
        """
        Retrieves from the database a given state, or a set of states, for the specified instance
        """
        if not identifier and not iname:
            raise Exception("Nothing to fetch. Either identifier or name must be previded")

        query = """
            SELECT id, iname, meta_level, version, time, author, ipnr, op_type, comment
            FROM asa_instance i
            """
        if not iname is None:
            query += " WHERE iname='%s'" %  iname
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

        identifier, iname, meta_level, version, time, author, ipnr, op_type, comment = row

        query = """
                SELECT property_instance_id, value
                FROM asa_value
                WHERE instance_id='%s' AND instance_version='%s'
                """ % (identifier, version)
        
        cursor.execute(query)
        contents_dict = dict(cursor.fetchall())

        query = """
                SELECT property_instance_id, property_instance_iname
                FROM asa_value
                WHERE instance_id='%s' AND instance_version='%s'
                """ % (identifier, version)

        cursor.execute(query)
        property_inames_dict = dict(cursor.fetchall())

        if ppool is None:
            ppool = PersistablePool.load(self.env)
        from AdaptiveArtifacts.model import Instance
        #TODO: maybe we should probably get this directly from PersistablePool?
        self.instance =  Instance.create_from_properties(ppool.pool, identifier, iname, meta_level, contents_dict, property_inames_dict)
        #    self.version = 1
        self.version = int(version)
        self.time = from_utimestamp(time)
        self.author = author
        self.comment = comment

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
            new_version = self.version + 1
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO asa_instance (id, iname, meta_level, version, time, author, ipnr, op_type, comment)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (self.instance.get_identifier(), self.instance.get_iname(), self.instance.get_meta_level(), new_version, to_utimestamp(t), author, remote_addr, 'C', comment))
            for property_ref in self.instance.state.slots: #TODO: state shouldn't be accessed directly
                #pool = self.instance.pool
                #instance_meta = pool.get(id=self.instance.get_value('__meta'))
                #properties_meta = pool.get_properties(instance_meta)
                #if property_ref in properties_meta:
                #self.env.log.error((self.instance.get_identifier(), new_version, property_ref, self.instance.state.slots[property_ref]))
                cursor.execute("""
                    INSERT INTO asa_value (instance_id, instance_version, property_instance_id, property_instance_iname, value)
                    VALUES (%s,%s,%s,%s,%s)
                    """, (self.instance.get_identifier(), new_version, property_ref, self.instance.get_property_iname(property_ref), self.instance.get_slot_value(property_ref)))
                
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
                       "ORDER BY version DESC", (self.instance.get_identifier(), self.version))
        for version, ts, author, comment, ipnr in cursor:
            yield version, from_utimestamp(ts), author, comment, ipnr

class PersistablePool(object):
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    def load_old(cls, env):
        # Loads the entire M2 level from the database
        from AdaptiveArtifacts.model import Instance, MetaElementInstance, Classifier, Package, Property, Entity, InstancePool
        ppool = PersistablePool(InstancePool())
        # TODO: FIXME: either I must expand this (currently very naive) list of M2 entities, or make it more dynamic. I probably want to just load everything marked as lvl 2 that exists in the database
        for m2_class in (Entity, Instance, MetaElementInstance, Classifier, Package, Property):
            pi = PersistableInstance.load(env, name=m2_class.__name__, ppool=ppool)
            m2_class.id = pi.instance.get_identifier()
            pi.instance.set_value_by_iname('__meta', Entity.id) # the meta of all M2 instances is Entity
            pi.instance.__class__ = Entity
        return ppool

    @classmethod
    def load(cls, env):
        # Loads the entire M2 level from the database
        from model import InstancePool
        ppool = PersistablePool(InstancePool())
        ppool.get_metamodel_instances(env)
        return ppool

    def get_instance(self, env, identifier=None, iname=None, version=None):
        return PersistableInstance.load(env, identifier=identifier, iname=iname, version=version, ppool=self)

    def get_metamodel_instances(self, env):
        p_instances = []
        db = env.get_read_db()
        cursor = db.cursor()
        # Note the exquisite acrobatics to ensure that "Entity" is the first result. This is because of the calls to meta
        rows = cursor.execute("""
            SELECT id, max(version) version, CASE WHEN i.iname = '__entity' THEN 0 WHEN i.iname in ('__property', '__classifier', '__instance', '__metaelement', '__package') THEN 1 ELSE 2 END AS is_not_entity
            FROM asa_instance i
            WHERE i.meta_level = 2
            GROUP BY id
            ORDER BY is_not_entity, i.iname""")
        for id, version, dummy in rows.fetchall():
            p_instances.append(PersistableInstance.load(env, id, version=version, ppool=self))
        return p_instances

    def get_instances_of(self, env, id_meta, levels=[0,1]):
        p_instances = []
        db = env.get_read_db()
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT id, max(version) version
                FROM asa_instance i
                    INNER JOIN asa_value v_idm ON v_idm.instance_id=i.id
                WHERE
                    v_idm.property_instance_iname='__meta' AND v_idm.value='%s' AND
                    i.meta_level in (%s)
                GROUP BY id""" % (id_meta, ",".join(["%s" % lvl for lvl in levels])))
        for id, iname, version in rows.fetchall():
            p_instances.append(PersistableInstance.load(env, id, version=version, ppool=self))
        return p_instances