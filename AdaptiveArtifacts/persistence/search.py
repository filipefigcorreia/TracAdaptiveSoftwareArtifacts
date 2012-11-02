from trac.search import search_to_sql

class Searcher(object):
    @classmethod
    def search(cls, env, terms):
        with env.db_query as db:
            sql_query, args = search_to_sql(db, ['val.attr_value'], terms)

            for id, attr_name, attr_value, vid, time, author in db("""
                    SELECT a.id, val.attr_name, val.attr_value, max(v.id), v.time, v.author
                    FROM asa_artifact_value val
                        INNER JOIN asa_version v ON v.id=val.version_id
                        INNER JOIN asa_artifact a ON a.id=val.artifact_id
                    WHERE """ + sql_query +
                    """ GROUP BY a.id""", args):
                yield (id, attr_name, attr_value, vid, time, author)

    @classmethod
    def search_artifacts(cls, dbp, terms):
        with dbp.env.db_query as db:
            sql_query, args = search_to_sql(db, ['val.attr_value'], [terms])

            results = []
            for id, vid, term in db("""
                    SELECT a.id, max(v.id), val.attr_value
                    FROM asa_artifact_value val
                        INNER JOIN asa_version v ON v.id=val.version_id
                        INNER JOIN asa_artifact a ON a.id=val.artifact_id
                    WHERE """ + sql_query +
                    """ GROUP BY a.id""", args):
                if dbp.pool.get_item(id) is None:
                    dbp.load_artifact(id, db)
                results.append((dbp.pool.get_item(id), term))

        return results

    @classmethod
    def search_spec_names(cls, dbp, term):
        with dbp.env.db_query as db:

            results = []
            for name, vid in db("""
                  SELECT s.name, max(v.id)
                  FROM asa_spec s
                      INNER JOIN asa_version v ON v.id=s.version_id
                  WHERE s.name """ + db.like() +
                  """ GROUP BY v.id""", ("%" + db.like_escape(term) + "%",)):
              results.append(name)
        return results