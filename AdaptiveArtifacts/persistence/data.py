# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import sys
from trac.db import with_transaction
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
from AdaptiveArtifacts.model.core import Instance, Entity, Attribute

class DBPool(object):
    def __init__(self, env, pool):
        self.env = env
        self.pool = pool
        self.version = None # default is latest version

    def load_artifact(self, id, db=None):
        if not db:
            db = self.env.get_read_db()
        version = self._get_latest_artifact_version(id, db)
        if version is None:
            raise ValueError("No version found for artifact with id '%d'" % (id,))

        # get the metaclass
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT meta_class
                FROM asa_artifact
                WHERE id='%d' AND version_id='%d'
                GROUP BY id""" % (id, version))
        meta_class_name = rows.fetchone()
        if meta_class_name is None or len(meta_class_name) == 0:
            raise ValueError("No artifact found with id '%d'" % (id,))
        meta_class_name = meta_class_name[0]
        self.load_spec(meta_class_name, db)
        meta_class = self.pool.get_item(meta_class_name)

        # get the values
        values={}
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT attr_name, attr_value
                FROM asa_artifact_value
                WHERE artifact_id='%d' AND version_id='%d'""" % (id, version))
        values = rows.fetchall()

        # create the instance
        artifact = meta_class(id=id, version=version, persisted=True)
        artifact.add_values(values)

        self.pool.add(artifact)

    def load_spec(self, name, db=None):
        if not db:
            db = self.env.get_read_db()
        version = self._get_latest_spec_version(name, db)
        if version is None:
            raise ValueError("No version found for spec with name '%s'" % (name,))

        # get the baseclass
        base_class = None
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT base_class
                FROM asa_spec
                WHERE name='%s' AND version_id='%d'
                GROUP BY name""" % (name, version))
        base_class_name = rows.fetchone()
        if not base_class_name is None and len(base_class_name) > 0:
            base_class_name = base_class_name[0]
            # load base classes (recursively until the root is reached)
            if base_class_name == Instance.get_name():
                base_class = Instance
            else:
                self.load_spec(base_class_name, db)
                base_class = self.pool.get_item(base_class_name)
        bases = (base_class,) if not base_class is None else tuple()

        # get the attributes
        attributes = []
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT name, multplicity_low, multplicity_high, type
                FROM asa_spec_attribute
                WHERE spec_name='%s' AND version_id='%d'""" % (name, version))
        for row in rows.fetchall():
            try:
                type = getattr(sys.modules['__builtin__'], str(row[3]))
            except ValueError:
                type = row[3]
            attributes.append(Attribute(name=row[0], multiplicity=(row[1], row[2]), type=type))

        # create the entity
        spec = Entity(name=name, bases=bases, version=version, persisted=True, attributes=attributes)

        self.pool.add(spec)

    def _get_latest_artifact_version(self, id, db=None):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()
        query = """
                SELECT max(version_id) version_id
                FROM asa_artifact
                WHERE id='%s' """  % (id,)
        if not self.version is None:
            query += 'AND version_id <= %s '  % (self.version,)
        query += """GROUP BY id"""
        rows = cursor.execute(query)
        row = rows.fetchone()
        return row[0] if not row is None and len(row)>0 else None

    def _get_latest_spec_version(self, name, db=None):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()
        query = """
                SELECT max(version_id) version_id
                FROM asa_spec
                WHERE name='%s' """  % (name,)
        if not self.version is None:
            query += 'AND version_id <= %s '  % (self.version,)
        query += """GROUP BY name"""
        rows = cursor.execute(query)
        row = rows.fetchone()
        return row[0] if not row is None and len(row)>0 else None

    def load_instances_of(self, id_meta, db=None):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT id, max(version) version
                FROM asa_instance i
                    INNER JOIN asa_value v_idm ON v_idm.instance_id=i.id
                WHERE
                    v_idm.property_instance_iname='__meta' AND v_idm.value='%s'
                GROUP BY id""" % (id_meta, self.version))
        for id, version in rows.fetchall():
            self.pool.add(self.load_artifact(id))

    def save(self, author, comment, remote_addr, t=None):
        @with_transaction(self.env)
        def do_save(db):
            uncommitted_items = [i for i in self.pool.get_items() if i.is_uncommitted()]
            if len(uncommitted_items) > 0:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO asa_version (time, author, ipnr, comment, readonly)
                    VALUES (%s,%s,%s,%s,%s)
                    """, (to_utimestamp(t), author, remote_addr, comment, 0))
                version_id = db.get_last_id(cursor, 'asa_version')

                for item in uncommitted_items:
                    if isinstance(item, Entity): # it's a spec
                        cursor.execute("""
                            INSERT INTO asa_spec (name, version_id, base_class)
                            VALUES (%s,%s, %s)
                            """, (item.get_name(), version_id, item.__bases__[0].get_name()))
                        for attribute in item.attributes:
                            cursor.execute("""
                                INSERT INTO asa_spec_attribute (spec_name, version_id, name, multplicity_low, multplicity_high, type)
                                VALUES (%s,%s,%s,%s,%s,%s)
                                """, (item.get_name(), version_id, attribute.name, attribute.multiplicity[0], attribute.multiplicity[1], attribute.type if not type(attribute.type)==type else attribute.type.__name__))
                    else: # it's an artifact
                        cursor.execute("""
                            INSERT INTO asa_artifact (version_id, meta_class)
                            VALUES (%s,%s)
                            """, (version_id, item.__class__.name))
                        art_id = cursor.lastrowid
                        for attr_name in item.attr_identifiers.keys():
                            values = item.get_value(attr_name)
                            if not isinstance(values, list):
                                values = [values]
                            for value in values:
                                cursor.execute("""
                                    INSERT INTO asa_artifact_value (artifact_id, version_id, attr_name, attr_value)
                                    VALUES (%s,%s,%s,%s)
                                    """, (art_id, version_id, attr_name, value))
                        item.id=art_id

    def delete(self, object, db=None):
        if not db:
            db = self.env.get_db_cnx()
        # ...  remove from pool and delete from DB
        return ()

    def get_history(cls, object, db=None):
        if not db:
            db = self.env.get_db_cnx()
        # ... returns list of versions for the specified object
        return ()


