from angel_app.maintainer.client import inspectResource
from angel_app.maintainer.setup import setupDefaultPeers

setupDefaultPeers()

from config.common import rootDir

from os import walk
import os.path 
for item in walk(rootDir): 
    print "walking: " + item[0]
    inspectResource(item[0])
    for fileItem in item[2]:
        inspectResource(os.path.join(item[0], fileItem))

