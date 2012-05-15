# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.db import with_transaction
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
from AdaptiveArtifacts.model.core import Instance

class DBPool(object):
    def __init__(self, env, pool):
        self.env = env
        self.pool = pool

    def cenas(self):
        db = self.env.get_read_db()
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT *
                FROM asa_artifact
                """)
        for r in rows.fetchall():
            print r

    def load_one(self, id, db=None):
        if not db:
            db = self.env.get_read_db()
        version = self._get_latest_version(id, db)

        # get the metaclass
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT meta_class
                FROM asa_artifact a
                WHERE
                    a.id='%s' AND version_id='%s'
                GROUP BY id""" % (id, version))
        meta_class = rows.fetchone()

        # get the values
        values = {}

        artifact = None
        if meta_class is None:
            artifact = Instance(**values)
        else:
            # load metaclass and its base class (recursively until Instance is reached)

            artifact = metaclass(**values)

        self.pool.add(artifact)

    def _get_latest_version(self, id, db=None):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT max(version_id) version_id
                FROM asa_artifact a
                WHERE
                    a.id='%s' AND version_id <= '%s'
                GROUP BY id""" % (id, self.pool.version))
        (version) = rows.fetchone()
        return version


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
                GROUP BY id""" % (id_meta, self.pool.version))
        for id, version in rows.fetchall():
            self.pool.add(self.load_one(id))

    def save(self, author, comment, remote_addr, t=None):
        @with_transaction(self.env)
        def do_save(db):
            uncommitted_instances = [i for i in self.pool.get_instances() if i.is_uncommitted()]
            if len(uncommitted_instances) > 0:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO asa_version (time, author, ipnr, comment, readonly)
                    VALUES (%s,%s,%s,%s,%s)
                    """, (to_utimestamp(t), author, remote_addr, comment, 0))
                version_id = db.get_last_id(cursor, 'asa_version')

                for instance in uncommitted_instances:
                    cursor.execute("""
                        INSERT INTO asa_artifact (id, version_id, meta_class)
                        VALUES (%s,%s,%s)
                        """, (instance.get_id(), version_id, instance.__class__.name))
                    for attr_name in instance.attr_identifiers.keys():
                        cursor.execute("""
                            INSERT INTO asa_artifact_value (artifact_id, version_id, attr_name, attr_value)
                            VALUES (%s,%s,%s,%s)
                            """, (instance.get_id(), version_id, attr_name, attr_name, getattr(instance, instance.attr_identifiers[attr_name])))

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


