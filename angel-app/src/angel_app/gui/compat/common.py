import os

def getResourcePath():
    """
    Returns the path containing the resources (images, icons, platform scripts)
    """
    if os.path.exists('../../distrib/'): # sort of a hack when running from the command line (bin/)
        return '../../distrib/'
    else:
        # with py2app, the cwd is Contents/Resources/ of the app-bundle
        return os.getcwd()
