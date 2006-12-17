from angel_app.resource.local.basic import Basic
from angel_app.resource.local.external.methods import delete, mkcol, proppatch, put

DEBUG = False

class External(proppatch.ProppatchMixin, put.PutMixin,  mkcol.MkcolMixin, delete.DeleteMixin, Basic):
    """
    An AngelFile, as seen on the external (unsafe) network interface.
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        Basic.__init__(self, path, defaultType, indexNames)
