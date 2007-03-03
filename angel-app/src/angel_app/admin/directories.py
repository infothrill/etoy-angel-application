"""
Utilities for creating the default repository directory layout.
"""

import os
from angel_app.config import config
from twisted.python.filepath import FilePath

AngelConfig = config.getConfig()

def conditionalCreate(path):
    rr = FilePath(path)
    if not rr.exists():
        os.mkdir(repository)
        
def makeDirectories():
    conditionalCreate(AngelConfig.get("common", "angelhome"))
    conditionalCreate(AngelConfig.get("common", "repository"))