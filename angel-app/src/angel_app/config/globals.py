"""

Globals for the angel-app. This contains values that influence the way
angel-app works, but which are _not_ user-configurable. They may be dynamic!

"""


"""
The name of the currently running application. This must be set during bootstrapping!
(e.g. to presenter/provider ...) It is currently used for logging and pidfiles.
"""

appname = "defaultAppname"
