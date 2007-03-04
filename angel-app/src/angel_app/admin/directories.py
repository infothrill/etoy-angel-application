"""
Utilities for creating the default repository directory layout.
"""

import os
from angel_app.config import config

AngelConfig = config.getConfig()

def conditionalCreate(path):
    if not os.path.exists(path):
        os.mkdir(path)
    elif not os.path.isdir(path):
        raise "Filesystem entry '%s' occupied, cannot create directory here." % path
        
def makeDirectories():
    conditionalCreate(AngelConfig.get("common", "angelhome"))
    conditionalCreate(AngelConfig.get("common", "repository"))
    conditionalCreate(AngelConfig.get("common", "keyring"))
    conditionalCreate(AngelConfig.get("common", "logdir"))
    conditionalCreate(os.path.join(AngelConfig.get("common","angelhome"), "tmp"))
