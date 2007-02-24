"""
Utility script to force resigning the repository root
"""

import angel_app.resource.local.internal.resource
from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common", "repository")
            
if __name__ == "__main__":
	r = angel_app.resource.local.internal.resource.Crypto(repository)
	r.sign()
	r.seal()


