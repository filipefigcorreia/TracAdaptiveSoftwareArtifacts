# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.resource import Resource
from trac.db import with_transaction
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
from AdaptiveArtifacts.model import Instance

class AdaptiveArtifact(object):
    """
    Wraps an instance of model.Instance (new or existing) and implements the Proxy pattern.
    It encapsulates Trac-specific concerns (like loading and saving instances from the
    database) and forwards to the instance all the calls that it doesn't know.
    """
    realm = 'asa'

    def __init__(self, env, id, version=None, db=None):
        self.env = env
        if isinstance(id, Resource): # when does this happen?
            self.resource = id
            id = self.resource.id
        else:
            if version:
                version = int(version) # must be a number or None
            self.resource = Resource('asa', id, version)
        self.id = id
        if id:
            self._fetch(id, version, db)
        else: # new instance?
            self.instance = Instance(id=id)
            self.version = 0
            self.comment = self.author = ''
            self.time = None
            self.readonly = 0

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def _fetch(self, id, version=None, db=None):
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        if version is not None:
            cursor.execute("SELECT version,time,author,comment,readonly "
                           "FROM ArtifactState "
                           "WHERE id=%s AND version=%s",
                           (id, int(version)))
        else:
            cursor.execute("SELECT version,time,author,comment,readonly "
                           "FROM ArtifactState "
                           "WHERE id=%s ORDER BY version DESC LIMIT 1",
                           (id,))
        row = cursor.fetchone()
        if row:
            version, time, author, comment, readonly = row
            self.version = int(version)
            self.author = author
            self.time = from_utimestamp(time)
            self.comment = comment
            self.readonly = readonly and int(readonly) or 0
        else:
            self.version = 0
            self.comment = self.author = ''
            self.time = None
            self.readonly = 0

        # reset attributes
        self.instance.attributes = {}
        self.instance.types = {}
        self.instance.multiplicities = {}

        # get attributes
        cursor.execute("SELECT attr_name, attr_value "
                       "FROM ArtifactValue v ON v.id=s.id AND v.version=s.version "
                       "WHERE id=%s AND version=%s",
                       (id, int(version)))
        for row in cursor.fetchall():
            attr_name, attr_value = row


    def delete(self, version=None, db=None):
        pass

    def save(self, author, comment, remote_addr, t=None, db=None):
        pass

    def get_history(self, db=None):
        pass

