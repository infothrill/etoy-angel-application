"""
Utilities for creating the default repository directory layout.
"""

import os
import shutil

from angel_app.config import config

AngelConfig = config.getConfig()

def conditionalCreate(path):
    if not os.path.exists(path):
        os.mkdir(path)
    elif not os.path.isdir(path):
        raise Exception, "Filesystem entry '%s' occupied, cannot create directory here." % path
        
def makeDirectories():
    conditionalCreate(AngelConfig.get("common", "angelhome"))
    conditionalCreate(AngelConfig.get("common", "repository"))
    conditionalCreate(AngelConfig.get("common", "keyring"))
    conditionalCreate(AngelConfig.get("common", "logdir"))
    conditionalCreate(os.path.join(AngelConfig.get("common","angelhome"), "tmp"))
    
def removeDirectory(name):
    """
    High level method for removing core angel-app directories
    
    @param name: string specyfiyng the directory to remove 
    """
    dirs = {
            'repository' : AngelConfig.get("common", "repository")
            }
    shutil.rmtree(dirs[name], ignore_errors = False)

