"""
Utility script to force inspect a local resource
"""

import angel_app.resource.remote.client

import angel_app.log
angel_app.log.setup()
angel_app.log.enableHandler('console')
angel_app.log.getReady()

from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common", "repository")
            
if __name__ == "__main__":
    angel_app.resource.remote.client.inspectResource(repository + "/MISSION ETERNITY")
