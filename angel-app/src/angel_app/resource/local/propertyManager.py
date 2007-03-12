"""
Provide a Mapping from XML-elements to xattr keys.
Hanlde initialization of attributes with default values.
"""

# a map from xml-elements corresponding to metadata fields to functions taking a resource 
# and returning appropriate values for those metadata fields
defaultMetaData = {
                   elements.Revision           : lambda x: "0",
                   elements.Encrypted          : lambda x: "0",
                   elements.PublicKeyString    : lambda x: x.parent() and x.parent().publicKeyString() or "",
                   elements.ContentSignature   : lambda x: "",
                   elements.ResourceID         : lambda x: util.getResourceIDFromParentLinks(x),
                   elements.Clones             : lambda x: []
                   }

class PropertyManagerMixin:
    
    def __init__(self):

        self.defaultValues = dict(defaultMetaData.values())

    def get(self, element):
        
        # the property is available in the property store
        if self.deadProperties().contains(element.qname()):
            return self.getAsString(element.qname())
        
        # the property is not available in the property store,
        # but we have an initializer   
        if element in self.defaultValues.keys():
            self.set(element(
                              self.defaultValues(element)(self)
                              ))
            
            return self.getAsString(element.qname())
        
        else:
            raise KeyError("Attribute for element %s not found on resource %s." % (`element`, self.fp.path))
    
    def getAsString(self, element):
        return "".join([
                        str(child) for child in 
                       self.deadProperties().get(element.qname()).children
                                                 ])
        
    def set(self, element, value):
        self.deadProperties().set(element)
            
            