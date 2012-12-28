# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import sys
from datetime import datetime
from trac.db import with_transaction
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
from AdaptiveArtifacts.model.core import Instance, Entity, Attribute

class DBPool(object):
    def __init__(self, env, pool):
        self.env = env
        self.pool = pool
        self.version = None # default is latest version

    def load_item(self, id, db=None):
        is_spec = False
        try:
            long(id)
        except ValueError:
            is_spec = True

        if not is_spec:
            self.load_artifact(id, db)
        else:
            self.load_spec(id, db)

    def load_artifact(self, id, db=None):
        if not db:
            db = self.env.get_read_db()
        version = self._get_latest_artifact_version(id, db)
        if version is None:
            raise ValueError("No version found for artifact with id '%s'" % (id,))

        # get the spec (metaclass) and title
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT spec, title_expr
                FROM asa_artifact
                WHERE id='%s' AND version_id='%d'
                GROUP BY id""" % (id, version))
        row = rows.fetchone()
        if row is None or len(row) == 0:
            raise ValueError("No artifact found with id '%d'" % (id,))
        spec_name = row[0]
        title_expr = row[1]
        self.load_spec(spec_name, db)
        spec = self.pool.get_item(spec_name)

        # get the values
        values={}
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT attr_name, attr_value, uiorder
                FROM asa_artifact_value
                WHERE artifact_id='%s' AND version_id='%d'""" % (id, version))
        values = rows.fetchall()

        # create the artifact
        artifact = spec(id=id, version=version, str_attr=title_expr, persisted=True)
        artifact.add_values([(name, value) for name, value, order in sorted(values, key=lambda valtpl: valtpl[2])])

        self.pool.add(artifact)

    def load_spec(self, spec_name, db=None):

        # Ignore requests to load the top-most classes of the instantiation chain (Entity and Instance),
        # as these will not be persisted to the database and will be always available from the pool.
        if spec_name in (Entity.get_name(), Instance.get_name()):
            return

        if not db:
            db = self.env.get_read_db()
        version = self._get_latest_spec_version(spec_name, db)
        if version is None:
            raise ValueError("No version found for spec with name '%s'" % (spec_name,))

        # get the baseclass
        base_class = None
        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT base_class
                FROM asa_spec
                WHERE name='%s' AND version_id='%d'
                GROUP BY name""" % (spec_name, version))
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
                SELECT name, multplicity_low, multplicity_high, type, uiorder
                FROM asa_spec_attribute
                WHERE spec_name='%s' AND version_id='%d'""" % (spec_name, version))
        for row in rows.fetchall():
            attributes.append(Attribute(name=row[0], multiplicity=(row[1], row[2]), atype=row[3], order=row[4]))

        # create the entity
        spec = Entity(name=spec_name, bases=bases, version=version, persisted=True, attributes=attributes)

        if self.pool.get_item(spec.get_name()) is None:
            self.pool.add(spec)

    def get_latest_version_details(self, id_artifact, db=None):
        if not db:
            db = self.env.get_read_db()

        version = self._get_latest_artifact_version(id_artifact)
        if not version:
            return None, None, None, None, None, None

        cursor = db.cursor()
        rows = cursor.execute("""
                       SELECT id, time, author, ipnr, comment, readonly
                       FROM asa_version
                       WHERE id=%s
                       """ % (id_artifact,))
        row = rows.fetchone()
        return row[0], row[1], row[2], row[3], row[4], row[5],

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

    def _get_latest_spec_version(self, spec_name, db=None):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()
        query = """
                SELECT max(version_id) version_id
                FROM asa_spec
                WHERE name='%s' """  % (spec_name,)
        if not self.version is None:
            query += 'AND version_id <= %s '  % (self.version,)
        query += """GROUP BY name"""
        rows = cursor.execute(query)
        row = rows.fetchone()
        return row[0] if not row is None and len(row)>0 else None

    def _get_latest_wiki_page_version(self, pagename, db=None):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()
        query = """
                SELECT max(version) version
                FROM wiki
                WHERE name='%s' """  % (pagename,)
        query += """GROUP BY name"""
        rows = cursor.execute(query)
        row = rows.fetchone()
        return row[0] if not row is None and len(row)>0 else None

    def load_specs(self, db=None):
        if not db:
            db = self.env.get_read_db()

        cursor = db.cursor()
        rows = cursor.execute("""
                SELECT DISTINCT name
                FROM asa_spec;""")
        for row in rows.fetchall():
            self.load_spec(row[0])

    def _get_filter(self, items):
        filter = "("
        for item in items:
            if len(filter) > 1:
                filter += ","
            filter += "'%s'" % (item,)
        filter += ")"
        return filter

    def _load_spec_and_child_specs(self, spec_name, db=None):
        """
        Loads the specified spec and discovers and loads all the specs that inherit from it
        """
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()

        self.load_spec(spec_name, db)
        current_specs = [spec_name]
        while True:
            filter = self._get_filter(current_specs)
            query = """
                SELECT name, max(version_id) version
                FROM asa_spec
                WHERE base_class in %s
                """ % (filter,)
            if not self.version is None:
                query += 'AND version_id <= %s ' % (self.version,)
            query += """GROUP BY name"""
            rows = cursor.execute(query)
            current_specs = []
            result = rows.fetchall()
            if len(result) == 0:
                break
            for name, version in result:
                self.load_spec(name)
                current_specs.append(name)

    def load_artifacts_of(self, spec_name, db=None):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()

        self._load_spec_and_child_specs(spec_name, db)
        specs = self.pool.get_spec_and_child_specs(spec_name)
        filter = self._get_filter([spec.get_name() for spec in specs])

        # load artifacts of these specs
        query = """
                SELECT id, max(version_id) version
                FROM asa_artifact
                WHERE spec in %s
                """ % (filter,)
        if not self.version is None:
            query += 'AND version_id <= %s '  % (self.version,)
        query += """GROUP BY id"""
        rows = cursor.execute(query)
        for id, version in rows.fetchall():
            self.load_item(id)

    def save(self, author, comment, remote_addr, t=None):
        @with_transaction(self.env)
        def do_save(db):
            time = t if not t is None else datetime.now(utc)
            uncommitted_items = [i for i in self.pool.get_items() if i.is_uncommitted()]
            if len(uncommitted_items) > 0:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO asa_version (time, author, ipnr, comment, readonly)
                    VALUES (%s,%s,%s,%s,%s)
                    """, (to_utimestamp(time), author, remote_addr, comment, 0))
                version_id = db.get_last_id(cursor, 'asa_version')

                for item in uncommitted_items:
                    if isinstance(item, Entity): # it's a spec
                        if item._is_renamed:
                            cursor.execute("""
                                UPDATE asa_spec SET name=%s WHERE name=%s
                                """, (item.get_name(), item.original_name))
                        cursor.execute("""
                            INSERT INTO asa_spec (name, version_id, base_class)
                            VALUES (%s,%s,%s)
                            """, (item.get_name(), version_id, item.__bases__[0].get_name()))

                        for attribute in item.attributes:
                            cursor.execute("""
                                INSERT INTO asa_spec_attribute (spec_name, version_id, name, multplicity_low, multplicity_high, type, uiorder)
                                VALUES (%s,%s,%s,%s,%s,%s,%s)
                                """, (item.get_name(), version_id, attribute.name, attribute.multiplicity[0], attribute.multiplicity[1], attribute.get_type_readable(), attribute.order))
                    else: # it's an artifact
                        if item.is_new():
                            cursor.execute("""
                                INSERT INTO asa_artifact_id VALUES (NULL)
                                """)
                            art_id = cursor.lastrowid
                        else:
                            art_id = item.get_id()
                        cursor.execute("""
                            INSERT INTO asa_artifact (id, version_id, spec, title_expr)
                            VALUES (%s,%s,%s,%s)
                            """, (art_id, version_id, item.__class__.name, item.str_attr))

                        for attr_name in item.attr_identifiers.keys():
                            order = item.get_order(attr_name)
                            values = item.get_value(attr_name)
                            if not isinstance(values, list):
                                values = [values]
                            for value in values:
                                cursor.execute("""
                                    INSERT INTO asa_artifact_value (artifact_id, version_id, attr_name, attr_value, uiorder)
                                    VALUES (%s,%s,%s,%s,%s)
                                    """, (art_id, version_id, attr_name, value, order))
                        item.id=art_id

                        self.update_artifact_ref_count(item, db)

    def delete(self, item, author, comment, remote_addr, t=None):
        if not item in self.pool.get_items():
            raise Exception("Item not in pool")

        if item.is_uncommitted():
            self.pool.remove(item)
            self.env.log.info("Deleted item '%s' (uncommitted item)" % item.get_id())
            return

        @with_transaction(self.env)
        def do_delete(db):
            cursor = db.cursor()
            if isinstance(item, Entity): # it's a spec

                # get a new version number for all changes we may need to make
                time = t if not t is None else datetime.now(utc)
                cursor.execute("""
                    INSERT INTO asa_version (time, author, ipnr, comment, readonly)
                    VALUES (%s,%s,%s,%s,%s)
                    """, (to_utimestamp(time), author, remote_addr, comment, 0))
                version_id = db.get_last_id(cursor, 'asa_version')

                # change artifacts of the deleted spec to point to the "Instance" spec
                cursor.execute("""
                    INSERT INTO asa_artifact (id, version_id, spec, title_expr)
                    SELECT id, %s, %s, title_expr
                    FROM (
                        SELECT id, max(version_id), title_expr
                        FROM asa_artifact
                        WHERE spec=%s
                        GROUP BY id
                    )""", (version_id, Instance.get_name(), item.get_name()))

                # change specs inheriting from the deleted spec to inherit from "Instance" instead
                cursor.execute("""
                    INSERT INTO asa_spec (name, version_id, base_class)
                    SELECT name, %s, %s
                    FROM (
                        SELECT name, max(version_id)
                        FROM asa_spec
                        WHERE base_class=%s
                        GROUP BY name
                    )""", (version_id, Instance.get_name(), item.get_name()))

                # change attributes that had the deleted spec as type
                cursor.execute("""
                    INSERT INTO asa_spec_attribute (spec_name, version_id, name, multplicity_low, multplicity_high, type, uiorder)
                    SELECT spec_name, %s, name, multplicity_low, multplicity_high, %s, uiorder
                    FROM (
                        SELECT spec_name, max(version_id), name, multplicity_low, multplicity_high, uiorder
                        FROM asa_spec_attribute
                        WHERE type=%s
                        GROUP BY spec_name, name
                    )""", (version_id, Instance.get_name(), item.get_name()))

                # finally, delete the spec
                cursor.execute("DELETE FROM asa_spec_attribute WHERE spec_name=%s", (item.get_name(),))
                cursor.execute("DELETE FROM asa_spec WHERE name=%s", (item.get_name(),))
            else: # it's an artifact
                cursor.execute("DELETE FROM asa_artifact_value WHERE artifact_id=%s", (item.get_id(),))
                cursor.execute("DELETE FROM asa_artifact_id WHERE id=%s", (item.get_id(),))
                cursor.execute("DELETE FROM asa_artifact WHERE id=%s", (item.get_id(),))
            self.pool.remove(item)
            self.env.log.info("Deleted item '%s'" % item.get_id())

    def get_history(self, item, db=None):
        if not item in self.pool.get_items():
            raise Exception("Item not in pool")

        if item.is_new():
            return

        if db is None:
            db = self.env.get_db_cnx()

        cursor = db.cursor()
        query = """
                SELECT v.id, v.time, v.author, v.ipnr, v.comment
                FROM asa_version v"""
        if isinstance(item, Entity): # it's a spec
            query += """
                    INNER JOIN asa_spec s ON s.version_id=v.id
                    WHERE s.name='%s'
                    """ % (item.get_name())
        else: # it's an artifact
            query += """
                    INNER JOIN asa_artifact a ON a.version_id=v.id
                    WHERE a.id=%d""" % (item.get_id())

        if not self.version is None:
            query += ' AND v.id <= %s' % (self.version,)
        query += ' ORDER BY v.id DESC'
        cursor.execute(query)
        for version, ts, author, ipnr, comment in cursor:
            yield version, from_utimestamp(ts), author, ipnr, comment

    def _get_aggregated_counts(self, artifacts_ids):
        artifacts_ids_count = set([(aid,artifacts_ids.count(aid)) for aid in artifacts_ids])
        artifacts_ids_versions = [(aid,vid,ref_count)
                                  for aid,vid,ref_count in ((aid, self._get_latest_artifact_version(aid), ref_count)
                                      for aid,ref_count in artifacts_ids_count)
                                          if not vid is None]
        return artifacts_ids_versions

    def update_wiki_page_references(self, page, artifacts_ids, db=None):
        if db is None:
            db = self.env.get_db_cnx()

        artifacts_ids_versions = self._get_aggregated_counts(artifacts_ids)

        cursor = db.cursor()
        query = """
                DELETE FROM asa_artifact_wiki_references
                WHERE page_name=%s AND page_version_id=%s;"""
        cursor.execute(query, (page.name, page.version))

        for aid,vid,ref_count in artifacts_ids_versions:
            query = """
                    INSERT INTO asa_artifact_wiki_references(artifact_id, artifact_version_id, page_name, page_version_id, ref_count)
                    VALUES (%s,%s,%s,%s,%s);"""
            cursor.execute(query, (int(aid), vid, page.name, page.version, ref_count))

        db.commit()

    # Returns list of wiki page names that reference the specified artifact and the number of times that it references it.
    def get_wiki_page_ref_counts(self, artifact, db=None):
        if not artifact in self.pool.get_items():
            raise Exception("Item not in pool")

        assert not isinstance(artifact, Entity)

        if artifact.is_new():
            return

        if db is None:
            db = self.env.get_db_cnx()

        version = self._get_latest_artifact_version(artifact.get_id(), db)
        if version is None:
            raise ValueError("No version found for artifact with id '%s'" % (artifact.get_id(),))

        cursor = db.cursor()
        query = """
                SELECT page_name, page_version_id AS page_version, ref_count
                FROM asa_artifact_wiki_references aw
                INNER JOIN (
                    SELECT name, max(version) AS version
                    FROM wiki
                    GROUP BY name
                ) pages ON pages.name=aw.page_name AND pages.version=aw.page_version_id
                WHERE aw.artifact_id=%d
                GROUP BY page_name""" % (int(artifact.get_id()))

        cursor.execute(query)
        for pagename, page_version_id, ref_count in cursor:
            yield pagename, page_version_id, ref_count


    def update_artifact_ref_count(self, artifact, db=None):
        text = u""
        for attr_name, value in artifact.get_values():
            text += " " + (" ".join(value) if type(value) is list else value)
        from AdaptiveArtifacts import get_artifact_ids_from_text
        related_artifacts_ids = get_artifact_ids_from_text(text)
        self.update_related_artifact_references(artifact, related_artifacts_ids, db)

    def update_related_artifact_references(self, artifact, related_artifacts_ids, db):
        artifact_version_id = self._get_latest_artifact_version(artifact.get_id())
        artifacts_ids_versions = self._get_aggregated_counts(related_artifacts_ids)

        cursor = db.cursor()
        query = """
                DELETE FROM asa_artifact_artifact_references
                WHERE artifact_id=%s AND artifact_version_id=%s;"""
        cursor.execute(query, (artifact.get_id(), artifact_version_id))

        for aid,vid,ref_count in artifacts_ids_versions:
            query = """
                    INSERT INTO asa_artifact_artifact_references(artifact_id, artifact_version_id, related_artifact_id, related_artifact_version_id, ref_count)
                    VALUES (%s,%s,%s,%s,%s);"""
            cursor.execute(query, (artifact.get_id(), artifact_version_id, int(aid), vid, ref_count))


    def get_related_artifact_ref_counts(self, artifact, db=None):
        if not artifact in self.pool.get_items():
            raise Exception("Item not in pool")

        assert not isinstance(artifact, Entity)

        if artifact.is_new():
            return

        if db is None:
            db = self.env.get_db_cnx()

        version = self._get_latest_artifact_version(artifact.get_id(), db)
        if version is None:
            raise ValueError("No version found for artifact with id '%s'" % (artifact.get_id(),))

        cursor = db.cursor()
        query = """
                SELECT artifact_id, aa.artifact_version_id, ref_count
                FROM asa_artifact_artifact_references aa
                INNER JOIN (
                    SELECT id, max(version_id) AS version
                    FROM asa_artifact
                    GROUP BY id
                ) maxv ON maxv.id=aa.artifact_id AND maxv.version=aa.artifact_version_id
                WHERE aa.related_artifact_id=%d
                GROUP BY artifact_id""" % (int(artifact.get_id()))

        cursor.execute(query)
        for pagename, related_artifact_version_id, ref_count in cursor:
            yield pagename, related_artifact_version_id, ref_count
