from angel_app.maintainer.client import inspectResource
from angel_app.maintainer.setup import setupDefaultPeers

setupDefaultPeers()

from config.common import rootDir

from os import walk
import os.path 
for directory, subDirectories, fileNames in walk(rootDir): 
    print "walking: " + directory
    inspectResource(directory)
    for name in fileNames:
        inspectResource(os.path.join(directory, name))

