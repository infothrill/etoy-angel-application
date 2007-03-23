import os

def getResourcePath():
    """
    Returns the path containing the resources (images, icons, platform scripts)
    """
    based = os.path.split(os.path.dirname(os.getcwd()))[0]
    for subdir in ["distrib", "Resources"]: # hm, this is sort of hacky
        p = os.path.join(based, "distrib")
        if os.path.exists(p):
            return p
    raise NameError, "Could not find the path to the resources!"
