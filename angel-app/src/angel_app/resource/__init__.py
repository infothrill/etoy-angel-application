"""
The angel-app defines three types of "views" on resources.

-- remote resources are resources that are physically stored on a remote file 
   system (and accessible via HTTP only).
-- local resources are resources that are physically stored on a local file system.
   they may be accessed via
   * a "public" webdav interface, facing the internet (see local.external)
   * a "secret" webdav interface, accessible only from the local host (see local.internal)
   obviously, the security settings on the internal interface are considerably more
   liberal than on the external one.

"""
all = [
        "abstractContentManager",
        "basic", 
        "IReadOnlyContentManager", 
        "IReadOnlyPropertyManager", 
        "IResource", 
        "local", 
        "remote", 
        "util"
       ]