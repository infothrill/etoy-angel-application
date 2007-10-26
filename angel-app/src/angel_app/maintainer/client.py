from angel_app import elements
from angel_app.config import config
from angel_app.log import getLogger
from angel_app.maintainer import sync
from angel_app.maintainer import update
from angel_app.resource.remote.clone import clonesToElement
import angel_app.singlefiletransaction
import os
import random

log = getLogger(__name__)

AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")


def inspectResource(af):

    update.updateResource(af)
    sync.broadCastAddress(af)
    
