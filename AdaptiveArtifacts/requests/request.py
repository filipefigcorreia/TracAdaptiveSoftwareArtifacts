from trac.resource import ResourceNotFound
from AdaptiveArtifacts.model.pool import Entity, Instance

class Request(object):
    def __init__(self, dbp, req):
        self.req = req

        self.resource_type = req.args.get('asa_resource_type', None)
        if not self.resource_type in ['spec', 'artifact', 'search', None]:
            raise ValueError("Unknown type of resource '%s'" % (self.resource_type,))

        self.resource_id = req.args.get('asa_resource', None)
        self.version = req.args.get('version')
        #old_version = req.args.get('old_version')

        self.res_format = req.args.get('format', None)
        if not self.res_format in ['page', 'dialog', 'json', None]:
            raise ValueError("Unknown format '%s'" % (self.res_format,))

        self._resolve_object_and_action(dbp)
        self._resolve_view(self.resource_type, self.action, self.req.method)


    def _resolve_object_and_action(self, dbp):
        self.action = self.req.args.get('action', None)
        if not self.action in ['view', 'edit', 'list', 'index', 'new', None]:
            raise ValueError("Unknown action '%s'" % (self.action,))

        if self.resource_type is None:
            self.obj = None
            self.action = 'index'
        elif self.resource_type == 'search':
            if not self.resource_id in ['no_spec', 'artifact', 'spec']:
                raise Exception("Unknown search '%s'" % (self.resource_id,))
            self.obj = self.resource_id
            self.action = 'list'
        elif self.resource_type in ['spec', 'artifact']:
            if self.resource_id is None:
                if self.resource_type == 'spec':
                    self.obj = Entity
                elif self.resource_type == 'artifact':
                    self.obj = Instance
            else:
                if not dbp:
                    raise ValueError("Cannot load the resource. No database pool provided.")
                dbp.load_item(self.resource_id)
                self.obj = dbp.pool.get_item(self.resource_id)
                if self.obj is None:
                    raise ResourceNotFound("No resource found with identifier '%s'" % (self.resource_id,))

        if self.action is None: # default action depends on the instance's meta-level
            if self.obj is Entity:
                self.action = 'index'
            elif isinstance(self.obj, type):
                self.action = 'list'
            else:
                self.action = 'view'


    def _resolve_view(self, res_type, action, method):
        from AdaptiveArtifacts import views
        mlist = [method_name for method_name in dir(views) if callable(getattr(views, method_name)) and method_name.startswith(('get_', 'post_'))]
        if res_type is None:
            mname = '%s_%s' % (method.lower(), action.lower())
        else:
            mname = '%s_%s_%s' % (method.lower(), action.lower(), res_type.lower())
        if mname in mlist:
            self.view = getattr(views, mname)
        else:
            raise Exception("Unable to find a view for %s, %s, %s" % (res_type, action, method))

    def get_format(self):
        return self.res_format.lower() if self.res_format else 'page'