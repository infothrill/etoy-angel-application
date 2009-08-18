"""
This module contains version information, only relevant when packaging
and releasing a public build.
This file must be patched during the build process to set correct
version information.
"""

def getVersionString():
    """
    Returns a string containing the version identifier. If no version is set,
    this will return the string '221e'.
    """
    # NOTE: VERSION and BUILD_ID number MUST be set during packaging! (most simply through sed/search+replace)
    v = "#!#VERSION#!#"
    if v[0] == "#":
        return "221e" # nicer looking fallback value
    return v

def getBuildString():
    # NOTE: VERSION and BUILD_ID number MUST be set during packaging! (most simply through sed/search+replace)
    b = "#!#BUILD_ID#!#"
    return b

def getPythonVersionString():
    import platform
    return platform.python_version()

def getTwistedVersionString():
    from twisted._version import version
    return version