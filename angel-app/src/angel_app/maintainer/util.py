from twisted.python.filepath import FilePath
from twisted.python import log

from config.common import rootDir

from os import sep

def relativePath(absolutePath = sep):
    """
    Given the absolute path of a resource (e.g. an AngelFile),
    return the relative path of that resource with respect to the root
    directory.
    """
    if absolutePath.find(rootDir) != 0:
        raise "the absolute path supplied must lie below the root directory."
    if rootDir[-1] != sep:
        return absolutePath.replace(rootDir, sep)
    else:
        return absolutePath.replace(rootDir, "")



def treeMap(function, filePath = FilePath(rootDir)):
    """
    apply a function to each node in a file tree rooted at
    filePath.
    """
    for resource in filePath.walk(): yield function(resource)
    
    
def inspectResource(resource = FilePath(rootDir)):
    log.err("inspecting resource: " + resource.path)