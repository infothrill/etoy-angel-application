#!/usr/bin/env python

"""
example5.py

Import a private key, and sign a document
"""

import ezPyCrypto

# Create a document
fd = open("ex_signeddoc.txt", "w")
fd.write("Signed document\n")
fd.write("I promise to sell you my left kidney\n")
fd.write("Send the surgeons tomorrow!.\n")
fd.close()

# Read in a private key
fd = open("ex_mykey.priv")
pubprivkey = fd.read()
fd.close()

# Create a key object, and auto-import private key
k = ezPyCrypto.key(pubprivkey)

# Read in the document that needs signing
fd = open("ex_signeddoc.txt")
doctxt = fd.read()
fd.close()

# Sign the string
sig = k.signString(doctxt)

# Write out the signature
fd = open("ex_signeddoc.txt.sig", "w")
fd.write(sig)
fd.close()

print "Document created as ex_signeddoc.txt"
print "Signature written to ex_signeddoc.txt.sig"
print "This signature will be verified in example6"
