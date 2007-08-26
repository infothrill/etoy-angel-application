all = ["copy", "delete", "lock", "mkcol", "move", "put"]

"""
Mixins for AngelFile-specific (i.e. extending standard twisted.dav) behaviour, where required. 
Each mixin implements one WebDAV method (PUT, LOCK, etc.).
"""