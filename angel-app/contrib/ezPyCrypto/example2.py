#!/usr/bin/env python

"""
example2.py

Create and save public and private keys
"""

import ezPyCrypto

# Create a key object
k = ezPyCrypto.key()

# Export private and public/private keys
publicKey = k.exportKey()
publicAndPrivateKey = k.exportKeyPrivate()

# Save these to disk
fd = open("ex_mykey.pub", "w")
fd.write(publicKey)
fd.close()

fd = open("ex_mykey.priv", "w")
fd.write(publicAndPrivateKey)
fd.close()

print "Keys successfully exported to ex_mykey.pub and ex_mykey.priv"
print "These keys will be used in later examples"

