from angel_app.maintainer.client import inspectResource
from angel_app.maintainer.setup import setupDefaultPeers
from angel_app.graph import graphWalker

setupDefaultPeers()

from config.common import rootDir

            
if __name__ == "__main__":
    inspectResource(rootDir)
    #walkTree()