class AdaptiveArtifact(object):
    """
    Wrapper of an instance of AdaptiveArtifacts.model.Instance (new or existing).
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

        self.time = None
        self.comment = self.author = ''
        #self.readonly = 0

    @classmethod
    def load(cls, env, identifier=None, iname=None, version=None, ppool=None, load_dependent=True):
        """
        Loads an existing PersistableInstance from the database.
        load_dependent -- determines if owned properties and metas should also be loaded
        """
        if ppool is None:
            ppool = PersistablePool.load(env)

        if not identifier is None:
            instance = ppool.pool.get_instance(identifier)
        else:
            instance = ppool.pool.get_instance_by_iname(iname)

        pi = AdaptiveArtifact(env, identifier, version)
        if instance is None:
            identifier, iname, meta_level, version, time, author, comment, contents_dict, property_inames_dict = \
                pi._fetch_contents(ppool, identifier, iname, version)
            from AdaptiveArtifacts.model import Instance
            pi.instance = Instance.create_from_properties(ppool.pool, identifier, iname, meta_level, contents_dict, property_inames_dict, version, time, author, comment)
        else:
            #TODO: fix. something is deeply wrong here. version should not be kept by PIs
            pi.instance = instance
            #pi.version = int(version)
            #pi.time =
            #pi.author = author
            #pi.comment = comment

        if load_dependent:
            pi.load_properties(ppool)
            if pi.instance.get_meta() is None:
                AdaptiveArtifact.load(env, identifier=pi.instance.get_id_meta(), ppool=ppool)
        return pi

    def load_properties(self, ppool):
        query = """
            SELECT id, max(version) version
            FROM asa_instance i
                INNER JOIN asa_value v_idm ON v_idm.instance_id=i.id
            WHERE
                v_idm.property_instance_iname='__owner' AND v_idm.value='%s'
            GROUP BY id
            """ % (self.instance.get_identifier(),)

        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute(query)

        property_ids = None
        try:
            property_ids = dict(cursor.fetchall())
        except Exception, e:
            raise Exception("""Could not determine properties for instance.\n %s \n %s""" % (e.message, query))

        for id, version in property_ids.items():
            AdaptiveArtifact.load(self.env, identifier=id, version=version,ppool=ppool)

    @staticmethod
    def _aggregate_values(contents_list):
        contents_dict = dict()
        for id, value in contents_list:
            if not id in contents_dict:
                contents_dict[id] = value
            else:
                if isinstance(contents_dict[id], list):
                    contents_dict[id].append(value)
                else:
                    contents_dict[id] = [contents_dict[id], value]
        return contents_dict

    def _fetch_contents(self, ppool, identifier, iname, version=None):
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
        contents_list = cursor.fetchall()
        contents_dict = AdaptiveArtifact._aggregate_values(contents_list)

        query = """
                SELECT DISTINCT property_instance_id, property_instance_iname
                FROM asa_value
                WHERE instance_id='%s' AND instance_version='%s'
                """ % (identifier, version)

        cursor.execute(query)
        property_inames_dict = dict(cursor.fetchall())

        return identifier, iname, meta_level, int(version), from_utimestamp(time), author, comment, contents_dict, property_inames_dict

    exists = property(fget=lambda self: self.version > 0)

    def delete_instance(self, env, version=None):
        assert self.exists, 'Cannot delete non-existent asa_instance'

        @with_transaction(env)
        def do_delete(db):
            def do_delete_instance(cursor, instance_id):
                cursor.execute("DELETE FROM asa_instance WHERE id=%s", (instance_id,))
                cursor.execute("DELETE FROM asa_value WHERE instance_id=%s", (instance_id,))
                self.env.log.info("Deleted asa_instance '%s'" % instance_id)

            cursor = db.cursor()
            # get and delete all properties owned by this instance (or more precisely, "entity", if any properties are found)
            cursor.execute("SELECT instance_id FROM asa_value WHERE property_instance_iname='__owner' and value='%s'", (self.identifier,))
            for instance_id in cursor:
                do_delete_instance(cursor, instance_id)
            # delete the instance itself
            do_delete_instance(cursor, self.identifier)

    def save(self, env, author, comment, remote_addr, t=None):
        def insert_property_value(cursor, instance_id, instance_version, property_instance_id, property_instance_iname, value):
            cursor.execute("""
                INSERT INTO asa_value (instance_id, instance_version, property_instance_id, property_instance_iname, value)
                VALUES (%s,%s,%s,%s,%s)
                """, (instance_id, instance_version, property_instance_id, property_instance_iname, value))

        @with_transaction(env)
        def do_save(db):
            state = self.instance.get_state()
            if not state.version is None:
                raise ValueError("Instance is already saved.")

            new_version = self.instance.get_highest_version_number() + 1
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO asa_instance (id, iname, meta_level, version, time, author, ipnr, op_type, comment)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (self.instance.get_identifier(), self.instance.get_iname(), self.instance.get_meta_level(), new_version, to_utimestamp(t), author, remote_addr, 'C', comment))
            for property_ref in self.instance.get_state().slots: #TODO: state shouldn't be accessed directly
                value = self.instance.get_slot_value(property_ref)
                if not isinstance(value, list):
                    insert_property_value(cursor, self.instance.get_identifier(), new_version, property_ref, self.instance.get_property_iname(property_ref), value)
                else: # multiplicity > 1 for this property
                    for v in value:
                        insert_property_value(cursor, self.instance.get_identifier(), new_version, property_ref, self.instance.get_property_iname(property_ref), v)

            state.version = new_version
            del self.instance._Instance__states[None]
            self.instance._Instance__states[state.version] = state # ugly hack until proper refactoring

        self.author = author
        self.comment = comment
        self.time = t

    def get_history(self, env):
        db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT version,time,author,comment,ipnr FROM asa_instance "
                       "WHERE id=%s AND version<=%s "
                       "ORDER BY version DESC", (self.instance.get_identifier(), self.version))
        for version, ts, author, comment, ipnr in cursor:
            yield version, from_utimestamp(ts), author, comment, ipnr

class PersistablePool(object):
    def __init__(self, env, pool):
        self.env = env
        self.pool = pool

    #TODO: rethink. why is this a classmethod and not an extra parameter in the constructor instead
    @classmethod
    def load(cls, env):
        # Loads the entire M2 level from the database
        from model import InstancePool
        ppool = PersistablePool(env, InstancePool())
        ppool.get_metamodel_instances(env)
        return ppool

    #TODO: check if the env param is really needed. there's already an env in self
    def get_instance(self, env, identifier=None, iname=None, version=None):
        return AdaptiveArtifact.load(env, identifier=identifier, iname=iname, version=version, ppool=self)

    #TODO: check if the env param is really needed. there's already an env in self
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
        results = rows.fetchall()
        for id, version, dummy in results:
            p_instances.append(AdaptiveArtifact.load(env, id, version=version, ppool=self, load_dependent=False))
        return p_instances

    #TODO: check if the env param is really needed. there's already an env in self
    def get_instances_of(self, env, id_meta, meta_levels=None):
        if meta_levels is None:
            meta_levels = [0,1]
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
                GROUP BY id""" % (id_meta, ",".join(["%s" % lvl for lvl in meta_levels])))
        for id, version in rows.fetchall():
            p_instances.append(AdaptiveArtifact.load(env, id, version=version, ppool=self))
        return p_instances

    #TODO: check if the env param is really needed. there's already an env in self
    def save(self, env):
        @with_transaction(env)
        def do_save(db):
            for instance in self.pool.get_instances():
                if instance.get_state().is_uncommitted():
                    pi = AdaptiveArtifact(self.env, instance.get_identifier(), 0)
                    pi.instance = instance
                    pi.save(env, "system", "", "")
