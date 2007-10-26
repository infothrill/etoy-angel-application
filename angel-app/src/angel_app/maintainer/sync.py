
def syncContents(resource, referenceClone):
    """
    Synchronize the contents of the resource from the reference clone.
    """
    path = resource.fp.path
    

    if referenceClone.isCollection():
        # handle directory
        
        if resource.exists() and not resource.isCollection():
            os.remove(path)
        if not resource.exists():
            os.mkdir(path)
    
    else:
        # handle file
        readResponseIntoFile(resource, referenceClone)
        

def readResponseIntoFile(resource, referenceClone):
    t = angel_app.singlefiletransaction.SingleFileTransaction()
    bufsize = 8192 # 8 kB
    safe = t.open(resource.fp.path, 'wb')
    readstream = referenceClone.open()
    EOF = False
    while not EOF:
        data = readstream.read(bufsize)
        if len(data) == 0:
            EOF = True
        else:
            safe.write(data)
    t.commit() # TODO: only commit if the download worked!
    

def updateMetaData(resource, referenceClone):    
    # then update the metadata
    keysToBeUpdated = elements.signedKeys + [elements.MetaDataSignature]
    
    for key in keysToBeUpdated:
        pp = referenceClone.getProperty(key)
        resource.deadProperties().set(pp)
        
    
def sync(resource, referenceClone):
    """
    Update the resource from the reference clone, by updating the contents,
    then the metadata, in that order.
    
    @return whether the update succeeded.
    """ 
    syncContents(resource, referenceClone)
    updateMetaData(resource, referenceClone)  