all = ["copy", "delete", "lock", "mkcol", "move", "proppatch", "put"]

"""
Mixins for AngelFile behaviour. Each mixin implements one WebDAV method (PUT, LOCK, etc.).
I feel this is cleaner than wilfredo's bindmethods() - approach.
"""