from config.common import rootDir

from os import sep

# TODO: could probably do this better
if rootDir[-1] != sep:
    raise "the last character of the root dir path must be a '/'"

def relativePath(absolutePath = sep):
    """
    Given the absolute path of a resource (e.g. an AngelFile),
    return the relative path of that resource with respect to the root
    directory.
    """
    if absolutePath.find(rootDir) != 0:
        raise "the absolute path supplied must lie below the root directory."
    
    return absolutePath.replace(rootDir, sep)