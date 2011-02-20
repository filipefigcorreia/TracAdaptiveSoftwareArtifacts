# AdaptiveArtifacts plugin

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider #, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, datefmt
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager
from AdaptiveArtifacts import schema

class ASAPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'adaptiveartifacts'

    def get_navigation_items(self, req):
        yield 'mainnav', 'adaptiveartifacts', Markup('<a href="%s">Adaptive Artifacts</a>' % (
                self.env.href.adaptiveartifacts() ) )

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/adaptiveartifacts'

    def process_request(self, req):
        #add_stylesheet(req, 'adaptiveartifacts/css/style.css')
        return "adaptive_artifacts.cs", "text/html"
        """response_str = 'Hello world!'
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Last-Modified', datefmt.http_date(time())) 
        req.send_header('Content-Length', len(response_str)) 
        req.end_headers()
        req.write(response_str)"""

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('adaptiveartifacts', resource_filename(__name__, 'htdocs'))]


class ASAEnvironmentSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        from distutils import version
        self.db_key = 'asa_plugin_version'
        self.schema_version = version.StrictVersion(get_system_value(self, self.db_key) or '0')
        self.running_version = version.StrictVersion('0.1')

    # IEnvironmentSetupParticipant
    def environment_created(self):
        self.log.debug("Creating environment for ASA plugin.")

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO system (name, value) VALUES ('%s', '%s')", \
                       (self.db_key, str(self.running_version)))
        for table in schema.schema:
            connector, _ = DatabaseManager(self.env, db, table)._get_connector()
            for stmt in connector.to_sql(table):
                self.env.log.debug("Running query: \n %s" % stmt)
                cursor.execute(stmt)
        db.commit()

        self.schema_version = self.running_version

    def environment_needs_upgrade(self, db):
        if self.schema_version == self.running_version:
            return False
        self.log.debug("The existing environment requires an upgrade for ASA plugin.")
        return True

    def upgrade_environment(self, db):
        self.log.debug("Upgrading existing environment for ASA plugin.")

        if self.schema_version == '0':
           self.environment_created()
#        elif self.schema_version == 'XXXX':
#            cursor = db.cursor()
#            cursor.execute("UPDATE various stuff ...")
#            cursor.execute("UPDATE system SET value=%s WHERE name='%s'" % (self.db_key, self.running_version))
#            self.log.info('Upgraded ASA tables from version %s to %s' % (self.db_key, self.running_version))

# additional methods
def get_system_value(env, key):
    return get_scalar_value(env, "SELECT value FROM system WHERE name=%s", 0, key)

def get_scalar_value(env, query, col=0, *params):
    data = get_first_row(env, query, *params)
    if data:
        return data[col]
    else:
        return None

def get_first_row(env, query, *params):
    cursor = env.get_read_db().cursor()
    data = None
    try:
        cursor.execute(query, params)
        data = cursor.fetchone()
    except Exception, e:
        env.log.exception( \
            'There was a problem executing sql: %s \n \
            with parameters: %s\n \
            Exception: %s' % (query, params, e))
        cursor.connection.rollback()
    return data