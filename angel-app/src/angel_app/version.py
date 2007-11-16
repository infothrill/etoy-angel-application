"""
This module contains version information, only relevant when packaging
and releasing a public build.
This file must be patched during the build process to set correct
version information.
"""

def getVersionString():
    # NOTE: VERSION and BUILD_ID number MUST be set during packaging! (most simply through sed/search+replace)
    v = "#!#VERSION#!#"
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