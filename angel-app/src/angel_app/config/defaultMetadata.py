from angel_app import elements
from angel_app.resource.local.internal import util
defaultMetaData = {
                   elements.Revision           : lambda x: "0",
                   elements.Encrypted          : lambda x: "0",
                   elements.PublicKeyString    : lambda x: x.parent() and x.parent().publicKeyString() or "",
                   elements.ContentSignature   : lambda x: "",
                   elements.ResourceID         : lambda x: util.makeResourceID(x.relativePath()),
                   elements.Clones             : lambda x: []
                   }