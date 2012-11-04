# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

from trac.search import search_to_sql

class Searcher(object):
    stopwords_en = set([u"a", u"about", u"above", u"after", u"again", u"against", u"all", u"am", u"an", u"and", u"any", u"are", u"aren't", u"as", u"at", u"be", u"because", u"been", u"before", u"being", u"below", u"between", u"both", u"but", u"by", u"can't", u"cannot", u"could", u"couldn't", u"did", u"didn't", u"do", u"does", u"doesn't", u"doing", u"don't", u"down", u"during", u"each", u"few", u"for", u"from", u"further", u"had", u"hadn't", u"has", u"hasn't", u"have", u"haven't", u"having", u"he", u"he'd", u"he'll", u"he's", u"her", u"here", u"here's", u"hers", u"herself", u"him", u"himself", u"his", u"how", u"how's", u"i", u"i'd", u"i'll", u"i'm", u"i've", u"if", u"in", u"into", u"is", u"isn't", u"it", u"it's", u"its", u"itself", u"let's", u"me", u"more", u"most", u"mustn't", u"my", u"myself", u"no", u"nor", u"not", u"of", u"off", u"on", u"once", u"only", u"or", u"other", u"ought", u"our", u"ours", u"ourselves", u"out", u"over", u"own", u"same", u"shan't", u"she", u"she'd", u"she'll", u"she's", u"should", u"shouldn't", u"so", u"some", u"such", u"than", u"that", u"that's", u"the", u"their", u"theirs", u"them", u"themselves", u"then", u"there", u"there's", u"these", u"they", u"they'd", u"they'll", u"they're", u"they've", u"this", u"those", u"through", u"to", u"too", u"under", u"until", u"up", u"very", u"was", u"wasn't", u"we", u"we'd", u"we'll", u"we're", u"we've", u"were", u"weren't", u"what", u"what's", u"when", u"when's", u"where", u"where's", u"which", u"while", u"who", u"who's", u"whom", u"why", u"why's", u"with", u"won't", u"would", u"wouldn't", u"you", u"you'd", u"you'll", u"you're", u"you've", u"your", u"yours", u"yourself", u"yourselves"])
    stopwords_pt = set([u"a", u"à", u"ao", u"aos", u"aquela", u"aquelas", u"aquele", u"aqueles", u"aquilo", u"as", u"às", u"até", u"com", u"como", u"da", u"das", u"de", u"dela", u"delas", u"dele", u"deles", u"depois", u"do", u"dos", u"e", u"ela", u"elas", u"ele", u"eles", u"em", u"entre", u"era", u"eram", u"éramos", u"essa", u"essas", u"esse", u"esses", u"está", u"esta", u"estamos", u"estão", u"estas", u"estava", u"estavam", u"estávamos", u"este", u"esteja", u"estejam", u"estejamos", u"estes", u"esteve", u"estive", u"estivemos", u"estiver", u"estivera", u"estiveram", u"estivéramos", u"estiverem", u"estivermos", u"estivesse", u"estivessem", u"estivéssemos", u"estou", u"eu", u"foi", u"fomos", u"for", u"fora", u"foram", u"fôramos", u"forem", u"formos", u"fosse", u"fossem", u"fôssemos", u"fui", u"há", u"haja", u"hajam", u"hajamos", u"hão", u"havemos", u"hei", u"houve", u"houvemos", u"houver", u"houvera", u"houverá", u"houveram", u"houvéramos", u"houverão", u"houverei", u"houverem", u"houveremos", u"houveria", u"houveriam", u"houveríamos", u"houvermos", u"houvesse", u"houvessem", u"houvéssemos", u"isso", u"isto", u"já", u"lhe", u"lhes", u"mais", u"mas", u"me", u"mesmo", u"meu", u"meus", u"minha", u"minhas", u"muito", u"na", u"não", u"nas", u"nem", u"no", u"nos", u"nós", u"nossa", u"nossas", u"nosso", u"nossos", u"num", u"numa", u"o", u"os", u"ou", u"para", u"pela", u"pelas", u"pelo", u"pelos", u"por", u"qual", u"quando", u"que", u"quem", u"são", u"se", u"seja", u"sejam", u"sejamos", u"sem", u"será", u"serão", u"serei", u"seremos", u"seria", u"seriam", u"seríamos", u"seu", u"seus", u"só", u"somos", u"sou", u"sua", u"suas", u"também", u"te", u"tem", u"tém", u"temos", u"tenha", u"tenham", u"tenhamos", u"tenho", u"terá", u"terão", u"terei", u"teremos", u"teria", u"teriam", u"teríamos", u"teu", u"teus", u"teve", u"tinha", u"tinham", u"tínhamos", u"tive", u"tivemos", u"tiver", u"tivera", u"tiveram", u"tivéramos", u"tiverem", u"tivermos", u"tivesse", u"tivessem", u"tivéssemos", u"tu", u"tua", u"tuas", u"um", u"uma", u"você", u"vocês", u"vos"])

    @classmethod
    def _filter_stopwords(cls, terms):
        return [t for t in terms if not t in cls.stopwords_en and not t in cls.stopwords_pt]

    @classmethod
    def search(cls, env, terms):
        terms = cls._filter_stopwords(terms)

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
        terms = cls._filter_stopwords([terms])
        if not terms:
            return []

        with dbp.env.db_query as db:
            sql_query, args = search_to_sql(db, ['val.attr_value'], terms)

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