"""

Defaults for the angel-app. This contains values/methods that influence the way
angel-app works, but which are _not_ user-configurable. They may be dynamic though!

"""


"""
The name of the currently running application. This must be set during bootstrapping!
(e.g. to presenter/provider ...) It is currently used for logging and pidfiles.
"""

appname = "defaultAppname"

from angel_app.config.config import getConfig

angelConfig = getConfig() # todo: command line parameter?

def getAngelHomePath(): # TODO: remove this function
    print "angel_app/config/defaults.py:getAngelHomePath() DEPRECATED!"
    angelhome = angelConfig.get("common", "angelhome")
    pass
