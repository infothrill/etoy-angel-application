import os

def getResourcePath():
    """
    Returns the path containing the resources (images, icons, platform scripts)
    """
    if 'RESOURCEPATH' in os.environ:
        return os.environ['RESOURCEPATH'] # on mac os x, this is set for executables in an app bundle
    if os.path.exists('../../distrib/'): # sort of a hack when running from the command line (bin/)
        return '../../distrib/'
    else:
        return os.getcwd() # fallback with at least an existing path. it's a wild guess though.
