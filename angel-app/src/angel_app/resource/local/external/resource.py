from angel_app.angelFile.basic import Basic
from angel_app.angelFile.dav.external.methods import proppatch, put

DEBUG = False

class External(proppatch.ProppatchMixin, put.PutMixin, Basic):
    """
    An AngelFile, as seen on the external (unsafe) network interface.
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        Basic.__init__(self, path, defaultType, indexNames)
